#!/usr/bin/env python3
"""
Verilife NY Scraper
Site: verilife.com/ny
Framework: Magento e-commerce platform (MSO)
Notes: Multi-store operator, Magento-based, likely has API endpoints
"""

import json
import re
import subprocess
import sys
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

class VerilifeScraper:
    def __init__(self):
        self.base_url = "https://www.verilife.com"
        self.ny_url = "https://www.verilife.com/ny"
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
            
    def find_magento_endpoints(self, html: str) -> List[str]:
        """Find Magento-specific endpoints and store info"""
        endpoints = []
        
        # Magento-specific patterns
        magento_patterns = [
            r'/rest/[^"\s]*',
            r'/pub/media/catalog/product/[^"\s]*',
            r'customer/section/load[^"\s]*',
            r'checkout/cart/[^"\s]*',
            r'/graphql[^"\s]*'
        ]
        
        for pattern in magento_patterns:
            matches = re.findall(pattern, html)
            endpoints.extend(matches)
            
        # Look for store-specific data
        store_patterns = [
            r'BASE_URL["\s]*:["\s]*([^"]+)',
            r'storeCode["\s]*:["\s]*([^"]+)',
            r'websiteId["\s]*:["\s]*([^"]+)'
        ]
        
        for pattern in store_patterns:
            matches = re.findall(pattern, html)
            endpoints.extend([f"store info: {m}" for m in matches])
            
        return list(set(endpoints))
        
    def extract_store_locations(self, html: str) -> List[Dict]:
        """Extract NY store locations from page"""
        locations = []
        
        # Look for store location data
        location_patterns = [
            r'<div[^>]*class="[^"]*store[^"]*location[^"]*"[^>]*>.*?</div>',
            r'<article[^>]*class="[^"]*location[^"]*"[^>]*>.*?</article>',
            r'"stores"\s*:\s*(\[.*?\])'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if match.startswith('['):
                    try:
                        store_data = json.loads(match)
                        for store in store_data:
                            if isinstance(store, dict):
                                locations.append({
                                    'name': store.get('name', ''),
                                    'address': store.get('address', ''),
                                    'url': store.get('url', '')
                                })
                    except json.JSONDecodeError:
                        continue
                else:
                    # Parse HTML for store info
                    name_match = re.search(r'<h[1-6][^>]*>([^<]+)</h[1-6]>', match)
                    addr_match = re.search(r'(\d+[^<]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)[^<]*)', match)
                    
                    if name_match:
                        locations.append({
                            'name': name_match.group(1).strip(),
                            'address': addr_match.group(1).strip() if addr_match else '',
                            'url': ''
                        })
                        
        return locations
        
    def extract_products_from_html(self, html: str) -> List[Dict]:
        """Extract product data from Magento HTML"""
        products = []
        
        # Magento product patterns
        product_patterns = [
            r'<div[^>]*class="[^"]*product[^"]*item[^"]*"[^>]*>.*?</div>',
            r'<li[^>]*class="[^"]*product[^"]*item[^"]*"[^>]*>.*?</li>',
            r'<article[^>]*class="[^"]*product[^"]*"[^>]*>.*?</article>'
        ]
        
        for pattern in product_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            print(f"Found {len(matches)} products with Magento pattern")
            
            for match in matches:
                product = self.parse_magento_product_html(match)
                if product:
                    products.append(product)
                    
        # Look for Magento JavaScript data
        js_patterns = [
            r'window\.checkout\s*=\s*({.*?});',
            r'hyva\.productListItems\s*=\s*(\[.*?\]);',
            r'"items"\s*:\s*(\[.*?\])',
            r'catalogAddToCart\s*=\s*({.*?});'
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
                    elif isinstance(data, dict):
                        if 'items' in data:
                            for item in data['items']:
                                product = self.parse_json_product(item)
                                if product:
                                    products.append(product)
                        elif 'products' in data:
                            for item in data['products']:
                                product = self.parse_json_product(item)
                                if product:
                                    products.append(product)
                except json.JSONDecodeError:
                    continue
                    
        return products
        
    def parse_magento_product_html(self, html: str) -> Optional[Dict]:
        """Parse product from Magento HTML structure"""
        try:
            # Extract product name
            name_patterns = [
                r'class="[^"]*product[^"]*name[^"]*"[^>]*>.*?<a[^>]*>([^<]+)</a>',
                r'<h[1-6][^>]*class="[^"]*product[^"]*title[^"]*"[^>]*>([^<]+)</h[1-6]>',
                r'data-product-name="([^"]*)"',
                r'<a[^>]*class="[^"]*product[^"]*link[^"]*"[^>]*>([^<]+)</a>'
            ]
            
            name = "Unknown Product"
            for pattern in name_patterns:
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    name = match.group(1).strip()
                    if len(name) > 3:
                        break
            
            # Extract price (Magento has complex pricing structure)
            price_patterns = [
                r'class="[^"]*price[^"]*"[^>]*>.*?\$([0-9,]+\.?\d*)',
                r'data-price-amount="([^"]*)"',
                r'<span[^>]*class="[^"]*regular[^"]*price[^"]*"[^>]*>\$([^<]+)</span>',
                r'\$\s*[\d,]+\.?\d*'
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
                r'class="[^"]*product[^"]*image[^"]*"[^>]*src="([^"]*)"',
                r'data-original="([^"]*)"',
                r'src="([^"]*pub/media/catalog/product[^"]*)"'
            ]
            
            image = ""
            for pattern in img_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    image = match.group(1)
                    if not image.startswith('http'):
                        image = urljoin(self.base_url, image)
                    break
            
            # Extract product attributes
            thc_match = re.search(r'THC[:\s]*([0-9.]+%?)', html, re.IGNORECASE)
            thc = thc_match.group(1) if thc_match else ""
            
            cbd_match = re.search(r'CBD[:\s]*([0-9.]+%?)', html, re.IGNORECASE)
            cbd = cbd_match.group(1) if cbd_match else ""
            
            # Extract category
            category_patterns = [
                r'class="[^"]*category[^"]*"[^>]*>([^<]+)<',
                r'data-category="([^"]*)"',
                r'breadcrumb[^>]*>.*?>([^<]+)<.*?product',
                r'(flower|edible|vape|concentrate|pre-roll|cartridge|tincture|topical)'
            ]
            
            category = "Cannabis"
            for pattern in category_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    category = match.group(1).strip().title()
                    if category.lower() not in ['unknown', 'cannabis', '', 'n/a']:
                        break
            
            # Extract brand
            brand_patterns = [
                r'class="[^"]*brand[^"]*"[^>]*>([^<]+)<',
                r'data-brand="([^"]*)"',
                r'by\s+([A-Za-z\s&]+)',
                r'manufacturer[^>]*>([^<]+)<'
            ]
            
            brand = "Verilife"
            for pattern in brand_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    extracted_brand = match.group(1).strip()
                    if len(extracted_brand) > 2 and extracted_brand.lower() != 'verilife':
                        brand = extracted_brand
                        break
            
            # Check stock status
            stock_status = "in_stock"
            if re.search(r'(out of stock|sold out|unavailable)', html, re.IGNORECASE):
                stock_status = "out_of_stock"
            elif re.search(r'(low stock|limited)', html, re.IGNORECASE):
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
                'url': self.ny_url
            }
            
            # Only return if we have meaningful data
            if name != "Unknown Product" and len(name) > 3:
                return product
                
            return None
            
        except Exception as e:
            print(f"Error parsing Magento product: {e}")
            return None
            
    def parse_json_product(self, data: Dict) -> Optional[Dict]:
        """Parse product from JSON data"""
        try:
            name = data.get('name', data.get('title', data.get('product_name', 'Unknown Product')))
            
            # Handle Magento price structure
            price_info = data.get('price', data.get('price_info', {}))
            if isinstance(price_info, dict):
                price = price_info.get('final_price', price_info.get('regular_price', 'Price not available'))
            else:
                price = price_info
                
            if isinstance(price, (int, float)):
                price = f"${price:.2f}"
            elif isinstance(price, str) and price.replace('.', '').replace(',', '').isdigit():
                price = f"${float(price.replace(',', '')):.2f}"
                
            # Handle Magento image structure
            image = ""
            if 'image' in data:
                if isinstance(data['image'], dict):
                    image = data['image'].get('url', data['image'].get('src', ''))
                else:
                    image = data['image']
            elif 'small_image' in data:
                image = data['small_image'].get('url', '') if isinstance(data['small_image'], dict) else data['small_image']
                
            if image and not image.startswith('http'):
                image = urljoin(self.base_url, image)
                
            return {
                'name': str(name),
                'price': str(price),
                'image': str(image),
                'thc': str(data.get('thc', data.get('thc_content', ''))),
                'cbd': str(data.get('cbd', data.get('cbd_content', ''))),
                'category': data.get('category', data.get('product_type', 'Cannabis')),
                'brand': data.get('brand', data.get('manufacturer', 'Verilife')),
                'stock_status': 'in_stock' if data.get('is_in_stock', True) else 'out_of_stock',
                'url': data.get('url', data.get('product_url', self.ny_url))
            }
        except Exception as e:
            print(f"Error parsing JSON product: {e}")
            return None
            
    def scrape_menu(self) -> List[Dict]:
        """Scrape products from Verilife NY pages"""
        print("Starting Verilife NY scraping...")
        
        # Get main NY page
        html = self.fetch_page(self.ny_url)
        if not html:
            print("Could not fetch NY page")
            return []
            
        products = []
        
        # Find store locations
        locations = self.extract_store_locations(html)
        print(f"Found {len(locations)} NY locations")
        
        # Try different menu/product URLs
        urls_to_try = [
            self.ny_url,
            f"{self.base_url}/ny/menu",
            f"{self.base_url}/ny/products",
            f"{self.base_url}/ny/shop",
            f"{self.base_url}/products?state=ny",
            f"{self.base_url}/menu?state=ny",
            f"{self.base_url}/dispensary/new-york"
        ]
        
        # Add specific store URLs if found
        for location in locations:
            if location.get('url'):
                urls_to_try.append(location['url'])
                if not location['url'].endswith('/menu'):
                    urls_to_try.append(f"{location['url']}/menu")
                    
        for url in urls_to_try:
            print(f"Checking URL: {url}")
            page_html = self.fetch_page(url)
            
            if page_html and len(page_html) > 2000:
                page_products = self.extract_products_from_html(page_html)
                if page_products:
                    print(f"Found {len(page_products)} products from {url}")
                    products.extend(page_products)
                    
                # Look for API endpoints
                endpoints = self.find_magento_endpoints(page_html)
                for endpoint in endpoints[:3]:
                    if endpoint.startswith('store info:'):
                        continue
                    if not endpoint.startswith('http'):
                        endpoint = urljoin(self.base_url, endpoint)
                    print(f"Trying Magento endpoint: {endpoint}")
                    api_html = self.fetch_page(endpoint)
                    if api_html:
                        try:
                            api_data = json.loads(api_html)
                            if isinstance(api_data, dict) and 'items' in api_data:
                                for item in api_data['items']:
                                    product = self.parse_json_product(item)
                                    if product:
                                        products.append(product)
                        except json.JSONDecodeError:
                            api_products = self.extract_products_from_html(api_html)
                            products.extend(api_products)
        
        print(f"Total products extracted: {len(products)}")
        return products
        
    def scrape_products(self, limit: int = 20) -> List[Dict]:
        """Main scraping method"""
        print("Starting Verilife scraper...")
        
        products = self.scrape_menu()
        
        # Remove duplicates
        seen_names = set()
        unique_products = []
        for product in products:
            name_key = product['name'].lower().strip()
            if name_key not in seen_names and name_key not in ['unknown product', '']:
                seen_names.add(name_key)
                unique_products.append(product)
                
        # Limit results
        if limit and len(unique_products) > limit:
            unique_products = unique_products[:limit]
            
        print(f"Successfully scraped {len(unique_products)} unique products")
        return unique_products

def main():
    scraper = VerilifeScraper()
    products = scraper.scrape_products(limit=15)
    
    # Save results
    output_file = "verilife_products.json"
    with open(output_file, 'w') as f:
        json.dump(products, f, indent=2)
        
    print(f"Results saved to {output_file}")
    
    # Print sample
    if products:
        print("\nSample products:")
        for i, product in enumerate(products[:3]):
            print(f"{i+1}. {product['name']} - {product['price']} - {product['brand']}")
    else:
        print("No products found - Magento site may require specific session/authentication")

if __name__ == "__main__":
    main()