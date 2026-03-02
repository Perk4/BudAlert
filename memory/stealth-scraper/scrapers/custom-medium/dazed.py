#!/usr/bin/env python3
"""
Dazed Cannabis Scraper
Site: dazed.fun
Framework: WordPress with custom theme and multi-store picker
Notes: Age gate popup, store selector for Holyoke MA and Union Square NYC
"""

import json
import re
import subprocess
import sys
from typing import List, Dict, Optional
from urllib.parse import urljoin

class DazedScraper:
    def __init__(self):
        self.base_url = "https://dazed.fun"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
    def fetch_page(self, url: str, cookies: str = None) -> str:
        """Fetch a page using curl with optional cookies"""
        cmd = [
            'curl', '-L', '-s', '-A', self.user_agent
        ]
        
        if cookies:
            cmd.extend(['-H', f'Cookie: {cookies}'])
            
        cmd.append(url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
            
    def bypass_age_gate(self) -> str:
        """Attempt to bypass age verification by setting cookies"""
        # Common age verification cookie names
        age_cookies = [
            "age_verified=1",
            "age_gate=passed",
            "over_21=true",
            "age_check=yes"
        ]
        
        for cookie in age_cookies:
            print(f"Trying age gate bypass with cookie: {cookie}")
            html = self.fetch_page(self.base_url, cookie)
            if html and "age" not in html.lower() or len(html) > 5000:
                print("Age gate bypass successful")
                return html
                
        print("Could not bypass age gate with cookies")
        return ""
        
    def extract_store_links(self, html: str) -> List[str]:
        """Extract store-specific menu links"""
        store_links = []
        
        # Look for store-specific URLs
        store_patterns = [
            r'href="([^"]*(?:menu|shop|dispensary|nyc|union|square)[^"]*)"',
            r'href="([^"]*store[^"]*)"',
            r'data-store-url="([^"]*)"'
        ]
        
        for pattern in store_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            store_links.extend(matches)
            
        # Clean and absolutify URLs
        cleaned_links = []
        for link in store_links:
            if link.startswith('/'):
                link = urljoin(self.base_url, link)
            elif not link.startswith('http'):
                continue
            cleaned_links.append(link)
            
        return list(set(cleaned_links))  # Remove duplicates
        
    def extract_products_from_html(self, html: str) -> List[Dict]:
        """Extract product data from WordPress HTML"""
        products = []
        
        # WordPress product patterns
        product_patterns = [
            r'<div[^>]*class="[^"]*product[^"]*"[^>]*>.*?</div>',
            r'<article[^>]*class="[^"]*product[^"]*"[^>]*>.*?</article>',
            r'<li[^>]*class="[^"]*product[^"]*"[^>]*>.*?</li>'
        ]
        
        for pattern in product_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            print(f"Found {len(matches)} products with pattern")
            
            for match in matches:
                product = self.parse_product_html(match)
                if product:
                    products.append(product)
                    
        # Also look for WooCommerce or other e-commerce JSON data
        json_patterns = [
            r'wc_add_to_cart_params\s*=\s*({.*?});',
            r'product_data\s*=\s*({.*?});',
            r'var\s+products\s*=\s*(\[.*?\]);'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, list):
                        for item in data:
                            product = self.parse_json_product(item)
                            if product:
                                products.append(product)
                    elif isinstance(data, dict) and 'products' in data:
                        for item in data['products']:
                            product = self.parse_json_product(item)
                            if product:
                                products.append(product)
                except json.JSONDecodeError:
                    continue
                    
        return products
        
    def parse_product_html(self, html: str) -> Optional[Dict]:
        """Parse product from HTML element"""
        try:
            # Extract product name
            name_patterns = [
                r'<h[1-6][^>]*>([^<]+)</h[1-6]>',
                r'class="[^"]*product[^"]*title[^"]*"[^>]*>([^<]+)<',
                r'title="([^"]+)"'
            ]
            
            name = "Unknown Product"
            for pattern in name_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    break
            
            # Extract price
            price_patterns = [
                r'[\$€£¥]\s*[\d,]+\.?\d*',
                r'class="[^"]*price[^"]*"[^>]*>.*?([\d,]+\.?\d*)',
                r'data-price="([^"]*)"'
            ]
            
            price = "Price not available"
            for pattern in price_patterns:
                match = re.search(pattern, html)
                if match:
                    price = match.group(0) if '$' in match.group(0) else f"${match.group(1)}"
                    break
            
            # Extract image
            img_match = re.search(r'src="([^"]*\.(jpg|jpeg|png|webp)[^"]*)"', html, re.IGNORECASE)
            image = img_match.group(1) if img_match else ""
            
            # Extract THC/CBD
            thc_match = re.search(r'THC[:\s]*([0-9.]+%?)', html, re.IGNORECASE)
            thc = thc_match.group(1) if thc_match else ""
            
            cbd_match = re.search(r'CBD[:\s]*([0-9.]+%?)', html, re.IGNORECASE)
            cbd = cbd_match.group(1) if cbd_match else ""
            
            # Extract category
            category_patterns = [
                r'class="[^"]*category[^"]*"[^>]*>([^<]+)<',
                r'data-category="([^"]*)"',
                r'(flower|edible|vape|concentrate|pre-roll|cartridge)'
            ]
            
            category = "Unknown"
            for pattern in category_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    category = match.group(1).strip().title()
                    break
            
            product = {
                'name': name,
                'price': price,
                'image': image,
                'thc': thc,
                'cbd': cbd,
                'category': category,
                'brand': "Dazed",
                'stock_status': 'in_stock',
                'url': self.base_url
            }
            
            return product
            
        except Exception as e:
            print(f"Error parsing product HTML: {e}")
            return None
            
    def parse_json_product(self, data: Dict) -> Optional[Dict]:
        """Parse product from JSON data"""
        try:
            name = data.get('name', data.get('title', 'Unknown Product'))
            price = data.get('price', data.get('cost', 'Price not available'))
            
            if isinstance(price, (int, float)):
                price = f"${price:.2f}"
                
            return {
                'name': str(name),
                'price': str(price),
                'image': data.get('image', data.get('image_url', '')),
                'thc': data.get('thc', data.get('thc_content', '')),
                'cbd': data.get('cbd', data.get('cbd_content', '')),
                'category': data.get('category', data.get('type', 'Unknown')),
                'brand': data.get('brand', 'Dazed'),
                'stock_status': 'in_stock' if data.get('in_stock', True) else 'out_of_stock',
                'url': data.get('url', self.base_url)
            }
        except Exception as e:
            print(f"Error parsing JSON product: {e}")
            return None
            
    def scrape_menu(self) -> List[Dict]:
        """Scrape products from menu pages"""
        print("Attempting to access Dazed menu...")
        
        # First try to bypass age gate
        html = self.bypass_age_gate()
        if not html:
            html = self.fetch_page(self.base_url)
            
        products = []
        
        # Try direct menu URLs
        menu_urls = [
            f"{self.base_url}/menu",
            f"{self.base_url}/shop",
            f"{self.base_url}/products",
            f"{self.base_url}/dispensary/nyc",
            f"{self.base_url}/dispensary/union-square"
        ]
        
        for url in menu_urls:
            print(f"Trying menu URL: {url}")
            page_html = self.fetch_page(url)
            if page_html:
                page_products = self.extract_products_from_html(page_html)
                products.extend(page_products)
                if page_products:
                    print(f"Found {len(page_products)} products from {url}")
                    
        # Also try to find store-specific links
        store_links = self.extract_store_links(html)
        for link in store_links:
            print(f"Trying store link: {link}")
            store_html = self.fetch_page(link)
            if store_html:
                store_products = self.extract_products_from_html(store_html)
                products.extend(store_products)
                
        print(f"Total products extracted: {len(products)}")
        return products
        
    def scrape_products(self, limit: int = 20) -> List[Dict]:
        """Main scraping method"""
        print("Starting Dazed scraper...")
        
        products = self.scrape_menu()
        
        # Remove duplicates based on name
        seen_names = set()
        unique_products = []
        for product in products:
            if product['name'] not in seen_names:
                seen_names.add(product['name'])
                unique_products.append(product)
                
        # Limit results for testing
        if limit and len(unique_products) > limit:
            unique_products = unique_products[:limit]
            
        print(f"Successfully scraped {len(unique_products)} unique products")
        return unique_products

def main():
    scraper = DazedScraper()
    products = scraper.scrape_products(limit=15)
    
    # Save results
    output_file = "dazed_products.json"
    with open(output_file, 'w') as f:
        json.dump(products, f, indent=2)
        
    print(f"Results saved to {output_file}")
    
    # Print sample
    if products:
        print("\nSample products:")
        for i, product in enumerate(products[:3]):
            print(f"{i+1}. {product['name']} - {product['price']} - {product['category']}")
    else:
        print("No products found - may require JS rendering or proper age verification")

if __name__ == "__main__":
    main()