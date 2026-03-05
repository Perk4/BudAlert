/**
 * WordPress Browser Method
 * Uses Playwright to bypass Cloudflare protection
 * 
 * Based on ~/clawd/budalert/scrapers/gotham/scraper-browser.mjs
 */

import { chromium, Browser, BrowserContext, Page } from 'playwright';
import * as cheerio from 'cheerio';
import {
  ScrapingMethod,
  ScrapeConfig,
  ScrapeResult,
  Product,
  calculateFieldCompleteness,
  sleep,
} from '../base.js';

export class WordPressBrowserMethod implements ScrapingMethod {
  name = 'wordpress-browser';
  provider = 'wordpress';
  type = 'browser' as const;
  
  requirements = {
    chromium: true,
    proxy: false,
    cookies: false,
    javascript: true,
  };
  
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;
  
  /**
   * Initialize browser
   */
  private async initBrowser(headless = true): Promise<void> {
    this.browser = await chromium.launch({
      headless,
      args: [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
      ],
    });
    
    this.context = await this.browser.newContext({
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      viewport: { width: 1920, height: 1080 },
    });
    
    // Remove webdriver flag
    this.page = await this.context.newPage();
    await this.page.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', {
        get: () => false,
      });
    });
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
   * Parse potency
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
   * Extract product from element
   */
  private extractProduct($: cheerio.CheerioAPI, element: any, sourceUrl: string): Product | null {
    const $elem = $(element);
    
    const name = this.trySelectors($, $elem, [
      '.product-title',
      '.woocommerce-loop-product__title',
      'h3',
      'h2',
      '.product-name',
    ]);
    
    if (!name) return null;
    
    const price = this.trySelectors($, $elem, [
      '.price .amount',
      '.price',
      '.woocommerce-Price-amount',
    ]);
    
    const category = this.trySelectors($, $elem, [
      '.product-category',
      '.category',
    ]);
    
    const thc = this.trySelectors($, $elem, [
      '.thc',
      '*[class*="thc"]',
    ]);
    
    const cbd = this.trySelectors($, $elem, [
      '.cbd',
      '*[class*="cbd"]',
    ]);
    
    return {
      id: `${name}-${price}`.replace(/\s+/g, '-').toLowerCase(),
      name,
      price: this.parsePrice(price),
      priceRaw: price,
      brand: null,
      category,
      weight: null,
      thc: this.parsePotency(thc),
      cbd: this.parsePotency(cbd),
      inStock: true,
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
      '.dt-product',
      'article.product',
      '.woocommerce-loop-product',
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
      await this.initBrowser(true);
      
      if (!this.page) {
        throw new Error('Failed to initialize browser');
      }
      
      // Navigate to menu page
      await this.page.goto(config.menuUrl || config.url, {
        waitUntil: 'domcontentloaded',
        timeout: config.timeout || 60000,
      });
      
      // Wait for Cloudflare challenge to complete
      await sleep(8000);
      
      // Wait for products to appear
      try {
        await this.page.waitForSelector('.product, .dt-product, article.product', {
          timeout: 15000,
        });
      } catch (e) {
        errors.push('Products not found - may still be on challenge page');
      }
      
      // Get HTML
      const html = await this.page.content();
      
      // Check if still on Cloudflare page
      if (html.includes('Please wait while your request is being verified')) {
        throw new Error('Cloudflare challenge not solved');
      }
      
      // Parse products
      const $ = cheerio.load(html);
      products = this.parseProducts($, config.url);
      
      if (products.length === 0) {
        errors.push('No products found in HTML');
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
    } finally {
      if (this.browser) {
        await this.browser.close();
      }
    }
  }
  
  /**
   * Diagnose failure
   */
  async diagnose(error: Error, html?: string): Promise<any> {
    const message = error.message.toLowerCase();
    
    if (message.includes('cloudflare') || html?.includes('cf_chl_opt')) {
      return {
        type: 'cloudflare',
        explanation: 'Cloudflare challenge not solved',
        suggestedFix: 'Increase wait time or use manual solve mode',
        confidence: 95,
      };
    }
    
    if (message.includes('timeout')) {
      return {
        type: 'network',
        explanation: 'Page load timeout',
        suggestedFix: 'Increase timeout value',
        confidence: 90,
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
