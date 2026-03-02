#!/usr/bin/env python3
"""
Metrics Calculator for Stealth Scraper

Calculates key performance metrics and trends for the scraping infrastructure.
Provides analytics beyond basic status reporting.
"""

import json
import sqlite3
import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics
import os
from dashboard import DashboardAggregator


@dataclass
class MetricTrend:
    """Represents a metric trend over time"""
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: str  # 'up', 'down', 'stable'
    
    
@dataclass  
class StoreMetrics:
    """Detailed metrics for a single store"""
    store_name: str
    platform: str
    
    # Performance metrics
    success_rate_1h: float
    success_rate_24h: float
    success_rate_7d: float
    success_rate_trend: MetricTrend
    
    # Latency metrics
    avg_latency_ms: int
    p95_latency_ms: int
    latency_trend: MetricTrend
    
    # Volume metrics
    products_extracted_24h: int
    products_extracted_7d: int
    extraction_rate_per_hour: float
    
    # Reliability metrics
    uptime_percentage: float
    consecutive_failures: int
    time_since_last_success_hours: Optional[float]
    error_rate_24h: float
    
    # Cost/efficiency
    runs_per_day: int
    cost_per_product: float  # Estimated based on tier
    

class MetricsCalculator:
    """Main metrics calculation engine"""
    
    def __init__(self, scrapers_dir: str = None):
        self.dashboard = DashboardAggregator(scrapers_dir)
        self.db_path = self.dashboard.db_path
        
        # Cost estimates per platform (monthly)
        self.platform_costs = {
            'Blaze': 5,              # Tier 2
            'Dutchie Embed': 5,      # Tier 2
            'Joint Ecommerce': 5,    # Tier 2
            'Custom Easy': 5,        # Tier 2
            'Custom Medium': 15,     # Tier 2 + more complexity
            'LeafBridge': 10,        # Tier 2
            'Jane + CF': 25,         # Tier 1
            'MSO + CF': 25,          # Tier 1
        }
    
    def calculate_store_metrics(self, store_name: str, 
                              reference_date: datetime.datetime = None) -> StoreMetrics:
        """Calculate comprehensive metrics for a specific store"""
        
        if reference_date is None:
            reference_date = datetime.datetime.now()
            
        # Get basic store info
        status = self.dashboard.get_store_status(store_name)
        platform = status.platform
        
        with sqlite3.connect(self.db_path) as conn:
            # Success rates for different time windows
            success_rate_1h = self._get_success_rate(conn, store_name, reference_date, hours=1)
            success_rate_24h = self._get_success_rate(conn, store_name, reference_date, hours=24)
            success_rate_7d = self._get_success_rate(conn, store_name, reference_date, hours=24*7)
            
            # Success rate trend (24h vs previous 24h)
            prev_24h_rate = self._get_success_rate(
                conn, store_name, reference_date - datetime.timedelta(hours=24), hours=24)
            success_rate_trend = self._calculate_trend(success_rate_24h, prev_24h_rate)
            
            # Latency metrics
            latency_stats = self._get_latency_stats(conn, store_name, reference_date)
            avg_latency_ms = int(latency_stats['avg']) if latency_stats['avg'] else 0
            p95_latency_ms = int(latency_stats['p95']) if latency_stats['p95'] else 0
            
            # Latency trend
            prev_latency = self._get_latency_stats(
                conn, store_name, reference_date - datetime.timedelta(hours=24))
            prev_avg_latency = prev_latency['avg'] if prev_latency['avg'] else 0
            latency_trend = self._calculate_trend(avg_latency_ms, prev_avg_latency, reverse=True)
            
            # Volume metrics
            products_24h = self._get_products_extracted(conn, store_name, reference_date, hours=24)
            products_7d = self._get_products_extracted(conn, store_name, reference_date, hours=24*7)
            
            # Calculate extraction rate per hour
            total_runs_24h = self._get_run_count(conn, store_name, reference_date, hours=24)
            extraction_rate = products_24h / 24 if products_24h > 0 else 0
            
            # Reliability metrics
            uptime_percentage = self._calculate_uptime(conn, store_name, reference_date)
            consecutive_failures = status.consecutive_failures
            
            # Time since last success
            time_since_success = None
            if status.last_successful_run:
                time_since_success = (reference_date - status.last_successful_run).total_seconds() / 3600
            
            # Error rate
            error_rate_24h = 100 - success_rate_24h
            
            # Cost/efficiency
            runs_per_day = self._get_run_count(conn, store_name, reference_date, hours=24)
            monthly_cost = self.platform_costs.get(platform, 10)
            cost_per_product = (monthly_cost / 30) / max(products_24h, 1)  # Daily cost / daily products
            
        return StoreMetrics(
            store_name=store_name,
            platform=platform,
            success_rate_1h=success_rate_1h,
            success_rate_24h=success_rate_24h,
            success_rate_7d=success_rate_7d,
            success_rate_trend=success_rate_trend,
            avg_latency_ms=avg_latency_ms,
            p95_latency_ms=p95_latency_ms,
            latency_trend=latency_trend,
            products_extracted_24h=products_24h,
            products_extracted_7d=products_7d,
            extraction_rate_per_hour=extraction_rate,
            uptime_percentage=uptime_percentage,
            consecutive_failures=consecutive_failures,
            time_since_last_success_hours=time_since_success,
            error_rate_24h=error_rate_24h,
            runs_per_day=runs_per_day,
            cost_per_product=cost_per_product
        )
    
    def get_infrastructure_metrics(self, reference_date: datetime.datetime = None) -> Dict[str, Any]:
        """Calculate infrastructure-wide metrics"""
        
        if reference_date is None:
            reference_date = datetime.datetime.now()
            
        # Get metrics for all stores
        all_stores = list(self.dashboard.stores_config.keys())
        store_metrics = [self.calculate_store_metrics(store, reference_date) 
                        for store in all_stores]
        
        # Infrastructure-level calculations
        active_stores = [m for m in store_metrics 
                        if self.dashboard.stores_config[m.store_name]['active']]
        
        if not active_stores:
            return self._empty_infrastructure_metrics(reference_date)
            
        # Overall performance
        overall_success_rate = statistics.mean([m.success_rate_24h for m in active_stores])
        overall_uptime = statistics.mean([m.uptime_percentage for m in active_stores])
        
        # Volume metrics
        total_products_24h = sum(m.products_extracted_24h for m in active_stores)
        total_products_7d = sum(m.products_extracted_7d for m in active_stores)
        
        # Latency stats
        avg_latency = statistics.mean([m.avg_latency_ms for m in active_stores if m.avg_latency_ms > 0])
        
        # Cost analysis
        total_daily_cost = sum(self.platform_costs.get(m.platform, 10) / 30 for m in active_stores)
        cost_per_product_overall = total_daily_cost / max(total_products_24h, 1)
        
        # Health distribution
        healthy_count = len([m for m in active_stores if m.success_rate_24h >= 80])
        warning_count = len([m for m in active_stores if 50 <= m.success_rate_24h < 80])
        critical_count = len([m for m in active_stores if m.success_rate_24h < 50])
        
        # Platform breakdown
        platform_breakdown = self._calculate_platform_metrics(active_stores)
        
        return {
            'timestamp': reference_date.isoformat(),
            'infrastructure_health': {
                'overall_success_rate': round(overall_success_rate, 2),
                'overall_uptime': round(overall_uptime, 2),
                'healthy_stores': healthy_count,
                'warning_stores': warning_count,
                'critical_stores': critical_count,
                'total_active_stores': len(active_stores)
            },
            'volume_metrics': {
                'products_extracted_24h': total_products_24h,
                'products_extracted_7d': total_products_7d,
                'extraction_rate_per_hour': total_products_24h / 24,
                'avg_products_per_store': total_products_24h / len(active_stores)
            },
            'performance_metrics': {
                'avg_latency_ms': round(avg_latency, 0) if avg_latency else 0,
                'stores_with_failures': len([m for m in active_stores if m.consecutive_failures > 0]),
                'max_consecutive_failures': max([m.consecutive_failures for m in active_stores], default=0)
            },
            'cost_metrics': {
                'total_daily_cost_usd': round(total_daily_cost, 2),
                'cost_per_product_usd': round(cost_per_product_overall, 4),
                'estimated_monthly_cost_usd': round(total_daily_cost * 30, 2)
            },
            'platform_breakdown': platform_breakdown,
            'store_details': [asdict(m) for m in store_metrics]
        }
    
    def _get_success_rate(self, conn, store_name: str, reference_date: datetime.datetime, 
                         hours: int) -> float:
        """Calculate success rate for a time window"""
        cutoff = reference_date - datetime.timedelta(hours=hours)
        
        result = conn.execute('''
            SELECT 
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                COUNT(*) as total
            FROM scrape_runs 
            WHERE store_name = ? AND timestamp > ? AND timestamp <= ?
        ''', (store_name, cutoff.isoformat(), reference_date.isoformat())).fetchone()
        
        if result and result[1] > 0:
            return (result[0] / result[1]) * 100
        return 0.0
    
    def _get_latency_stats(self, conn, store_name: str, reference_date: datetime.datetime, 
                          hours: int = 24) -> Dict[str, Optional[float]]:
        """Get latency statistics for successful runs"""
        cutoff = reference_date - datetime.timedelta(hours=hours)
        
        latencies = conn.execute('''
            SELECT latency_ms FROM scrape_runs 
            WHERE store_name = ? AND success = 1 
            AND timestamp > ? AND timestamp <= ?
            AND latency_ms > 0
        ''', (store_name, cutoff.isoformat(), reference_date.isoformat())).fetchall()
        
        if not latencies:
            return {'avg': None, 'p95': None}
            
        values = [row[0] for row in latencies]
        return {
            'avg': statistics.mean(values),
            'p95': statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values)
        }
    
    def _get_products_extracted(self, conn, store_name: str, reference_date: datetime.datetime, 
                               hours: int) -> int:
        """Get total products extracted in time window"""
        cutoff = reference_date - datetime.timedelta(hours=hours)
        
        result = conn.execute('''
            SELECT SUM(products_extracted) FROM scrape_runs 
            WHERE store_name = ? AND success = 1 
            AND timestamp > ? AND timestamp <= ?
        ''', (store_name, cutoff.isoformat(), reference_date.isoformat())).fetchone()
        
        return result[0] if result and result[0] else 0
    
    def _get_run_count(self, conn, store_name: str, reference_date: datetime.datetime, 
                      hours: int) -> int:
        """Get total number of runs in time window"""
        cutoff = reference_date - datetime.timedelta(hours=hours)
        
        result = conn.execute('''
            SELECT COUNT(*) FROM scrape_runs 
            WHERE store_name = ? AND timestamp > ? AND timestamp <= ?
        ''', (store_name, cutoff.isoformat(), reference_date.isoformat())).fetchone()
        
        return result[0] if result else 0
    
    def _calculate_uptime(self, conn, store_name: str, reference_date: datetime.datetime, 
                         hours: int = 24) -> float:
        """Calculate uptime percentage based on successful runs"""
        # This is simplified - in reality you'd want to consider expected run frequency
        success_rate = self._get_success_rate(conn, store_name, reference_date, hours)
        return success_rate  # For now, uptime = success rate
    
    def _calculate_trend(self, current: float, previous: float, reverse: bool = False) -> MetricTrend:
        """Calculate trend direction and percentage change"""
        if previous == 0:
            change_percent = 100 if current > 0 else 0
            direction = 'up' if current > 0 else 'stable'
        else:
            change_percent = ((current - previous) / previous) * 100
            
            if abs(change_percent) < 5:  # Within 5% is considered stable
                direction = 'stable'
            elif change_percent > 0:
                direction = 'down' if reverse else 'up'
            else:
                direction = 'up' if reverse else 'down'
        
        return MetricTrend(
            current_value=current,
            previous_value=previous,
            change_percent=change_percent,
            trend_direction=direction
        )
    
    def _calculate_platform_metrics(self, store_metrics: List[StoreMetrics]) -> Dict[str, Any]:
        """Calculate per-platform performance metrics"""
        platforms = {}
        
        for metric in store_metrics:
            platform = metric.platform
            if platform not in platforms:
                platforms[platform] = {
                    'stores': [],
                    'success_rates': [],
                    'latencies': [],
                    'products': 0,
                    'costs': 0
                }
            
            platforms[platform]['stores'].append(metric.store_name)
            platforms[platform]['success_rates'].append(metric.success_rate_24h)
            if metric.avg_latency_ms > 0:
                platforms[platform]['latencies'].append(metric.avg_latency_ms)
            platforms[platform]['products'] += metric.products_extracted_24h
            platforms[platform]['costs'] += self.platform_costs.get(platform, 10) / 30
        
        # Calculate platform averages
        for platform, data in platforms.items():
            data['avg_success_rate'] = statistics.mean(data['success_rates']) if data['success_rates'] else 0
            data['avg_latency'] = statistics.mean(data['latencies']) if data['latencies'] else 0
            data['store_count'] = len(data['stores'])
            data['cost_per_product'] = data['costs'] / max(data['products'], 1)
            
            # Clean up intermediate data
            del data['success_rates']
            del data['latencies']
        
        return platforms
    
    def _empty_infrastructure_metrics(self, reference_date: datetime.datetime) -> Dict[str, Any]:
        """Return empty metrics structure when no active stores"""
        return {
            'timestamp': reference_date.isoformat(),
            'infrastructure_health': {
                'overall_success_rate': 0,
                'overall_uptime': 0,
                'healthy_stores': 0,
                'warning_stores': 0,
                'critical_stores': 0,
                'total_active_stores': 0
            },
            'volume_metrics': {
                'products_extracted_24h': 0,
                'products_extracted_7d': 0,
                'extraction_rate_per_hour': 0,
                'avg_products_per_store': 0
            },
            'performance_metrics': {
                'avg_latency_ms': 0,
                'stores_with_failures': 0,
                'max_consecutive_failures': 0
            },
            'cost_metrics': {
                'total_daily_cost_usd': 0,
                'cost_per_product_usd': 0,
                'estimated_monthly_cost_usd': 0
            },
            'platform_breakdown': {},
            'store_details': []
        }


