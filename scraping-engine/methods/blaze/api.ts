/**
 * Blaze HTTP Method
 * Lightweight HTTP scraper for Blaze platform
 * 
 * Based on ~/clawd/budalert/scrapers/housing-works/scraper.mjs
 */

import axios from 'axios';
import * as cheerio from 'cheerio';
import {
  ScrapingMethod,
  ScrapeConfig,
  ScrapeResult,
  Product,
  calculateFieldCompleteness,
  sleep,
} from '../base.js';

export class BlazeAPIMethod implements ScrapingMethod {
  name = 'blaze-http';
  provider = 'blaze';
  type = 'http' as const;
  
  requirements = {
    chromium: false,
    proxy: false,
    cookies: false,
    javascript: false,
  };
  
  /**
   * Fetch page HTML
   */
  private async fetchPage(url: string, timeout: number): Promise<string> {
    const response = await axios.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
      },
      timeout,
      maxRedirects: 5,
    });
    
    return response.data;
  }
  
  /**
   * Try multiple selectors
   */
  private trySelectors($: cheerio.CheerioAPI, $elem: cheerio.Cheerio<any>, selectors: string[]): string | null {
    for (const selector of selectors) {
      try {
        const text = $elem.find(selector).first().text();
        if (text && text.trim()) {
          return text.trim();
        }
      } catch (e) {
        // Try next
      }
    }
    return null;
  }
  
  /**
   * Parse price string
   */
  private parsePrice(priceString: string | null): number | null {
    if (!priceString) return null;
    
    const match = priceString.match(/[\d,]+\.?\d*/);
    if (match) {
      return parseFloat(match[0].replace(/,/g, ''));
    }
    
    return null;
  }
  
  /**
   * Parse potency string
   */
  private parsePotency(potencyString: string | null): { formatted: string; value: number } | null {
    if (!potencyString) return null;
    
    const match = potencyString.match(/(\d+\.?\d*)%?/);
    if (match) {
      return {
        formatted: potencyString.trim(),
        value: parseFloat(match[1]),
      };
    }
    
    return null;
  }
  
  /**
   * Extract product from HTML element
   */
  private extractProduct($: cheerio.CheerioAPI, element: any, sourceUrl: string): Product | null {
    const $elem = $(element);
    
    const name = this.trySelectors($, $elem, [
      '.product-name',
      '.product-title',
      'h3',
      'h2',
      '.name',
      'strong',
    ]);
    
    if (!name) return null;
    
    const price = this.trySelectors($, $elem, [
      '.price',
      '.product-price',
      '.cost',
      'span[class*="price"]',
    ]);
    
    const thc = this.trySelectors($, $elem, [
      '.thc',
      '.thc-content',
      '*[class*="thc"]',
    ]);
    
    const cbd = this.trySelectors($, $elem, [
      '.cbd',
      '.cbd-content',
      '*[class*="cbd"]',
    ]);
    
    const category = this.trySelectors($, $elem, [
      '.category',
      '.product-category',
      '.type',
    ]);
    
    const brand = this.trySelectors($, $elem, [
      '.brand',
      '.product-brand',
    ]);
    
    const weight = this.trySelectors($, $elem, [
      '.weight',
      '.size',
      '.amount',
    ]);
    
    // Check stock status
    const text = $elem.text().toLowerCase();
    const inStock = !(
      text.includes('out of stock') ||
      text.includes('sold out') ||
      text.includes('unavailable')
    );
    
    return {
      id: `${name}-${price}`.replace(/\s+/g, '-').toLowerCase(),
      name,
      price: this.parsePrice(price),
      priceRaw: price,
      brand,
      category,
      weight,
      thc: this.parsePotency(thc),
      cbd: this.parsePotency(cbd),
      inStock,
      quantity: null,
      url: null,
      imageUrl: null,
      description: null,
      metadata: {},
    };
  }
  
  /**
   * Parse products from HTML
   */
  private parseProducts($: cheerio.CheerioAPI, sourceUrl: string): Product[] {
    const products: Product[] = [];
    
    const productSelectors = [
      '.product',
      '.product-item',
      '.menu-item',
      '[data-product]',
      '.product-card',
      'article.product',
    ];
    
    const elements = new Set<any>();
    
    for (const selector of productSelectors) {
      $(selector).each((_, elem) => {
        elements.add(elem);
      });
      
      if (elements.size > 0) break;
    }
    
    elements.forEach((elem) => {
      const product = this.extractProduct($, elem, sourceUrl);
      if (product) {
        products.push(product);
      }
    });
    
    return products;
  }
  
  /**
   * Main scrape function
   */
  async scrape(config: ScrapeConfig): Promise<ScrapeResult> {
    const startTime = Date.now();
    const errors: string[] = [];
    let products: Product[] = [];
    
    try {
      const html = await this.fetchPage(config.menuUrl || config.url, config.timeout || 30000);
      const $ = cheerio.load(html);
      
      products = this.parseProducts($, config.url);
      
      if (products.length === 0) {
        // Save HTML for debugging
        errors.push('No products found - HTML structure may have changed');
      }
      
      const scrapeTimeMs = Date.now() - startTime;
      
      return {
        success: products.length > 0,
        products,
        fieldCompleteness: calculateFieldCompleteness(products),
        metadata: {
          scrapeTimeMs,
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
  
  /**
   * Diagnose failure
   */
  async diagnose(error: Error, html?: string): Promise<any> {
    const message = error.message.toLowerCase();
    
    if (html && html.includes('cloudflare')) {
      return {
        type: 'cloudflare',
        explanation: 'Cloudflare protection detected',
        suggestedFix: 'Switch to browser-based method',
        confidence: 90,
      };
    }
    
    if (message.includes('timeout')) {
      return {
        type: 'network',
        explanation: 'Request timed out',
        suggestedFix: 'Increase timeout or check network',
        confidence: 90,
      };
    }
    
    if (html && !html.includes('product')) {
      return {
        type: 'structure_change',
        explanation: 'HTML structure changed - no product elements found',
        suggestedFix: 'Update product selectors',
        confidence: 80,
      };
    }
    
    return {
      type: 'other',
      explanation: error.message,
      suggestedFix: null,
      confidence: 50,
    };
  }
}
