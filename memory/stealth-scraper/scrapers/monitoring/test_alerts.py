#!/usr/bin/env python3
"""
Alert Testing Framework for Stealth Scraper

Tests all alert scenarios to verify end-to-end alerting functionality:
- Price changes
- Stock changes  
- New/removed products
- Scraper failures
- Success rate drops

Run with: python test_alerts.py --scenario <scenario_name>
"""

import asyncio
import json
import os
import sys
import datetime
import tempfile
import shutil
import sqlite3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from monitoring.alerter import AlertManager, Alert
from inventory.change_detector import InventoryChangeDetector, InventoryChange


@dataclass
class TestScenario:
    """Represents a test scenario"""
    id: str
    name: str
    description: str
    expected_alerts: List[str]
    setup_data: Dict[str, Any]


class AlertTestFramework:
    """Framework for testing alert scenarios"""
    
    def __init__(self, test_dir: str = None):
        self.test_dir = test_dir or tempfile.mkdtemp(prefix='alert_test_')
        self.original_scrapers_dir = os.path.join(os.path.dirname(__file__), '..')
        
        # Create test environment
        self.setup_test_environment()
        
        # Initialize components with test directory
        self.alert_manager = AlertManager(self.test_dir)
        self.change_detector = InventoryChangeDetector(os.path.join(self.test_dir, 'data'))
        
        # Test results storage
        self.test_results = []
        
    def setup_test_environment(self):
        """Set up isolated test environment"""
        # Copy essential config files
        monitoring_src = os.path.join(self.original_scrapers_dir, 'monitoring')
        monitoring_dst = os.path.join(self.test_dir, 'monitoring')
        
        os.makedirs(monitoring_dst, exist_ok=True)
        
        # Copy alert config
        config_src = os.path.join(monitoring_src, 'alert_config.json')
        config_dst = os.path.join(monitoring_dst, 'alert_config.json')
        if os.path.exists(config_src):
            shutil.copy2(config_src, config_dst)
        
        # Create necessary directories
        os.makedirs(os.path.join(self.test_dir, 'data'), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, 'logs'), exist_ok=True)
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        try:
            shutil.rmtree(self.test_dir)
        except Exception as e:
            print(f"Warning: Failed to cleanup test directory: {e}")
    
    def create_mock_health_data(self, store_name: str, scenario_data: Dict[str, Any]):
        """Create mock health check data for testing"""
        health_dir = os.path.join(self.test_dir, 'health')
        os.makedirs(health_dir, exist_ok=True)
        
        # Create mock health check results
        for i, result in enumerate(scenario_data.get('health_results', [])):
            timestamp = datetime.datetime.now() - datetime.timedelta(minutes=i * 10)
            result['timestamp'] = timestamp.isoformat()
            result['store'] = store_name
            
            filename = f"health_{store_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(health_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=2)
    
    def create_mock_inventory_data(self, store_name: str, products: List[Dict]):
        """Create mock inventory snapshot"""
        return self.change_detector.save_snapshot(store_name, products)
    
    def simulate_inventory_changes(self, store_name: str, old_products: List[Dict], new_products: List[Dict]) -> List[InventoryChange]:
        """Simulate inventory changes between two snapshots"""
        # Save old snapshot first
        self.create_mock_inventory_data(store_name, old_products)
        
        # Process new products to detect changes
        changes, _ = self.change_detector.process_inventory_update(store_name, new_products)
        return changes
    
    def define_test_scenarios(self) -> List[TestScenario]:
        """Define all test scenarios"""
        return [
            TestScenario(
                id='price_drop',
                name='Price Drop Alert',
                description='Product price drops significantly ($50 → $40)',
                expected_alerts=['price_change'],
                setup_data={
                    'old_products': [
                        {'id': '1', 'name': 'Blue Dream 3.5g', 'price': 50.0, 'category': 'flower', 'in_stock': True}
                    ],
                    'new_products': [
                        {'id': '1', 'name': 'Blue Dream 3.5g', 'price': 40.0, 'category': 'flower', 'in_stock': True}
                    ]
                }
            ),
            TestScenario(
                id='stock_out',
                name='Stock Out Alert',
                description='Product goes from in_stock to out_of_stock',
                expected_alerts=['stock_out'],
                setup_data={
                    'old_products': [
                        {'id': '2', 'name': 'OG Kush 1g', 'price': 20.0, 'category': 'flower', 'in_stock': True}
                    ],
                    'new_products': [
                        {'id': '2', 'name': 'OG Kush 1g', 'price': 20.0, 'category': 'flower', 'in_stock': False}
                    ]
                }
            ),
            TestScenario(
                id='new_product',
                name='New Product Alert',
                description='New product added to inventory',
                expected_alerts=['new_product'],
                setup_data={
                    'old_products': [],
                    'new_products': [
                        {'id': '3', 'name': 'White Widow 7g', 'price': 80.0, 'category': 'flower', 'in_stock': True}
                    ]
                }
            ),
            TestScenario(
                id='product_removed',
                name='Product Removed Alert',
                description='Product removed from inventory',
                expected_alerts=['removed_product'],
                setup_data={
                    'old_products': [
                        {'id': '4', 'name': 'Edible Gummies 10mg', 'price': 15.0, 'category': 'edibles', 'in_stock': True}
                    ],
                    'new_products': []
                }
            ),
            TestScenario(
                id='consecutive_failures',
                name='Consecutive Scraper Failures',
                description='3 consecutive scraper failures',
                expected_alerts=['consecutive_failures'],
                setup_data={
                    'health_results': [
                        {'success': False, 'error': 'Connection timeout', 'products_extracted': 0},
                        {'success': False, 'error': 'HTTP 503 error', 'products_extracted': 0},
                        {'success': False, 'error': 'Parse error', 'products_extracted': 0}
                    ]
                }
            ),
            TestScenario(
                id='low_success_rate',
                name='Low Success Rate',
                description='Success rate drops below 80%',
                expected_alerts=['low_success_rate'],
                setup_data={
                    'health_results': [
                        {'success': False, 'error': 'Failed', 'products_extracted': 0},
                        {'success': False, 'error': 'Failed', 'products_extracted': 0},
                        {'success': False, 'error': 'Failed', 'products_extracted': 0},
                        {'success': False, 'error': 'Failed', 'products_extracted': 0},
                        {'success': True, 'error': None, 'products_extracted': 10}
                    ]
                }
            )
        ]
    
    def define_suppression_scenarios(self) -> List[TestScenario]:
        """Define scenarios that should NOT trigger alerts"""
        return [
            TestScenario(
                id='minor_price_change',
                name='Minor Price Change (Should NOT Alert)',
                description='Price changes by $0.01 ($50.00 → $50.01)',
                expected_alerts=[],
                setup_data={
                    'old_products': [
                        {'id': '1', 'name': 'Blue Dream 3.5g', 'price': 50.00, 'category': 'flower', 'in_stock': True}
                    ],
                    'new_products': [
                        {'id': '1', 'name': 'Blue Dream 3.5g', 'price': 50.01, 'category': 'flower', 'in_stock': True}
                    ]
                }
            ),
            TestScenario(
                id='no_change',
                name='No Changes (Should NOT Alert)',
                description='Same product re-extracted with no changes',
                expected_alerts=[],
                setup_data={
                    'old_products': [
                        {'id': '1', 'name': 'Blue Dream 3.5g', 'price': 50.0, 'category': 'flower', 'in_stock': True}
                    ],
                    'new_products': [
                        {'id': '1', 'name': 'Blue Dream 3.5g', 'price': 50.0, 'category': 'flower', 'in_stock': True}
                    ]
                }
            ),
            TestScenario(
                id='temporary_recovery',
                name='Temporary Error Recovery (Should NOT Alert)',
                description='Single failure followed by recovery',
                expected_alerts=[],
                setup_data={
                    'health_results': [
                        {'success': False, 'error': 'Temporary network error', 'products_extracted': 0},
                        {'success': True, 'error': None, 'products_extracted': 15},
                        {'success': True, 'error': None, 'products_extracted': 14}
                    ]
                }
            )
        ]
    
    async def run_scenario(self, scenario: TestScenario, store_name: str = 'test_store') -> Dict[str, Any]:
        """Run a single test scenario"""
        print(f"\n🧪 Running scenario: {scenario.name}")
        print(f"   Description: {scenario.description}")
        
        try:
            # Set up scenario data
            if 'old_products' in scenario.setup_data and 'new_products' in scenario.setup_data:
                # Inventory change scenario
                changes = self.simulate_inventory_changes(
                    store_name, 
                    scenario.setup_data['old_products'],
                    scenario.setup_data['new_products']
                )
                
                detected_changes = [change.type for change in changes]
                
            elif 'health_results' in scenario.setup_data:
                # Health/failure scenario - we'll need to mock the dashboard/metrics
                self.create_mock_health_data(store_name, scenario.setup_data)
                detected_changes = []
                
            else:
                detected_changes = []
            
            # Run alert checks
            alerts = await self.alert_manager.check_all_stores()
            alert_types = [alert.alert_type for alert in alerts]
            
            # Check results
            success = True
            missing_alerts = []
            unexpected_alerts = []
            
            for expected in scenario.expected_alerts:
                if expected not in alert_types and expected not in detected_changes:
                    missing_alerts.append(expected)
                    success = False
            
            for actual in alert_types:
                if actual not in scenario.expected_alerts:
                    unexpected_alerts.append(actual)
                    success = False
            
            result = {
                'scenario_id': scenario.id,
                'scenario_name': scenario.name,
                'success': success,
                'expected_alerts': scenario.expected_alerts,
                'detected_changes': detected_changes,
                'actual_alerts': alert_types,
                'missing_alerts': missing_alerts,
                'unexpected_alerts': unexpected_alerts,
                'alert_details': [{'type': a.alert_type, 'message': a.message} for a in alerts]
            }
            
            # Display results
            if success:
                print(f"   ✅ PASSED")
            else:
                print(f"   ❌ FAILED")
                if missing_alerts:
                    print(f"      Missing alerts: {missing_alerts}")
                if unexpected_alerts:
                    print(f"      Unexpected alerts: {unexpected_alerts}")
            
            if detected_changes:
                print(f"   📋 Detected changes: {detected_changes}")
            if alert_types:
                print(f"   🚨 Triggered alerts: {alert_types}")
            
            return result
            
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            return {
                'scenario_id': scenario.id,
                'scenario_name': scenario.name,
                'success': False,
                'error': str(e)
            }
    
    async def test_webhook_integration(self):
        """Test webhook integration with a test endpoint"""
        print(f"\n🕸️ Testing Webhook Integration")
        
        # Create test webhook endpoint using webhook.site
        import aiohttp
        
        try:
            # Get a webhook.site endpoint
            async with aiohttp.ClientSession() as session:
                async with session.post('https://webhook.site/token') as response:
                    if response.status == 201:
                        data = await response.json()
                        webhook_url = f"https://webhook.site/{data['uuid']}"
                        print(f"   📡 Test webhook URL: {webhook_url}")
                        
                        # Update alert config for webhook testing
                        self.alert_manager.config['channels']['webhook']['enabled'] = True
                        self.alert_manager.config['channels']['webhook']['url'] = webhook_url
                        self.alert_manager.config['channels']['webhook']['format'] = 'slack'
                        
                        # Send test alert
                        test_alert = Alert(
                            alert_id=f"webhook_test_{int(datetime.datetime.now().timestamp())}",
                            timestamp=datetime.datetime.now(),
                            severity='info',
                            store_name='test_store',
                            alert_type='webhook_test',
                            message='Webhook integration test alert',
                            details={'test': True}
                        )
                        
                        await self.alert_manager.send_alert(test_alert)
                        print(f"   ✅ Test alert sent to webhook")
                        print(f"   🔍 Check webhook for received payload: {webhook_url}")
                        
                        return {
                            'success': True,
                            'webhook_url': webhook_url,
                            'test_alert_sent': True
                        }
                    else:
                        print(f"   ❌ Failed to create test webhook endpoint")
                        return {'success': False, 'error': 'Failed to create webhook endpoint'}
                        
        except Exception as e:
            print(f"   💥 Webhook test error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_alert_cooldowns(self):
        """Test that alert cooldowns work correctly"""
        print(f"\n❄️ Testing Alert Cooldowns")
        
        try:
            store_name = 'cooldown_test_store'
            
            # Create test alert condition
            test_alert = Alert(
                alert_id=f"cooldown_test_{int(datetime.datetime.now().timestamp())}",
                timestamp=datetime.datetime.now(),
                severity='warning',
                store_name=store_name,
                alert_type='test_cooldown',
                message='Test cooldown alert',
                details={'test': True}
            )
            
            # Save first alert
            self.alert_manager.save_alert(test_alert)
            
            # Check if we're in cooldown (should be true)
            in_cooldown = self.alert_manager._is_in_cooldown(store_name, 'test_cooldown', 5)  # 5 minute cooldown
            
            if in_cooldown:
                print(f"   ✅ Cooldown working correctly - subsequent alerts blocked")
                return {'success': True, 'cooldown_working': True}
            else:
                print(f"   ❌ Cooldown not working - alerts not being suppressed")
                return {'success': False, 'cooldown_working': False}
                
        except Exception as e:
            print(f"   💥 Cooldown test error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Starting Alert Testing Framework")
        print(f"   Test directory: {self.test_dir}")
        
        # Test regular scenarios
        scenarios = self.define_test_scenarios()
        suppression_scenarios = self.define_suppression_scenarios()
        
        print(f"\n📋 Running {len(scenarios)} main scenarios...")
        for scenario in scenarios:
            result = await self.run_scenario(scenario)
            self.test_results.append(result)
        
        print(f"\n🔕 Running {len(suppression_scenarios)} suppression scenarios...")
        for scenario in suppression_scenarios:
            result = await self.run_scenario(scenario)
            self.test_results.append(result)
        
        # Test webhook integration
        webhook_result = await self.test_webhook_integration()
        self.test_results.append({
            'scenario_id': 'webhook_test',
            'scenario_name': 'Webhook Integration Test',
            **webhook_result
        })
        
        # Test cooldowns
        cooldown_result = await self.test_alert_cooldowns()
        self.test_results.append({
            'scenario_id': 'cooldown_test',
            'scenario_name': 'Alert Cooldown Test',
            **cooldown_result
        })
        
        # Generate summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate and display test summary"""
        print("\n" + "="*60)
        print("📊 ALERT TESTING SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.get('success', False)])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result.get('success', False):
                    print(f"  • {result['scenario_name']}")
                    if 'error' in result:
                        print(f"    Error: {result['error']}")
                    if 'missing_alerts' in result and result['missing_alerts']:
                        print(f"    Missing: {result['missing_alerts']}")
                    if 'unexpected_alerts' in result and result['unexpected_alerts']:
                        print(f"    Unexpected: {result['unexpected_alerts']}")
        
        # Save detailed results
        results_file = os.path.join(self.test_dir, 'alert_test_results.json')
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.datetime.now().isoformat(),
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'results': self.test_results
            }, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: {results_file}")


async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Alert Testing Framework')
    parser.add_argument('--scenario', help='Run specific scenario')
    parser.add_argument('--list', action='store_true', help='List available scenarios')
    parser.add_argument('--all', action='store_true', help='Run all test scenarios')
    parser.add_argument('--webhook', action='store_true', help='Test webhook integration only')
    parser.add_argument('--cooldown', action='store_true', help='Test alert cooldowns only')
    parser.add_argument('--keep-test-dir', action='store_true', help='Keep test directory after completion')
    
    args = parser.parse_args()
    
    framework = AlertTestFramework()
    
    try:
        if args.list:
            scenarios = framework.define_test_scenarios() + framework.define_suppression_scenarios()
            print("Available test scenarios:")
            for scenario in scenarios:
                print(f"  {scenario.id}: {scenario.name}")
                print(f"    {scenario.description}")
        
        elif args.scenario:
            scenarios = framework.define_test_scenarios() + framework.define_suppression_scenarios()
            scenario = next((s for s in scenarios if s.id == args.scenario), None)
            if scenario:
                await framework.run_scenario(scenario)
            else:
                print(f"Scenario '{args.scenario}' not found")
        
        elif args.webhook:
            await framework.test_webhook_integration()
        
        elif args.cooldown:
            await framework.test_alert_cooldowns()
        
        elif args.all:
            await framework.run_all_tests()
        
        else:
            print("Use --all to run all tests, --scenario <name> for specific test, or --list to see available scenarios")
    
    finally:
        if not args.keep_test_dir:
            framework.cleanup_test_environment()


if __name__ == '__main__':
    asyncio.run(main())