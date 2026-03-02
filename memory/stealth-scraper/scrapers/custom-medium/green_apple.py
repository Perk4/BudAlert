#!/usr/bin/env python3
"""
Green Apple Scraper
Site: greenapple.nyc
Framework: Custom WordPress theme with heavy JavaScript
Notes: Age verification popup, JS-heavy product loading, Brooklyn location
"""

import json
import re
import subprocess
import sys
from typing import List, Dict, Optional
from urllib.parse import urljoin

class GreenAppleScraper:
    def __init__(self):
        self.base_url = "https://greenapple.nyc"
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
        """Attempt to bypass age verification popup"""
        print("Attempting age gate bypass...")
        
        # Common age verification cookies for cannabis sites
        age_cookies = [
            "age_verified=1; age_gate_passed=true",
            "over_21=true; age_check=passed",
            "green_apple_age_verified=1",
            "wp_age_verify=1"
        ]
        
        for cookie in age_cookies:
            html = self.fetch_page(self.base_url, cookie)
            # Check if we bypassed the popup (look for product content)
            if html and ("product" in html.lower() or "menu" in html.lower() or len(html) > 10000):
                print(f"Age gate bypass successful with cookie: {cookie}")
                return html
                
        # Try direct menu access
        menu_url = f"{self.base_url}/menu"
        html = self.fetch_page(menu_url)
        if html and len(html) > 5000:
            print("Age gate bypassed via direct menu access")
            return html
            
        print("Could not bypass age gate")
        return ""
        
    def extract_ajax_endpoints(self, html: str) -> List[str]:
        """Extract AJAX endpoints for product data"""
        endpoints = []
        
        # Look for WordPress AJAX URLs
        ajax_patterns = [
            r'ajaxurl["\s]*:["\s]*([^"]+)',
            r'wp-admin/admin-ajax.php[^"]*',
            r'api/products[^"]*',
            r'wp-json/[^"]*'
        ]
        
        for pattern in ajax_patterns:
            matches = re.findall(pattern, html)
            endpoints.extend(matches)
            
        return list(set(endpoints))
        
    def extract_products_from_html(self, html: str) -> List[Dict]:
        """Extract product data from HTML"""
        products = []
        
        # Look for product container patterns
        product_patterns = [
            r'<div[^>]*class="[^"]*product[^"]*"[^>]*>.*?</div>',
            r'<article[^>]*class="[^"]*product[^"]*"[^>]*>.*?</article>',
            r'<section[^>]*class="[^"]*product[^"]*"[^>]*>.*?</section>'
        ]
        
        for pattern in product_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            print(f"Found {len(matches)} products with pattern")
            
            for match in matches:
                product = self.parse_product_html(match)
                if product:
                    products.append(product)
                    
        # Look for JavaScript product data
        js_patterns = [
            r'var\s+products\s*=\s*(\[.*?\]);',
            r'window\.products\s*=\s*(\[.*?\]);',
            r'productData\s*:\s*(\[.*?\])',
            r'"products"\s*:\s*(\[.*?\])'
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, list):
                        for item in data:
                            product = self.parse_json_product(item)
                            if product:
                                products.append(product)
                except json.JSONDecodeError:
                    continue
                    
        return products
        
    def parse_product_html(self, html: str) -> Optional[Dict]:
        """Parse individual product from HTML"""
        try:
            # Extract product name
            name_patterns = [
                r'<h[1-6][^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h[1-6]>',
                r'<span[^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)</span>',
                r'data-product-name="([^"]*)"',
                r'<h[1-6][^>]*>([^<]+)</h[1-6]>'
            ]
            
            name = "Unknown Product"
            for pattern in name_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    if len(name) > 5:  # Avoid empty or very short titles
                        break
            
            # Extract price
            price_patterns = [
                r'\$\s*[\d,]+\.?\d*',
                r'class="[^"]*price[^"]*"[^>]*>.*?\$([0-9,]+\.?\d*)',
                r'data-price="([^"]*)"'
            ]
            
            price = "Price not available"
            for pattern in price_patterns:
                match = re.search(pattern, html)
                if match:
                    if '$' in match.group(0):
                        price = match.group(0)
                    else:
                        price = f"${match.group(1)}"
                    break
            
            # Extract image
            img_patterns = [
                r'src="([^"]*\.(jpg|jpeg|png|webp)[^"]*)"',
                r'data-src="([^"]*\.(jpg|jpeg|png|webp)[^"]*)"',
                r'background-image:\s*url\(([^)]+)\)'
            ]
            
            image = ""
            for pattern in img_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    image = match.group(1)
                    break
                    
            # Convert relative URLs to absolute
            if image and image.startswith('/'):
                image = urljoin(self.base_url, image)
            
            # Extract THC/CBD content
            thc_match = re.search(r'THC[:\s]*([0-9.]+%?)', html, re.IGNORECASE)
            thc = thc_match.group(1) if thc_match else ""
            
            cbd_match = re.search(r'CBD[:\s]*([0-9.]+%?)', html, re.IGNORECASE)
            cbd = cbd_match.group(1) if cbd_match else ""
            
            # Extract category/strain type
            category_patterns = [
                r'class="[^"]*category[^"]*"[^>]*>([^<]+)<',
                r'data-category="([^"]*)"',
                r'(indica|sativa|hybrid|flower|edible|vape|concentrate|pre-roll|cartridge)',
                r'strain[^:]*:[^>]*>([^<]+)<'
            ]
            
            category = "Unknown"
            for pattern in category_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    category = match.group(1).strip().title()
                    if category.lower() not in ['unknown', '', 'n/a']:
                        break
            
            # Extract brand
            brand_patterns = [
                r'class="[^"]*brand[^"]*"[^>]*>([^<]+)<',
                r'data-brand="([^"]*)"',
                r'by\s+([A-Za-z\s]+)',
            ]
            
            brand = "Green Apple"
            for pattern in brand_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    brand = match.group(1).strip()
                    if len(brand) > 2:
                        break
            
            product = {
                'name': name,
                'price': price,
                'image': image,
                'thc': thc,
                'cbd': cbd,
                'category': category,
                'brand': brand,
                'stock_status': 'in_stock',  # Assume in stock if listed
                'url': self.base_url
            }
            
            # Only return if we have meaningful data
            if name != "Unknown Product" or price != "Price not available":
                return product
                
            return None
            
        except Exception as e:
            print(f"Error parsing product HTML: {e}")
            return None
            
    def parse_json_product(self, data: Dict) -> Optional[Dict]:
        """Parse product from JSON data"""
        try:
            name = data.get('name', data.get('title', data.get('product_name', 'Unknown Product')))
            price = data.get('price', data.get('cost', data.get('product_price', 'Price not available')))
            
            if isinstance(price, (int, float)):
                price = f"${price:.2f}"
            elif isinstance(price, str) and price.isdigit():
                price = f"${float(price):.2f}"
                
            return {
                'name': str(name),
                'price': str(price),
                'image': data.get('image', data.get('image_url', data.get('product_image', ''))),
                'thc': data.get('thc', data.get('thc_content', data.get('thc_percentage', ''))),
                'cbd': data.get('cbd', data.get('cbd_content', data.get('cbd_percentage', ''))),
                'category': data.get('category', data.get('type', data.get('product_type', 'Unknown'))),
                'brand': data.get('brand', data.get('manufacturer', 'Green Apple')),
                'stock_status': 'in_stock' if data.get('in_stock', True) else 'out_of_stock',
                'url': data.get('url', data.get('link', self.base_url))
            }
        except Exception as e:
            print(f"Error parsing JSON product: {e}")
            return None
            
    def scrape_menu(self) -> List[Dict]:
        """Scrape products from menu pages"""
        print("Starting Green Apple menu scraping...")
        
        # First try to bypass age gate
        html = self.bypass_age_gate()
        if not html:
            print("Could not access site, trying without bypass...")
            html = self.fetch_page(self.base_url)
            
        products = []
        
        # Try different menu/shop URLs
        menu_urls = [
            f"{self.base_url}/menu",
            f"{self.base_url}/shop", 
            f"{self.base_url}/products",
            f"{self.base_url}/dispensary",
            f"{self.base_url}/cannabis",
            f"{self.base_url}/store"
        ]
        
        for url in menu_urls:
            print(f"Checking URL: {url}")
            page_html = self.fetch_page(url)
            
            if page_html and len(page_html) > 1000:  # Has substantial content
                page_products = self.extract_products_from_html(page_html)
                if page_products:
                    print(f"Found {len(page_products)} products from {url}")
                    products.extend(page_products)
                else:
                    print(f"No products found in {url}")
            else:
                print(f"Minimal content from {url}")
                
        # Also try AJAX endpoints if found
        if html:
            endpoints = self.extract_ajax_endpoints(html)
            for endpoint in endpoints[:3]:  # Limit to first 3
                print(f"Trying AJAX endpoint: {endpoint}")
                if not endpoint.startswith('http'):
                    endpoint = urljoin(self.base_url, endpoint)
                ajax_html = self.fetch_page(endpoint)
                if ajax_html:
                    ajax_products = self.extract_products_from_html(ajax_html)
                    products.extend(ajax_products)
                    
        print(f"Total products extracted: {len(products)}")
        return products
        
    def scrape_products(self, limit: int = 20) -> List[Dict]:
        """Main scraping method"""
        print("Starting Green Apple scraper...")
        
        products = self.scrape_menu()
        
        # Remove duplicates based on name
        seen_names = set()
        unique_products = []
        for product in products:
            name_key = product['name'].lower().strip()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_products.append(product)
                
        # Limit results for testing
        if limit and len(unique_products) > limit:
            unique_products = unique_products[:limit]
            
        print(f"Successfully scraped {len(unique_products)} unique products")
        return unique_products

def main():
    scraper = GreenAppleScraper()
    products = scraper.scrape_products(limit=15)
    
    # Save results
    output_file = "green_apple_products.json"
    with open(output_file, 'w') as f:
        json.dump(products, f, indent=2)
        
    print(f"Results saved to {output_file}")
    
    # Print sample
    if products:
        print("\nSample products:")
        for i, product in enumerate(products[:3]):
            print(f"{i+1}. {product['name']} - {product['price']} - {product['category']}")
    else:
        print("No products found - site likely requires JavaScript rendering")

if __name__ == "__main__":
    main()