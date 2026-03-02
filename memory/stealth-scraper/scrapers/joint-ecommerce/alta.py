"""
Alta-specific scraper implementation.
Extends the base Joint Ecommerce scraper with Alta-specific selectors and logic.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from .base_scraper import JointEcommerceScraper

logger = logging.getLogger(__name__)


class AltaScraper(JointEcommerceScraper):
    """Alta-specific implementation of Joint Ecommerce scraper."""
    
    def __init__(self):
        # Alta website URL - you may need to adjust this
        super().__init__(
            store_name="alta",
            base_url="https://alta.nyc",  # Adjust if different
            config={
                'delay_between_pages': 2,
                'max_retries': 3,
                'timeout': 30
            }
        )
        
        # Alta-specific selectors (override base selectors)
        self.selectors.update({
            'product_grid': '.product-item, .product-card, .menu-item',
            'product_name': '.product-title, .item-name, h3, .product-name',
            'product_price': '.price, .product-price, .item-price',
            'product_link': 'a',
            'category_nav': '.menu-categories, .category-nav, nav',
            'category_links': 'a[href*="category"], a[href*="menu"], a[href*="flower"], a[href*="edible"]',
            'next_page': '.next-page, .pagination-next, [data-next]',
            'load_more': '.load-more, .show-more, [data-load-more]',
            'product_description': '.product-description, .item-description',
            'product_thc': '.thc-content, .thc-level, [data-thc]',
            'product_cbd': '.cbd-content, .cbd-level, [data-cbd]',
            'stock_status': '.in-stock, .out-of-stock, .stock-status'
        })
    
    async def extract_single_product(self, element) -> Optional[Dict[str, Any]]:
        """Extract data from a single product element with Alta-specific fields."""
        try:
            # Get base product data
            product = await super().extract_single_product(element)
            if not product:
                return None
            
            # Add Alta-specific fields
            
            # Description
            desc_elem = await element.query_selector(self.selectors['product_description'])
            description = await desc_elem.inner_text() if desc_elem else ""
            
            # THC content
            thc_elem = await element.query_selector(self.selectors['product_thc'])
            thc_content = await thc_elem.inner_text() if thc_elem else ""
            
            # CBD content
            cbd_elem = await element.query_selector(self.selectors['product_cbd'])
            cbd_content = await cbd_elem.inner_text() if cbd_elem else ""
            
            # Stock status
            stock_elem = await element.query_selector(self.selectors['stock_status'])
            if stock_elem:
                stock_text = await stock_elem.inner_text()
                in_stock = "in stock" in stock_text.lower() or "available" in stock_text.lower()
            else:
                in_stock = True  # Assume in stock if no status indicator
            
            # Extract strain type from category or name
            strain_type = self.detect_strain_type(product['name'], product.get('category', ''))
            
            # Update product with Alta-specific data
            product.update({
                'description': description.strip(),
                'thc_content': self.parse_cannabinoid_content(thc_content),
                'cbd_content': self.parse_cannabinoid_content(cbd_content),
                'in_stock': in_stock,
                'strain_type': strain_type,
                'raw_thc': thc_content.strip(),
                'raw_cbd': cbd_content.strip()
            })
            
            return product
            
        except Exception as e:
            logger.warning(f"Failed to extract Alta product details: {e}")
            return None
    
    def parse_cannabinoid_content(self, content_text: str) -> Optional[float]:
        """Parse THC/CBD percentage from text."""
        import re
        
        if not content_text:
            return None
        
        # Look for patterns like "18.5%", "18.5 %", "18.5"
        match = re.search(r'(\d+\.?\d*)\s*%?', content_text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        return None
    
    def detect_strain_type(self, name: str, category: str) -> str:
        """Detect strain type (indica, sativa, hybrid) from name or category."""
        text = f"{name} {category}".lower()
        
        if any(word in text for word in ['indica', 'ind']):
            return 'indica'
        elif any(word in text for word in ['sativa', 'sat']):
            return 'sativa'
        elif any(word in text for word in ['hybrid', 'hyb']):
            return 'hybrid'
        else:
            return 'unknown'
    
    async def extract_categories(self) -> List[Dict[str, str]]:
        """Extract categories with Alta-specific navigation logic."""
        categories = []
        
        try:
            # First try the standard approach
            categories = await super().extract_categories()
            
            # If no categories found, try Alta-specific fallbacks
            if not categories:
                # Try different navigation patterns
                alt_selectors = [
                    'nav a',
                    '.menu a',
                    '.navigation a',
                    '[data-category]',
                    'a[href*="products"]'
                ]
                
                for selector in alt_selectors:
                    try:
                        links = await self.page.query_selector_all(selector)
                        for link in links:
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            
                            if href and text and any(word in text.lower() for word in ['flower', 'edible', 'vape', 'concentrate', 'product']):
                                full_url = self.make_absolute_url(href)
                                categories.append({
                                    'name': text.strip(),
                                    'url': full_url
                                })
                        
                        if categories:
                            break
                            
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                        continue
            
            # Add fallback categories if still none found
            if not categories:
                fallback_categories = [
                    {'name': 'Flower', 'url': f"{self.base_url}/flower"},
                    {'name': 'Edibles', 'url': f"{self.base_url}/edibles"},
                    {'name': 'Vapes', 'url': f"{self.base_url}/vapes"},
                    {'name': 'All Products', 'url': self.base_url}
                ]
                
                for cat in fallback_categories:
                    # Test if URL exists
                    try:
                        await self.page.goto(cat['url'], timeout=10000)
                        await self.page.wait_for_timeout(1000)
                        
                        # Check if page has products
                        products = await self.page.query_selector_all(self.selectors['product_grid'])
                        if products:
                            categories.append(cat)
                    except Exception:
                        continue
        
        except Exception as e:
            logger.error(f"Failed to extract categories: {e}")
            # Ultimate fallback
            categories = [{'name': 'All Products', 'url': self.base_url}]
        
        logger.info(f"Alta categories found: {[c['name'] for c in categories]}")
        return categories
    
    def make_absolute_url(self, href: str) -> str:
        """Helper to make URLs absolute."""
        from urllib.parse import urljoin
        return urljoin(self.base_url, href)
    
    async def handle_pagination(self, products: List[Dict[str, Any]]):
        """Handle Alta-specific pagination patterns."""
        try:
            # Try load more button first
            load_more_selectors = [
                '.load-more',
                '.show-more', 
                '[data-load-more]',
                'button[data-action="load-more"]',
                '.btn-load-more'
            ]
            
            for selector in load_more_selectors:
                load_more = await self.page.query_selector(selector)
                if load_more:
                    try:
                        # Check if button is visible and clickable
                        is_visible = await load_more.is_visible()
                        if is_visible:
                            await load_more.click()
                            await self.page.wait_for_timeout(3000)
                            
                            # Extract new products
                            new_products = await self.extract_products_from_page()
                            if new_products:
                                products.extend(new_products)
                                # Recursively handle more pages
                                await self.handle_pagination(products)
                            return
                    except Exception as e:
                        logger.debug(f"Load more with {selector} failed: {e}")
                        continue
            
            # If no load more button, try infinite scroll
            try:
                # Scroll to bottom
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.page.wait_for_timeout(2000)
                
                # Check if new products loaded
                new_products = await self.extract_products_from_page()
                current_count = len(products)
                products.extend(new_products)
                
                # If we got new products, try scrolling again
                if len(products) > current_count:
                    await self.handle_pagination(products)
                    
            except Exception as e:
                logger.debug(f"Infinite scroll failed: {e}")
                
        except Exception as e:
            logger.warning(f"Pagination handling failed: {e}")


async def scrape_alta():
    """Main function to scrape Alta products."""
    async with AltaScraper() as scraper:
        try:
            logger.info("Starting Alta scrape...")
            products = await scraper.scrape_all()
            
            if products:
                # Save to the requested filename
                scraper.save_products("alta_products.json")
                
                # Also save to workspace for analysis
                scraper.save_products("memory/stealth-scraper/scrapers/joint-ecommerce/alta_products.json")
                
                logger.info(f"✅ Alta scrape completed! Extracted {len(products)} products")
                
                # Print summary
                categories = {}
                for product in products:
                    cat = product.get('category', 'unknown')
                    categories[cat] = categories.get(cat, 0) + 1
                
                print(f"\n🎯 Alta Scrape Results:")
                print(f"Total products: {len(products)}")
                print(f"Categories: {dict(categories)}")
                
                return products
            else:
                logger.warning("No products extracted from Alta")
                return []
                
        except Exception as e:
            logger.error(f"Alta scrape failed: {e}")
            return []


if __name__ == "__main__":
    asyncio.run(scrape_alta())