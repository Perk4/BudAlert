"""
Stoops Brooklyn Scraper (Joint Ecommerce Platform)
Extends the base Joint Ecommerce scraper with quantity extraction
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .base_scraper import JointEcommerceScraper

# Import our quantity extraction tools
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inventory.quantity_parser import QuantityParser
from inventory.cart_prober import CartProber

logger = logging.getLogger(__name__)


class StoopsScraper(JointEcommerceScraper):
    """Stoops Brooklyn-specific implementation with quantity extraction."""
    
    def __init__(self, enable_quantity_analysis: bool = True):
        super().__init__(
            store_name="stoops",
            base_url="https://stoopsbrooklyn.com",
            config={
                'delay_between_pages': 2,
                'max_retries': 3,
                'timeout': 30,
                'enable_quantity_analysis': enable_quantity_analysis
            }
        )
        
        # Initialize quantity extraction tools
        self.quantity_parser = QuantityParser()
        self.cart_prober = CartProber()
        
        # Stoops-specific selectors
        self.selectors.update({
            'product_grid': '.product, .product-item, .menu-item, .product-card',
            'product_name': '.product-title, .product-name, .item-name, h3',
            'product_price': '.price, .product-price, .item-price, .cost',
            'product_link': 'a',
            'category_nav': '.menu-categories, .category-nav, nav, .categories',
            'category_links': 'a[href*="category"], a[href*="menu"], a[href*="flower"], a[href*="edible"]',
            'next_page': '.next-page, .pagination-next, [data-next]',
            'load_more': '.load-more, .show-more, [data-load-more]',
            'product_description': '.product-description, .item-description, .description',
            'product_thc': '.thc-content, .thc-level, [data-thc]',
            'product_cbd': '.cbd-content, .cbd-level, [data-cbd]',
            'stock_status': '.in-stock, .out-of-stock, .stock-status, .availability',
            'quantity_dropdown': 'select[name*="quantity"], select[name*="qty"], .quantity-select select',
            'quantity_input': 'input[name*="quantity"], input[name*="qty"], .quantity-input input',
            'add_to_cart': '.add-to-cart, button[data-add-to-cart], .btn-add-to-cart'
        })
    
    async def extract_single_product(self, element) -> Optional[Dict[str, Any]]:
        """Extract data from a single product element with Stoops-specific fields and quantity."""
        try:
            # Get base product data
            product = await super().extract_single_product(element)
            if not product:
                return None
            
            # Add Stoops-specific fields
            
            # Description
            desc_elem = await element.query_selector(self.selectors['product_description'])
            description = await desc_elem.inner_text() if desc_elem else ""
            
            # THC content
            thc_elem = await element.query_selector(self.selectors['product_thc'])
            thc_content = await thc_elem.inner_text() if thc_elem else ""
            
            # CBD content
            cbd_elem = await element.query_selector(self.selectors['product_cbd'])
            cbd_content = await cbd_elem.inner_text() if cbd_elem else ""
            
            # Extract quantity information
            quantity_info = await self.extract_quantity_info(element, product.get('url'))
            
            # Detect strain type
            strain_type = self.detect_strain_type(product['name'], product.get('category', ''))
            
            # Update product with Stoops-specific data
            product.update({
                'description': description.strip(),
                'thc_content': self.parse_cannabinoid_content(thc_content),
                'cbd_content': self.parse_cannabinoid_content(cbd_content),
                'strain_type': strain_type,
                'raw_thc': thc_content.strip(),
                'raw_cbd': cbd_content.strip()
            })
            
            # Add quantity information
            product.update(quantity_info)
            
            return product
            
        except Exception as e:
            logger.warning(f"Failed to extract Stoops product details: {e}")
            return None
    
    async def extract_quantity_info(self, element, product_url: str = None) -> Dict[str, Any]:
        """Extract quantity information for a Stoops product."""
        quantity_info = {
            'quantity_available': None,
            'quantity_method': 'unknown',
            'max_quantity': None,
            'in_stock': False,
            'quantity_signals': []
        }
        
        try:
            # Method 1: Check for quantity dropdown in product element
            dropdown_elem = await element.query_selector(self.selectors['quantity_dropdown'])
            if dropdown_elem:
                options = await dropdown_elem.query_selector_all('option')
                max_qty = 0
                
                for option in options:
                    value_attr = await option.get_attribute('value')
                    text_content = await option.inner_text()
                    
                    # Extract quantity from option
                    for content in [value_attr, text_content]:
                        if content and content.isdigit():
                            qty = int(content)
                            max_qty = max(max_qty, qty)
                
                if max_qty > 0:
                    quantity_info.update({
                        'quantity_available': max_qty,
                        'quantity_method': 'dropdown',
                        'max_quantity': max_qty,
                        'in_stock': True,
                        'quantity_signals': [f'dropdown_max_{max_qty}']
                    })
                    return quantity_info
            
            # Method 2: Check for quantity input max attribute
            input_elem = await element.query_selector(self.selectors['quantity_input'])
            if input_elem:
                max_attr = await input_elem.get_attribute('max')
                if max_attr and max_attr.isdigit():
                    max_qty = int(max_attr)
                    if max_qty > 0:
                        quantity_info.update({
                            'quantity_available': max_qty,
                            'quantity_method': 'input_max',
                            'max_quantity': max_qty,
                            'in_stock': True,
                            'quantity_signals': [f'input_max_{max_qty}']
                        })
                        return quantity_info
            
            # Method 3: Check stock status text in element
            stock_elem = await element.query_selector(self.selectors['stock_status'])
            if stock_elem:
                stock_text = await stock_elem.inner_text()
                quantity = self.quantity_parser.extract_quantity_from_text(stock_text)
                
                if quantity is not None:
                    quantity_info.update({
                        'quantity_available': quantity,
                        'quantity_method': 'stock_text',
                        'max_quantity': quantity,
                        'in_stock': quantity > 0,
                        'quantity_signals': [f'stock_text_{quantity}']
                    })
                    return quantity_info
                
                # Check for basic in/out of stock
                stock_text_lower = stock_text.lower()
                if 'in stock' in stock_text_lower or 'available' in stock_text_lower:
                    quantity_info.update({
                        'in_stock': True,
                        'quantity_method': 'stock_indicator',
                        'quantity_signals': ['stock_text_positive']
                    })
                    return quantity_info
                elif 'out of stock' in stock_text_lower or 'unavailable' in stock_text_lower:
                    quantity_info.update({
                        'quantity_available': 0,
                        'in_stock': False,
                        'quantity_method': 'stock_indicator',
                        'quantity_signals': ['stock_text_negative']
                    })
                    return quantity_info
            
            # Method 4: Check add to cart button availability
            cart_elem = await element.query_selector(self.selectors['add_to_cart'])
            if cart_elem:
                is_visible = await cart_elem.is_visible()
                is_enabled = await cart_elem.is_enabled()
                cart_text = await cart_elem.inner_text() if cart_elem else ""
                
                if is_visible and is_enabled and 'out of stock' not in cart_text.lower():
                    quantity_info.update({
                        'in_stock': True,
                        'quantity_method': 'add_to_cart_available',
                        'quantity_signals': ['cart_button_enabled']
                    })
                    return quantity_info
                elif 'out of stock' in cart_text.lower():
                    quantity_info.update({
                        'quantity_available': 0,
                        'in_stock': False,
                        'quantity_method': 'add_to_cart_disabled',
                        'quantity_signals': ['cart_button_out_of_stock']
                    })
                    return quantity_info
            
            # Method 5: If deep analysis enabled and we have a product URL, visit it
            if (self.config.get('enable_quantity_analysis', False) and 
                product_url and 
                self.config.get('deep_quantity_analysis', False)):
                
                try:
                    original_url = self.page.url
                    await self.page.goto(product_url, timeout=15000)
                    await self.page.wait_for_timeout(3000)
                    
                    # Use full quantity parser on product page
                    page_quantity = await self.quantity_parser.extract_quantity_from_page(self.page)
                    if page_quantity['quantity_available'] is not None:
                        quantity_info.update(page_quantity)
                        await self.page.goto(original_url)
                        return quantity_info
                    
                    # Try cart probing if enabled
                    if self.config.get('enable_cart_probing', False):
                        probe_result = await self.cart_prober.probe_product_quantity(self.page)
                        if probe_result['success']:
                            quantity_info.update(probe_result)
                            await self.page.goto(original_url)
                            return quantity_info
                    
                    await self.page.goto(original_url)
                    
                except Exception as e:
                    logger.debug(f"Deep quantity analysis failed for {product_url}: {e}")
            
            # Default: assume in stock if no clear indicators
            quantity_info.update({
                'in_stock': True,
                'quantity_method': 'default_assume_stock',
                'quantity_signals': ['default_assumption']
            })
        
        except Exception as e:
            logger.debug(f"Quantity extraction failed: {e}")
        
        return quantity_info
    
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
        """Extract categories with Stoops-specific navigation logic."""
        categories = []
        
        try:
            # First try the standard approach
            categories = await super().extract_categories()
            
            # If no categories found, try Stoops-specific fallbacks
            if not categories:
                # Try different navigation patterns specific to Stoops
                alt_selectors = [
                    'nav a',
                    '.menu a',
                    '.navigation a',
                    '[data-category]',
                    'a[href*="products"]',
                    'a[href*="shop"]',
                    '.category a'
                ]
                
                for selector in alt_selectors:
                    try:
                        links = await self.page.query_selector_all(selector)
                        for link in links:
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            
                            if href and text:
                                text_lower = text.lower()
                                if any(word in text_lower for word in ['flower', 'edible', 'vape', 'concentrate', 'product', 'pre-roll']):
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
                    {'name': 'Pre-rolls', 'url': f"{self.base_url}/pre-rolls"},
                    {'name': 'All Products', 'url': self.base_url}
                ]
                categories = fallback_categories
        
        except Exception as e:
            logger.error(f"Failed to extract categories: {e}")
            categories = [{'name': 'All Products', 'url': self.base_url}]
        
        logger.info(f"Stoops categories found: {[c['name'] for c in categories]}")
        return categories
    
    def make_absolute_url(self, href: str) -> str:
        """Helper to make URLs absolute."""
        from urllib.parse import urljoin
        return urljoin(self.base_url, href)
    
    async def scrape_all(self) -> List[Dict[str, Any]]:
        """Scrape all Stoops products with quantity information."""
        logger.info("Starting Stoops scrape with quantity analysis...")
        products = await super().scrape_all()
        
        # Log quantity extraction stats
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
        
        logger.info(f"Stoops quantity extraction stats:")
        logger.info(f"  Total products: {len(products)}")
        logger.info(f"  Products in stock: {in_stock_count}")
        logger.info(f"  Quantities found: {quantities_found}")
        logger.info(f"  Quantity methods: {quantity_methods}")
        
        return products


async def scrape_stoops(enable_quantity_analysis: bool = True):
    """Main function to scrape Stoops with quantity analysis."""
    async with StoopsScraper(enable_quantity_analysis) as scraper:
        try:
            logger.info("Starting Stoops scrape...")
            products = await scraper.scrape_all()
            
            if products:
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
                filename = f"stoops_products_{timestamp}.json"
                scraper.save_products(filename)
                
                # Also save to workspace
                scraper.save_products("memory/stealth-scraper/scrapers/joint-ecommerce/stoops_products.json")
                
                logger.info(f"✅ Stoops scrape completed! Extracted {len(products)} products")
                
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
                
                print(f"\n🏪 Stoops Brooklyn (Joint Ecommerce Platform) Results:")
                print(f"Total products: {len(products)}")
                print(f"Products in stock: {in_stock_count}")
                print(f"Quantities found: {quantities_found}")
                print(f"Quantity methods: {quantity_methods}")
                
                return products
            else:
                logger.warning("No products extracted from Stoops")
                return []
                
        except Exception as e:
            logger.error(f"Stoops scrape failed: {e}")
            return []


if __name__ == "__main__":
    asyncio.run(scrape_stoops())