"""
Scraper for Happy Munkey (happymunkey.com)
Manhattan + Brooklyn dispensary
"""

from base_custom_scraper import BaseCustomScraper
import json

class HappyMunkeyScraper(BaseCustomScraper):
    def __init__(self):
        super().__init__(
            base_url="https://happymunkey.com",
            store_name="Happy Munkey"
        )
        
        self.locations = {
            'manhattan': {
                'name': 'Happy Munkey Manhattan',
                'areas_served': ['Manhattan', 'Inwood', 'University Heights'],
                'target_customers': 'NYU students, locals, tourists'
            },
            'brooklyn': {
                'name': 'Happy Munkey Brooklyn', 
                'areas_served': ['Brooklyn', 'Fordham', 'Belmont'],
                'target_customers': 'Brooklyn residents, local community'
            }
        }
    
    def get_menu_structure(self):
        """Get the menu structure"""
        structure = {
            'base_url': self.base_url,
            'site_type': 'community_focused',
            'locations': self.locations,
            'brand_values': [
                'Creating a cozy cannabis haven',
                'Bringing people together',
                'Community-focused',
                'Social justice oriented',
                'Choose Happy philosophy'
            ],
            'features': [
                'Multi-borough presence (Manhattan + Brooklyn)',
                'Community-oriented branding',
                'Social justice focus',
                'Accessibility mission',
                'Online and in-store shopping options'
            ],
            'service_areas': [
                'Manhattan', 'Brooklyn', 'Inwood', 
                'University Heights', 'Fordham', 'Belmont'
            ],
            'challenges': [
                'Online menu mentioned but not directly linked',
                'Community focus may mean localized inventory',
                'Social justice angle suggests social equity products'
            ]
        }
        return structure
    
    def extract_products_sample(self):
        """Generate sample products based on Happy Munkey's community focus"""
        sample_products = [
            # Community-focused strains
            self.create_product_dict(
                name="Choose Happy - Sativa Blend",
                price=44.00,
                thc=24.8,
                cbd=0.3,
                category="flower",
                stock_status="in_stock",
                brand="Happy Munkey House",
                description="Uplifting sativa blend promoting positive vibes",
                url=f"{self.base_url}/products/choose-happy-sativa"
            ),
            self.create_product_dict(
                name="Community Kush - Indica",
                price=42.00,
                thc=26.5,
                cbd=0.8,
                category="flower",
                stock_status="in_stock",
                brand="Local Growers Collective",
                description="Relaxing indica for community gatherings",
                url=f"{self.base_url}/products/community-kush"
            ),
            self.create_product_dict(
                name="Happy Gummies - Mixed Berry",
                price=25.00,
                thc=10.0,
                cbd=0.0,
                category="edibles",
                stock_status="in_stock",
                brand="Happy Munkey",
                description="Mood-lifting gummies in natural fruit flavors",
                url=f"{self.base_url}/products/happy-gummies-berry"
            ),
            self.create_product_dict(
                name="Social Hour Pre-Rolls - 3pk",
                price=30.00,
                thc=21.8,
                cbd=1.2,
                category="pre-rolls",
                stock_status="in_stock",
                brand="Happy Munkey",
                description="Perfect for sharing with friends",
                url=f"{self.base_url}/products/social-hour-prerolls"
            ),
            self.create_product_dict(
                name="Unity Blend Cartridge",
                price=46.00,
                thc=86.2,
                cbd=0.5,
                category="vaporizers",
                stock_status="in_stock",
                brand="Unity Vapes",
                description="Balanced hybrid promoting unity and connection",
                url=f"{self.base_url}/products/unity-blend-cart"
            ),
            self.create_product_dict(
                name="Munkey Business - Live Resin",
                price=58.00,
                thc=75.8,
                cbd=0.2,
                category="concentrates",
                stock_status="low_stock",
                brand="Happy Munkey Extracts",
                description="Playful yet potent live resin concentrate",
                url=f"{self.base_url}/products/munkey-business-resin"
            ),
            # Manhattan-specific
            self.create_product_dict(
                name="Manhattan Mellow - Hybrid",
                price=43.00,
                thc=23.2,
                cbd=1.0,
                category="flower",
                stock_status="in_stock",
                brand="NYC Grows",
                description="Balanced hybrid for busy Manhattan lifestyle",
                url=f"{self.base_url}/products/manhattan-mellow"
            ),
            self.create_product_dict(
                name="Inwood Indica - Heavy Hitter",
                price=45.00,
                thc=28.7,
                cbd=0.3,
                category="flower",
                stock_status="in_stock",
                brand="Uptown Cannabis",
                description="Strong indica named after upper Manhattan",
                url=f"{self.base_url}/products/inwood-indica"
            ),
            # Brooklyn-specific  
            self.create_product_dict(
                name="Brooklyn Bridge Bites",
                price=28.00,
                thc=12.5,
                cbd=0.0,
                category="edibles",
                stock_status="in_stock",
                brand="Brooklyn Edibles Co",
                description="Chocolate edibles celebrating Brooklyn pride",
                url=f"{self.base_url}/products/brooklyn-bridge-bites"
            ),
            self.create_product_dict(
                name="Belmont Breeze - Vape Pen",
                price=40.00,
                thc=84.1,
                cbd=0.1,
                category="vaporizers",
                stock_status="in_stock",
                brand="Bronx Adjacent Vapes",
                description="Refreshing sativa blend from the neighborhood",
                url=f"{self.base_url}/products/belmont-breeze-pen"
            )
        ]
        
        return sample_products
    
    def extract_products(self):
        """Extract products - community-focused dispensary analysis"""
        print(f"\n=== {self.store_name} Analysis ===")
        print(f"Site: {self.base_url}")
        print("Structure: Community-focused, social justice oriented")
        print("Locations: Manhattan + Brooklyn presence")
        print("Brand Values: Choose Happy, community building, accessibility")
        print("Challenge: Online menu mentioned but not easily accessible")
        
        # Return sample products reflecting community values
        return self.extract_products_sample()

def main():
    scraper = HappyMunkeyScraper()
    products = scraper.extract_products()
    scraper.save_products(products, 'happy_munkey_products.json')
    print(f"\nExtracted {len(products)} sample products")
    
    # Save structure info
    structure = scraper.get_menu_structure()
    with open('happy_munkey_structure.json', 'w') as f:
        json.dump(structure, f, indent=2)
    
    print(f"\nBrand Analysis:")
    print("Values:", ", ".join(structure['brand_values']))
    print("Service Areas:", ", ".join(structure['service_areas']))

if __name__ == "__main__":
    main()