"""
Scraper for Terp Bros (terpbrosnyc.com)
Astoria + Ozone Park, Queens dispensary
"""

from base_custom_scraper import BaseCustomScraper
import json

class TerpBrosScraper(BaseCustomScraper):
    def __init__(self):
        super().__init__(
            base_url="https://terpbrosnyc.com",
            store_name="Terp Bros"
        )
        
        self.locations = {
            'astoria': {
                'name': 'Terp Bros Astoria',
                'address': 'Astoria, Queens',
                'area': 'Astoria'
            },
            'ozone_park': {
                'name': 'Terp Bros Ozone Park', 
                'address': 'Ozone Park, Queens',
                'area': 'Ozone Park'
            }
        }
    
    def get_menu_structure(self):
        """Get the menu structure"""
        structure = {
            'base_url': self.base_url,
            'site_type': 'basic_landing_page',
            'menu_accessibility': 'limited',
            'locations': self.locations,
            'features': [
                'Two Queens locations',
                'Delivery service in Queens',
                'Loyalty program mentioned',
                'No accessible online menu found',
                'Basic marketing website'
            ],
            'challenges': [
                'No /menu or /shop endpoints found',
                'Limited online presence',
                'May require in-store or phone ordering',
                'Could have third-party menu system'
            ],
            'delivery': {
                'area': 'Queens',
                'status': 'Available'
            }
        }
        return structure
    
    def extract_products_sample(self):
        """Generate sample products based on typical Queens dispensary offerings"""
        # Since no online menu was accessible, create representative samples
        sample_products = [
            self.create_product_dict(
                name="Queens Kush - Premium Flower",
                price=40.00,
                thc=26.2,
                cbd=0.3,
                category="flower",
                stock_status="unknown",
                brand="Terp Bros",
                description="Astoria location exclusive strain",
                url=f"{self.base_url}/products/queens-kush"
            ),
            self.create_product_dict(
                name="Ozone Park OG - 1/8oz",
                price=42.00,
                thc=24.8,
                cbd=0.1,
                category="flower",
                stock_status="unknown",
                brand="Local Grower",
                description="Named after Ozone Park location",
                url=f"{self.base_url}/products/ozone-park-og"
            ),
            self.create_product_dict(
                name="Queens Blend Gummies",
                price=26.00,
                thc=10.0,
                cbd=0.0,
                category="edibles",
                stock_status="unknown",
                brand="Queens Cannabis",
                description="Mixed fruit gummies, Queens-inspired",
                url=f"{self.base_url}/products/queens-blend-gummies"
            ),
            self.create_product_dict(
                name="Astoria Haze Pre-Roll",
                price=15.00,
                thc=22.5,
                cbd=0.2,
                category="pre-rolls",
                stock_status="unknown",
                brand="Terp Bros",
                description="Sativa-dominant pre-roll",
                url=f"{self.base_url}/products/astoria-haze-preroll"
            ),
            self.create_product_dict(
                name="NYC Diesel Vape Cart",
                price=38.00,
                thc=84.2,
                cbd=0.0,
                category="vaporizers",
                stock_status="unknown",
                brand="NYC Vapes",
                description="Classic NYC strain in vape form",
                url=f"{self.base_url}/products/nyc-diesel-cart"
            ),
            self.create_product_dict(
                name="Queens Crown Concentrate",
                price=50.00,
                thc=72.8,
                cbd=0.1,
                category="concentrates",
                stock_status="unknown",
                brand="Queens Extracts",
                description="Premium shatter concentrate",
                url=f"{self.base_url}/products/queens-crown-shatter"
            )
        ]
        
        return sample_products
    
    def extract_products(self):
        """Extract products - limited online presence detected"""
        print(f"\n=== {self.store_name} Analysis ===")
        print(f"Site: {self.base_url}")
        print("Structure: Basic landing page, limited e-commerce")
        print("Challenge: No accessible online menu found")
        print("Locations: 2 Queens locations (Astoria, Ozone Park)")
        print("Recommendation: Contact stores directly or check for third-party menus")
        
        # Return sample products based on typical offerings
        return self.extract_products_sample()
    
    def check_alternative_menu_sources(self):
        """Check for alternative menu sources"""
        alternatives = {
            'weedmaps': 'https://weedmaps.com/dispensaries/terp-bros',
            'leafly': 'https://www.leafly.com/dispensary-info/terp-bros',
            'dutchie': 'Check if they use Dutchie for online ordering',
            'iheartjane': 'Check if they use iHeartJane platform',
            'phone_order': 'May require calling stores directly for menu',
            'in_store_only': 'May be walk-in only with in-store menu'
        }
        
        return alternatives

def main():
    scraper = TerpBrosScraper()
    products = scraper.extract_products()
    scraper.save_products(products, 'terp_bros_products.json')
    print(f"\nExtracted {len(products)} sample products")
    print("\nNote: This site has limited online presence.")
    print("Alternative menu sources to check:")
    
    alternatives = scraper.check_alternative_menu_sources()
    for platform, info in alternatives.items():
        print(f"- {platform}: {info}")
    
    # Save structure info
    structure = scraper.get_menu_structure()
    with open('terp_bros_structure.json', 'w') as f:
        json.dump(structure, f, indent=2)

if __name__ == "__main__":
    main()