#!/usr/bin/env python3
"""
Gotham NYC Scraper
Site: gotham.nyc
Framework: WordPress with Dovetail ecommerce plugin
Notes: WordPress-based with product data in HTML, potential age gate
"""

import json
import re
import subprocess
import sys
from typing import List, Dict, Optional
from urllib.parse import urljoin

class GothamScraper:
    def __init__(self):
        self.base_url = "https://gotham.nyc"
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
        """Extract product data from WordPress/Dovetail HTML structure"""
        products = []
        
        # Look for Dovetail product elements with dt- classes
        product_pattern = r'<[^>]*class="[^"]*dt-[^"]*product[^"]*"[^>]*>.*?</[^>]+>'
        product_matches = re.findall(product_pattern, html, re.DOTALL | re.IGNORECASE)
        
        if not product_matches:
            # Try alternative patterns for WordPress product listings
            product_pattern = r'<article[^>]*class="[^"]*product[^"]*"[^>]*>.*?</article>'
            product_matches = re.findall(product_pattern, html, re.DOTALL | re.IGNORECASE)
            
        print(f"Found {len(product_matches)} potential product elements")
        
        for match in product_matches:
            product = self.parse_product_html(match)
            if product:
                products.append(product)
                
        # Also look for JSON-LD structured data
        json_ld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        json_matches = re.findall(json_ld_pattern, html, re.DOTALL)
        
        for json_text in json_matches:
            try:
                data = json.loads(json_text)
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    product = self.parse_json_ld_product(data)
                    if product:
                        products.append(product)
            except json.JSONDecodeError:
                continue
                
        return products
        
    def parse_product_html(self, html: str) -> Optional[Dict]:
        """Parse product from HTML element"""
        try:
            # Extract product name
            name_match = re.search(r'<h[1-6][^>]*[^>]*>([^<]+)</h[1-6]>', html)
            if not name_match:
                name_match = re.search(r'title="([^"]+)"', html)
            
            name = name_match.group(1).strip() if name_match else "Unknown Product"
            
            # Extract price
            price_match = re.search(r'[\$€£¥][\d,]+\.?\d*', html)
            price = price_match.group(0) if price_match else "Price not available"
            
            # Extract image
            img_match = re.search(r'src="([^"]*dutchie[^"]*|[^"]*\.(jpg|jpeg|png|webp)[^"]*)"', html, re.IGNORECASE)
            image = img_match.group(1) if img_match else ""
            
            # Extract THC/CBD
            thc_match = re.search(r'THC[:\s]*([0-9.]+%?)', html, re.IGNORECASE)
            thc = thc_match.group(1) if thc_match else ""
            
            cbd_match = re.search(r'CBD[:\s]*([0-9.]+%?)', html, re.IGNORECASE)
            cbd = cbd_match.group(1) if cbd_match else ""
            
            # Extract category/type
            category_match = re.search(r'(flower|edible|vape|concentrate|pre-roll)', html, re.IGNORECASE)
            category = category_match.group(1).title() if category_match else "Unknown"
            
            product = {
                'name': name,
                'price': price,
                'image': image,
                'thc': thc,
                'cbd': cbd,
                'category': category,
                'brand': "Various",  # Gotham carries multiple brands
                'stock_status': 'in_stock',
                'url': self.base_url
            }
            
            return product
            
        except Exception as e:
            print(f"Error parsing product HTML: {e}")
            return None
            
    def parse_json_ld_product(self, data: Dict) -> Optional[Dict]:
        """Parse product from JSON-LD structured data"""
        try:
            offers = data.get('offers', {})
            price = offers.get('price', 'Price not available')
            if isinstance(price, (int, float)):
                price = f"${price:.2f}"
                
            return {
                'name': data.get('name', 'Unknown Product'),
                'price': price,
                'image': data.get('image', ''),
                'brand': data.get('brand', {}).get('name', 'Various'),
                'category': data.get('category', 'Unknown'),
                'thc': '',
                'cbd': '',
                'stock_status': 'in_stock' if offers.get('availability') == 'InStock' else 'unknown',
                'url': data.get('url', self.base_url)
            }
        except Exception as e:
            print(f"Error parsing JSON-LD product: {e}")
            return None
            
    def scrape_menu(self) -> List[Dict]:
        """Scrape products from the menu page"""
        menu_url = f"{self.base_url}/menu"
        print(f"Fetching menu from: {menu_url}")
        
        html = self.fetch_page(menu_url)
        if not html:
            print("Failed to fetch menu page")
            return []
            
        # Check for age gate and try to bypass by looking for direct product links
        if "age" in html.lower() and "verify" in html.lower():
            print("Detected potential age gate")
            # Try different menu URLs
            for path in ["/shop", "/products", "/cannabis", "/dispensary"]:
                alt_url = f"{self.base_url}{path}"
                print(f"Trying alternative URL: {alt_url}")
                alt_html = self.fetch_page(alt_url)
                if alt_html and len(alt_html) > len(html):
                    html = alt_html
                    break
        
        products = self.extract_products_from_html(html)
        print(f"Extracted {len(products)} products from menu")
        
        return products
        
    def scrape_products(self, limit: int = 20) -> List[Dict]:
        """Main scraping method"""
        print("Starting Gotham scraper...")
        
        products = self.scrape_menu()
        
        # Limit results for testing
        if limit and len(products) > limit:
            products = products[:limit]
            
        print(f"Successfully scraped {len(products)} products")
        return products

def main():
    scraper = GothamScraper()
    products = scraper.scrape_products(limit=15)
    
    # Save results
    output_file = "gotham_products.json"
    with open(output_file, 'w') as f:
        json.dump(products, f, indent=2)
        
    print(f"Results saved to {output_file}")
    
    # Print sample
    if products:
        print("\nSample products:")
        for i, product in enumerate(products[:3]):
            print(f"{i+1}. {product['name']} - {product['price']} - {product['category']}")
    else:
        print("No products found - may need JS rendering or age verification")

if __name__ == "__main__":
    main()