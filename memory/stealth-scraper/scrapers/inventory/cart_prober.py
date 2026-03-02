"""
Cart Prober for Dispensary Scrapers
Tests actual inventory quantities by attempting to add items to cart
"""

import asyncio
import json
import logging
import re
from typing import Optional, Dict, Any, List
from playwright.async_api import Page, Error as PlaywrightError

logger = logging.getLogger(__name__)


class CartProber:
    """Probe actual inventory quantities by testing cart operations."""
    
    def __init__(self):
        # Common selectors for cart operations
        self.cart_selectors = {
            'quantity_input': [
                'input[name*="quantity"]',
                'input[name*="qty"]', 
                'input.quantity',
                '.quantity-input input',
                '[data-quantity]',
                'input[type="number"]'
            ],
            'add_to_cart_button': [
                'button[type="submit"]',
                '.add-to-cart button',
                '.add-to-cart',
                'button[data-add-to-cart]',
                'input[type="submit"]',
                '.btn-add-to-cart',
                'button:has-text("Add to Cart")',
                'button:has-text("Add to Bag")',
                'button:has-text("Buy Now")'
            ],
            'cart_error_messages': [
                '.error-message',
                '.alert-error',
                '.cart-error',
                '.validation-error', 
                '.quantity-error',
                '[data-error]',
                '.error',
                '.alert'
            ],
            'cart_success_indicators': [
                '.cart-success',
                '.added-to-cart',
                '.cart-notification',
                '.success-message',
                '.alert-success'
            ],
            'cart_modal': [
                '.modal',
                '.cart-modal',
                '.popup',
                '.overlay'
            ]
        }
        
        # Error patterns that indicate quantity limits
        self.quantity_error_patterns = [
            r'maximum\s*(?:of\s*)?(\d+)',  # "Maximum of 5"
            r'only\s*(\d+)\s*available',  # "Only 3 available"
            r'limit\s*(?:of\s*)?(\d+)',   # "Limit of 10"
            r'(\d+)\s*in\s*stock',        # "5 in stock"
            r'cannot\s*add\s*more\s*than\s*(\d+)',  # "Cannot add more than 2"
            r'exceeds\s*available\s*quantity\s*of\s*(\d+)',  # "Exceeds available quantity of 7"
            r'insufficient\s*inventory.*?(\d+)',  # "Insufficient inventory. Only 4 available"
        ]
    
    async def probe_product_quantity(self, page: Page, product_url: str = None, max_attempts: int = 99) -> Dict[str, Any]:
        """Probe a product's actual quantity by testing cart operations."""
        result = {
            'quantity_available': None,
            'quantity_method': 'cart_probe',
            'max_quantity': None,
            'in_stock': False,
            'probe_attempts': 0,
            'error_messages': [],
            'success': False,
            'method_details': {}
        }
        
        try:
            # Navigate to product page if URL provided
            if product_url:
                await page.goto(product_url, timeout=30000)
                await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Method 1: Try high quantity and check error message
            high_qty_result = await self._probe_with_high_quantity(page, max_attempts)
            if high_qty_result['success']:
                result.update(high_qty_result)
                return result
            
            # Method 2: Binary search for max quantity
            binary_result = await self._binary_search_quantity(page, max_attempts)
            if binary_result['success']:
                result.update(binary_result)
                return result
            
            # Method 3: Incremental test
            incremental_result = await self._incremental_quantity_test(page)
            if incremental_result['success']:
                result.update(incremental_result)
                return result
            
            # If all methods fail, check basic stock status
            basic_result = await self._check_basic_cart_availability(page)
            result.update(basic_result)
            
        except Exception as e:
            logger.error(f"Cart probing failed: {e}")
            result['error_messages'].append(str(e))
        
        return result

    async def _probe_with_high_quantity(self, page: Page, high_qty: int = 99) -> Dict[str, Any]:
        """Try adding a high quantity and parse the error message for actual limit."""
        result = {'success': False, 'method_details': {'method': 'high_quantity_probe'}}
        
        try:
            logger.info(f"Probing with high quantity: {high_qty}")
            
            # Set quantity to high number
            quantity_set = await self._set_quantity_input(page, high_qty)
            if not quantity_set:
                return result
            
            # Try to add to cart
            add_result = await self._attempt_add_to_cart(page)
            result['probe_attempts'] = 1
            
            if add_result['error_message']:
                # Parse error message for actual quantity
                actual_qty = self._extract_quantity_from_error(add_result['error_message'])
                if actual_qty is not None:
                    result.update({
                        'success': True,
                        'quantity_available': actual_qty,
                        'max_quantity': actual_qty,
                        'in_stock': actual_qty > 0,
                        'error_messages': [add_result['error_message']],
                        'method_details': {
                            'method': 'high_quantity_probe',
                            'probe_quantity': high_qty,
                            'error_parsed': actual_qty
                        }
                    })
                    logger.info(f"Found quantity from error message: {actual_qty}")
                    return result
            
            elif add_result['success']:
                # High quantity was accepted - probably unlimited or very high stock
                result.update({
                    'success': True,
                    'quantity_available': high_qty,  # At least this much
                    'max_quantity': high_qty,
                    'in_stock': True,
                    'method_details': {
                        'method': 'high_quantity_probe',
                        'probe_quantity': high_qty,
                        'note': 'High quantity accepted - likely high stock'
                    }
                })
                return result
        
        except Exception as e:
            logger.debug(f"High quantity probe failed: {e}")
            result['error_messages'] = [str(e)]
        
        return result

    async def _binary_search_quantity(self, page: Page, max_qty: int = 50) -> Dict[str, Any]:
        """Use binary search to find maximum addable quantity."""
        result = {'success': False, 'method_details': {'method': 'binary_search'}}
        
        try:
            low = 1
            high = max_qty
            found_max = 0
            attempts = 0
            max_binary_attempts = 10  # Prevent infinite loops
            
            logger.info(f"Starting binary search for quantity (1-{max_qty})")
            
            while low <= high and attempts < max_binary_attempts:
                mid = (low + high) // 2
                attempts += 1
                
                logger.debug(f"Binary search attempt {attempts}: trying quantity {mid}")
                
                # Reset any existing cart state
                await self._clear_quantity_input(page)
                await asyncio.sleep(0.5)
                
                # Set quantity to mid point
                if not await self._set_quantity_input(page, mid):
                    break
                
                # Try to add to cart
                add_result = await self._attempt_add_to_cart(page)
                
                if add_result['success']:
                    # Success - try higher quantity
                    found_max = mid
                    low = mid + 1
                    logger.debug(f"Quantity {mid} succeeded, trying higher")
                else:
                    # Failed - try lower quantity
                    high = mid - 1
                    logger.debug(f"Quantity {mid} failed, trying lower")
                
                # Brief delay between attempts
                await asyncio.sleep(1)
            
            if found_max > 0:
                result.update({
                    'success': True,
                    'quantity_available': found_max,
                    'max_quantity': found_max,
                    'in_stock': True,
                    'probe_attempts': attempts,
                    'method_details': {
                        'method': 'binary_search',
                        'attempts': attempts,
                        'search_range': f"1-{max_qty}",
                        'final_max': found_max
                    }
                })
                logger.info(f"Binary search found max quantity: {found_max}")
        
        except Exception as e:
            logger.debug(f"Binary search failed: {e}")
            result['error_messages'] = [str(e)]
        
        return result

    async def _incremental_quantity_test(self, page: Page, max_test: int = 20) -> Dict[str, Any]:
        """Test quantities incrementally until failure."""
        result = {'success': False, 'method_details': {'method': 'incremental'}}
        
        try:
            found_max = 0
            attempts = 0
            
            logger.info(f"Starting incremental test (1-{max_test})")
            
            for qty in range(1, max_test + 1):
                attempts += 1
                
                # Reset quantity input
                await self._clear_quantity_input(page)
                await asyncio.sleep(0.3)
                
                # Set quantity
                if not await self._set_quantity_input(page, qty):
                    break
                
                # Try to add to cart
                add_result = await self._attempt_add_to_cart(page)
                
                if add_result['success']:
                    found_max = qty
                    logger.debug(f"Quantity {qty} succeeded")
                else:
                    logger.debug(f"Quantity {qty} failed - stopping incremental test")
                    break
                
                # Brief delay between attempts
                await asyncio.sleep(0.5)
            
            if found_max > 0:
                result.update({
                    'success': True,
                    'quantity_available': found_max,
                    'max_quantity': found_max,
                    'in_stock': True,
                    'probe_attempts': attempts,
                    'method_details': {
                        'method': 'incremental',
                        'attempts': attempts,
                        'max_tested': max_test,
                        'final_max': found_max
                    }
                })
                logger.info(f"Incremental test found max quantity: {found_max}")
        
        except Exception as e:
            logger.debug(f"Incremental test failed: {e}")
            result['error_messages'] = [str(e)]
        
        return result

    async def _set_quantity_input(self, page: Page, quantity: int) -> bool:
        """Set the quantity input field."""
        try:
            for selector in self.cart_selectors['quantity_input']:
                input_field = await page.query_selector(selector)
                if input_field:
                    # Clear existing value and set new one
                    await input_field.click()
                    await input_field.fill('')
                    await input_field.fill(str(quantity))
                    
                    # Verify value was set
                    value = await input_field.get_attribute('value')
                    if value == str(quantity):
                        logger.debug(f"Successfully set quantity to {quantity}")
                        return True
            
            logger.warning("Could not find or set quantity input field")
            return False
        
        except Exception as e:
            logger.debug(f"Failed to set quantity: {e}")
            return False

    async def _clear_quantity_input(self, page: Page) -> bool:
        """Clear the quantity input field."""
        try:
            for selector in self.cart_selectors['quantity_input']:
                input_field = await page.query_selector(selector)
                if input_field:
                    await input_field.click()
                    await input_field.fill('')
                    return True
            return False
        except Exception:
            return False

    async def _attempt_add_to_cart(self, page: Page) -> Dict[str, Any]:
        """Attempt to add the current product to cart."""
        add_result = {
            'success': False,
            'error_message': '',
            'success_message': ''
        }
        
        try:
            # Find and click add to cart button
            button_clicked = False
            
            for selector in self.cart_selectors['add_to_cart_button']:
                button = await page.query_selector(selector)
                if button:
                    # Check if button is visible and enabled
                    is_visible = await button.is_visible()
                    is_enabled = await button.is_enabled()
                    
                    if is_visible and is_enabled:
                        await button.click()
                        button_clicked = True
                        logger.debug(f"Clicked add to cart button: {selector}")
                        break
            
            if not button_clicked:
                add_result['error_message'] = "Could not find or click add to cart button"
                return add_result
            
            # Wait for response (either success or error)
            await asyncio.sleep(2)  # Give time for response
            
            # Check for error messages
            error_found = False
            for selector in self.cart_selectors['cart_error_messages']:
                error_elements = await page.query_selector_all(selector)
                for element in error_elements:
                    if await element.is_visible():
                        error_text = await element.inner_text()
                        if error_text.strip():
                            add_result['error_message'] = error_text.strip()
                            error_found = True
                            logger.debug(f"Found error message: {error_text}")
                            break
                if error_found:
                    break
            
            # Check for success indicators if no error
            if not error_found:
                for selector in self.cart_selectors['cart_success_indicators']:
                    success_elements = await page.query_selector_all(selector)
                    for element in success_elements:
                        if await element.is_visible():
                            success_text = await element.inner_text()
                            if success_text.strip():
                                add_result['success'] = True
                                add_result['success_message'] = success_text.strip()
                                logger.debug(f"Found success message: {success_text}")
                                return add_result
                
                # If no explicit success/error message, assume success
                add_result['success'] = True
                add_result['success_message'] = "Add to cart completed (no explicit message)"
        
        except Exception as e:
            logger.debug(f"Add to cart attempt failed: {e}")
            add_result['error_message'] = str(e)
        
        return add_result

    async def _check_basic_cart_availability(self, page: Page) -> Dict[str, Any]:
        """Check if product can be added to cart at all (basic availability)."""
        result = {
            'in_stock': False,
            'method_details': {'method': 'basic_availability'}
        }
        
        try:
            # Look for add to cart button
            for selector in self.cart_selectors['add_to_cart_button']:
                button = await page.query_selector(selector)
                if button:
                    is_visible = await button.is_visible()
                    is_enabled = await button.is_enabled()
                    
                    if is_visible and is_enabled:
                        result['in_stock'] = True
                        result['method_details']['found_button'] = selector
                        break
            
            # Also check for out of stock indicators in button text
            if result['in_stock']:
                button_text = await button.inner_text() if button else ""
                if any(phrase in button_text.lower() for phrase in ['out of stock', 'sold out', 'unavailable']):
                    result['in_stock'] = False
                    result['method_details']['button_text'] = button_text
        
        except Exception as e:
            logger.debug(f"Basic availability check failed: {e}")
        
        return result

    def _extract_quantity_from_error(self, error_message: str) -> Optional[int]:
        """Extract actual quantity from error message."""
        if not error_message:
            return None
        
        error_lower = error_message.lower()
        
        for pattern in self.quantity_error_patterns:
            match = re.search(pattern, error_lower)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None

    async def probe_multiple_products(self, page: Page, product_urls: List[str]) -> List[Dict[str, Any]]:
        """Probe quantity for multiple products."""
        results = []
        
        for i, url in enumerate(product_urls):
            try:
                logger.info(f"Probing product {i+1}/{len(product_urls)}: {url}")
                
                result = await self.probe_product_quantity(page, url)
                result['product_url'] = url
                results.append(result)
                
                # Add delay between products to be respectful
                if i < len(product_urls) - 1:
                    await asyncio.sleep(3)
            
            except Exception as e:
                logger.error(f"Failed to probe product {url}: {e}")
                results.append({
                    'product_url': url,
                    'error': str(e),
                    'success': False
                })
        
        return results