#!/usr/bin/env python3
"""
The Travel Agency Scraper
Site: thetravelagency.co
Framework: Remix/React with server-side rendering
Notes: Products are embedded in HTML as JSON data, uses Dutchie for images
"""

import json
import re
import subprocess
import sys
from typing import List, Dict, Optional

class TravelAgencyScraper:
    def __init__(self):
        self.base_url = "https://thetravelagency.co"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
    def fetch_page(self, url: str) -> str:
        """Fetch a page using curl"""
        cmd = [
            'curl', '-L', '-s', '-A', self.user_agent, url
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
            
    def extract_products_from_html(self, html: str) -> List[Dict]:
        """Extract product data from the embedded JSON in HTML"""
        products = []
        
        # Look for the embedded window.__remixContext data
        remix_match = re.search(r'window\.__remixContext\s*=\s*({.+?});', html, re.DOTALL)
        if not remix_match:
            print("No Remix context found in HTML")
            return products
            
        try:
            remix_data = json.loads(remix_match.group(1))
            
            # Navigate through the Remix data structure to find products
            loader_data = remix_data.get('state', {}).get('loaderData', {})
            
            for route_key, route_data in loader_data.items():
                if isinstance(route_data, dict) and 'products' in route_data:
                    raw_products = route_data['products']
                    
                    if isinstance(raw_products, list):
                        for product in raw_products:
                            extracted = self.parse_product(product)
                            if extracted:
                                products.append(extracted)
                                
        except json.JSONDecodeError as e:
            print(f"Error parsing Remix JSON: {e}")
            
        return products
        
    def parse_product(self, product_data: Dict) -> Optional[Dict]:
        """Parse individual product data"""
        if not isinstance(product_data, dict):
            return None
            
        try:
            # Extract basic product info
            product = {
                'id': product_data.get('_17', ''),
                'name': product_data.get('_33', ''),
                'brand': product_data.get('_95', ''),
                'category': product_data.get('_98', ''),
                'price': product_data.get('_102', 0),
                'image': product_data.get('_96', ''),
                'thc': product_data.get('_109', ''),
                'cbd': product_data.get('_111', ''),
                'size': product_data.get('_112', ''),
                'classification': product_data.get('_91', ''),
                'stock_status': 'in_stock',  # Assume in stock if listed
                'url': f"{self.base_url}/products/{product_data.get('_107', '')}"
            }
            
            # Clean up data
            if isinstance(product['price'], (int, float)) and product['price'] > 0:
                product['price'] = f"${product['price']:.2f}"
            else:
                product['price'] = "Price not available"
                
            return product
            
        except Exception as e:
            print(f"Error parsing product: {e}")
            return None
            
    def scrape_menu(self) -> List[Dict]:
        """Scrape products from the menu page"""
        menu_url = f"{self.base_url}/menu"
        print(f"Fetching menu from: {menu_url}")
        
        html = self.fetch_page(menu_url)
        if not html:
            print("Failed to fetch menu page")
            return []
            
        products = self.extract_products_from_html(html)
        print(f"Extracted {len(products)} products from menu")
        
        return products
        
    def scrape_products(self, limit: int = 20) -> List[Dict]:
        """Main scraping method"""
        print("Starting Travel Agency scraper...")
        
        products = self.scrape_menu()
        
        # Limit results for testing
        if limit and len(products) > limit:
            products = products[:limit]
            
        print(f"Successfully scraped {len(products)} products")
        return products

def main():
    scraper = TravelAgencyScraper()
    products = scraper.scrape_products(limit=15)
    
    # Save results
    output_file = "travel_agency_products.json"
    with open(output_file, 'w') as f:
        json.dump(products, f, indent=2)
        
    print(f"Results saved to {output_file}")
    
    # Print sample
    if products:
        print("\nSample products:")
        for i, product in enumerate(products[:3]):
            print(f"{i+1}. {product['name']} - {product['price']} - THC: {product['thc']}")

if __name__ == "__main__":
    main()