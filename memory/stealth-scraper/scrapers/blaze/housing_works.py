"""
Housing Works Cannabis Co. Scraper (Blaze Platform)
Scraper for hwcannabis.co with quantity extraction
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, Page, Browser

# Import our quantity extraction tools
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inventory.quantity_parser import QuantityParser
from inventory.cart_prober import CartProber

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HousingWorksScraper:
    """Housing Works Cannabis Co. scraper with quantity extraction."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.store_name = "housing_works"
        self.base_url = "https://hwcannabis.co"
        self.config = config or {}
        
        # Broadway location as default
        self.menu_url = "https://hwcannabis.co/menu/broadway/"
        
        self.page = None
        self.browser = None
        self.playwright = None
        self.products = []
        
        # Initialize quantity extraction tools
        self.quantity_parser = QuantityParser()
        self.cart_prober = CartProber()
        
        # Blaze platform selectors (will be refined based on actual site inspection)
        self.selectors = {
            'category_nav': '.category-menu, .menu-nav, nav, .categories',
            'category_links': 'a[href*="categories"], a[href*="category"], .category-link',
            'product_grid': '.product, .product-item, .menu-item, [data-product]',
            'product_name': '.product-name, .product-title, h3, .name',
            'product_price': '.price, .product-price, .cost',
            'product_link': 'a',
            'product_description': '.description, .product-description',
            'product_thc': '.thc, .thc-content, [data-thc]',
            'product_cbd': '.cbd, .cbd-content, [data-cbd]',
            'product_weight': '.weight, .size, .amount',
            'quantity_dropdown': 'select[name*="quantity"], select[name*="qty"]',
            'quantity_input': 'input[name*="quantity"], input[name*="qty"]',
            'add_to_cart': '.add-to-cart, button[data-add-to-cart]',
            'load_more': '.load-more, .show-more',
            'next_page': '.next-page, .pagination-next'
        }
        
        # User agent rotation for stealth
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    async def start(self):
        """Initialize browser session with stealth settings."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # Create context with stealth settings
        context = await self.browser.new_context(
            user_agent=self.user_agents[0],
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            # Reduce resource usage
            java_script_enabled=True,
        )
        
        self.page = await context.new_page()
        
        # Block unnecessary resources for speed
        await self.page.route(
            "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,mp4,mp3}",
            lambda route: route.abort()
        )
        
        # Intercept requests to identify API endpoints
        self.api_requests = []
        self.page.on('request', self._track_requests)
        self.page.on('response', self._track_responses)
        
        logger.info("Housing Works browser session started")
    
    async def cleanup(self):
        """Clean up browser session."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Housing Works browser session closed")
    
    def _track_requests(self, request):
        """Track API requests for potential quantity data."""
        url = request.url
        if any(keyword in url.lower() for keyword in ['api', 'graphql', 'inventory', 'products', 'cart']):
            self.api_requests.append({
                'url': url,
                'method': request.method,
                'type': 'request',
                'timestamp': datetime.utcnow().isoformat()
            })
    
    def _track_responses(self, response):
        """Track API responses for potential quantity data."""
        url = response.url
        if any(keyword in url.lower() for keyword in ['api', 'graphql', 'inventory', 'products', 'cart']):
            self.api_requests.append({
                'url': url,
                'status': response.status,
                'type': 'response',
                'timestamp': datetime.utcnow().isoformat()
            })
    
    async def navigate_to_menu(self) -> bool:
        """Navigate to the Housing Works menu page."""
        try:
            logger.info(f"Navigating to {self.menu_url}")
            await self.page.goto(self.menu_url, timeout=30000)
            
            # Wait for content to load (Blaze sites are often SPA)
            await self.page.wait_for_timeout(5000)
            
            # Try to wait for products to appear
            try:
                await self.page.wait_for_selector(self.selectors['product_grid'], timeout=10000)
                logger.info("Products loaded successfully")
            except:
                logger.warning("Products selector not found, but continuing...")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to menu: {e}")
            return False
    
    async def extract_categories(self) -> List[Dict[str, str]]:
        """Extract product categories from navigation."""
        categories = []
        
        try:
            # Wait a bit for dynamic content
            await self.page.wait_for_timeout(3000)
            
            # Try different navigation patterns
            nav_selectors = [
                '.category-menu a',
                '.menu-nav a', 
                'nav a',
                '.categories a',
                'a[href*="categories"]',
                '.category-link'
            ]
            
            for selector in nav_selectors:
                try:
                    links = await self.page.query_selector_all(selector)
                    for link in links:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        
                        if href and text:
                            # Filter for category-like links
                            text_lower = text.lower().strip()
                            if any(word in text_lower for word in ['flower', 'edible', 'vape', 'concentrate', 'pre-roll', 'tincture']):
                                full_url = urljoin(self.base_url, href)
                                categories.append({
                                    'name': text.strip(),
                                    'url': full_url
                                })
                    
                    if categories:
                        break
                        
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            # Add default categories if none found
            if not categories:
                categories = [
                    {'name': 'Flower', 'url': f"{self.menu_url}categories/flower/"},
                    {'name': 'Edibles', 'url': f"{self.menu_url}categories/edibles/"},
                    {'name': 'Vapes', 'url': f"{self.menu_url}categories/vapes/"},
                    {'name': 'Pre-rolls', 'url': f"{self.menu_url}categories/pre-rolls/"},
                    {'name': 'All Products', 'url': self.menu_url}
                ]
            
            logger.info(f"Found categories: {[c['name'] for c in categories]}")
            
        except Exception as e:
            logger.warning(f"Could not extract categories: {e}")
            categories = [{'name': 'All Products', 'url': self.menu_url}]
        
        return categories
    
    async def extract_products_from_page(self) -> List[Dict[str, Any]]:
        """Extract products from the current page with quantity information."""
        products = []
        
        try:
            # Wait for products to load
            await self.page.wait_for_timeout(3000)
            
            # Try different product selectors
            product_selectors = [
                '.product',
                '.product-item',
                '.menu-item', 
                '[data-product]',
                '.product-card'
            ]
            
            product_elements = []
            for selector in product_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    product_elements = elements
                    logger.info(f"Found {len(elements)} products using selector: {selector}")
                    break
            
            if not product_elements:
                logger.warning("No product elements found on page")
                return products
            
            for i, element in enumerate(product_elements[:50]):  # Limit to 50 products per page
                try:
                    product = await self.extract_single_product(element, i)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Failed to extract product {i}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to extract products from page: {e}")
        
        return products
    
    async def extract_single_product(self, element, index: int = 0) -> Optional[Dict[str, Any]]:
        """Extract data from a single product element with quantity information."""
        try:
            # Basic product info
            name_elem = await element.query_selector(self.selectors['product_name'])
            name = await name_elem.inner_text() if name_elem else f"Unknown Product {index}"
            
            # Price
            price_elem = await element.query_selector(self.selectors['product_price'])
            price_text = await price_elem.inner_text() if price_elem else "0"
            price = self.parse_price(price_text)
            
            # Product link
            link_elem = await element.query_selector(self.selectors['product_link'])
            link = await link_elem.get_attribute('href') if link_elem else ""
            if link:
                link = urljoin(self.base_url, link)
            
            # Product ID
            product_id = await self.extract_product_id(element, link)
            
            # Basic product data
            product = {
                'id': product_id,
                'name': name.strip(),
                'price': price,
                'price_raw': price_text.strip(),
                'url': link,
                'store': self.store_name,
                'scraped_at': datetime.utcnow().isoformat(),
                'category': getattr(self, 'current_category', 'unknown')
            }
            
            # Try to extract quantity information
            quantity_info = await self.extract_quantity_info(element, link)
            product.update(quantity_info)
            
            return product
            
        except Exception as e:
            logger.warning(f"Failed to extract product details: {e}")
            return None
    
    async def extract_quantity_info(self, element, product_url: str = None) -> Dict[str, Any]:
        """Extract quantity information for a product."""
        quantity_info = {
            'quantity_available': None,
            'quantity_method': 'unknown',
            'max_quantity': None,
            'in_stock': False,
            'quantity_signals': []
        }
        
        try:
            # Method 1: Check for quantity info in product element
            element_quantity = await self.quantity_parser.extract_quantity_from_page(self.page)
            if element_quantity['quantity_available'] is not None:
                quantity_info.update(element_quantity)
                return quantity_info
            
            # Method 2: If product has URL, visit it for detailed quantity info
            if product_url and self.config.get('deep_quantity_analysis', False):
                # Note: This would be expensive, so only do for sample products
                try:
                    original_url = self.page.url
                    await self.page.goto(product_url, timeout=15000)
                    await self.page.wait_for_timeout(3000)
                    
                    # Try quantity parser on product page
                    page_quantity = await self.quantity_parser.extract_quantity_from_page(self.page)
                    if page_quantity['quantity_available'] is not None:
                        quantity_info.update(page_quantity)
                        await self.page.goto(original_url)  # Go back
                        return quantity_info
                    
                    # Try cart probing if enabled
                    if self.config.get('enable_cart_probing', False):
                        probe_result = await self.cart_prober.probe_product_quantity(self.page)
                        if probe_result['success']:
                            quantity_info.update(probe_result)
                            await self.page.goto(original_url)  # Go back
                            return quantity_info
                    
                    await self.page.goto(original_url)  # Go back
                    
                except Exception as e:
                    logger.debug(f"Deep quantity analysis failed for {product_url}: {e}")
            
            # Method 3: Check for basic stock status in element
            stock_indicators = ['.in-stock', '.out-of-stock', '.stock-status', '.availability']
            for selector in stock_indicators:
                stock_elem = await element.query_selector(selector)
                if stock_elem:
                    stock_text = await stock_elem.inner_text()
                    if 'in stock' in stock_text.lower() or 'available' in stock_text.lower():
                        quantity_info['in_stock'] = True
                        quantity_info['quantity_method'] = 'stock_indicator'
                        quantity_info['quantity_signals'].append('stock_text_positive')
                        break
                    elif 'out of stock' in stock_text.lower() or 'unavailable' in stock_text.lower():
                        quantity_info['in_stock'] = False
                        quantity_info['quantity_available'] = 0
                        quantity_info['quantity_method'] = 'stock_indicator'
                        quantity_info['quantity_signals'].append('stock_text_negative')
                        break
            
            # Default: assume in stock if no clear indicators
            if quantity_info['quantity_method'] == 'unknown':
                quantity_info['in_stock'] = True
                quantity_info['quantity_method'] = 'default_assume_stock'
                quantity_info['quantity_signals'].append('default_assumption')
        
        except Exception as e:
            logger.debug(f"Quantity extraction failed: {e}")
        
        return quantity_info
    
    async def extract_product_id(self, element, link: str) -> str:
        """Extract product ID from element or URL."""
        # Try data attributes
        for attr in ['data-product-id', 'data-id', 'data-sku', 'data-product']:
            product_id = await element.get_attribute(attr)
            if product_id:
                return product_id
        
        # Extract from URL
        if link:
            parts = link.split('/')
            for part in reversed(parts):
                if part and (part.isdigit() or len(part) > 5):
                    return part
        
        # Fallback to hash of name
        name_elem = await element.query_selector(self.selectors['product_name'])
        if name_elem:
            name = await name_elem.inner_text()
            return f"hw_{hash(name.strip()) % 1000000}"
        
        return f"hw_unknown_{hash(str(element)) % 1000000}"
    
    def parse_price(self, price_text: str) -> float:
        """Parse price from text."""
        import re
        
        if not price_text:
            return 0.0
        
        # Remove currency symbols and extract numeric value
        price_clean = re.sub(r'[^\d.,]', '', price_text)
        
        try:
            if '.' in price_clean:
                return float(price_clean.replace(',', ''))
            elif ',' in price_clean:
                return float(price_clean.replace(',', '.'))
            else:
                return float(price_clean) if price_clean else 0.0
        except ValueError:
            logger.warning(f"Could not parse price: {price_text}")
            return 0.0
    
    async def scrape_category(self, category: Dict[str, str]) -> List[Dict[str, Any]]:
        """Scrape all products from a category."""
        self.current_category = category['name']
        category_products = []
        
        logger.info(f"Scraping category: {category['name']} ({category['url']})")
        
        try:
            await self.page.goto(category['url'], timeout=30000)
            await self.page.wait_for_timeout(5000)
            
            # Extract products from first page
            products = await self.extract_products_from_page()
            category_products.extend(products)
            
            # Handle pagination/infinite scroll
            await self.handle_pagination(category_products)
            
        except Exception as e:
            logger.error(f"Failed to scrape category {category['name']}: {e}")
        
        logger.info(f"Extracted {len(category_products)} products from {category['name']}")
        return category_products
    
    async def handle_pagination(self, products: List[Dict[str, Any]]):
        """Handle pagination or infinite scroll."""
        try:
            # Try load more button
            load_more = await self.page.query_selector(self.selectors['load_more'])
            if load_more and await load_more.is_visible():
                await load_more.click()
                await self.page.wait_for_timeout(3000)
                new_products = await self.extract_products_from_page()
                if new_products:
                    products.extend(new_products)
                    # Recursively handle more pages
                    await self.handle_pagination(products)
                return
            
            # Try infinite scroll
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(3000)
            new_products = await self.extract_products_from_page()
            current_count = len(products)
            products.extend(new_products)
            
            # If new products were loaded, try again
            if len(products) > current_count:
                await self.handle_pagination(products)
                
        except Exception as e:
            logger.debug(f"Pagination handling failed: {e}")
    
    async def scrape_all(self, enable_quantity_analysis: bool = True) -> List[Dict[str, Any]]:
        """Scrape all products with quantity information."""
        self.products = []
        
        # Configure quantity analysis
        self.config['deep_quantity_analysis'] = enable_quantity_analysis
        self.config['enable_cart_probing'] = enable_quantity_analysis
        
        # Navigate to menu
        if not await self.navigate_to_menu():
            logger.error("Failed to access Housing Works menu")
            return self.products
        
        # Extract categories
        categories = await self.extract_categories()
        
        # Scrape each category
        for i, category in enumerate(categories[:3]):  # Limit to first 3 categories for testing
            try:
                logger.info(f"Scraping category {i+1}/{len(categories[:3])}: {category['name']}")
                category_products = await self.scrape_category(category)
                self.products.extend(category_products)
                
                # Add delay between categories
                if i < len(categories) - 1:
                    await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to scrape category {category['name']}: {e}")
                continue
        
        # Remove duplicates
        unique_products = {}
        for product in self.products:
            unique_products[product['id']] = product
        
        self.products = list(unique_products.values())
        
        logger.info(f"Housing Works scrape completed: {len(self.products)} unique products")
        
        # Log quantity extraction stats
        quantity_methods = {}
        in_stock_count = 0
        for product in self.products:
            method = product.get('quantity_method', 'unknown')
            quantity_methods[method] = quantity_methods.get(method, 0) + 1
            if product.get('in_stock', False):
                in_stock_count += 1
        
        logger.info(f"Quantity methods used: {quantity_methods}")
        logger.info(f"Products in stock: {in_stock_count}/{len(self.products)}")
        
        return self.products
    
    def save_products(self, filename: str):
        """Save products to JSON file."""
        output_data = {
            'store': self.store_name,
            'scraped_at': datetime.utcnow().isoformat(),
            'total_products': len(self.products),
            'api_requests_tracked': self.api_requests,
            'products': self.products
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Saved {len(self.products)} Housing Works products to {filename}")


# Main scraping function
async def scrape_housing_works(enable_quantity_analysis: bool = True):
    """Main function to scrape Housing Works."""
    async with HousingWorksScraper() as scraper:
        try:
            logger.info("Starting Housing Works scrape...")
            products = await scraper.scrape_all(enable_quantity_analysis)
            
            if products:
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"housing_works_products_{timestamp}.json"
                scraper.save_products(filename)
                
                # Also save to workspace
                scraper.save_products("memory/stealth-scraper/scrapers/blaze/housing_works_products.json")
                
                logger.info(f"✅ Housing Works scrape completed! Extracted {len(products)} products")
                
                # Print summary
                quantity_methods = {}
                in_stock_count = 0
                quantities_found = 0
                
                for product in products:
                    method = product.get('quantity_method', 'unknown')
                    quantity_methods[method] = quantity_methods.get(method, 0) + 1
                    if product.get('in_stock', False):
                        in_stock_count += 1
                    if product.get('quantity_available') is not None:
                        quantities_found += 1
                
                print(f"\n🏪 Housing Works (Blaze Platform) Results:")
                print(f"Total products: {len(products)}")
                print(f"Products in stock: {in_stock_count}")
                print(f"Quantities found: {quantities_found}")
                print(f"Quantity methods: {quantity_methods}")
                
                return products
            else:
                logger.warning("No products extracted from Housing Works")
                return []
                
        except Exception as e:
            logger.error(f"Housing Works scrape failed: {e}")
            return []


if __name__ == "__main__":
    asyncio.run(scrape_housing_works())