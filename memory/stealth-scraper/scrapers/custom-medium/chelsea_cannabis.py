#!/usr/bin/env python3
"""
Chelsea Cannabis Co. Scraper
Site: chelseacannabis.co
Framework: Ruby on Rails application
Notes: Separate shop subdomain, CSRF tokens, Rails-style routing
"""

import json
import re
import subprocess
import sys
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

class ChelseaCannabisScraper:
    def __init__(self):
        self.base_url = "https://chelseacannabis.co"
        self.shop_url = "https://shop.chelseacannabis.co"  # Potential shop subdomain
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
    def fetch_page(self, url: str, headers: Dict = None) -> str:
        """Fetch a page using curl with optional headers"""
        cmd = [
            'curl', '-L', '-s', '-A', self.user_agent
        ]
        
        if headers:
            for key, value in headers.items():
                cmd.extend(['-H', f'{key}: {value}'])
                
        cmd.append(url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
            
    def extract_csrf_token(self, html: str) -> Optional[str]:
        """Extract CSRF token from Rails application"""
        csrf_patterns = [
            r'name="csrf-token"\s+content="([^"]+)"',
            r'name="authenticity_token"[^>]*value="([^"]+)"',
            r'"csrf-token"[^:]*:\s*"([^"]+)"'
        ]
        
        for pattern in csrf_patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
                
        return None
        
    def find_api_endpoints(self, html: str) -> List[str]:
        """Find API endpoints in Rails application"""
        endpoints = []
        
        # Look for Rails routes and API endpoints
        api_patterns = [
            r'"/api/[^"]*"',
            r'"/products[^"]*\.json"',
            r'/menu[^"]*',
            r'/shop[^"]*',
            r'data-url="([^"]*)"'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, html)
            endpoints.extend([m.strip('"') for m in matches])
            
        return list(set(endpoints))
        
    def extract_products_from_html(self, html: str) -> List[Dict]:
        """Extract product data from HTML"""
        products = []
        
        # Rails/ERB product patterns
        product_patterns = [
            r'<div[^>]*class="[^"]*product[^"]*"[^>]*>.*?</div>',
            r'<article[^>]*class="[^"]*product[^"]*"[^>]*>.*?</article>',
            r'<section[^>]*data-product[^>]*>.*?</section>',
            r'<li[^>]*class="[^"]*product[^"]*"[^>]*>.*?</li>'
        ]
        
        for pattern in product_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            print(f"Found {len(matches)} products with pattern")
            
            for match in matches:
                product = self.parse_product_html(match)
                if product:
                    products.append(product)
                    
        # Look for JSON data embedded in Rails views
        json_patterns = [
            r'window\.products\s*=\s*(\[.*?\]);',
            r'var\s+productData\s*=\s*(\[.*?\]);',
            r'@products\s*=\s*(\[.*?\])',  # Rails instance variable
            r'"products"\s*:\s*(\[.*?\])'
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
                except json.JSONDecodeError:
                    continue
                    
        return products
        
    def parse_product_html(self, html: str) -> Optional[Dict]:
        """Parse product from HTML element"""
        try:
            # Extract product name
            name_patterns = [
                r'<h[1-6][^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h[1-6]>',
                r'<h[1-6][^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)</h[1-6]>',
                r'data-product-name="([^"]*)"',
                r'class="[^"]*product[^"]*name[^"]*"[^>]*>([^<]+)<'
            ]
            
            name = "Unknown Product"
            for pattern in name_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    if len(name) > 3:
                        break
            
            # Extract price
            price_patterns = [
                r'\$\s*[\d,]+\.?\d*',
                r'class="[^"]*price[^"]*"[^>]*>.*?\$([0-9,]+\.?\d*)',
                r'data-price="([^"]*)"',
                r'<span[^>]*class="[^"]*amount[^"]*"[^>]*>\$([^<]+)</span>'
            ]
            
            price = "Price not available"
            for pattern in price_patterns:
                match = re.search(pattern, html)
                if match:
                    if '$' in match.group(0):
                        price = match.group(0).strip()
                    else:
                        price = f"${match.group(1).strip()}"
                    break
            
            # Extract image
            img_patterns = [
                r'src="([^"]*\.(jpg|jpeg|png|webp)[^"]*)"',
                r'data-src="([^"]*\.(jpg|jpeg|png|webp)[^"]*)"',
                r'data-image="([^"]*)"'
            ]
            
            image = ""
            for pattern in img_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    image = match.group(1)
                    break
                    
            # Convert relative URLs
            if image and image.startswith('/'):
                image = urljoin(self.base_url, image)
            
            # Extract THC/CBD
            thc_match = re.search(r'THC[:\s]*([0-9.]+%?)', html, re.IGNORECASE)
            thc = thc_match.group(1) if thc_match else ""
            
            cbd_match = re.search(r'CBD[:\s]*([0-9.]+%?)', html, re.IGNORECASE)
            cbd = cbd_match.group(1) if cbd_match else ""
            
            # Extract category/type
            category_patterns = [
                r'class="[^"]*category[^"]*"[^>]*>([^<]+)<',
                r'data-category="([^"]*)"',
                r'<span[^>]*class="[^"]*type[^"]*"[^>]*>([^<]+)</span>',
                r'(flower|edible|vape|concentrate|pre-roll|cartridge|tincture)'
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
                r'<span[^>]*class="[^"]*manufacturer[^"]*"[^>]*>([^<]+)</span>'
            ]
            
            brand = "Chelsea Cannabis Co."
            for pattern in brand_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    extracted_brand = match.group(1).strip()
                    if len(extracted_brand) > 2:
                        brand = extracted_brand
                        break
            
            # Extract stock status
            stock_status = "in_stock"
            if re.search(r'(out of stock|sold out|unavailable)', html, re.IGNORECASE):
                stock_status = "out_of_stock"
            elif re.search(r'(low stock|few left)', html, re.IGNORECASE):
                stock_status = "low_stock"
            
            product = {
                'name': name,
                'price': price,
                'image': image,
                'thc': thc,
                'cbd': cbd,
                'category': category,
                'brand': brand,
                'stock_status': stock_status,
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
            price = data.get('price', data.get('cost', data.get('amount', 'Price not available')))
            
            if isinstance(price, (int, float)):
                price = f"${price:.2f}"
            elif isinstance(price, str) and price.replace('.', '').replace(',', '').isdigit():
                price = f"${float(price.replace(',', '')):.2f}"
                
            return {
                'name': str(name),
                'price': str(price),
                'image': data.get('image', data.get('image_url', data.get('photo', ''))),
                'thc': str(data.get('thc', data.get('thc_content', data.get('thc_percentage', '')))),
                'cbd': str(data.get('cbd', data.get('cbd_content', data.get('cbd_percentage', '')))),
                'category': data.get('category', data.get('product_type', data.get('type', 'Unknown'))),
                'brand': data.get('brand', data.get('manufacturer', data.get('producer', 'Chelsea Cannabis Co.'))),
                'stock_status': 'in_stock' if data.get('in_stock', True) else 'out_of_stock',
                'url': data.get('url', data.get('product_url', self.base_url))
            }
        except Exception as e:
            print(f"Error parsing JSON product: {e}")
            return None
            
    def scrape_menu(self) -> List[Dict]:
        """Scrape products from menu/shop pages"""
        print("Starting Chelsea Cannabis scraping...")
        
        # Get main page to extract CSRF and find routes
        html = self.fetch_page(self.base_url)
        csrf_token = self.extract_csrf_token(html) if html else None
        
        headers = {}
        if csrf_token:
            headers['X-CSRF-Token'] = csrf_token
            print(f"Found CSRF token: {csrf_token[:10]}...")
        
        products = []
        
        # Try different potential URLs
        urls_to_try = [
            self.base_url,
            f"{self.base_url}/menu",
            f"{self.base_url}/shop",
            f"{self.base_url}/products",
            f"{self.base_url}/dispensary",
            f"{self.base_url}/store",
            self.shop_url,  # Potential shop subdomain
            f"{self.shop_url}/menu",
            f"{self.shop_url}/products"
        ]
        
        for url in urls_to_try:
            print(f"Checking URL: {url}")
            page_html = self.fetch_page(url, headers)
            
            if page_html and len(page_html) > 1000:
                page_products = self.extract_products_from_html(page_html)
                if page_products:
                    print(f"Found {len(page_products)} products from {url}")
                    products.extend(page_products)
                    
                # Look for additional API endpoints
                endpoints = self.find_api_endpoints(page_html)
                for endpoint in endpoints[:3]:  # Limit to avoid spam
                    if not endpoint.startswith('http'):
                        endpoint = urljoin(url, endpoint)
                    print(f"Trying API endpoint: {endpoint}")
                    api_html = self.fetch_page(endpoint, headers)
                    if api_html:
                        try:
                            # Try parsing as JSON first
                            api_data = json.loads(api_html)
                            if isinstance(api_data, list):
                                for item in api_data:
                                    product = self.parse_json_product(item)
                                    if product:
                                        products.append(product)
                            elif isinstance(api_data, dict) and 'products' in api_data:
                                for item in api_data['products']:
                                    product = self.parse_json_product(item)
                                    if product:
                                        products.append(product)
                        except json.JSONDecodeError:
                            # Parse as HTML
                            api_products = self.extract_products_from_html(api_html)
                            products.extend(api_products)
        
        print(f"Total products extracted: {len(products)}")
        return products
        
    def scrape_products(self, limit: int = 20) -> List[Dict]:
        """Main scraping method"""
        print("Starting Chelsea Cannabis Co. scraper...")
        
        products = self.scrape_menu()
        
        # Remove duplicates based on name
        seen_names = set()
        unique_products = []
        for product in products:
            name_key = product['name'].lower().strip()
            if name_key not in seen_names and name_key != "unknown product":
                seen_names.add(name_key)
                unique_products.append(product)
                
        # Limit results
        if limit and len(unique_products) > limit:
            unique_products = unique_products[:limit]
            
        print(f"Successfully scraped {len(unique_products)} unique products")
        return unique_products

def main():
    scraper = ChelseaCannabisScraper()
    products = scraper.scrape_products(limit=15)
    
    # Save results
    output_file = "chelsea_cannabis_products.json"
    with open(output_file, 'w') as f:
        json.dump(products, f, indent=2)
        
    print(f"Results saved to {output_file}")
    
    # Print sample
    if products:
        print("\nSample products:")
        for i, product in enumerate(products[:3]):
            print(f"{i+1}. {product['name']} - {product['price']} - {product['category']}")
    else:
        print("No products found - Rails app may require complex authentication or JS")

if __name__ == "__main__":
    main()