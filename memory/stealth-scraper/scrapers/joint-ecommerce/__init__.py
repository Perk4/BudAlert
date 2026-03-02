"""
Joint Ecommerce platform scrapers package.
Contains scrapers for Torches, Stoops, and Alta dispensaries.
"""

from .base_scraper import JointEcommerceScraper
from .alta import AltaScraper, scrape_alta

__all__ = ['JointEcommerceScraper', 'AltaScraper', 'scrape_alta']