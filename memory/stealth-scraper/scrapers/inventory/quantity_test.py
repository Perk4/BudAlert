"""
Quantity Extraction Test Script
Tests quantity extraction on 3 stores: Housing Works, Stoops, and Alta
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import scrapers
from blaze.housing_works import scrape_housing_works
from joint_ecommerce.stoops import scrape_stoops  
from joint_ecommerce.alta import scrape_alta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuantityExtractionTest:
    """Test quantity extraction across multiple stores."""
    
    def __init__(self):
        self.results = {
            'test_started_at': datetime.utcnow().isoformat(),
            'stores_tested': [],
            'overall_stats': {},
            'detailed_results': {}
        }
    
    async def test_all_stores(self, limit_per_store: int = 5) -> Dict[str, Any]:
        """Test quantity extraction on all three target stores."""
        
        stores_to_test = [
            {
                'name': 'housing_works',
                'platform': 'blaze',
                'scraper_function': scrape_housing_works,
                'description': 'Housing Works Cannabis Co. (Blaze Platform)'
            },
            {
                'name': 'stoops',
                'platform': 'joint_ecommerce', 
                'scraper_function': scrape_stoops,
                'description': 'Stoops Brooklyn (Joint Ecommerce Platform)'
            },
            {
                'name': 'alta',
                'platform': 'joint_ecommerce',
                'scraper_function': scrape_alta,
                'description': 'Alta NYC (Joint Ecommerce Platform)'
            }
        ]
        
        logger.info(f"🧪 Starting quantity extraction test on {len(stores_to_test)} stores")
        logger.info(f"Limited to {limit_per_store} products per store for testing")
        
        for store in stores_to_test:
            try:
                logger.info(f"\n{'='*50}")
                logger.info(f"Testing store: {store['description']}")
                logger.info(f"{'='*50}")
                
                # Run the scraper
                products = await store['scraper_function'](enable_quantity_analysis=True)
                
                # Limit products for analysis
                if limit_per_store > 0:
                    products = products[:limit_per_store]
                
                # Analyze results
                store_results = self.analyze_store_results(store, products)
                
                # Store results
                self.results['detailed_results'][store['name']] = store_results
                self.results['stores_tested'].append(store['name'])
                
                logger.info(f"✅ {store['name']} test completed")
                
                # Brief delay between stores
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Failed to test {store['name']}: {e}")
                self.results['detailed_results'][store['name']] = {
                    'error': str(e),
                    'success': False
                }
        
        # Generate overall statistics
        self.generate_overall_stats()
        
        # Save results
        self.save_test_results()
        
        return self.results
    
    def analyze_store_results(self, store_config: Dict, products: List[Dict]) -> Dict[str, Any]:
        """Analyze quantity extraction results for a single store."""
        
        analysis = {
            'store_name': store_config['name'],
            'platform': store_config['platform'],
            'description': store_config['description'],
            'total_products': len(products),
            'success': True,
            'quantity_methods_used': {},
            'in_stock_count': 0,
            'out_of_stock_count': 0,
            'quantities_found_count': 0,
            'quantities_not_found_count': 0,
            'sample_products': [],
            'method_effectiveness': {},
            'recommendations': []
        }
        
        # Analyze each product
        for product in products:
            # Count stock status
            if product.get('in_stock', False):
                analysis['in_stock_count'] += 1
            else:
                analysis['out_of_stock_count'] += 1
            
            # Count quantity extraction methods
            method = product.get('quantity_method', 'unknown')
            analysis['quantity_methods_used'][method] = analysis['quantity_methods_used'].get(method, 0) + 1
            
            # Count successful quantity extraction
            if product.get('quantity_available') is not None:
                analysis['quantities_found_count'] += 1
            else:
                analysis['quantities_not_found_count'] += 1
            
            # Collect sample products for review
            if len(analysis['sample_products']) < 3:
                sample = {
                    'name': product.get('name', 'Unknown'),
                    'price': product.get('price', 0),
                    'quantity_available': product.get('quantity_available'),
                    'quantity_method': product.get('quantity_method', 'unknown'),
                    'in_stock': product.get('in_stock', False),
                    'quantity_signals': product.get('quantity_signals', [])
                }
                analysis['sample_products'].append(sample)
        
        # Calculate method effectiveness
        for method, count in analysis['quantity_methods_used'].items():
            percentage = (count / len(products)) * 100 if products else 0
            analysis['method_effectiveness'][method] = {
                'count': count,
                'percentage': round(percentage, 1)
            }
        
        # Generate recommendations
        analysis['recommendations'] = self.generate_store_recommendations(analysis)
        
        return analysis
    
    def generate_store_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations for improving quantity extraction."""
        recommendations = []
        
        total_products = analysis['total_products']
        quantities_found = analysis['quantities_found_count']
        
        if total_products == 0:
            recommendations.append("❌ No products extracted - check scraper functionality")
            return recommendations
        
        success_rate = (quantities_found / total_products) * 100
        
        if success_rate < 20:
            recommendations.append("🔧 Very low quantity extraction rate - platform may require specialized approach")
        elif success_rate < 50:
            recommendations.append("⚠️ Low quantity extraction rate - consider implementing cart probing")
        elif success_rate < 80:
            recommendations.append("📈 Moderate success rate - fine-tune selectors for better coverage")
        else:
            recommendations.append("✅ Good quantity extraction rate")
        
        # Analyze methods used
        methods = analysis['quantity_methods_used']
        
        if 'dropdown' in methods and methods['dropdown'] > 0:
            recommendations.append("✅ Quantity dropdowns working - this is reliable method")
        
        if 'stock_text' in methods and methods['stock_text'] > 0:
            recommendations.append("✅ Stock text parsing working - good fallback method")
        
        if 'default_assume_stock' in methods and methods['default_assume_stock'] > total_products * 0.5:
            recommendations.append("⚠️ Many products using default assumption - improve quantity detection")
        
        if 'cart_probe' in methods and methods['cart_probe'] > 0:
            recommendations.append("🔬 Cart probing successful - consider expanding to more products")
        
        return recommendations
    
    def generate_overall_stats(self):
        """Generate overall statistics across all tested stores."""
        
        overall = {
            'total_stores_tested': len(self.results['stores_tested']),
            'successful_stores': 0,
            'failed_stores': 0,
            'total_products_across_stores': 0,
            'total_quantities_found': 0,
            'overall_success_rate': 0,
            'best_performing_store': None,
            'worst_performing_store': None,
            'most_effective_methods': {},
            'platform_comparison': {}
        }
        
        store_success_rates = {}
        all_methods = {}
        platform_stats = {}
        
        for store_name, results in self.results['detailed_results'].items():
            if results.get('success', False):
                overall['successful_stores'] += 1
                
                total = results['total_products']
                found = results['quantities_found_count']
                
                overall['total_products_across_stores'] += total
                overall['total_quantities_found'] += found
                
                # Calculate success rate for this store
                if total > 0:
                    success_rate = (found / total) * 100
                    store_success_rates[store_name] = success_rate
                
                # Aggregate methods
                for method, count in results['quantity_methods_used'].items():
                    all_methods[method] = all_methods.get(method, 0) + count
                
                # Platform stats
                platform = results['platform']
                if platform not in platform_stats:
                    platform_stats[platform] = {'stores': 0, 'products': 0, 'quantities': 0}
                platform_stats[platform]['stores'] += 1
                platform_stats[platform]['products'] += total
                platform_stats[platform]['quantities'] += found
                
            else:
                overall['failed_stores'] += 1
        
        # Calculate overall success rate
        if overall['total_products_across_stores'] > 0:
            overall['overall_success_rate'] = round(
                (overall['total_quantities_found'] / overall['total_products_across_stores']) * 100, 1
            )
        
        # Find best and worst performing stores
        if store_success_rates:
            overall['best_performing_store'] = max(store_success_rates.items(), key=lambda x: x[1])
            overall['worst_performing_store'] = min(store_success_rates.items(), key=lambda x: x[1])
        
        # Most effective methods
        total_method_uses = sum(all_methods.values())
        for method, count in all_methods.items():
            percentage = (count / total_method_uses) * 100 if total_method_uses > 0 else 0
            overall['most_effective_methods'][method] = {
                'count': count,
                'percentage': round(percentage, 1)
            }
        
        # Platform comparison
        for platform, stats in platform_stats.items():
            if stats['products'] > 0:
                platform_success_rate = (stats['quantities'] / stats['products']) * 100
                overall['platform_comparison'][platform] = {
                    'stores_tested': stats['stores'],
                    'total_products': stats['products'],
                    'quantities_found': stats['quantities'],
                    'success_rate': round(platform_success_rate, 1)
                }
        
        self.results['overall_stats'] = overall
    
    def save_test_results(self):
        """Save test results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"memory/stealth-scraper/scrapers/inventory/quantity_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📊 Test results saved to {filename}")
        
        # Also save a summary report
        self.generate_summary_report(filename.replace('.json', '_summary.txt'))
    
    def generate_summary_report(self, filename: str):
        """Generate a human-readable summary report."""
        
        with open(filename, 'w') as f:
            f.write("QUANTITY EXTRACTION TEST SUMMARY REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Test completed at: {self.results['test_started_at']}\n")
            f.write(f"Stores tested: {len(self.results['stores_tested'])}\n\n")
            
            # Overall stats
            overall = self.results['overall_stats']
            f.write("OVERALL RESULTS:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total products tested: {overall['total_products_across_stores']}\n")
            f.write(f"Quantities successfully extracted: {overall['total_quantities_found']}\n")
            f.write(f"Overall success rate: {overall['overall_success_rate']}%\n\n")
            
            # Platform comparison
            if overall.get('platform_comparison'):
                f.write("PLATFORM COMPARISON:\n")
                f.write("-" * 20 + "\n")
                for platform, stats in overall['platform_comparison'].items():
                    f.write(f"{platform.upper()}:\n")
                    f.write(f"  Stores: {stats['stores_tested']}\n")
                    f.write(f"  Products: {stats['total_products']}\n")
                    f.write(f"  Success Rate: {stats['success_rate']}%\n\n")
            
            # Individual store results
            f.write("INDIVIDUAL STORE RESULTS:\n")
            f.write("-" * 30 + "\n")
            
            for store_name, results in self.results['detailed_results'].items():
                if results.get('success'):
                    f.write(f"\n{store_name.upper()} ({results['platform']}):\n")
                    f.write(f"  Products: {results['total_products']}\n")
                    f.write(f"  In stock: {results['in_stock_count']}\n")
                    f.write(f"  Quantities found: {results['quantities_found_count']}\n")
                    
                    if results['total_products'] > 0:
                        success_rate = (results['quantities_found_count'] / results['total_products']) * 100
                        f.write(f"  Success rate: {success_rate:.1f}%\n")
                    
                    f.write("  Methods used:\n")
                    for method, effectiveness in results['method_effectiveness'].items():
                        f.write(f"    {method}: {effectiveness['count']} ({effectiveness['percentage']}%)\n")
                    
                    f.write("  Recommendations:\n")
                    for rec in results['recommendations']:
                        f.write(f"    • {rec}\n")
                else:
                    f.write(f"\n{store_name.upper()}: FAILED\n")
                    f.write(f"  Error: {results.get('error', 'Unknown error')}\n")
        
        logger.info(f"📋 Summary report saved to {filename}")
    
    def print_results(self):
        """Print a quick summary to console."""
        print("\n" + "=" * 60)
        print("🧪 QUANTITY EXTRACTION TEST RESULTS")
        print("=" * 60)
        
        overall = self.results['overall_stats']
        print(f"📊 Overall Success Rate: {overall['overall_success_rate']}%")
        print(f"📦 Total Products Tested: {overall['total_products_across_stores']}")
        print(f"✅ Quantities Found: {overall['total_quantities_found']}")
        print(f"🏪 Stores Tested: {overall['total_stores_tested']}")
        
        print(f"\n🏆 Platform Performance:")
        for platform, stats in overall.get('platform_comparison', {}).items():
            print(f"  {platform.upper()}: {stats['success_rate']}% ({stats['quantities_found']}/{stats['total_products']})")
        
        print(f"\n🔧 Most Used Methods:")
        for method, stats in overall.get('most_effective_methods', {}).items():
            print(f"  {method}: {stats['percentage']}% of products")
        
        if overall.get('best_performing_store'):
            store, rate = overall['best_performing_store']
            print(f"\n🥇 Best performing store: {store} ({rate:.1f}%)")
        
        print("=" * 60)


async def main():
    """Main test function."""
    test = QuantityExtractionTest()
    
    try:
        # Run test on all stores with limited products for faster testing
        await test.test_all_stores(limit_per_store=5)
        
        # Print results
        test.print_results()
        
        return test.results
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return None


if __name__ == "__main__":
    # Run the test
    results = asyncio.run(main())
    
    if results:
        print("\n✅ Test completed successfully!")
        print("Check the generated files for detailed results.")
    else:
        print("\n❌ Test failed!")