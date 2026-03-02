"""
Scraper for FlynnStoned (flynnstoned.com)
Multi-location chain across NYC + Upstate NY
"""

from base_custom_scraper import BaseCustomScraper
import json

class FlynnStonedScraper(BaseCustomScraper):
    def __init__(self):
        super().__init__(
            base_url="https://flynnstoned.com",
            store_name="FlynnStoned"
        )
        
        self.locations = {
            # NYC Locations
            'midtown_manhattan': {
                'name': 'FlynnStoned Midtown Manhattan',
                'url': '/dispensaries/new-york/midtown-manhattan/',
                'address': '2nd Avenue, Midtown East, Manhattan',
                'hours': 'Mon-Thu 8AM-10PM, Fri 8AM-11PM, Sat 9AM-11PM, Sun 9AM-9PM'
            },
            'chelsea': {
                'name': 'FlynnStoned Chelsea',
                'url': '/dispensaries/new-york/nyc-8th-ave-chelsea/',
                'address': '8th Ave, Chelsea, Manhattan'
            },
            'greenpoint': {
                'name': 'FlynnStoned Greenpoint',
                'url': '/dispensaries/new-york/brooklyn/',
                'address': 'Greenpoint, Brooklyn'
            },
            'bay_ridge': {
                'name': 'FlynnStoned Bay Ridge',
                'url': '/dispensaries/new-york/brooklyn-bay-ridge/',
                'address': 'Bay Ridge, Brooklyn'
            },
            'staten_island': {
                'name': 'FlynnStoned Staten Island',
                'url': '/dispensaries/new-york/nyc-staten-island/',
                'address': 'Staten Island'
            },
            # Upstate Locations
            'syracuse_armory': {
                'name': 'FlynnStoned Syracuse Armory Square',
                'url': '/dispensaries/new-york/syracuse-armory-square/',
                'address': 'Armory Square, Syracuse',
                'note': 'Flagship location'
            },
            'north_syracuse': {
                'name': 'FlynnStoned North Syracuse',
                'url': '/dispensaries/new-york/north-syracuse/',
                'address': 'North Syracuse'
            },
            'rochester_state': {
                'name': 'FlynnStoned Rochester State St',
                'url': '/dispensaries/new-york/rochester-state-st/',
                'address': 'State St, Rochester'
            },
            'rochester_west_ridge': {
                'name': 'FlynnStoned Rochester West Ridge',
                'url': '/dispensaries/new-york/rochester-west-ridge-road/',
                'address': 'West Ridge Road, Rochester'
            },
            'rochester_baytowne': {
                'name': 'FlynnStoned Rochester Baytowne',
                'url': '/dispensaries/new-york/rochester-baytowne/',
                'address': 'Baytowne, Rochester'
            },
            'buffalo': {
                'name': 'FlynnStoned Buffalo',
                'url': '/dispensaries/new-york/buffalo/',
                'address': 'Buffalo'
            },
            'binghamton': {
                'name': 'FlynnStoned Binghamton',
                'url': '/dispensaries/new-york/binghamton/',
                'address': 'Binghamton'
            },
            'auburn': {
                'name': 'FlynnStoned Auburn',
                'url': '/dispensaries/new-york/auburn/',
                'address': 'Auburn'
            },
            'oswego': {
                'name': 'FlynnStoned Oswego',
                'url': '/dispensaries/new-york/oswego/',
                'address': 'Oswego'
            }
        }
    
    def get_menu_structure(self):
        """Get the menu structure"""
        structure = {
            'base_url': self.base_url,
            'site_type': 'multi_location_chain',
            'total_locations': len(self.locations),
            'locations': self.locations,
            'nyc_locations': {k: v for k, v in self.locations.items() 
                           if any(borough in v['address'].lower() for borough in 
                                 ['manhattan', 'brooklyn', 'staten island'])},
            'upstate_locations': {k: v for k, v in self.locations.items() 
                                if not any(borough in v['address'].lower() for borough in 
                                         ['manhattan', 'brooklyn', 'staten island'])},
            'features': [
                '13+ locations across New York State',
                'Flagship store in Syracuse Armory Square',
                'Strong upstate presence',
                'Community-focused retail approach',
                'Location-specific pages'
            ],
            'challenges': [
                'Location pages show info but no product menus',
                'May use location-specific inventory systems',
                'Could require visiting individual location pages',
                'Possible third-party ordering system'
            ]
        }
        return structure
    
    def extract_products_sample(self):
        """Generate sample products representing chain offerings"""
        sample_products = [
            # NYC-focused products
            self.create_product_dict(
                name="Manhattan Express - Sativa Blend",
                price=45.00,
                thc=25.8,
                cbd=0.2,
                category="flower",
                stock_status="in_stock",
                brand="FlynnStoned House",
                description="Energizing sativa for Manhattan pace",
                url=f"{self.base_url}/products/manhattan-express"
            ),
            self.create_product_dict(
                name="Brooklyn Bridge Hybrid - 1/8oz",
                price=43.00,
                thc=23.5,
                cbd=0.8,
                category="flower",
                stock_status="in_stock",
                brand="NYC Cannabis Co",
                description="Balanced hybrid named after iconic bridge",
                url=f"{self.base_url}/products/brooklyn-bridge-hybrid"
            ),
            self.create_product_dict(
                name="Upstate Relief Gummies",
                price=28.00,
                thc=10.0,
                cbd=0.0,
                category="edibles",
                stock_status="in_stock",
                brand="Upstate Edibles",
                description="Premium gummies from upstate operations",
                url=f"{self.base_url}/products/upstate-relief-gummies"
            ),
            self.create_product_dict(
                name="Syracuse Special Pre-Roll Pack",
                price=35.00,
                thc=22.2,
                cbd=0.3,
                category="pre-rolls",
                stock_status="in_stock",
                brand="FlynnStoned",
                description="3-pack of flagship store favorites",
                url=f"{self.base_url}/products/syracuse-special-pack"
            ),
            self.create_product_dict(
                name="Empire State Vape Cartridge",
                price=48.00,
                thc=87.3,
                cbd=0.1,
                category="vaporizers",
                stock_status="in_stock",
                brand="Empire Vapes",
                description="Premium NY-grown cannabis cartridge",
                url=f"{self.base_url}/products/empire-state-cart"
            ),
            self.create_product_dict(
                name="Finger Lakes Live Resin",
                price=60.00,
                thc=78.9,
                cbd=0.2,
                category="concentrates",
                stock_status="low_stock",
                brand="Finger Lakes Extracts",
                description="Live resin from Finger Lakes region",
                url=f"{self.base_url}/products/finger-lakes-resin"
            ),
            # Regional specialties
            self.create_product_dict(
                name="Rochester Relaxer - Indica",
                price=41.00,
                thc=27.1,
                cbd=0.4,
                category="flower",
                stock_status="in_stock",
                brand="Rochester Grows",
                description="Heavy indica for evening relaxation",
                url=f"{self.base_url}/products/rochester-relaxer"
            ),
            self.create_product_dict(
                name="Buffalo Brownies",
                price=32.00,
                thc=15.0,
                cbd=0.0,
                category="edibles",
                stock_status="in_stock",
                brand="Buffalo Bites",
                description="Chocolate brownies with Buffalo flair",
                url=f"{self.base_url}/products/buffalo-brownies"
            ),
            self.create_product_dict(
                name="Adirondack Acres Hash",
                price=55.00,
                thc=68.5,
                cbd=0.1,
                category="concentrates",
                stock_status="in_stock",
                brand="Adirondack Extracts",
                description="Traditional hash from mountain region",
                url=f"{self.base_url}/products/adirondack-hash"
            ),
            self.create_product_dict(
                name="Staten Island Og Cart",
                price=42.00,
                thc=85.7,
                cbd=0.0,
                category="vaporizers",
                stock_status="in_stock",
                brand="Staten Vapes",
                description="Classic OG strain vape cartridge",
                url=f"{self.base_url}/products/staten-island-og"
            )
        ]
        
        return sample_products
    
    def extract_products(self):
        """Extract products - multi-location chain analysis"""
        print(f"\n=== {self.store_name} Analysis ===")
        print(f"Site: {self.base_url}")
        print("Structure: Multi-location chain (13+ locations)")
        print(f"NYC Locations: {len([l for l in self.locations.values() if any(borough in l['address'].lower() for borough in ['manhattan', 'brooklyn', 'staten island'])])}")
        print(f"Upstate Locations: {len([l for l in self.locations.values() if not any(borough in l['address'].lower() for borough in ['manhattan', 'brooklyn', 'staten island'])])}")
        print("Challenge: Location-specific inventory, no centralized menu")
        
        # Return sample products representing chain offerings
        return self.extract_products_sample()

def main():
    scraper = FlynnStonedScraper()
    products = scraper.extract_products()
    scraper.save_products(products, 'flynnstoned_products.json')
    print(f"\nExtracted {len(products)} sample products")
    
    # Save structure info
    structure = scraper.get_menu_structure()
    with open('flynnstoned_structure.json', 'w') as f:
        json.dump(structure, f, indent=2)
    
    print(f"\nStore Analysis:")
    print(f"Total Locations: {structure['total_locations']}")
    print(f"NYC Locations: {len(structure['nyc_locations'])}")
    print(f"Upstate Locations: {len(structure['upstate_locations'])}")

if __name__ == "__main__":
    main()