"""
Base scraper for Joint Ecommerce platform stores.
Provides common functionality for Torches, Stoops, and Alta.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import aiohttp
from playwright.async_api import async_playwright, Page, Browser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JointEcommerceScraper:
    """Base scraper for Joint Ecommerce platform stores."""
    
    def __init__(self, store_name: str, base_url: str, config: Optional[Dict] = None):
        self.store_name = store_name
        self.base_url = base_url.rstrip('/')
        self.config = config or {}
        self.session = None
        self.page = None
        self.browser = None
        self.products = []
        
        # Default selectors (can be overridden by subclasses)
        self.selectors = {
            'product_grid': '.product-item, .product-card, [data-product]',
            'product_name': 'h3, .product-title, .product-name',
            'product_price': '.price, .product-price, [data-price]',
            'product_link': 'a',
            'category_nav': '.category-menu, .menu-categories, nav',
            'category_links': 'a[href*="category"], a[href*="menu"]',
            'next_page': '.next-page, .pagination-next',
            'load_more': '.load-more, .show-more'
        }
        
        # User agent rotation
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
        """Initialize browser session."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await self.browser.new_context(
            user_agent=self.user_agents[0],
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'
        )
        
        self.page = await context.new_page()
        
        # Set up request interception to block images/media for speed
        await self.page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort())
        
        logger.info(f"Browser session started for {self.store_name}")
    
    async def cleanup(self):
        """Clean up browser session."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        logger.info(f"Browser session closed for {self.store_name}")
    
    async def navigate_to_page(self, url: str, wait_for: Optional[str] = None) -> bool:
        """Navigate to a page and wait for content."""
        try:
            await self.page.goto(url, timeout=30000)
            
            if wait_for:
                await self.page.wait_for_selector(wait_for, timeout=10000)
            else:
                await self.page.wait_for_load_state('networkidle', timeout=10000)
            
            logger.info(f"Successfully navigated to {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return False
    
    async def extract_categories(self) -> List[Dict[str, str]]:
        """Extract category links from the navigation."""
        categories = []
        
        try:
            # Wait for navigation to load
            await self.page.wait_for_selector(self.selectors['category_nav'], timeout=5000)
            
            # Find category links
            links = await self.page.query_selector_all(f"{self.selectors['category_nav']} {self.selectors['category_links']}")
            
            for link in links:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                
                if href and text:
                    # Make URL absolute
                    full_url = urljoin(self.base_url, href)
                    categories.append({
                        'name': text.strip(),
                        'url': full_url
                    })
            
            logger.info(f"Found {len(categories)} categories: {[c['name'] for c in categories]}")
            
        except Exception as e:
            logger.warning(f"Could not extract categories: {e}")
            # Return default categories if navigation fails
            categories = [{'name': 'All Products', 'url': self.base_url}]
        
        return categories
    
    async def extract_products_from_page(self) -> List[Dict[str, Any]]:
        """Extract products from the current page."""
        products = []
        
        try:
            # Wait for products to load
            await self.page.wait_for_selector(self.selectors['product_grid'], timeout=10000)
            
            product_elements = await self.page.query_selector_all(self.selectors['product_grid'])
            logger.info(f"Found {len(product_elements)} product elements on page")
            
            for element in product_elements:
                try:
                    product = await self.extract_single_product(element)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Failed to extract product: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to extract products from page: {e}")
        
        return products
    
    async def extract_single_product(self, element) -> Optional[Dict[str, Any]]:
        """Extract data from a single product element."""
        try:
            # Product name
            name_elem = await element.query_selector(self.selectors['product_name'])
            name = await name_elem.inner_text() if name_elem else "Unknown Product"
            
            # Product price
            price_elem = await element.query_selector(self.selectors['product_price'])
            price_text = await price_elem.inner_text() if price_elem else "0"
            price = self.parse_price(price_text)
            
            # Product link
            link_elem = await element.query_selector(self.selectors['product_link'])
            link = await link_elem.get_attribute('href') if link_elem else ""
            if link:
                link = urljoin(self.base_url, link)
            
            # Product ID (try to extract from link or data attributes)
            product_id = await self.extract_product_id(element, link)
            
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
            
            return product
            
        except Exception as e:
            logger.warning(f"Failed to extract product details: {e}")
            return None
    
    async def extract_product_id(self, element, link: str) -> str:
        """Extract product ID from element or URL."""
        # Try data attributes first
        for attr in ['data-product-id', 'data-id', 'data-sku']:
            product_id = await element.get_attribute(attr)
            if product_id:
                return product_id
        
        # Try to extract from URL
        if link:
            parts = link.split('/')
            for part in reversed(parts):
                if part and part.isdigit():
                    return part
                if part and len(part) > 3:  # Likely an ID or slug
                    return part
        
        # Fallback to a hash of the name
        name_elem = await element.query_selector(self.selectors['product_name'])
        if name_elem:
            name = await name_elem.inner_text()
            return f"hash_{hash(name.strip()) % 100000}"
        
        return f"unknown_{hash(str(element)) % 100000}"
    
    def parse_price(self, price_text: str) -> float:
        """Parse price from text."""
        import re
        
        # Remove currency symbols and extract numeric value
        price_clean = re.sub(r'[^\d.,]', '', price_text)
        
        try:
            # Handle formats like "12.50" or "12,50"
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
        
        if not await self.navigate_to_page(category['url']):
            return category_products
        
        # Extract products from first page
        products = await self.extract_products_from_page()
        category_products.extend(products)
        
        # Check for pagination or load more
        await self.handle_pagination(category_products)
        
        logger.info(f"Extracted {len(category_products)} products from {category['name']}")
        return category_products
    
    async def handle_pagination(self, products: List[Dict[str, Any]]):
        """Handle pagination or infinite scroll."""
        page_num = 2
        max_pages = 10  # Safety limit
        
        while page_num <= max_pages:
            # Try "Load More" button first
            load_more = await self.page.query_selector(self.selectors['load_more'])
            if load_more:
                try:
                    await load_more.click()
                    await self.page.wait_for_timeout(2000)  # Wait for content to load
                    new_products = await self.extract_products_from_page()
                    if new_products:
                        products.extend(new_products)
                        page_num += 1
                        continue
                    else:
                        break
                except Exception as e:
                    logger.warning(f"Load more failed: {e}")
                    break
            
            # Try next page link
            next_page = await self.page.query_selector(self.selectors['next_page'])
            if next_page:
                try:
                    href = await next_page.get_attribute('href')
                    if href:
                        next_url = urljoin(self.base_url, href)
                        await self.navigate_to_page(next_url)
                        new_products = await self.extract_products_from_page()
                        if new_products:
                            products.extend(new_products)
                            page_num += 1
                            continue
                    break
                except Exception as e:
                    logger.warning(f"Next page navigation failed: {e}")
                    break
            
            # No more pages
            break
    
    async def scrape_all(self) -> List[Dict[str, Any]]:
        """Scrape all products from all categories."""
        self.products = []
        
        # Start by visiting the main page
        if not await self.navigate_to_page(self.base_url):
            logger.error(f"Failed to access {self.base_url}")
            return self.products
        
        # Extract categories
        categories = await self.extract_categories()
        
        # Scrape each category
        for category in categories:
            try:
                category_products = await self.scrape_category(category)
                self.products.extend(category_products)
                
                # Add delay between categories to be respectful
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to scrape category {category['name']}: {e}")
                continue
        
        # Remove duplicates based on product ID
        unique_products = {}
        for product in self.products:
            unique_products[product['id']] = product
        
        self.products = list(unique_products.values())
        
        logger.info(f"Total unique products extracted: {len(self.products)}")
        return self.products
    
    def save_products(self, filename: str):
        """Save products to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.products, f, indent=2)
        logger.info(f"Saved {len(self.products)} products to {filename}")


# Example usage
async def main():
    # This is just for testing the base class
    async with JointEcommerceScraper("test", "https://example.com") as scraper:
        products = await scraper.scrape_all()
        scraper.save_products("test_products.json")

if __name__ == "__main__":
    asyncio.run(main())