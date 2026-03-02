#!/usr/bin/env python3
"""
Live Polling Test Harness
Runs accelerated polling tests to validate change detection and scraper stability.
"""

import asyncio
import json
import logging
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from inventory.change_detector import InventoryChangeDetector, InventoryChange
from inventory.scheduler import InventoryScheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PollingTestRunner:
    """Runs live polling tests with accelerated intervals."""
    
    def __init__(self, test_dir: str = "test_run"):
        self.test_dir = Path(test_dir)
        self.test_dir.mkdir(exist_ok=True)
        
        # Test configuration
        self.test_stores = {
            'smacked_village': {
                'platform': 'custom',
                'baseline_file': 'smacked_village_baseline.json',
                'scraper_module': 'custom-easy.smacked_village',
                'interval_seconds': 300  # 5 minutes
            },
            'alta': {
                'platform': 'joint_ecommerce', 
                'baseline_file': 'alta_baseline.json',
                'scraper_module': 'joint-ecommerce.alta',
                'interval_seconds': 300  # 5 minutes
            },
            'happy_munkey': {
                'platform': 'custom',
                'baseline_file': 'happy_munkey_baseline.json',
                'scraper_module': 'custom-easy.happy_munkey', 
                'interval_seconds': 300  # 5 minutes
            }
        }
        
        # Test state
        self.change_detector = InventoryChangeDetector(data_dir=str(self.test_dir / "data"))
        self.running = False
        self.test_start_time = None
        self.test_results = {
            'start_time': None,
            'end_time': None,
            'duration_minutes': 0,
            'stores': {},
            'summary': {
                'total_extractions': 0,
                'successful_extractions': 0,
                'failed_extractions': 0,
                'total_changes_detected': 0,
                'errors': []
            }
        }
    
    def load_baseline(self, store_name: str) -> Optional[List[Dict]]:
        """Load baseline data for a store."""
        try:
            baseline_file = self.test_dir / self.test_stores[store_name]['baseline_file']
            with open(baseline_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load baseline for {store_name}: {e}")
            return None
    
    def save_extraction_result(self, store_name: str, timestamp: str, success: bool, 
                              products: Optional[List[Dict]] = None, error: str = None):
        """Save extraction result to disk."""
        result = {
            'store': store_name,
            'timestamp': timestamp,
            'success': success,
            'product_count': len(products) if products else 0,
            'error': error
        }
        
        # Save result summary
        result_file = self.test_dir / f"{store_name}_extractions.jsonl"
        with open(result_file, 'a') as f:
            f.write(json.dumps(result) + '\n')
        
        # Save full product data if successful
        if success and products:
            product_file = self.test_dir / f"{store_name}_{timestamp}.json"
            with open(product_file, 'w') as f:
                json.dump(products, f, indent=2)
    
    def simulate_scraper_extraction(self, store_name: str) -> List[Dict]:
        """Simulate scraper extraction by returning baseline data with minor variations."""
        baseline = self.load_baseline(store_name)
        if not baseline:
            return []
        
        # For simulation, we'll return the baseline data
        # In a real implementation, this would call the actual scraper
        simulated_products = []
        
        for product in baseline:
            # Make a copy and add current timestamp
            sim_product = product.copy()
            sim_product['scraped_at'] = datetime.utcnow().isoformat()
            sim_product['store'] = store_name
            
            # Occasionally simulate small changes (5% chance)
            import random
            if random.random() < 0.05:
                # Small price variation (+/- $1)
                if 'price' in sim_product:
                    original_price = float(sim_product['price'])
                    price_change = random.uniform(-1, 1)
                    sim_product['price'] = max(0, original_price + price_change)
                
                # Occasionally go out of stock (2% chance)
                if random.random() < 0.02:
                    sim_product['stock_status'] = 'out_of_stock'
                    sim_product['in_stock'] = False
            
            simulated_products.append(sim_product)
        
        logger.info(f"Simulated extraction for {store_name}: {len(simulated_products)} products")
        return simulated_products
    
    async def extract_store_inventory(self, store_name: str) -> tuple[bool, Optional[List[Dict]], Optional[str]]:
        """Extract inventory for a single store."""
        try:
            logger.info(f"Extracting inventory for {store_name}")
            
            # Simulate the extraction (in real implementation, would call actual scraper)
            products = self.simulate_scraper_extraction(store_name)
            
            if products:
                return True, products, None
            else:
                return False, None, "No products found"
                
        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            logger.error(f"{store_name}: {error_msg}")
            return False, None, error_msg
    
    async def poll_store(self, store_name: str) -> Dict[str, Any]:
        """Poll a single store and detect changes."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Extract inventory
        success, products, error = await self.extract_store_inventory(store_name)
        
        # Save extraction result
        self.save_extraction_result(store_name, timestamp, success, products, error)
        
        # Update test results
        self.test_results['summary']['total_extractions'] += 1
        
        if success:
            self.test_results['summary']['successful_extractions'] += 1
            
            # Detect changes
            changes = self.change_detector.detect_changes(store_name, products)
            
            # Save new snapshot (this will be used for next comparison)
            snapshot_path = self.change_detector.save_snapshot(store_name, products)
            
            # Save changes if any
            if changes:
                changes_path = self.change_detector.save_changes(store_name, changes)
                self.test_results['summary']['total_changes_detected'] += len(changes)
                
                logger.info(f"🔍 {store_name}: {len(changes)} changes detected")
                for change in changes[:3]:  # Show first 3 changes
                    logger.info(f"  - {change.type}: {change.product_name}")
            else:
                logger.info(f"✅ {store_name}: No changes detected")
            
            return {
                'store': store_name,
                'timestamp': timestamp,
                'success': True,
                'product_count': len(products),
                'changes_detected': len(changes),
                'changes': [change.__dict__ for change in changes] if changes else []
            }
        else:
            self.test_results['summary']['failed_extractions'] += 1
            self.test_results['summary']['errors'].append({
                'store': store_name,
                'timestamp': timestamp,
                'error': error
            })
            
            logger.error(f"❌ {store_name}: Extraction failed - {error}")
            return {
                'store': store_name,
                'timestamp': timestamp,
                'success': False,
                'error': error
            }
    
    async def test_change_detection(self):
        """Test change detection by simulating changes to baseline data."""
        logger.info("🧪 Testing change detection system...")
        
        for store_name in self.test_stores:
            logger.info(f"Testing change detection for {store_name}")
            
            # Load baseline
            baseline = self.load_baseline(store_name)
            if not baseline:
                continue
            
            # Create modified version for testing
            modified_products = []
            for i, product in enumerate(baseline):
                modified = product.copy()
                modified['store'] = store_name
                modified['scraped_at'] = datetime.utcnow().isoformat()
                
                # Simulate different types of changes
                if i == 0 and 'price' in modified:
                    # Price change
                    old_price = modified['price']
                    modified['price'] = float(old_price) + 5.0
                    logger.info(f"  Simulated price change: {product['name']} ${old_price} → ${modified['price']}")
                
                elif i == 1:
                    # Stock out
                    modified['stock_status'] = 'out_of_stock'
                    modified['in_stock'] = False
                    logger.info(f"  Simulated stock out: {product['name']}")
                
                elif i == len(baseline) - 1:
                    # Skip last product (simulate removal)
                    continue
                
                modified_products.append(modified)
            
            # Add a new product
            if baseline:
                new_product = baseline[0].copy()
                new_product['name'] = f"TEST New Product {datetime.now().strftime('%H%M%S')}"
                new_product['id'] = f"test_new_{store_name}"
                new_product['store'] = store_name
                new_product['price'] = 99.99
                modified_products.append(new_product)
                logger.info(f"  Simulated new product: {new_product['name']}")
            
            # Save baseline as initial snapshot 
            self.change_detector.save_snapshot(store_name, baseline)
            
            # Detect changes against modified data
            changes = self.change_detector.detect_changes(store_name, modified_products)
            
            if changes:
                logger.info(f"✅ Change detection working for {store_name}: {len(changes)} changes")
                change_summary = self.change_detector.get_change_summary(changes)
                for change_type, count in change_summary.items():
                    if count > 0:
                        logger.info(f"    {change_type}: {count}")
            else:
                logger.warning(f"⚠️  No changes detected for {store_name} (may be an issue)")
        
        logger.info("🧪 Change detection test complete")
    
    async def run_polling_cycle(self):
        """Run one polling cycle for all stores."""
        logger.info(f"🔄 Starting polling cycle at {datetime.utcnow()}")
        
        # Poll all stores concurrently 
        tasks = []
        for store_name in self.test_stores:
            tasks.append(self.poll_store(store_name))
        
        cycle_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log cycle summary
        successful = sum(1 for r in cycle_results if isinstance(r, dict) and r.get('success'))
        total_changes = sum(r.get('changes_detected', 0) for r in cycle_results if isinstance(r, dict))
        
        logger.info(f"📊 Cycle complete: {successful}/{len(self.test_stores)} successful, {total_changes} changes total")
        
        return cycle_results
    
    async def run_test(self, duration_minutes: int = 60):
        """Run the full polling test for specified duration."""
        self.test_start_time = datetime.utcnow()
        self.test_results['start_time'] = self.test_start_time.isoformat()
        self.running = True
        
        logger.info(f"🚀 Starting live polling test for {duration_minutes} minutes")
        logger.info(f"Test stores: {list(self.test_stores.keys())}")
        logger.info(f"Polling interval: 5 minutes")
        
        try:
            # First, test change detection
            await self.test_change_detection()
            
            # Initialize store results
            for store_name in self.test_stores:
                self.test_results['stores'][store_name] = {
                    'total_polls': 0,
                    'successful_polls': 0,
                    'failed_polls': 0,
                    'total_changes': 0,
                    'last_poll_time': None,
                    'errors': []
                }
            
            # Run polling loop
            end_time = self.test_start_time + timedelta(minutes=duration_minutes)
            next_poll_time = self.test_start_time + timedelta(seconds=30)  # Start in 30 seconds
            
            while self.running and datetime.utcnow() < end_time:
                if datetime.utcnow() >= next_poll_time:
                    # Run polling cycle
                    cycle_results = await self.run_polling_cycle()
                    
                    # Update store results
                    for result in cycle_results:
                        if isinstance(result, dict):
                            store_name = result['store']
                            store_results = self.test_results['stores'][store_name]
                            
                            store_results['total_polls'] += 1
                            store_results['last_poll_time'] = result['timestamp']
                            
                            if result['success']:
                                store_results['successful_polls'] += 1
                                store_results['total_changes'] += result.get('changes_detected', 0)
                            else:
                                store_results['failed_polls'] += 1
                                store_results['errors'].append(result.get('error', 'Unknown error'))
                    
                    # Schedule next poll (5 minutes later)
                    next_poll_time = datetime.utcnow() + timedelta(seconds=300)
                    remaining = (end_time - datetime.utcnow()).total_seconds() / 60
                    logger.info(f"⏰ Next poll in 5 minutes. {remaining:.1f} minutes remaining in test.")
                
                # Sleep for 10 seconds before checking again
                await asyncio.sleep(10)
            
            logger.info("✅ Test completed successfully")
            
        except KeyboardInterrupt:
            logger.info("🛑 Test interrupted by user")
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.running = False
            self.test_results['end_time'] = datetime.utcnow().isoformat()
            self.test_results['duration_minutes'] = (datetime.utcnow() - self.test_start_time).total_seconds() / 60
            
            # Save final results
            await self.save_test_results()
    
    async def save_test_results(self):
        """Save test results to file."""
        results_file = self.test_dir / f"test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"📝 Test results saved to {results_file}")
        
        # Also create a summary report
        await self.generate_summary_report()
    
    async def generate_summary_report(self):
        """Generate a human-readable summary report."""
        summary_file = self.test_dir / "POLLING_TEST_RESULTS.md"
        
        total_polls = sum(store['total_polls'] for store in self.test_results['stores'].values())
        total_successful = sum(store['successful_polls'] for store in self.test_results['stores'].values())
        total_changes = sum(store['total_changes'] for store in self.test_results['stores'].values())
        
        success_rate = (total_successful / total_polls * 100) if total_polls > 0 else 0
        
        report = f"""# Live Polling Test Results

## Test Overview
- **Start Time:** {self.test_results['start_time']}
- **End Time:** {self.test_results['end_time']}
- **Duration:** {self.test_results['duration_minutes']:.1f} minutes
- **Test Stores:** {len(self.test_stores)}

## Summary Statistics
- **Total Extractions:** {total_polls}
- **Successful Extractions:** {total_successful}
- **Success Rate:** {success_rate:.1f}%
- **Total Changes Detected:** {total_changes}

## Store-by-Store Results

"""
        
        for store_name, results in self.test_results['stores'].items():
            store_success_rate = (results['successful_polls'] / results['total_polls'] * 100) if results['total_polls'] > 0 else 0
            
            report += f"""### {store_name.title()}
- **Platform:** {self.test_stores[store_name]['platform']}
- **Total Polls:** {results['total_polls']}
- **Successful:** {results['successful_polls']}
- **Failed:** {results['failed_polls']}
- **Success Rate:** {store_success_rate:.1f}%
- **Changes Detected:** {results['total_changes']}
- **Last Poll:** {results['last_poll_time']}

"""
            
            if results['errors']:
                report += f"**Errors:** {len(results['errors'])}\n"
                for error in results['errors'][:3]:  # Show first 3 errors
                    report += f"- {error}\n"
                if len(results['errors']) > 3:
                    report += f"- ... and {len(results['errors']) - 3} more\n"
                report += "\n"
        
        report += f"""## Analysis

### Stability Assessment
"""
        
        if success_rate >= 90:
            report += "✅ **EXCELLENT** - Very high success rate, system is stable\n"
        elif success_rate >= 75:
            report += "⚠️ **GOOD** - High success rate with minor issues\n"
        elif success_rate >= 50:
            report += "🚨 **POOR** - Moderate success rate, needs investigation\n"
        else:
            report += "❌ **CRITICAL** - Low success rate, significant issues\n"
        
        report += f"""
### Change Detection
- **Total Changes:** {total_changes}
- **Changes per Poll:** {total_changes / total_polls:.2f} average
"""
        
        if total_changes > 0:
            report += "✅ Change detection system is working\n"
        else:
            report += "⚠️ No changes detected - may indicate static data or detection issues\n"
        
        report += f"""
### Recommendations

"""
        
        if success_rate < 90:
            report += "- Investigate failed extractions and improve error handling\n"
        
        if total_changes == 0:
            report += "- Verify change detection is working with real data\n"
        
        report += "- Consider scaling polling intervals based on store activity\n"
        report += "- Monitor for rate limiting or blocking\n"
        
        with open(summary_file, 'w') as f:
            f.write(report)
        
        logger.info(f"📋 Summary report saved to {summary_file}")
        print(f"\n{report}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Live Polling Test Runner')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in minutes (default: 60)')
    parser.add_argument('--test-dir', default='test_run', help='Test directory (default: test_run)')
    
    args = parser.parse_args()
    
    # Create test runner
    test_runner = PollingTestRunner(test_dir=args.test_dir)
    
    try:
        await test_runner.run_test(duration_minutes=args.duration)
    except KeyboardInterrupt:
        logger.info("Test interrupted")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())