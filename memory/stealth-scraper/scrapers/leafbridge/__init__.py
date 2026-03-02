"""
LeafBridge Cannabis Dispensary Platform Scrapers

This package contains scrapers for cannabis dispensaries using the LeafBridge platform,
which integrates WordPress with Dutchie E-Commerce Pro for cannabis retail management.

Modules:
    leafbridge_base: Base scraper class for LeafBridge-powered sites
    qube_nyc: Specific scraper for QUBE NYC (Times Square location)

Platform Overview:
    - WordPress plugin architecture
    - Dutchie E-Commerce Pro backend integration
    - AJAX-based product loading via wp-admin/admin-ajax.php
    - UUID-based retailer identification system
    - Standardized API actions across implementations

Usage:
    from leafbridge import QubeNYCScraper
    
    scraper = QubeNYCScraper()
    products = scraper.scrape_all_products()
"""

from .leafbridge_base import LeafBridgeBaseScraper
from .qube_nyc import QubeNYCScraper

__version__ = "1.0.0"
__author__ = "Stealth Scraper Team"
__email__ = "scraper@example.com"

__all__ = ["LeafBridgeBaseScraper", "QubeNYCScraper"]