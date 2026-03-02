#!/usr/bin/env python3
"""
LeafBridge Platform Base Scraper

LeafBridge is a WordPress plugin that integrates with Dutchie Plus/Dutchie E-Commerce Pro.
It provides a standardized way for cannabis retailers to manage their online menus.

Architecture discovered:
- WordPress plugin with custom AJAX endpoints
- Integrates with Dutchie E-Commerce backend  
- Uses retail IDs to identify stores (e.g., 5fb99a40-9e34-4b1e-88be-b37b754a33d8 for QUBE)
- AJAX actions: wizard_show_products, show_featured_products_func, leafbridge_single_product
- Age verification gate often required
- Menu types: RECREATIONAL, MEDICAL
- Order types: pickup, delivery
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import logging

class LeafBridgeBaseScraper:
    """Base class for scraping LeafBridge-powered cannabis dispensary websites."""
    
    def __init__(self, base_url: str, retailer_id: Optional[str] = None):
        """
        Initialize the LeafBridge scraper.
        
        Args:
            base_url: The base URL of the LeafBridge-powered site (e.g., "https://qubenyc.com")
            retailer_id: The Dutchie retailer ID (can be auto-detected if not provided)
        """
        self.base_url = base_url.rstrip('/')
        self.retailer_id = retailer_id
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # LeafBridge endpoint patterns
        self.ajax_url = f"{self.base_url}/wp-admin/admin-ajax.php"
        self.api_endpoints = {
            'default_retailer': {'action': 'get_default_retailer'},
            'products': {'action': 'wizard_show_products'},
            'featured_products': {'action': 'show_featured_products_func'},
            'single_product': {'action': 'leafbridge_single_product'},
            'cart_items': {'action': 'leafbridge_get_cart_items'},
            'delivery_pickup': {'action': 'show_delivery_pickup_ajax'},
            'nearby_retailers': {'action': 'leafbridge_nearby_retailers'},
        }
        
        self.logger = logging.getLogger(__name__)
        
    def initialize_session(self) -> bool:
        """
        Initialize the session by visiting the main page and handling age gates.
        
        Returns:
            bool: True if session initialized successfully
        """
        try:
            # Visit main page to establish session
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            # Auto-detect retailer ID if not provided
            if not self.retailer_id:
                self.retailer_id = self._detect_retailer_id()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize session: {e}")
            return False
    
    def _detect_retailer_id(self) -> Optional[str]:
        """
        Auto-detect the retailer ID from the site configuration.
        
        Returns:
            str: The retailer ID if found, None otherwise
        """
        try:
            response = self._make_ajax_request('default_retailer')
            if response and response.get('success'):
                data = response.get('data', {})
                settings = data.get('leafbridge_default_settings', {})
                return settings.get('default_store')
                
        except Exception as e:
            self.logger.error(f"Failed to detect retailer ID: {e}")
            
        return None
    
    def _make_ajax_request(self, endpoint: str, extra_data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make an AJAX request to a LeafBridge endpoint.
        
        Args:
            endpoint: The endpoint key from self.api_endpoints
            extra_data: Additional data to include in the request
            
        Returns:
            dict: The JSON response if successful, None otherwise
        """
        if endpoint not in self.api_endpoints:
            raise ValueError(f"Unknown endpoint: {endpoint}")
            
        data = self.api_endpoints[endpoint].copy()
        
        # Add retailer context if available
        if self.retailer_id:
            data.update({
                'retailer_id': self.retailer_id,
                'menu_type': 'RECREATIONAL'  # Default to recreational
            })
            
        # Add any extra data
        if extra_data:
            data.update(extra_data)
            
        try:
            response = self.session.post(
                self.ajax_url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"AJAX request failed for {endpoint}: {e}")
            return None
    
    def get_products(self, category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get products from the LeafBridge menu.
        
        Args:
            category: Optional category filter
            limit: Maximum number of products to return
            
        Returns:
            list: List of product dictionaries
        """
        extra_data = {
            'prods_per_page': limit,
            'current_page': 1
        }
        
        if category:
            extra_data['category'] = category
            
        response = self._make_ajax_request('products', extra_data)
        
        if response and response.get('success'):
            data = response.get('data', {})
            products_html = data.get('products_html', '')
            
            # If we get HTML, we'd need to parse it
            # If we get structured data, extract it
            if data.get('products_list'):
                return data['products_list']
            else:
                # Parse HTML or try alternative methods
                return self._parse_products_html(products_html)
                
        return []
    
    def _parse_products_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse product data from HTML response.
        
        Args:
            html: The HTML content containing product data
            
        Returns:
            list: List of product dictionaries
        """
        # This would require BeautifulSoup or similar HTML parsing
        # For now, return empty list if no structured data
        if "Could not find products" in html:
            return []
            
        # TODO: Implement HTML parsing for product extraction
        return []
    
    def get_featured_products(self) -> List[Dict[str, Any]]:
        """Get featured products."""
        response = self._make_ajax_request('featured_products')
        
        if response and response.get('success'):
            # Process featured products response
            return response.get('data', {}).get('products', [])
            
        return []
    
    def get_single_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a single product.
        
        Args:
            product_id: The product ID
            
        Returns:
            dict: Product details if found, None otherwise
        """
        response = self._make_ajax_request('single_product', {'product_id': product_id})
        
        if response and response.get('success'):
            return response.get('data')
            
        return None
    
    def handle_age_verification(self) -> bool:
        """
        Handle age verification gate if present.
        
        Returns:
            bool: True if handled successfully
        """
        # Age verification is often handled client-side via JavaScript
        # The exact implementation varies by site configuration
        try:
            # Some sites may have an age verification AJAX endpoint
            # Others handle it purely via cookies/localStorage
            
            # For now, assume age verification is handled by visiting the main page
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to handle age verification: {e}")
            return False
    
    def get_platform_info(self) -> Dict[str, Any]:
        """
        Get information about the LeafBridge platform configuration.
        
        Returns:
            dict: Platform configuration information
        """
        response = self._make_ajax_request('default_retailer')
        
        info = {
            'platform': 'LeafBridge',
            'retailer_id': self.retailer_id,
            'base_url': self.base_url,
            'integration': 'Dutchie E-Commerce',
        }
        
        if response and response.get('success'):
            data = response.get('data', {})
            settings = data.get('leafbridge_default_settings', {})
            info.update({
                'default_menu_type': settings.get('default_menu_type'),
                'default_order_type': settings.get('default_order_type'),
                'age_confirmation': settings.get('age_confirmation'),
                'pagination_style': settings.get('pagination_style'),
            })
            
        return info