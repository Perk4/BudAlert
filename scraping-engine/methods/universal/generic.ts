/**
 * Universal Generic HTML Method
 * Fallback scraper that tries common patterns
 */

import axios from 'axios';
import * as cheerio from 'cheerio';
import {
  ScrapingMethod,
  ScrapeConfig,
  ScrapeResult,
  Product,
  calculateFieldCompleteness,
} from '../base.js';

export class GenericHTMLMethod implements ScrapingMethod {
  name = 'universal-generic-html';
  provider = 'universal';
  type = 'http' as const;
  
  requirements = {
    chromium: false,
    proxy: false,
    cookies: false,
    javascript: false,
  };
  
  /**
   * Try to find products using common patterns
   */
  private findProductElements($: cheerio.CheerioAPI): cheerio.Cheerio<any>[] {
    const selectors = [
      '.product',
      '.product-item',
      '.menu-item',
      '[data-product]',
      '.product-card',
      'article.product',
      '.item',
      '.product-list-item',
      '[itemtype*="Product"]',
    ];
    
    for (const selector of selectors) {
      const elements = $(selector);
      if (elements.length > 0) {
        return elements.toArray().map(e => $(e));
      }
    }
    
    return [];
  }
  
  /**
   * Try to extract data from element
   */
  private extractFromElement($: cheerio.CheerioAPI, $elem: cheerio.Cheerio<any>): Partial<Product> {
    const data: Partial<Product> = {};
    
    // Name
    const nameSelectors = ['h1', 'h2', 'h3', '.name', '.title', '.product-name', '[itemprop="name"]'];
    for (const sel of nameSelectors) {
      const text = $elem.find(sel).first().text().trim();
      if (text) {
        data.name = text;
        break;
      }
    }
    
    // Price
    const priceSelectors = ['.price', '.cost', '[itemprop="price"]', '.amount'];
    for (const sel of priceSelectors) {
      const text = $elem.find(sel).first().text().trim();
      const match = text.match(/[\d,]+\.?\d*/);
      if (match) {
        data.price = parseFloat(match[0].replace(/,/g, ''));
        data.priceRaw = text;
        break;
      }
    }
    
    return data;
  }
  
  /**
   * Main scrape function
   */
  async scrape(config: ScrapeConfig): Promise<ScrapeResult> {
    const startTime = Date.now();
    const errors: string[] = [];
    const products: Product[] = [];
    
    try {
      const response = await axios.get(config.menuUrl || config.url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        },
        timeout: config.timeout || 30000,
      });
      
      const $ = cheerio.load(response.data);
      const elements = this.findProductElements($);
      
      if (elements.length === 0) {
        errors.push('No product elements found with generic selectors');
      }
      
      for (const $elem of elements) {
        const data = this.extractFromElement($, $elem);
        
        if (data.name) {
          products.push({
            id: data.name.replace(/\s+/g, '-').toLowerCase(),
            name: data.name,
            price: data.price || null,
            priceRaw: data.priceRaw || null,
            brand: null,
            category: null,
            weight: null,
            thc: null,
            cbd: null,
            inStock: true,
            quantity: null,
            url: null,
            imageUrl: null,
            description: null,
            metadata: {},
          });
        }
      }
      
      return {
        success: products.length > 0,
        products,
        fieldCompleteness: calculateFieldCompleteness(products),
        metadata: {
          scrapeTimeMs: Date.now() - startTime,
          pagesVisited: 1,
          requestsMade: 1,
          method: this.name,
        },
        errors: errors.length > 0 ? errors : undefined,
      };
    } catch (error: any) {
      errors.push(error.message);
      
      return {
        success: false,
        products,
        fieldCompleteness: calculateFieldCompleteness(products),
        metadata: {
          scrapeTimeMs: Date.now() - startTime,
          pagesVisited: 0,
          requestsMade: 1,
          method: this.name,
        },
        errors,
      };
    }
  }
}
