/**
 * Inventory Detector
 * Hacky methods to detect product inventory levels
 */

import { Page } from 'playwright';
import { InventoryResult } from '../methods/base.js';

export class InventoryDetector {
  /**
   * Method 1: Cart Probing
   * Try adding max quantity and check for error message
   */
  async probeCart(page: Page, productUrl: string): Promise<number | null> {
    try {
      await page.goto(productUrl, { timeout: 30000 });
      
      // Try to find quantity input
      const quantityInput = await page.locator('input[name="quantity"], input[type="number"]').first();
      
      if (await quantityInput.isVisible({ timeout: 5000 })) {
        // Set to high number
        await quantityInput.fill('999');
        
        // Click add to cart
        const addButton = await page.locator(
          'button:has-text("Add to Cart"), button[data-add-to-cart], .add-to-cart'
        ).first();
        
        if (await addButton.isVisible({ timeout: 3000 })) {
          await addButton.click();
          
          // Wait for error message
          await page.waitForTimeout(2000);
          
          // Check for error with actual limit
          const errorText = await page.locator('.error, .message, .notice').first().textContent();
          
          if (errorText) {
            const match = errorText.match(/only (\d+) (available|in stock|remaining)/i);
            if (match) {
              return parseInt(match[1]);
            }
          }
        }
      }
      
      return null;
    } catch (error) {
      console.error('[Cart Probe] Error:', error);
      return null;
    }
  }
  
  /**
   * Method 2: Dropdown Options
   * Check quantity dropdown for max value
   */
  async checkDropdown(page: Page): Promise<number | null> {
    try {
      const select = await page.locator('select[name="quantity"]').first();
      
      if (await select.isVisible({ timeout: 3000 })) {
        const options = await select.locator('option').allTextContents();
        
        const numbers = options
          .map(opt => parseInt(opt))
          .filter(n => !isNaN(n));
        
        if (numbers.length > 0) {
          return Math.max(...numbers);
        }
      }
      
      return null;
    } catch (error) {
      return null;
    }
  }
  
  /**
   * Method 3: Stock Badge Detection
   * Look for stock indicators in HTML
   */
  async detectBadge(html: string): Promise<{ status: string; quantity?: number } | null> {
    const patterns = [
      { regex: /(\d+)\s*(?:left|remaining|in stock)/i, type: 'quantity' },
      { regex: /(?:low stock|limited|few left)/i, type: 'low' },
      { regex: /(?:out of stock|sold out|unavailable)/i, type: 'out' },
      { regex: /(?:in stock|available)/i, type: 'in' },
    ];
    
    for (const pattern of patterns) {
      const match = html.match(pattern.regex);
      if (match) {
        if (pattern.type === 'quantity') {
          return {
            status: 'in_stock',
            quantity: parseInt(match[1]),
          };
        } else {
          return {
            status: pattern.type,
          };
        }
      }
    }
    
    return null;
  }
  
  /**
   * Method 4: API Response Inspection
   * Intercept API calls and look for inventory data
   */
  async interceptInventory(
    page: Page,
    url: string,
    timeout: number = 10000
  ): Promise<Map<string, number>> {
    const inventoryData = new Map<string, number>();
    
    // Set up response listener
    page.on('response', async (response) => {
      if (response.status() === 200) {
        try {
          const json = await response.json();
          const found = this.findInventoryFields(json);
          
          if (found) {
            for (const [id, qty] of Object.entries(found)) {
              inventoryData.set(id, qty as number);
            }
          }
        } catch (e) {
          // Not JSON
        }
      }
    });
    
    await page.goto(url, { timeout });
    await page.waitForTimeout(timeout);
    
    return inventoryData;
  }
  
  /**
   * Recursively search for inventory-like fields in JSON
   */
  private findInventoryFields(obj: any, depth: number = 0): Record<string, number> | null {
    if (depth > 5 || !obj || typeof obj !== 'object') {
      return null;
    }
    
    const result: Record<string, number> = {};
    
    // Look for inventory-like fields
    const inventoryKeys = [
      'inventory',
      'stock',
      'quantity',
      'qty',
      'available',
      'inStock',
      'quantityAvailable',
    ];
    
    for (const [key, value] of Object.entries(obj)) {
      const lowerKey = key.toLowerCase();
      
      // Check if this is an inventory field
      if (inventoryKeys.some(k => lowerKey.includes(k))) {
        if (typeof value === 'number') {
          // Found inventory value
          const productId = obj.id || obj.productId || obj.sku || 'unknown';
          result[productId] = value;
        }
      }
      
      // Recurse into nested objects
      if (typeof value === 'object' && value !== null) {
        const nested = this.findInventoryFields(value, depth + 1);
        if (nested) {
          Object.assign(result, nested);
        }
      }
    }
    
    return Object.keys(result).length > 0 ? result : null;
  }
  
  /**
   * Method 5: DOM Attribute Sniffing
   * Look for data attributes with inventory info
   */
  async sniffAttributes(page: Page): Promise<Map<string, number>> {
    try {
      const inventoryMap = await page.evaluate(() => {
        const map: Record<string, number> = {};
        
        // Look for elements with inventory data attributes
        const selectors = [
          '[data-quantity]',
          '[data-stock]',
          '[data-inventory]',
          '[data-available]',
        ];
        
        for (const selector of selectors) {
          const elements = document.querySelectorAll(selector);
          
          elements.forEach((el) => {
            const productId =
              el.getAttribute('data-product-id') ||
              el.getAttribute('data-id') ||
              el.getAttribute('id') ||
              'unknown';
            
            const qty =
              el.getAttribute('data-quantity') ||
              el.getAttribute('data-stock') ||
              el.getAttribute('data-inventory') ||
              el.getAttribute('data-available');
            
            if (qty && !isNaN(parseInt(qty))) {
              map[productId] = parseInt(qty);
            }
          });
        }
        
        return map;
      });
      
      return new Map(Object.entries(inventoryMap));
    } catch (error) {
      return new Map();
    }
  }
  
  /**
   * Run all detection methods and return best result
   */
  async detect(page: Page, url: string): Promise<InventoryResult> {
    console.log('[Inventory] Running detection methods...');
    
    // Try API interception first (most reliable)
    const apiData = await this.interceptInventory(page, url, 5000);
    if (apiData.size > 0) {
      console.log(`[Inventory] ✅ API interception found ${apiData.size} items`);
      return {
        method: 'api',
        confidence: 95,
        inventoryData: apiData,
      };
    }
    
    // Try DOM attributes
    const attrData = await this.sniffAttributes(page);
    if (attrData.size > 0) {
      console.log(`[Inventory] ✅ Attribute sniffing found ${attrData.size} items`);
      return {
        method: 'api', // Data attributes are usually from API
        confidence: 85,
        inventoryData: attrData,
      };
    }
    
    // Try dropdown
    const dropdownQty = await this.checkDropdown(page);
    if (dropdownQty !== null) {
      console.log(`[Inventory] ✅ Dropdown method found max: ${dropdownQty}`);
      return {
        method: 'dropdown',
        confidence: 70,
        notes: `Max quantity: ${dropdownQty}`,
      };
    }
    
    // Try badge detection
    const html = await page.content();
    const badge = await this.detectBadge(html);
    if (badge) {
      console.log(`[Inventory] ✅ Badge detection found: ${badge.status}`);
      return {
        method: 'badge',
        confidence: 60,
        notes: JSON.stringify(badge),
      };
    }
    
    console.log('[Inventory] ❌ No inventory detection method succeeded');
    return {
      method: 'none',
      confidence: 0,
    };
  }
}
