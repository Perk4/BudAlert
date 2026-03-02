"""
Base scraper for custom cannabis dispensary sites
Handles common patterns found across custom dispensary sites
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

class BaseCustomScraper:
    """Base class for scraping custom cannabis dispensary websites"""
    
    def __init__(self, base_url: str, store_name: str):
        self.base_url = base_url
        self.store_name = store_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        # Remove $ and other characters, extract first number
        price_match = re.search(r'\$?(\d+\.?\d*)', price_text.replace(',', ''))
        return float(price_match.group(1)) if price_match else None
    
    def extract_thc_cbd(self, text: str) -> Dict[str, Optional[float]]:
        """Extract THC/CBD percentages from text"""
        result = {'thc': None, 'cbd': None}
        if not text:
            return result
            
        # Look for THC: 25.5% or THC 25.5%
        thc_match = re.search(r'THC:?\s*(\d+\.?\d*)%?', text, re.IGNORECASE)
        if thc_match:
            result['thc'] = float(thc_match.group(1))
            
        # Look for CBD: 2.5% or CBD 2.5%
        cbd_match = re.search(r'CBD:?\s*(\d+\.?\d*)%?', text, re.IGNORECASE)
        if cbd_match:
            result['cbd'] = float(cbd_match.group(1))
            
        return result
    
    def standardize_category(self, category: str) -> str:
        """Standardize category names"""
        if not category:
            return "unknown"
        
        category_lower = category.lower()
        if 'flower' in category_lower or 'bud' in category_lower:
            return 'flower'
        elif 'edible' in category_lower or 'gummy' in category_lower:
            return 'edibles'
        elif 'vape' in category_lower or 'cartridge' in category_lower:
            return 'vaporizers'
        elif 'concentrate' in category_lower or 'wax' in category_lower or 'shatter' in category_lower:
            return 'concentrates'
        elif 'pre-roll' in category_lower or 'joint' in category_lower:
            return 'pre-rolls'
        else:
            return category.lower()
    
    def extract_products(self) -> List[Dict]:
        """Override this method in child classes"""
        raise NotImplementedError("Subclasses must implement extract_products")
    
    def save_products(self, products: List[Dict], filename: str = None):
        """Save products to JSON file"""
        if not filename:
            filename = f"{self.store_name.lower().replace(' ', '_')}_products.json"
        
        with open(filename, 'w') as f:
            json.dump(products, f, indent=2)
        
        print(f"Saved {len(products)} products to {filename}")
    
    def create_product_dict(self, name: str, price: float = None, 
                          thc: float = None, cbd: float = None,
                          category: str = None, stock_status: str = "unknown",
                          brand: str = None, description: str = None,
                          url: str = None) -> Dict:
        """Create standardized product dictionary"""
        return {
            'name': name,
            'price': price,
            'thc_percent': thc,
            'cbd_percent': cbd,
            'category': self.standardize_category(category),
            'stock_status': stock_status,
            'brand': brand,
            'description': description,
            'url': url,
            'store': self.store_name,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

class JSBasedScraper(BaseCustomScraper):
    """For sites that load products via JavaScript (requires browser automation)"""
    
    def __init__(self, base_url: str, store_name: str, menu_selectors: Dict[str, str]):
        super().__init__(base_url, store_name)
        self.menu_selectors = menu_selectors
        
    def extract_products(self) -> List[Dict]:
        """This would require browser automation like Playwright/Selenium"""
        print(f"WARNING: {self.store_name} requires browser automation for product extraction")
        print("Product data is loaded via JavaScript and cannot be scraped with basic requests")
        return []

# Common selectors that might be useful across custom sites
COMMON_SELECTORS = {
    'product_cards': [
        '.product-card', '.product-item', '.menu-item', 
        '.product', '.listing-item', '.weed-product'
    ],
    'product_names': [
        '.product-name', '.product-title', '.item-name',
        'h3', 'h4', '.name', '.title'
    ],
    'prices': [
        '.price', '.cost', '.amount', '.product-price',
        '.price-display', '[data-price]'
    ],
    'categories': [
        '.category', '.product-type', '.type', 
        '.tag', '.classification'
    ],
    'stock_status': [
        '.stock', '.availability', '.in-stock', '.out-of-stock',
        '.status', '[data-stock]'
    ],
    'potency': [
        '.thc', '.cbd', '.potency', '.strength',
        '.percentage', '.cannabinoids'
    ]
}