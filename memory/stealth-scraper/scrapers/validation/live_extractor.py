#!/usr/bin/env python3
"""
Live Data Extractor
Uses browser automation to extract current product data from live sites
"""

import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import re

class LiveDataExtractor:
    """Extracts live product data from websites"""
    
    def __init__(self):
        self.screenshots_dir = "memory/stealth-scraper/scrapers/validation/screenshots"
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def extract_thc_from_text(self, text: str) -> Optional[float]:
        """Extract THC percentage from text"""
        if not text:
            return None
        # Look for patterns like "18.5%", "THC: 18.5", etc.
        patterns = [
            r'thc[:\s]*(\d+\.?\d*)\s*%',
            r'(\d+\.?\d*)\s*%\s*thc',
            r'thc[:\s]*(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None
    
    def extract_price_from_text(self, text: str) -> Optional[float]:
        """Extract price from text"""
        if not text:
            return None
        # Look for patterns like "$55.00", "$55", "55.00"
        match = re.search(r'\$?(\d+\.?\d*)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None
    
    def determine_stock_status(self, page_text: str) -> bool:
        """Determine if product is in stock based on page text"""
        if not page_text:
            return False
        
        text_lower = page_text.lower()
        
        # Out of stock indicators
        out_of_stock_terms = [
            'out of stock',
            'sold out',
            'unavailable',
            'not available',
            'temporarily unavailable',
            'coming soon'
        ]
        
        for term in out_of_stock_terms:
            if term in text_lower:
                return False
        
        # In stock indicators
        in_stock_terms = [
            'add to cart',
            'buy now',
            'in stock',
            'available',
            'order now'
        ]
        
        for term in in_stock_terms:
            if term in text_lower:
                return True
        
        # Default to in stock if no clear indicators
        return True
    
    def classify_category(self, name: str, description: str = "") -> str:
        """Classify product category based on name and description"""
        text = (name + " " + description).lower()
        
        if any(term in text for term in ['flower', 'bud', 'gram', '3.5g', '7g', '14g', 'oz']):
            return 'flower'
        elif any(term in text for term in ['cartridge', 'cart', 'vape', 'pen']):
            return 'cartridge'  
        elif any(term in text for term in ['edible', 'gummy', 'chocolate', 'cookie']):
            return 'edible'
        elif any(term in text for term in ['concentrate', 'wax', 'shatter', 'rosin']):
            return 'concentrate'
        else:
            return 'other'
    
    async def extract_alta_product(self, browser_tool, url: str, product_id: str) -> Optional[Dict]:
        """Extract product data from Alta NYC"""
        try:
            # Navigate to product page
            result = await browser_tool("open", {"targetUrl": url})
            if not result.get("success"):
                return None
            
            # Take screenshot
            screenshot_path = f"{self.screenshots_dir}/alta_{product_id}.png"
            await browser_tool("screenshot", {"path": screenshot_path})
            
            # Get page snapshot
            snapshot = await browser_tool("snapshot")
            page_text = snapshot.get("text", "")
            
            # Extract product information
            live_data = {
                'url': url,
                'extracted_at': datetime.now().isoformat(),
                'page_text_length': len(page_text),
                'screenshot_path': screenshot_path
            }
            
            # Try to extract specific elements (Alta-specific selectors would go here)
            # For now, we'll use text-based extraction as fallback
            
            # Extract name (look for product title)
            name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', page_text, re.IGNORECASE)
            if name_match:
                live_data['name'] = name_match.group(1).strip()
            
            # Extract price
            price = self.extract_price_from_text(page_text)
            if price:
                live_data['price'] = price
            
            # Extract THC content
            thc = self.extract_thc_from_text(page_text)
            if thc:
                live_data['thc_content'] = thc
            
            # Determine stock status
            live_data['in_stock'] = self.determine_stock_status(page_text)
            
            # Classify category
            live_data['category'] = self.classify_category(
                live_data.get('name', ''), 
                page_text[:500]  # Use first 500 chars for category classification
            )
            
            return live_data
            
        except Exception as e:
            print(f"Error extracting Alta product {product_id}: {e}")
            return None
    
    async def extract_custom_product(self, browser_tool, url: str, store: str, product_id: str) -> Optional[Dict]:
        """Extract product data from custom stores"""
        try:
            # Navigate to product page
            result = await browser_tool("open", {"targetUrl": url})
            if not result.get("success"):
                return None
            
            # Take screenshot
            screenshot_path = f"{self.screenshots_dir}/{store}_{product_id}.png"
            await browser_tool("screenshot", {"path": screenshot_path})
            
            # Get page snapshot
            snapshot = await browser_tool("snapshot")
            page_text = snapshot.get("text", "")
            
            # Extract product information
            live_data = {
                'url': url,
                'store': store,
                'extracted_at': datetime.now().isoformat(),
                'page_text_length': len(page_text),
                'screenshot_path': screenshot_path
            }
            
            # Generic extraction logic for custom stores
            # Extract name (look for common title selectors)
            title_patterns = [
                r'<h1[^>]*>([^<]+)</h1>',
                r'<title>([^<]+)</title>',
                r'class="[^"]*title[^"]*">([^<]+)<',
                r'class="[^"]*name[^"]*">([^<]+)<'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    live_data['name'] = match.group(1).strip()
                    break
            
            # Extract price
            price = self.extract_price_from_text(page_text)
            if price:
                live_data['price'] = price
            
            # Extract THC content  
            thc = self.extract_thc_from_text(page_text)
            if thc:
                live_data['thc_content'] = thc
            
            # Determine stock status
            live_data['in_stock'] = self.determine_stock_status(page_text)
            
            # Classify category
            live_data['category'] = self.classify_category(
                live_data.get('name', ''),
                page_text[:500]
            )
            
            return live_data
            
        except Exception as e:
            print(f"Error extracting {store} product {product_id}: {e}")
            return None

async def main():
    """Demo of live extraction (would be integrated with validator)"""
    extractor = LiveDataExtractor()
    
    # Example usage
    print("🌐 Live Data Extractor initialized")
    print("📸 Screenshots will be saved to:", extractor.screenshots_dir)
    print("⚠️  This script provides the framework for live extraction")
    print("   Integration with browser automation would happen in the main validator")

if __name__ == "__main__":
    asyncio.run(main())