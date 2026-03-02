#!/usr/bin/env python3
"""
QUBE NYC LeafBridge Scraper

QUBE NYC (qubenyc.com) is a cannabis dispensary in Times Square, New York
using the LeafBridge platform with Dutchie E-Commerce integration.

Store Details:
- Name: QUBE NYC / Qube Times Square Dispensary
- Location: 1412 Broadway #102, New York, NY 10018 (Times Square)
- License: OCM-CAURD-24-000127 (New York State)
- Retailer ID: 5fb99a40-9e34-4b1e-88be-b37b754a33d8
- Platform: LeafBridge (WordPress plugin) + Dutchie E-Commerce Pro
"""

import json
import logging
from typing import Dict, List, Optional, Any
from .leafbridge_base import LeafBridgeBaseScraper

class QubeNYCScraper(LeafBridgeBaseScraper):
    """Scraper for QUBE NYC LeafBridge-powered dispensary."""
    
    def __init__(self):
        """Initialize the QUBE NYC scraper."""
        super().__init__(
            base_url="https://qubenyc.com",
            retailer_id="5fb99a40-9e34-4b1e-88be-b37b754a33d8"
        )
        
        self.store_info = {
            'name': 'QUBE NYC',
            'legal_name': 'Qube Times Square Dispensary', 
            'address': '1412 Broadway #102, New York, NY 10018',
            'location': 'Times Square, Manhattan',
            'phone': '+1-212-871-0169',
            'license': 'OCM-CAURD-24-000127',
            'state': 'New York',
            'retailer_id': self.retailer_id,
            'platform': 'LeafBridge + Dutchie E-Commerce Pro'
        }
        
        # QUBE-specific category mappings (based on site analysis)
        self.category_mapping = {
            'FLOWER': 'flower',
            'PRE_ROLLS': 'pre-rolls',
            'EDIBLES': 'edibles',
            'CONCENTRATES': 'concentrates',
            'VAPORIZERS': 'vaporizers',
            'TOPICALS': 'topicals',
            'TINCTURES': 'tinctures',
            'ACCESSORIES': 'accessories'
        }
        
        self.logger = logging.getLogger(__name__)
    
    def scrape_all_products(self) -> List[Dict[str, Any]]:
        """
        Scrape all available products from QUBE NYC.
        
        Returns:
            list: List of all products with standardized format
        """
        all_products = []
        
        if not self.initialize_session():
            self.logger.error("Failed to initialize session")
            return []
            
        self.logger.info(f"Scraping products from QUBE NYC (Retailer ID: {self.retailer_id})")
        
        # Try to get products via API first
        products = self.get_products(limit=100)  # Start with high limit
        
        if products:
            all_products.extend(products)
        else:
            # If API doesn't work, try category-based scraping
            self.logger.info("API returned no products, trying category-based approach")
            for category_key, category_name in self.category_mapping.items():
                try:
                    category_products = self.get_products(category=category_key, limit=50)
                    if category_products:
                        all_products.extend(category_products)
                        self.logger.info(f"Found {len(category_products)} products in {category_name}")
                except Exception as e:
                    self.logger.error(f"Error scraping {category_name}: {e}")
                    
                # Rate limiting
                import time
                time.sleep(1)
        
        # Standardize product format
        standardized_products = []
        for product in all_products:
            standardized_product = self._standardize_product(product)
            if standardized_product:
                standardized_products.append(standardized_product)
        
        self.logger.info(f"Successfully scraped {len(standardized_products)} products from QUBE NYC")
        return standardized_products
    
    def _standardize_product(self, raw_product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Standardize a raw product into our common format.
        
        Args:
            raw_product: Raw product data from LeafBridge
            
        Returns:
            dict: Standardized product data
        """
        try:
            # Extract basic product information
            standardized = {
                'store_name': 'QUBE NYC',
                'store_location': 'Times Square, New York, NY',
                'store_license': 'OCM-CAURD-24-000127',
                'platform': 'LeafBridge + Dutchie',
                'scraped_at': self._get_timestamp(),
                
                # Product basics
                'name': raw_product.get('name', '').strip(),
                'brand': raw_product.get('brand', '').strip(),
                'category': self._normalize_category(raw_product.get('category', '')),
                'subcategory': raw_product.get('subcategory', '').strip(),
                
                # Pricing
                'price': self._extract_price(raw_product),
                'price_per_gram': self._calculate_price_per_gram(raw_product),
                
                # Cannabis-specific attributes
                'thc_percent': self._extract_potency(raw_product, 'thc'),
                'cbd_percent': self._extract_potency(raw_product, 'cbd'),
                'strain_type': raw_product.get('strainType', '').lower(),
                'effects': raw_product.get('effects', []),
                
                # Inventory
                'in_stock': self._extract_stock_status(raw_product),
                'weight': self._extract_weight(raw_product),
                
                # Additional data
                'description': raw_product.get('description', '').strip(),
                'image_url': raw_product.get('image', ''),
                'product_id': raw_product.get('id', ''),
                
                # Raw data for debugging
                'raw_data': raw_product
            }
            
            # Validate required fields
            if not standardized['name']:
                self.logger.warning(f"Product missing name: {raw_product}")
                return None
                
            return standardized
            
        except Exception as e:
            self.logger.error(f"Error standardizing product: {e}")
            return None
    
    def _normalize_category(self, category: str) -> str:
        """Normalize category name."""
        category = category.upper().strip()
        return self.category_mapping.get(category, category.lower())
    
    def _extract_price(self, product: Dict[str, Any]) -> Optional[float]:
        """Extract price from product data."""
        price_fields = ['price', 'displayPrice', 'priceRec', 'retail_price']
        
        for field in price_fields:
            if field in product:
                try:
                    price_str = str(product[field]).replace('$', '').replace(',', '')
                    return float(price_str)
                except (ValueError, TypeError):
                    continue
                    
        return None
    
    def _extract_potency(self, product: Dict[str, Any], cannabinoid: str) -> Optional[float]:
        """Extract THC or CBD potency percentage."""
        potency_fields = [
            f'{cannabinoid}Percent',
            f'{cannabinoid}_percent', 
            f'potency{cannabinoid.upper()}',
            f'{cannabinoid}Content'
        ]
        
        for field in potency_fields:
            if field in product and product[field] is not None:
                try:
                    potency_str = str(product[field]).replace('%', '')
                    return float(potency_str)
                except (ValueError, TypeError):
                    continue
                    
        return None
    
    def _extract_stock_status(self, product: Dict[str, Any]) -> bool:
        """Extract stock status."""
        stock_fields = ['inStock', 'in_stock', 'available', 'isAvailable']
        
        for field in stock_fields:
            if field in product:
                return bool(product[field])
                
        # Default to True if no stock info available
        return True
    
    def _extract_weight(self, product: Dict[str, Any]) -> Optional[str]:
        """Extract product weight/size."""
        weight_fields = ['weight', 'size', 'netWeight', 'amount']
        
        for field in weight_fields:
            if field in product and product[field]:
                return str(product[field])
                
        return None
    
    def _calculate_price_per_gram(self, product: Dict[str, Any]) -> Optional[float]:
        """Calculate price per gram if possible."""
        price = self._extract_price(product)
        weight = self._extract_weight(product)
        
        if not price or not weight:
            return None
            
        try:
            # Parse weight to get grams
            weight_str = weight.lower().replace('g', '').replace('gram', '').strip()
            grams = float(weight_str)
            
            if grams > 0:
                return round(price / grams, 2)
                
        except (ValueError, TypeError):
            pass
            
        return None
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
    
    def save_products_to_file(self, products: List[Dict[str, Any]], filename: str = "qube_products.json") -> bool:
        """
        Save scraped products to a JSON file.
        
        Args:
            products: List of product dictionaries
            filename: Output filename
            
        Returns:
            bool: True if saved successfully
        """
        try:
            output_data = {
                'store_info': self.store_info,
                'platform_info': self.get_platform_info(),
                'scrape_timestamp': self._get_timestamp(),
                'product_count': len(products),
                'products': products
            }
            
            filepath = f"memory/stealth-scraper/scrapers/leafbridge/{filename}"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Saved {len(products)} products to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save products: {e}")
            return False
    
    def run_full_extraction(self) -> Dict[str, Any]:
        """
        Run a complete product extraction for QUBE NYC.
        
        Returns:
            dict: Summary of extraction results
        """
        self.logger.info("Starting full product extraction for QUBE NYC")
        
        # Scrape all products
        products = self.scrape_all_products()
        
        # Save to file
        if products:
            self.save_products_to_file(products)
        
        # Generate summary
        summary = {
            'store': 'QUBE NYC',
            'platform': 'LeafBridge + Dutchie',
            'total_products': len(products),
            'categories': self._get_category_breakdown(products),
            'extraction_timestamp': self._get_timestamp(),
            'status': 'success' if products else 'no_products_found'
        }
        
        return summary
    
    def _get_category_breakdown(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of products by category."""
        categories = {}
        for product in products:
            category = product.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        return categories


def main():
    """Main function for testing the QUBE NYC scraper."""
    logging.basicConfig(level=logging.INFO)
    
    scraper = QubeNYCScraper()
    summary = scraper.run_full_extraction()
    
    print(f"\nQUBE NYC Extraction Summary:")
    print(f"Platform: {summary['platform']}")
    print(f"Total Products: {summary['total_products']}")
    print(f"Categories: {summary['categories']}")
    print(f"Status: {summary['status']}")
    
    return summary


if __name__ == "__main__":
    main()