def main():
    """CLI interface for metrics operations"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stealth Scraper Metrics Calculator')
    parser.add_argument('--store', help='Calculate metrics for specific store')
    parser.add_argument('--infrastructure', action='store_true', help='Show infrastructure-wide metrics')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    calculator = MetricsCalculator()
    
    if args.store:
        metrics = calculator.calculate_store_metrics(args.store)
        if args.json:
            print(json.dumps(asdict(metrics), indent=2, default=str))
        else:
            print(f"Metrics for {metrics.store_name} ({metrics.platform})")
            print("=" * 50)
            print(f"Success Rate: {metrics.success_rate_24h:.1f}% (24h)")
            print(f"Products Extracted: {metrics.products_extracted_24h} (24h)")
            print(f"Average Latency: {metrics.avg_latency_ms}ms")
            print(f"Uptime: {metrics.uptime_percentage:.1f}%")
            print(f"Cost per Product: ${metrics.cost_per_product:.4f}")
    
    elif args.infrastructure:
        metrics = calculator.get_infrastructure_metrics()
        if args.json:
            print(json.dumps(metrics, indent=2, default=str))
        else:
            health = metrics['infrastructure_health']
            volume = metrics['volume_metrics']
            cost = metrics['cost_metrics']
            
            print("Infrastructure Metrics")
            print("=" * 40)
            print(f"Overall Success Rate: {health['overall_success_rate']:.1f}%")
            print(f"Active Stores: {health['total_active_stores']}")
            print(f"Products Extracted (24h): {volume['products_extracted_24h']}")
            print(f"Daily Cost: ${cost['total_daily_cost_usd']:.2f}")
            print(f"Cost per Product: ${cost['cost_per_product_usd']:.4f}")


if __name__ == '__main__':
    main()