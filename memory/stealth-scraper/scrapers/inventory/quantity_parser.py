"""
Quantity Parser for Dispensary Scrapers
Extracts actual inventory quantities from various signals (dropdowns, text, etc.)
"""

import re
import logging
from typing import Optional, Dict, Any, List
from playwright.async_api import Page, ElementHandle

logger = logging.getLogger(__name__)


class QuantityParser:
    """Extract quantity information from various page elements."""
    
    def __init__(self):
        # Common patterns for quantity indicators
        self.quantity_patterns = {
            'dropdown_max': r'(\d+)',  # Extract number from option values
            'stock_text': [
                r'only\s*(\d+)\s*left',  # "Only 5 left"
                r'(\d+)\s*in\s*stock',   # "12 in stock"  
                r'(\d+)\s*available',    # "8 available"
                r'stock:\s*(\d+)',       # "Stock: 15"
                r'qty:\s*(\d+)',         # "Qty: 7"
                r'quantity:\s*(\d+)',    # "Quantity: 9"
            ],
            'out_of_stock': [
                r'out\s*of\s*stock',
                r'sold\s*out',
                r'unavailable',
                r'not\s*available',
                r'temporarily\s*unavailable'
            ]
        }
        
        # Common selectors for quantity elements
        self.quantity_selectors = {
            'quantity_dropdown': [
                'select[name*="quantity"]',
                'select[name*="qty"]', 
                'select.quantity',
                '.quantity-select select',
                '[data-quantity-select]'
            ],
            'quantity_input': [
                'input[name*="quantity"]',
                'input[name*="qty"]',
                'input.quantity',
                '.quantity-input input',
                '[data-quantity-input]'
            ],
            'stock_indicators': [
                '.stock-status',
                '.inventory-status', 
                '.quantity-available',
                '.stock-level',
                '[data-stock]',
                '.in-stock',
                '.out-of-stock'
            ],
            'add_to_cart_area': [
                '.add-to-cart',
                '.cart-actions',
                '.purchase-options',
                '.product-actions',
                '[data-add-to-cart]'
            ]
        }

    async def extract_quantity_from_page(self, page: Page) -> Dict[str, Any]:
        """Extract quantity information from the current page."""
        quantity_info = {
            'quantity_available': None,
            'quantity_method': 'unknown',
            'max_quantity': None,
            'in_stock': False,
            'stock_text': '',
            'signals_found': []
        }
        
        try:
            # Method 1: Check quantity dropdown
            dropdown_result = await self._check_quantity_dropdown(page)
            if dropdown_result['found']:
                quantity_info.update(dropdown_result)
                quantity_info['quantity_method'] = 'dropdown'
                return quantity_info
            
            # Method 2: Check quantity input max attribute
            input_result = await self._check_quantity_input(page)
            if input_result['found']:
                quantity_info.update(input_result)
                quantity_info['quantity_method'] = 'input_max'
                return quantity_info
            
            # Method 3: Parse stock status text
            text_result = await self._check_stock_text(page)
            if text_result['found']:
                quantity_info.update(text_result)
                quantity_info['quantity_method'] = 'stock_text'
                return quantity_info
            
            # Method 4: Check for basic in/out of stock
            basic_stock = await self._check_basic_stock_status(page)
            quantity_info.update(basic_stock)
            if basic_stock['in_stock']:
                quantity_info['quantity_method'] = 'boolean_stock'
            
        except Exception as e:
            logger.warning(f"Error extracting quantity: {e}")
        
        return quantity_info

    async def _check_quantity_dropdown(self, page: Page) -> Dict[str, Any]:
        """Check for quantity dropdown and extract max value."""
        result = {'found': False, 'signals_found': []}
        
        try:
            for selector in self.quantity_selectors['quantity_dropdown']:
                dropdown = await page.query_selector(selector)
                if dropdown:
                    # Get all option values
                    options = await dropdown.query_selector_all('option')
                    max_qty = 0
                    
                    for option in options:
                        value_attr = await option.get_attribute('value')
                        text_content = await option.inner_text()
                        
                        # Try to extract number from value attribute
                        if value_attr:
                            match = re.search(self.quantity_patterns['dropdown_max'], value_attr)
                            if match:
                                qty = int(match.group(1))
                                max_qty = max(max_qty, qty)
                        
                        # Also try from text content
                        if text_content:
                            match = re.search(r'(\d+)', text_content)
                            if match:
                                qty = int(match.group(1))
                                max_qty = max(max_qty, qty)
                    
                    if max_qty > 0:
                        result.update({
                            'found': True,
                            'quantity_available': max_qty,
                            'max_quantity': max_qty,
                            'in_stock': True,
                            'signals_found': [f'dropdown_max_{max_qty}']
                        })
                        logger.info(f"Found quantity dropdown with max: {max_qty}")
                        return result
        
        except Exception as e:
            logger.debug(f"Dropdown check failed: {e}")
        
        return result

    async def _check_quantity_input(self, page: Page) -> Dict[str, Any]:
        """Check quantity input field for max attribute."""
        result = {'found': False, 'signals_found': []}
        
        try:
            for selector in self.quantity_selectors['quantity_input']:
                input_field = await page.query_selector(selector)
                if input_field:
                    max_attr = await input_field.get_attribute('max')
                    if max_attr:
                        try:
                            max_qty = int(max_attr)
                            if max_qty > 0:
                                result.update({
                                    'found': True,
                                    'quantity_available': max_qty,
                                    'max_quantity': max_qty,
                                    'in_stock': True,
                                    'signals_found': [f'input_max_{max_qty}']
                                })
                                logger.info(f"Found quantity input with max: {max_qty}")
                                return result
                        except ValueError:
                            continue
        
        except Exception as e:
            logger.debug(f"Input check failed: {e}")
        
        return result

    async def _check_stock_text(self, page: Page) -> Dict[str, Any]:
        """Check for stock quantity in text content."""
        result = {'found': False, 'signals_found': []}
        
        try:
            # Check stock indicator elements
            for selector in self.quantity_selectors['stock_indicators']:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    text = text.lower().strip()
                    
                    # Check for out of stock patterns first
                    for pattern in self.quantity_patterns['out_of_stock']:
                        if re.search(pattern, text, re.IGNORECASE):
                            result.update({
                                'found': True,
                                'quantity_available': 0,
                                'max_quantity': 0,
                                'in_stock': False,
                                'stock_text': text,
                                'signals_found': ['out_of_stock_text']
                            })
                            return result
                    
                    # Check for quantity patterns
                    for pattern in self.quantity_patterns['stock_text']:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            qty = int(match.group(1))
                            result.update({
                                'found': True,
                                'quantity_available': qty,
                                'max_quantity': qty,
                                'in_stock': qty > 0,
                                'stock_text': text,
                                'signals_found': [f'stock_text_{qty}']
                            })
                            logger.info(f"Found stock text with quantity: {qty}")
                            return result
            
            # Also check the entire page for stock indicators
            page_text = await page.inner_text('body')
            page_text = page_text.lower()
            
            for pattern in self.quantity_patterns['stock_text']:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    qty = int(match.group(1))
                    result.update({
                        'found': True,
                        'quantity_available': qty,
                        'max_quantity': qty,
                        'in_stock': qty > 0,
                        'stock_text': match.group(0),
                        'signals_found': [f'page_text_{qty}']
                    })
                    logger.info(f"Found stock text in page: {qty}")
                    return result
        
        except Exception as e:
            logger.debug(f"Stock text check failed: {e}")
        
        return result

    async def _check_basic_stock_status(self, page: Page) -> Dict[str, Any]:
        """Check for basic in/out of stock indicators."""
        result = {'in_stock': False, 'signals_found': []}
        
        try:
            # Check for "Add to Cart" button or similar
            for selector in self.quantity_selectors['add_to_cart_area']:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    text = text.lower()
                    
                    # Positive indicators
                    if any(phrase in text for phrase in ['add to cart', 'buy now', 'purchase', 'order']):
                        result.update({
                            'in_stock': True,
                            'signals_found': ['add_to_cart_available']
                        })
                        return result
                    
                    # Negative indicators  
                    if any(phrase in text for phrase in ['out of stock', 'sold out', 'unavailable']):
                        result.update({
                            'in_stock': False,
                            'signals_found': ['add_to_cart_unavailable']
                        })
                        return result
            
            # Check for stock status classes
            for selector in self.quantity_selectors['stock_indicators']:
                element = await page.query_selector(selector)
                if element:
                    class_name = await element.get_attribute('class') or ''
                    class_name = class_name.lower()
                    
                    if any(cls in class_name for cls in ['in-stock', 'available', 'instock']):
                        result.update({
                            'in_stock': True,
                            'signals_found': ['stock_class_positive']
                        })
                        return result
                    
                    if any(cls in class_name for cls in ['out-of-stock', 'unavailable', 'soldout', 'outofstock']):
                        result.update({
                            'in_stock': False,
                            'signals_found': ['stock_class_negative']
                        })
                        return result
        
        except Exception as e:
            logger.debug(f"Basic stock check failed: {e}")
        
        # Default to assuming in stock if no clear indicators
        result.update({
            'in_stock': True,
            'signals_found': ['default_assume_stock']
        })
        
        return result

    def extract_quantity_from_text(self, text: str) -> Optional[int]:
        """Extract quantity from plain text."""
        if not text:
            return None
        
        text = text.lower().strip()
        
        # Check out of stock first
        for pattern in self.quantity_patterns['out_of_stock']:
            if re.search(pattern, text, re.IGNORECASE):
                return 0
        
        # Check for quantity patterns
        for pattern in self.quantity_patterns['stock_text']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None