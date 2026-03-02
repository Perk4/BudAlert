"""
Scraper for Yerba Buena (yerbabuena.nyc)
Cobble Hill, Brooklyn dispensary
"""

from base_custom_scraper import JSBasedScraper
import json

class YerbaBuenaScraper(JSBasedScraper):
    def __init__(self):
        super().__init__(
            base_url="https://yerbabuena.nyc",
            store_name="Yerba Buena",
            menu_selectors={
                'menu_url': '/shop/cobblehill',
                'categories': {
                    'flower': '/shop/cobblehill/categories/flower',
                    'edibles': '/shop/cobblehill/categories/edibles',
                    'pre-rolls': '/shop/cobblehill/categories/pre-rolls',
                    'vaporizers': '/shop/cobblehill/categories/vaporizers',
                    'concentrates': '/shop/cobblehill/categories/concentrates',
                    'tinctures': '/shop/cobblehill/categories/tinctures',
                    'topicals': '/shop/cobblehill/categories/topicals',
                    'accessories': '/shop/cobblehill/categories/accessories',
                    'beverages': '/shop/cobblehill/categories/beverages',
                    'merchandise': '/shop/cobblehill/categories/merchandise'
                },
                'offers': '/shop/cobblehill/offers'
            }
        )
    
    def get_menu_structure(self):
        """Get the menu structure"""
        structure = {
            'base_url': self.base_url,
            'menu_page': f"{self.base_url}/shop/cobblehill",
            'categories': self.menu_selectors['categories'],
            'offers_page': f"{self.base_url}/shop/cobblehill/offers",
            'location_specific': True,
            'location_slug': 'cobblehill',
            'features': [
                'Location-specific inventory (cobblehill)',
                'Offers/specials page',
                '10 product categories including beverages',
                'Seed Circle Rewards program',
                'Minority-owned, family-owned, women-owned'
            ],
            'location': {
                'address': '292 Atlantic Avenue, Cobble Hill, Brooklyn, NY 11201',
                'neighborhood': 'Cobble Hill, Brooklyn',
                'target_customers': 'Local Brooklyn residents, tourists'
            }
        }
        return structure
    
    def extract_products_sample(self):
        """Generate sample products based on site structure"""
        sample_products = [
            self.create_product_dict(
                name="Sativa Sunrise Flower - 1/8oz",
                price=38.00,
                thc=23.4,
                cbd=0.2,
                category="flower",
                stock_status="in_stock",
                brand="Local Grower",
                description="Energizing sativa for morning use",
                url=f"{self.base_url}/shop/cobblehill/products/sativa-sunrise"
            ),
            self.create_product_dict(
                name="Brooklyn Blend Gummies - 10mg",
                price=24.00,
                thc=10.0,
                cbd=0.0,
                category="edibles",
                stock_status="in_stock",
                brand="Local Brand",
                description="Locally inspired fruit gummies",
                url=f"{self.base_url}/shop/cobblehill/products/brooklyn-blend-gummies"
            ),
            self.create_product_dict(
                name="Cobble Hill Calm Pre-Roll",
                price=16.00,
                thc=20.1,
                cbd=1.2,
                category="pre-rolls",
                stock_status="in_stock",
                brand="House Brand",
                description="Indica-dominant pre-roll for relaxation",
                url=f"{self.base_url}/shop/cobblehill/products/cobble-hill-calm"
            ),
            self.create_product_dict(
                name="Atlantic Avenue Vape Cart",
                price=45.00,
                thc=88.5,
                cbd=0.0,
                category="vaporizers",
                stock_status="low_stock",
                brand="Premium Vapes",
                description="Hybrid strain vape cartridge",
                url=f"{self.base_url}/shop/cobblehill/products/atlantic-avenue-cart"
            ),
            self.create_product_dict(
                name="Brooklyn Heights Hash",
                price=55.00,
                thc=65.8,
                cbd=0.1,
                category="concentrates",
                stock_status="in_stock",
                brand="Brooklyn Extracts",
                description="Traditional hash, local favorite",
                url=f"{self.base_url}/shop/cobblehill/products/brooklyn-heights-hash"
            ),
            self.create_product_dict(
                name="CBD Relief Tincture - 30ml",
                price=35.00,
                thc=0.0,
                cbd=25.0,
                category="tinctures",
                stock_status="in_stock",
                brand="Wellness Co",
                description="High CBD tincture for pain relief",
                url=f"{self.base_url}/shop/cobblehill/products/cbd-relief-tincture"
            ),
            self.create_product_dict(
                name="Soothing Balm - 2oz",
                price=28.00,
                thc=0.0,
                cbd=15.0,
                category="topicals",
                stock_status="in_stock",
                brand="Natural Remedies",
                description="CBD-infused topical balm",
                url=f"{self.base_url}/shop/cobblehill/products/soothing-balm"
            ),
            self.create_product_dict(
                name="Glass Pipe - Brooklyn Design",
                price=32.00,
                thc=None,
                cbd=None,
                category="accessories",
                stock_status="in_stock",
                brand="Local Glass",
                description="Hand-blown glass pipe with Brooklyn skyline",
                url=f"{self.base_url}/shop/cobblehill/products/brooklyn-glass-pipe"
            ),
            self.create_product_dict(
                name="THC Sparkling Water - Citrus",
                price=12.00,
                thc=5.0,
                cbd=0.0,
                category="beverages",
                stock_status="in_stock",
                brand="Refresh Cannabis",
                description="Low-dose THC beverage, citrus flavor",
                url=f"{self.base_url}/shop/cobblehill/products/thc-sparkling-citrus"
            ),
            self.create_product_dict(
                name="Yerba Buena T-Shirt",
                price=25.00,
                thc=None,
                cbd=None,
                category="merchandise",
                stock_status="in_stock",
                brand="Yerba Buena",
                description="Official store merchandise",
                url=f"{self.base_url}/shop/cobblehill/products/yerba-buena-tshirt"
            )
        ]
        
        return sample_products
    
    def extract_products(self):
        """Extract products - would need browser automation for real data"""
        print(f"\n=== {self.store_name} Analysis ===")
        print(f"Site: {self.base_url}")
        print("Structure: Location-specific inventory system")
        print("Categories: 10 categories including beverages/merchandise")
        print("Special Features: Minority/family/women-owned business")
        print("Location: Cobble Hill, Brooklyn - residential area")
        
        # Return sample products to demonstrate structure
        return self.extract_products_sample()

def main():
    scraper = YerbaBuenaScraper()
    products = scraper.extract_products()
    scraper.save_products(products, 'yerba_buena_products.json')
    print(f"\nExtracted {len(products)} sample products")
    
    # Save structure info
    structure = scraper.get_menu_structure()
    with open('yerba_buena_structure.json', 'w') as f:
        json.dump(structure, f, indent=2)

if __name__ == "__main__":
    main()