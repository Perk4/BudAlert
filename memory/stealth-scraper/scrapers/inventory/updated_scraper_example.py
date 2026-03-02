"""
Example of Updated Scraper with Quantity Fields
Shows how to modify existing scrapers to include quantity extraction
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import quantity extraction tools
from quantity_parser import QuantityParser
from cart_prober import CartProber

logger = logging.getLogger(__name__)


class UpdatedBaseScraper:
    """
    Example base scraper class showing how to integrate quantity extraction
    into existing scrapers.
    """
    
    def __init__(self, store_name: str, base_url: str, config: Optional[Dict] = None):
        self.store_name = store_name
        self.base_url = base_url
        self.config = config or {}
        
        # Initialize quantity extraction tools
        self.quantity_parser = QuantityParser()
        self.cart_prober = CartProber()
        
        # Configuration for quantity analysis
        self.enable_quantity_extraction = config.get('enable_quantity_extraction', True)
        self.enable_deep_analysis = config.get('enable_deep_analysis', False)
        self.enable_cart_probing = config.get('enable_cart_probing', False)
        
        self.products = []
    
    async def extract_single_product(self, element, index: int = 0) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single product element.
        UPDATED to include quantity information.
        """
        try:
            # === EXISTING PRODUCT EXTRACTION ===
            # (Keep all existing product extraction logic)
            
            # Product name
            name = await self._extract_product_name(element, index)
            
            # Product price
            price, price_text = await self._extract_product_price(element)
            
            # Product link
            link = await self._extract_product_link(element)
            
            # Product ID
            product_id = await self._extract_product_id(element, link)
            
            # Basic product data (existing structure)
            product = {
                'id': product_id,
                'name': name,
                'price': price,
                'price_raw': price_text,
                'url': link,
                'store': self.store_name,
                'scraped_at': datetime.utcnow().isoformat(),
                'category': getattr(self, 'current_category', 'unknown'),
                
                # === NEW QUANTITY FIELDS ===
                'quantity_available': None,     # Actual quantity number
                'quantity_method': 'unknown',   # Method used to determine quantity
                'max_quantity': None,           # Maximum selectable quantity
                'in_stock': False,              # Boolean stock status (enhanced)
                'quantity_signals': [],         # List of signals found
                'quantity_confidence': 'low'    # Confidence in quantity data
            }
            
            # === NEW: EXTRACT QUANTITY INFORMATION ===
            if self.enable_quantity_extraction:
                quantity_info = await self.extract_quantity_info(element, link)
                product.update(quantity_info)
            
            return product
            
        except Exception as e:
            logger.warning(f"Failed to extract product {index}: {e}")
            return None
    
    async def extract_quantity_info(self, element, product_url: str = None) -> Dict[str, Any]:
        """
        NEW METHOD: Extract quantity information using multiple techniques.
        """
        quantity_info = {
            'quantity_available': None,
            'quantity_method': 'unknown',
            'max_quantity': None,
            'in_stock': False,
            'quantity_signals': [],
            'quantity_confidence': 'low'
        }
        
        try:
            # Method 1: Quick element-based analysis
            element_result = await self._extract_quantity_from_element(element)
            if element_result['found']:
                quantity_info.update(element_result)
                quantity_info['quantity_confidence'] = 'medium'
                return quantity_info
            
            # Method 2: Deep page analysis (if enabled and URL available)
            if (self.enable_deep_analysis and 
                product_url and 
                self.config.get('sample_deep_analysis', False)):
                
                page_result = await self._extract_quantity_from_page(product_url)
                if page_result['found']:
                    quantity_info.update(page_result)
                    quantity_info['quantity_confidence'] = 'high'
                    return quantity_info
            
            # Method 3: Basic stock status (fallback)
            basic_result = await self._extract_basic_stock_status(element)
            quantity_info.update(basic_result)
            
        except Exception as e:
            logger.debug(f"Quantity extraction failed: {e}")
            # Default fallback
            quantity_info.update({
                'in_stock': True,  # Assume in stock if present on page
                'quantity_method': 'default_assume_stock',
                'quantity_signals': ['default_assumption'],
                'quantity_confidence': 'low'
            })
        
        return quantity_info
    
    async def _extract_quantity_from_element(self, element) -> Dict[str, Any]:
        """Extract quantity info directly from product element."""
        result = {'found': False}
        
        try:
            # Check for quantity dropdown
            dropdown = await element.query_selector('select[name*="quantity"], select[name*="qty"]')
            if dropdown:
                max_qty = await self._get_dropdown_max_quantity(dropdown)
                if max_qty > 0:
                    result.update({
                        'found': True,
                        'quantity_available': max_qty,
                        'quantity_method': 'dropdown',
                        'max_quantity': max_qty,
                        'in_stock': True,
                        'quantity_signals': [f'dropdown_max_{max_qty}']
                    })
                    return result
            
            # Check for quantity input with max
            input_field = await element.query_selector('input[name*="quantity"], input[type="number"]')
            if input_field:
                max_attr = await input_field.get_attribute('max')
                if max_attr and max_attr.isdigit():
                    max_qty = int(max_attr)
                    result.update({
                        'found': True,
                        'quantity_available': max_qty,
                        'quantity_method': 'input_max',
                        'max_quantity': max_qty,
                        'in_stock': True,
                        'quantity_signals': [f'input_max_{max_qty}']
                    })
                    return result
            
            # Check for stock text
            text_elements = await element.query_selector_all('.stock-status, .availability, .quantity-text')
            for text_elem in text_elements:
                text = await text_elem.inner_text()
                quantity = self.quantity_parser.extract_quantity_from_text(text)
                if quantity is not None:
                    result.update({
                        'found': True,
                        'quantity_available': quantity,
                        'quantity_method': 'stock_text',
                        'max_quantity': quantity,
                        'in_stock': quantity > 0,
                        'quantity_signals': [f'stock_text_{quantity}']
                    })
                    return result
            
        except Exception as e:
            logger.debug(f"Element quantity extraction failed: {e}")
        
        return result
    
    async def _extract_quantity_from_page(self, product_url: str) -> Dict[str, Any]:
        """Extract quantity by visiting product page (expensive operation)."""
        result = {'found': False}
        
        try:
            # This would require navigating to the product page
            # Implementation depends on whether we have page context available
            
            # For now, just return not found since this is expensive
            # In real implementation, would:
            # 1. Save current page state
            # 2. Navigate to product URL
            # 3. Use QuantityParser.extract_quantity_from_page()
            # 4. Optionally use CartProber if enabled
            # 5. Return to original page
            
            logger.debug(f"Deep page analysis not implemented for {product_url}")
            
        except Exception as e:
            logger.debug(f"Page quantity extraction failed: {e}")
        
        return result
    
    async def _extract_basic_stock_status(self, element) -> Dict[str, Any]:
        """Extract basic in/out of stock status."""
        result = {
            'in_stock': True,  # Default assumption
            'quantity_method': 'default_assume_stock',
            'quantity_signals': ['default_assumption']
        }
        
        try:
            # Check for stock status indicators
            stock_selectors = [
                '.in-stock', '.out-of-stock', '.stock-status', 
                '.availability', '[data-stock]'
            ]
            
            for selector in stock_selectors:
                stock_elem = await element.query_selector(selector)
                if stock_elem:
                    text = await stock_elem.inner_text()
                    class_name = await stock_elem.get_attribute('class') or ''
                    
                    # Check text content
                    text_lower = text.lower()
                    if any(phrase in text_lower for phrase in ['out of stock', 'sold out', 'unavailable']):
                        result.update({
                            'in_stock': False,
                            'quantity_available': 0,
                            'quantity_method': 'stock_indicator',
                            'quantity_signals': ['stock_text_negative']
                        })
                        return result
                    elif any(phrase in text_lower for phrase in ['in stock', 'available', 'add to cart']):
                        result.update({
                            'in_stock': True,
                            'quantity_method': 'stock_indicator',
                            'quantity_signals': ['stock_text_positive']
                        })
                        return result
                    
                    # Check CSS classes
                    if any(cls in class_name.lower() for cls in ['out-of-stock', 'unavailable', 'soldout']):
                        result.update({
                            'in_stock': False,
                            'quantity_available': 0,
                            'quantity_method': 'stock_class',
                            'quantity_signals': ['stock_class_negative']
                        })
                        return result
                    elif any(cls in class_name.lower() for cls in ['in-stock', 'available', 'instock']):
                        result.update({
                            'in_stock': True,
                            'quantity_method': 'stock_class',
                            'quantity_signals': ['stock_class_positive']
                        })
                        return result
            
            # Check for add to cart button
            cart_button = await element.query_selector('.add-to-cart, button[data-add-to-cart], .btn-add-to-cart')
            if cart_button:
                is_enabled = await cart_button.is_enabled()
                button_text = await cart_button.inner_text()
                
                if is_enabled and 'out of stock' not in button_text.lower():
                    result.update({
                        'in_stock': True,
                        'quantity_method': 'add_to_cart_available',
                        'quantity_signals': ['cart_button_enabled']
                    })
                else:
                    result.update({
                        'in_stock': False,
                        'quantity_available': 0,
                        'quantity_method': 'add_to_cart_disabled',
                        'quantity_signals': ['cart_button_disabled']
                    })
        
        except Exception as e:
            logger.debug(f"Basic stock status check failed: {e}")
        
        return result
    
    async def _get_dropdown_max_quantity(self, dropdown) -> int:
        """Get maximum quantity from dropdown options."""
        max_qty = 0
        
        try:
            options = await dropdown.query_selector_all('option')
            for option in options:
                value = await option.get_attribute('value')
                text = await option.inner_text()
                
                # Try to extract number from value or text
                for content in [value, text]:
                    if content and content.strip().isdigit():
                        qty = int(content.strip())
                        max_qty = max(max_qty, qty)
        
        except Exception as e:
            logger.debug(f"Dropdown max quantity extraction failed: {e}")
        
        return max_qty
    
    async def _extract_product_name(self, element, index: int) -> str:
        """Extract product name (existing method)."""
        # Implementation of existing name extraction
        name_selectors = ['.product-name', '.product-title', 'h3', '.name']
        
        for selector in name_selectors:
            name_elem = await element.query_selector(selector)
            if name_elem:
                name = await name_elem.inner_text()
                if name.strip():
                    return name.strip()
        
        return f"Unknown Product {index}"
    
    async def _extract_product_price(self, element) -> tuple:
        """Extract product price (existing method)."""
        # Implementation of existing price extraction
        price_selectors = ['.price', '.product-price', '.cost']
        
        for selector in price_selectors:
            price_elem = await element.query_selector(selector)
            if price_elem:
                price_text = await price_elem.inner_text()
                if price_text.strip():
                    price = self._parse_price(price_text)
                    return price, price_text.strip()
        
        return 0.0, "0"
    
    async def _extract_product_link(self, element) -> str:
        """Extract product link (existing method)."""
        # Implementation of existing link extraction
        link_elem = await element.query_selector('a')
        if link_elem:
            href = await link_elem.get_attribute('href')
            if href:
                # Make absolute URL
                from urllib.parse import urljoin
                return urljoin(self.base_url, href)
        
        return ""
    
    async def _extract_product_id(self, element, link: str) -> str:
        """Extract product ID (existing method)."""
        # Implementation of existing ID extraction
        # Try data attributes
        for attr in ['data-product-id', 'data-id', 'data-sku']:
            product_id = await element.get_attribute(attr)
            if product_id:
                return product_id
        
        # Extract from URL
        if link:
            parts = link.split('/')
            for part in reversed(parts):
                if part and (part.isdigit() or len(part) > 3):
                    return part
        
        # Fallback
        return f"{self.store_name}_{hash(str(element)) % 1000000}"
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price from text (existing method)."""
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
            return 0.0
    
    def save_products(self, filename: str):
        """
        Save products to JSON file.
        UPDATED to include quantity statistics in output.
        """
        # Calculate quantity extraction statistics
        total_products = len(self.products)
        in_stock_count = sum(1 for p in self.products if p.get('in_stock', False))
        quantities_found = sum(1 for p in self.products if p.get('quantity_available') is not None)
        
        quantity_methods = {}
        confidence_levels = {}
        
        for product in self.products:
            method = product.get('quantity_method', 'unknown')
            confidence = product.get('quantity_confidence', 'low')
            
            quantity_methods[method] = quantity_methods.get(method, 0) + 1
            confidence_levels[confidence] = confidence_levels.get(confidence, 0) + 1
        
        output_data = {
            'store': self.store_name,
            'scraped_at': datetime.utcnow().isoformat(),
            'total_products': total_products,
            'products': self.products,
            
            # NEW: Quantity extraction statistics
            'quantity_stats': {
                'total_products': total_products,
                'in_stock_count': in_stock_count,
                'out_of_stock_count': total_products - in_stock_count,
                'quantities_found': quantities_found,
                'quantities_not_found': total_products - quantities_found,
                'quantity_extraction_rate': round((quantities_found / total_products) * 100, 1) if total_products > 0 else 0,
                'methods_used': quantity_methods,
                'confidence_distribution': confidence_levels
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Saved {total_products} products to {filename}")
        logger.info(f"Quantity extraction rate: {output_data['quantity_stats']['quantity_extraction_rate']}%")


# Example usage showing the migration pattern
async def example_migration():
    """
    Example showing how to migrate existing scraper to include quantities.
    """
    
    # OLD WAY (example of what existing scrapers look like)
    old_product = {
        'id': 'product_123',
        'name': 'Blue Dream 3.5g',
        'price': 55.0,
        'url': 'https://example.com/product/123',
        'store': 'example_store',
        'scraped_at': '2026-03-02T02:48:00Z'
        # Missing quantity information
    }
    
    # NEW WAY (what products should include)
    new_product = {
        'id': 'product_123',
        'name': 'Blue Dream 3.5g',
        'price': 55.0,
        'url': 'https://example.com/product/123',
        'store': 'example_store',
        'scraped_at': '2026-03-02T02:48:00Z',
        
        # NEW: Quantity information
        'quantity_available': 8,
        'quantity_method': 'cart_probe',
        'max_quantity': 8,
        'in_stock': True,
        'quantity_signals': ['cart_error_max_8'],
        'quantity_confidence': 'high'
    }
    
    print("Migration example:")
    print(f"Old product fields: {len(old_product)}")
    print(f"New product fields: {len(new_product)}")
    print(f"Added quantity fields: {set(new_product.keys()) - set(old_product.keys())}")


if __name__ == "__main__":
    asyncio.run(example_migration())