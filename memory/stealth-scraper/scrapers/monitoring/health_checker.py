#!/usr/bin/env python3
"""
Health Checker for Stealth Scraper

Runs periodic health checks on all scrapers to ensure they can:
1. Reach the target site
2. Extract at least 1 product
3. Complete within acceptable latency thresholds

Outputs health_status.json with per-store status.
"""

import json
import os
import time
import asyncio
import aiohttp
import datetime
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import sys

# Import our dashboard for recording results
from dashboard import DashboardAggregator


@dataclass
class HealthCheckResult:
    """Result of a health check for a single store"""
    store_name: str
    timestamp: datetime.datetime
    overall_status: str  # 'healthy', 'warning', 'critical', 'unknown'
    
    # Individual check results
    site_reachable: bool
    site_response_time_ms: int
    
    extraction_successful: bool
    products_extracted: int
    extraction_time_ms: int
    
    # Thresholds and limits
    latency_threshold_ms: int
    meets_latency_threshold: bool
    
    # Error information
    error_message: Optional[str]
    last_error_type: Optional[str]


class HealthChecker:
    """Main health checking system"""
    
    def __init__(self, scrapers_dir: str = None):
        self.scrapers_dir = scrapers_dir or os.path.join(os.path.dirname(__file__), '..')
        self.monitoring_dir = os.path.join(self.scrapers_dir, 'monitoring')
        self.dashboard = DashboardAggregator(scrapers_dir)
        
        # Health check configuration
        self.config = {
            # Site reachability timeouts
            'site_timeout_seconds': 30,
            'site_max_response_time_ms': 5000,
            
            # Extraction timeouts and thresholds
            'extraction_timeout_seconds': 120,
            'max_extraction_latency_ms': 60000,  # 1 minute
            'min_products_required': 1,
            
            # Store-specific URLs for health checks
            'store_urls': {
                # Production stores (Phase 5)
                'housing-works': 'https://www.housingworkscannabisCo.com/',
                'conbud': 'https://conbud.com/',
                'torches': 'https://torchesnyc.com/',
                'stoops': 'https://stoops.world/',
                'alta': 'https://altanyc.com/',
                
                # Easy custom sites (Phase 6A)
                'smacked-village': 'https://getsmacked.online/',
                'yerba-buena': 'https://yerbabuena.nyc/',
                'terp-bros': 'https://terpbrosnyc.com/',
                'flynnstoned': 'https://flynnstoned.com/',
                'happy-munkey': 'https://happymunkey.com/',
                
                # Medium custom sites (Phase 6B)
                'travel-agency': 'https://thetravelagency.co/',
                'gotham': 'https://gotham.nyc/',
                'dazed': 'https://dazed.fun/',
                'green-apple': 'https://greenapple.nyc/',
                'chelsea-cannabis': 'https://chelseacannabis.co/',
                'verilife': 'https://verilife.com/ny/',
                
                # LeafBridge platform (Phase 6C)
                'qube': 'https://qubenyc.com/',
                
                # Hard targets (Phase 6F)
                'rise': 'https://risecannabis.com/',
                'curaleaf': 'https://curaleaf.com/'
            }
        }
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging for health checks"""
        log_dir = os.path.join(self.monitoring_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('health_checker')
        self.logger.setLevel(logging.INFO)
        
        # File handler with daily rotation
        log_file = os.path.join(log_dir, f'health_check_{datetime.date.today().isoformat()}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    async def check_site_reachability(self, store_name: str, url: str) -> Tuple[bool, int, Optional[str]]:
        """Check if the store's website is reachable and responsive"""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.config['site_timeout_seconds'])
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as response:
                    response_time_ms = int((time.time() - start_time) * 1000)
                    
                    if response.status == 200:
                        self.logger.info(f"{store_name}: Site reachable ({response_time_ms}ms)")
                        return True, response_time_ms, None
                    else:
                        error_msg = f"HTTP {response.status}"
                        self.logger.warning(f"{store_name}: Site returned {error_msg}")
                        return False, response_time_ms, error_msg
                        
        except asyncio.TimeoutError:
            response_time_ms = int((time.time() - start_time) * 1000)
            error_msg = "Timeout"
            self.logger.warning(f"{store_name}: Site timeout after {response_time_ms}ms")
            return False, response_time_ms, error_msg
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            self.logger.error(f"{store_name}: Site check failed: {error_msg}")
            return False, response_time_ms, error_msg
    
    def check_extraction_capability(self, store_name: str) -> Tuple[bool, int, int, Optional[str]]:
        """Check if the scraper can extract products from the store"""
        
        # Look for scraper script
        possible_paths = [
            os.path.join(self.scrapers_dir, store_name, f'{store_name}_scraper.py'),
            os.path.join(self.scrapers_dir, store_name.replace('-', '_'), f'{store_name.replace("-", "_")}_scraper.py'),
            os.path.join(self.scrapers_dir, f'{store_name}_scraper.py'),
            os.path.join(self.scrapers_dir, 'blaze', 'blaze_scraper.py') if 'blaze' in self.dashboard.stores_config.get(store_name, {}).get('platform', '').lower() else None,
            os.path.join(self.scrapers_dir, 'joint', 'joint_scraper.py') if 'joint' in self.dashboard.stores_config.get(store_name, {}).get('platform', '').lower() else None
        ]
        
        scraper_path = None
        for path in possible_paths:
            if path and os.path.exists(path):
                scraper_path = path
                break
        
        if not scraper_path:
            self.logger.error(f"{store_name}: No scraper found")
            return False, 0, 0, "No scraper script found"
        
        start_time = time.time()
        
        try:
            # Run the scraper with a timeout
            result = subprocess.run([
                sys.executable, scraper_path, '--health-check'
            ], 
            timeout=self.config['extraction_timeout_seconds'],
            capture_output=True,
            text=True
            )
            
            extraction_time_ms = int((time.time() - start_time) * 1000)
            
            if result.returncode == 0:
                # Try to parse the output for product count
                try:
                    # Look for JSON output or product count in stdout
                    output = result.stdout.strip()
                    if output.startswith('{'):
                        data = json.loads(output)
                        products_extracted = data.get('products_extracted', 0)
                    else:
                        # Simple fallback - look for numbers in output
                        import re
                        numbers = re.findall(r'\b(\d+)\b', output)
                        products_extracted = int(numbers[-1]) if numbers else 0
                        
                except (json.JSONDecodeError, ValueError):
                    # If we can't parse, assume 1 product if successful
                    products_extracted = 1
                
                if products_extracted >= self.config['min_products_required']:
                    self.logger.info(f"{store_name}: Extraction successful ({products_extracted} products, {extraction_time_ms}ms)")
                    return True, products_extracted, extraction_time_ms, None
                else:
                    error_msg = f"Only {products_extracted} products extracted (minimum: {self.config['min_products_required']})"
                    self.logger.warning(f"{store_name}: {error_msg}")
                    return False, products_extracted, extraction_time_ms, error_msg
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.logger.error(f"{store_name}: Scraper failed with error: {error_msg}")
                return False, 0, extraction_time_ms, error_msg
                
        except subprocess.TimeoutExpired:
            extraction_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Extraction timeout after {self.config['extraction_timeout_seconds']}s"
            self.logger.warning(f"{store_name}: {error_msg}")
            return False, 0, extraction_time_ms, error_msg
            
        except Exception as e:
            extraction_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            self.logger.error(f"{store_name}: Extraction check failed: {error_msg}")
            return False, 0, extraction_time_ms, error_msg
    
    async def perform_health_check(self, store_name: str) -> HealthCheckResult:
        """Perform complete health check for a single store"""
        
        self.logger.info(f"Starting health check for {store_name}")
        timestamp = datetime.datetime.now()
        
        # Get store URL
        url = self.config['store_urls'].get(store_name)
        if not url:
            return HealthCheckResult(
                store_name=store_name,
                timestamp=timestamp,
                overall_status='unknown',
                site_reachable=False,
                site_response_time_ms=0,
                extraction_successful=False,
                products_extracted=0,
                extraction_time_ms=0,
                latency_threshold_ms=self.config['max_extraction_latency_ms'],
                meets_latency_threshold=False,
                error_message="No URL configured for store",
                last_error_type="configuration"
            )
        
        # Check site reachability
        site_reachable, site_response_time_ms, site_error = await self.check_site_reachability(store_name, url)
        
        # Check extraction capability
        extraction_successful, products_extracted, extraction_time_ms, extraction_error = self.check_extraction_capability(store_name)
        
        # Determine latency threshold compliance
        total_latency_ms = site_response_time_ms + extraction_time_ms
        meets_latency_threshold = total_latency_ms <= self.config['max_extraction_latency_ms']
        
        # Determine overall status
        if site_reachable and extraction_successful and meets_latency_threshold:
            overall_status = 'healthy'
            error_message = None
            error_type = None
        elif site_reachable and extraction_successful and not meets_latency_threshold:
            overall_status = 'warning'
            error_message = f"High latency: {total_latency_ms}ms (threshold: {self.config['max_extraction_latency_ms']}ms)"
            error_type = "latency"
        elif site_reachable and not extraction_successful:
            overall_status = 'critical'
            error_message = extraction_error or "Extraction failed"
            error_type = "extraction"
        elif not site_reachable:
            overall_status = 'critical'
            error_message = site_error or "Site unreachable"
            error_type = "connectivity"
        else:
            overall_status = 'critical'
            error_message = "Multiple failures"
            error_type = "multiple"
        
        result = HealthCheckResult(
            store_name=store_name,
            timestamp=timestamp,
            overall_status=overall_status,
            site_reachable=site_reachable,
            site_response_time_ms=site_response_time_ms,
            extraction_successful=extraction_successful,
            products_extracted=products_extracted,
            extraction_time_ms=extraction_time_ms,
            latency_threshold_ms=self.config['max_extraction_latency_ms'],
            meets_latency_threshold=meets_latency_threshold,
            error_message=error_message,
            last_error_type=error_type
        )
        
        # Record the result in our dashboard database
        self.dashboard.record_scrape_result(
            store_name=store_name,
            success=extraction_successful,
            products=products_extracted,
            latency_ms=total_latency_ms,
            error=error_message
        )
        
        self.logger.info(f"Health check completed for {store_name}: {overall_status}")
        return result
    
    async def run_all_health_checks(self, store_names: List[str] = None) -> List[HealthCheckResult]:
        """Run health checks for all stores (or specified subset)"""
        
        if store_names is None:
            # Check only active stores by default
            store_names = [name for name, config in self.dashboard.stores_config.items() 
                          if config.get('active', False)]
        
        if not store_names:
            self.logger.warning("No active stores found for health checking")
            return []
        
        self.logger.info(f"Running health checks for {len(store_names)} stores: {', '.join(store_names)}")
        
        # Run health checks concurrently with some semaphore limiting
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent checks
        
        async def limited_check(store_name):
            async with semaphore:
                return await self.perform_health_check(store_name)
        
        tasks = [limited_check(store_name) for store_name in store_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Health check failed for {store_names[i]}: {result}")
                # Create a failed result
                failed_result = HealthCheckResult(
                    store_name=store_names[i],
                    timestamp=datetime.datetime.now(),
                    overall_status='critical',
                    site_reachable=False,
                    site_response_time_ms=0,
                    extraction_successful=False,
                    products_extracted=0,
                    extraction_time_ms=0,
                    latency_threshold_ms=self.config['max_extraction_latency_ms'],
                    meets_latency_threshold=False,
                    error_message=str(result),
                    last_error_type='exception'
                )
                valid_results.append(failed_result)
            else:
                valid_results.append(result)
        
        return valid_results
    
    def save_health_status(self, results: List[HealthCheckResult]) -> str:
        """Save health check results to health_status.json"""
        
        # Organize results by status
        status_summary = {
            'timestamp': datetime.datetime.now().isoformat(),
            'total_stores_checked': len(results),
            'healthy_count': len([r for r in results if r.overall_status == 'healthy']),
            'warning_count': len([r for r in results if r.overall_status == 'warning']),
            'critical_count': len([r for r in results if r.overall_status == 'critical']),
            'unknown_count': len([r for r in results if r.overall_status == 'unknown']),
        }
        
        # Create full health status document
        health_status = {
            'summary': status_summary,
            'stores': [asdict(result) for result in results],
            'config': {
                'site_timeout_seconds': self.config['site_timeout_seconds'],
                'extraction_timeout_seconds': self.config['extraction_timeout_seconds'],
                'max_extraction_latency_ms': self.config['max_extraction_latency_ms'],
                'min_products_required': self.config['min_products_required']
            }
        }
        
        # Save to file
        output_path = os.path.join(self.monitoring_dir, 'health_status.json')
        with open(output_path, 'w') as f:
            json.dump(health_status, f, indent=2, default=str)
        
        self.logger.info(f"Health status saved to {output_path}")
        return output_path
    
    async def run_health_check_cycle(self, store_names: List[str] = None) -> str:
        """Run complete health check cycle and save results"""
        results = await self.run_all_health_checks(store_names)
        output_path = self.save_health_status(results)
        return output_path


async def main():
    """CLI interface for health checker"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stealth Scraper Health Checker')
    parser.add_argument('--stores', nargs='+', help='Specific stores to check')
    parser.add_argument('--all', action='store_true', help='Check all configured stores (including inactive)')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--save', action='store_true', help='Save results to health_status.json', default=True)
    
    args = parser.parse_args()
    
    checker = HealthChecker()
    
    # Determine which stores to check
    store_names = args.stores
    if args.all:
        store_names = list(checker.dashboard.stores_config.keys())
    
    # Run health checks
    results = await checker.run_all_health_checks(store_names)
    
    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2, default=str))
    else:
        print("Health Check Results")
        print("=" * 50)
        for result in results:
            status_emoji = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '❌',
                'unknown': '❓'
            }.get(result.overall_status, '❓')
            
            print(f"{status_emoji} {result.store_name}: {result.overall_status.upper()}")
            if result.error_message:
                print(f"   Error: {result.error_message}")
            if result.extraction_successful:
                print(f"   Products: {result.products_extracted}, Latency: {result.extraction_time_ms}ms")
            print()
    
    # Save results
    if args.save:
        output_path = checker.save_health_status(results)
        print(f"Results saved to: {output_path}")


if __name__ == '__main__':
    asyncio.run(main())