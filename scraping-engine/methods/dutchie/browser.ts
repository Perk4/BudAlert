/**
 * Dutchie Browser Method
 * Uses Playwright to intercept network requests
 * 
 * Based on ~/clawd/budalert/scrapers/conbud/browser-scraper.mjs
 */

import { chromium, Browser, BrowserContext, Page } from 'playwright';
import {
  ScrapingMethod,
  ScrapeConfig,
  ScrapeResult,
  Product,
  calculateFieldCompleteness,
  sleep,
} from '../base.js';

interface GraphQLRequest {
  url: string;
  timestamp: number;
  query: string;
  variables: any;
  operationName: string | null;
}

interface GraphQLResponse {
  url: string;
  timestamp: number;
  data: any;
}

export class DutchieBrowserMethod implements ScrapingMethod {
  name = 'dutchie-browser-intercept';
  provider = 'dutchie';
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
  private graphqlRequests: GraphQLRequest[] = [];
  private graphqlResponses: GraphQLResponse[] = [];
  private products: Product[] = [];
  
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
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    });
    
    this.page = await this.context.newPage();
    
    // Set up network interception
    await this.setupNetworkIntercept();
  }
  
  /**
   * Set up network request/response interception
   */
  private async setupNetworkIntercept(): Promise<void> {
    if (!this.page) return;
    
    // Intercept requests
    this.page.on('request', (request) => {
      const url = request.url();
      
      if (url.includes('api.dutchie.com') && request.method() === 'POST') {
        const postData = request.postData();
        
        if (postData) {
          try {
            const payload = JSON.parse(postData);
            this.graphqlRequests.push({
              url,
              timestamp: Date.now(),
              query: payload.query,
              variables: payload.variables,
              operationName: payload.operationName,
            });
          } catch (e) {
            // Not JSON, skip
          }
        }
      }
    });
    
    // Intercept responses
    this.page.on('response', async (response) => {
      const url = response.url();
      
      if (url.includes('api.dutchie.com') && response.status() === 200) {
        try {
          const json = await response.json();
          this.graphqlResponses.push({
            url,
            timestamp: Date.now(),
            data: json,
          });
          
          // Extract products from this response
          this.extractProductsFromResponse(json);
        } catch (e) {
          // Not JSON or failed to parse
        }
      }
    });
  }
  
  /**
   * Extract products from GraphQL response
   */
  private extractProductsFromResponse(json: any): void {
    const possiblePaths = [
      json?.data?.menu?.products,
      json?.data?.filteredProducts?.products,
      json?.data?.products,
    ];
    
    for (const rawProducts of possiblePaths) {
      if (Array.isArray(rawProducts) && rawProducts.length > 0) {
        rawProducts.forEach((raw) => {
          const product = this.normalizeProduct(raw);
          if (product) {
            this.products.push(product);
          }
        });
        break;
      }
    }
  }
  
  /**
   * Normalize Dutchie product
   */
  private normalizeProduct(raw: any): Product | null {
    if (!raw.id || !raw.name) return null;
    
    const variant = raw.variants?.[0];
    const price = variant?.priceRec || variant?.priceMed || null;
    
    return {
      id: raw.id,
      name: raw.name,
      price,
      priceRaw: price ? `$${price}` : null,
      brand: raw.brand?.name || null,
      category: raw.category || null,
      weight: variant?.option || null,
      thc: raw.potencyThc?.formatted
        ? {
            formatted: raw.potencyThc.formatted,
            value: parseFloat(raw.potencyThc.formatted) || 0,
          }
        : null,
      cbd: raw.potencyCbd?.formatted
        ? {
            formatted: raw.potencyCbd.formatted,
            value: parseFloat(raw.potencyCbd.formatted) || 0,
          }
        : null,
      inStock: true,
      quantity: null,
      url: null,
      imageUrl: raw.image || null,
      description: raw.description || null,
      metadata: {
        effects: raw.effects || [],
      },
    };
  }
  
  /**
   * Scroll page to trigger lazy loading
   */
  private async scrollToLoadAll(steps = 5, delay = 1000): Promise<void> {
    if (!this.page) return;
    
    for (let i = 0; i < steps; i++) {
      await this.page.evaluate(() => {
        window.scrollBy(0, window.innerHeight);
      });
      await sleep(delay);
    }
    
    await this.page.evaluate(() => window.scrollTo(0, 0));
  }
  
  /**
   * Main scrape function
   */
  async scrape(config: ScrapeConfig): Promise<ScrapeResult> {
    const startTime = Date.now();
    const errors: string[] = [];
    
    try {
      await this.initBrowser(true);
      
      if (!this.page) {
        throw new Error('Failed to initialize browser');
      }
      
      // Navigate to store
      await this.page.goto(config.url, {
        waitUntil: 'networkidle',
        timeout: config.timeout || 60000,
      });
      
      // Wait for React app to hydrate
      await sleep(5000);
      
      // Scroll to trigger lazy loading
      await this.scrollToLoadAll();
      
      // Wait for additional requests
      await sleep(3000);
      
      // Deduplicate products
      const seen = new Set<string>();
      const uniqueProducts = this.products.filter((p) => {
        if (seen.has(p.id)) return false;
        seen.add(p.id);
        return true;
      });
      
      const scrapeTimeMs = Date.now() - startTime;
      
      return {
        success: true,
        products: uniqueProducts,
        fieldCompleteness: calculateFieldCompleteness(uniqueProducts),
        metadata: {
          scrapeTimeMs,
          pagesVisited: 1,
          requestsMade: this.graphqlRequests.length,
          method: this.name,
        },
      };
    } catch (error: any) {
      errors.push(error.message);
      
      return {
        success: false,
        products: this.products,
        fieldCompleteness: calculateFieldCompleteness(this.products),
        metadata: {
          scrapeTimeMs: Date.now() - startTime,
          pagesVisited: 0,
          requestsMade: this.graphqlRequests.length,
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
}
