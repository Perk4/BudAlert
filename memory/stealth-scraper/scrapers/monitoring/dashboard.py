#!/usr/bin/env python3
"""
Unified Dashboard Data Aggregator for Stealth Scraper

Aggregates status and metrics from all store scrapers to provide
a unified view of the entire scraping infrastructure.
"""

import json
import os
import glob
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import sqlite3


@dataclass
class StoreStatus:
    """Status information for a single store"""
    store_name: str
    platform: str
    is_active: bool
    last_successful_run: Optional[datetime.datetime]
    last_error: Optional[str]
    products_extracted: int
    success_rate_24h: float
    avg_latency_ms: int
    consecutive_failures: int


class DashboardAggregator:
    """Main dashboard data aggregation class"""
    
    def __init__(self, scrapers_dir: str = None):
        self.scrapers_dir = scrapers_dir or os.path.join(os.path.dirname(__file__), '..')
        self.monitoring_dir = os.path.join(self.scrapers_dir, 'monitoring')
        self.logs_dir = os.path.join(self.monitoring_dir, 'logs')
        self.db_path = os.path.join(self.monitoring_dir, 'dashboard.db')
        
        # Ensure directories exist
        os.makedirs(self.logs_dir, exist_ok=True)
        self._init_database()
        
        # Store configuration based on project documentation
        self.stores_config = {
            # Production stores (Phase 5)
            'housing-works': {'platform': 'Blaze', 'active': True},
            'conbud': {'platform': 'Dutchie Embed', 'active': True},
            'torches': {'platform': 'Joint Ecommerce', 'active': True},
            'stoops': {'platform': 'Joint Ecommerce', 'active': True},
            'alta': {'platform': 'Joint Ecommerce', 'active': False},
            
            # Easy custom sites (Phase 6A)
            'smacked-village': {'platform': 'Custom Easy', 'active': False},
            'yerba-buena': {'platform': 'Custom Easy', 'active': False},
            'terp-bros': {'platform': 'Custom Easy', 'active': False},
            'flynnstoned': {'platform': 'Custom Easy', 'active': False},
            'happy-munkey': {'platform': 'Custom Easy', 'active': False},
            
            # Medium custom sites (Phase 6B)
            'travel-agency': {'platform': 'Custom Medium', 'active': False},
            'gotham': {'platform': 'Custom Medium', 'active': False},
            'dazed': {'platform': 'Custom Medium', 'active': False},
            'green-apple': {'platform': 'Custom Medium', 'active': False},
            'chelsea-cannabis': {'platform': 'Custom Medium', 'active': False},
            'verilife': {'platform': 'Custom Medium', 'active': False},
            
            # LeafBridge platform (Phase 6C)
            'qube': {'platform': 'LeafBridge', 'active': False},
            
            # Hard targets (Phase 6F)
            'rise': {'platform': 'Jane + CF', 'active': False},
            'curaleaf': {'platform': 'MSO + CF', 'active': False}
        }
    
    def _init_database(self):
        """Initialize SQLite database for storing metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS scrape_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_name TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN NOT NULL,
                    products_extracted INTEGER DEFAULT 0,
                    latency_ms INTEGER DEFAULT 0,
                    error_message TEXT,
                    metadata TEXT
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_store_timestamp 
                ON scrape_runs(store_name, timestamp)
            ''')
    
    def record_scrape_result(self, store_name: str, success: bool, 
                           products: int = 0, latency_ms: int = 0, 
                           error: str = None, metadata: Dict = None):
        """Record the result of a scraping run"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO scrape_runs 
                (store_name, success, products_extracted, latency_ms, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (store_name, success, products, latency_ms, error, 
                  json.dumps(metadata) if metadata else None))
    
    def get_store_status(self, store_name: str) -> StoreStatus:
        """Get current status for a specific store"""
        
        # Get basic config
        config = self.stores_config.get(store_name, {})
        platform = config.get('platform', 'Unknown')
        is_active = config.get('active', False)
        
        # Query database for recent metrics
        with sqlite3.connect(self.db_path) as conn:
            # Last successful run
            last_success_row = conn.execute('''
                SELECT timestamp, products_extracted FROM scrape_runs 
                WHERE store_name = ? AND success = 1 
                ORDER BY timestamp DESC LIMIT 1
            ''', (store_name,)).fetchone()
            
            last_successful_run = None
            products_extracted = 0
            if last_success_row:
                last_successful_run = datetime.datetime.fromisoformat(last_success_row[0])
                products_extracted = last_success_row[1]
            
            # Last error
            last_error_row = conn.execute('''
                SELECT error_message FROM scrape_runs 
                WHERE store_name = ? AND success = 0 
                ORDER BY timestamp DESC LIMIT 1
            ''', (store_name,)).fetchone()
            
            last_error = last_error_row[0] if last_error_row else None
            
            # 24h success rate
            cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
            success_stats = conn.execute('''
                SELECT 
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                    COUNT(*) as total
                FROM scrape_runs 
                WHERE store_name = ? AND timestamp > ?
            ''', (store_name, cutoff.isoformat())).fetchone()
            
            success_rate_24h = 0.0
            if success_stats and success_stats[1] > 0:
                success_rate_24h = (success_stats[0] / success_stats[1]) * 100
            
            # Average latency (successful runs only)
            avg_latency = conn.execute('''
                SELECT AVG(latency_ms) FROM scrape_runs 
                WHERE store_name = ? AND success = 1 AND timestamp > ?
            ''', (store_name, cutoff.isoformat())).fetchone()
            
            avg_latency_ms = int(avg_latency[0]) if avg_latency and avg_latency[0] else 0
            
            # Consecutive failures
            consecutive_failures = 0
            recent_runs = conn.execute('''
                SELECT success FROM scrape_runs 
                WHERE store_name = ? 
                ORDER BY timestamp DESC LIMIT 10
            ''', (store_name,)).fetchall()
            
            for run in recent_runs:
                if run[0]:  # success
                    break
                consecutive_failures += 1
        
        return StoreStatus(
            store_name=store_name,
            platform=platform,
            is_active=is_active,
            last_successful_run=last_successful_run,
            last_error=last_error,
            products_extracted=products_extracted,
            success_rate_24h=success_rate_24h,
            avg_latency_ms=avg_latency_ms,
            consecutive_failures=consecutive_failures
        )
    
    def get_all_stores_status(self) -> List[StoreStatus]:
        """Get status for all configured stores"""
        return [self.get_store_status(store) for store in self.stores_config.keys()]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Generate complete dashboard data"""
        stores = self.get_all_stores_status()
        
        # Calculate overall metrics
        active_stores = [s for s in stores if s.is_active]
        total_products = sum(s.products_extracted for s in active_stores)
        
        # Overall success rate
        total_success_rate = 0
        if active_stores:
            total_success_rate = sum(s.success_rate_24h for s in active_stores) / len(active_stores)
        
        # Health status
        healthy_stores = len([s for s in active_stores if s.success_rate_24h >= 80])
        warning_stores = len([s for s in active_stores if 50 <= s.success_rate_24h < 80])
        critical_stores = len([s for s in active_stores if s.success_rate_24h < 50])
        
        return {
            'timestamp': datetime.datetime.now().isoformat(),
            'summary': {
                'total_stores': len(self.stores_config),
                'active_stores': len(active_stores),
                'total_products_extracted': total_products,
                'overall_success_rate': round(total_success_rate, 1),
                'healthy_stores': healthy_stores,
                'warning_stores': warning_stores,
                'critical_stores': critical_stores
            },
            'stores': [asdict(store) for store in stores],
            'by_platform': self._group_by_platform(stores)
        }
    
    def _group_by_platform(self, stores: List[StoreStatus]) -> Dict[str, Any]:
        """Group stores by platform for platform-level insights"""
        platforms = {}
        
        for store in stores:
            if store.platform not in platforms:
                platforms[store.platform] = {
                    'stores': [],
                    'active_count': 0,
                    'total_products': 0,
                    'avg_success_rate': 0,
                    'avg_latency': 0
                }
            
            platform_data = platforms[store.platform]
            platform_data['stores'].append(store.store_name)
            
            if store.is_active:
                platform_data['active_count'] += 1
                platform_data['total_products'] += store.products_extracted
        
        # Calculate averages
        for platform, data in platforms.items():
            active_stores_for_platform = [s for s in stores 
                                        if s.platform == platform and s.is_active]
            if active_stores_for_platform:
                data['avg_success_rate'] = sum(s.success_rate_24h for s in active_stores_for_platform) / len(active_stores_for_platform)
                data['avg_latency'] = sum(s.avg_latency_ms for s in active_stores_for_platform) / len(active_stores_for_platform)
        
        return platforms
    
    def save_dashboard_snapshot(self) -> str:
        """Save current dashboard state to JSON file"""
        data = self.get_dashboard_data()
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(self.logs_dir, f'dashboard_{timestamp}.json')
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return filepath


def main():
    """CLI interface for dashboard operations"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stealth Scraper Dashboard')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--save', action='store_true', help='Save snapshot to file')
    parser.add_argument('--store', help='Show specific store status')
    
    args = parser.parse_args()
    
    dashboard = DashboardAggregator()
    
    if args.store:
        status = dashboard.get_store_status(args.store)
        if args.json:
            print(json.dumps(asdict(status), indent=2, default=str))
        else:
            print(f"Store: {status.store_name}")
            print(f"Platform: {status.platform}")
            print(f"Active: {status.is_active}")
            print(f"Last Success: {status.last_successful_run}")
            print(f"Products: {status.products_extracted}")
            print(f"Success Rate (24h): {status.success_rate_24h:.1f}%")
            print(f"Avg Latency: {status.avg_latency_ms}ms")
            print(f"Consecutive Failures: {status.consecutive_failures}")
    else:
        data = dashboard.get_dashboard_data()
        
        if args.json:
            print(json.dumps(data, indent=2, default=str))
        else:
            summary = data['summary']
            print("Stealth Scraper Dashboard")
            print("=" * 40)
            print(f"Total Stores: {summary['total_stores']}")
            print(f"Active Stores: {summary['active_stores']}")
            print(f"Products Extracted: {summary['total_products_extracted']}")
            print(f"Overall Success Rate: {summary['overall_success_rate']}%")
            print(f"Health: {summary['healthy_stores']} healthy, {summary['warning_stores']} warning, {summary['critical_stores']} critical")
    
    if args.save:
        filepath = dashboard.save_dashboard_snapshot()
        print(f"Snapshot saved: {filepath}")


if __name__ == '__main__':
    main()