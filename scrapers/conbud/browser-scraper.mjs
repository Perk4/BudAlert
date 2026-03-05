/**
 * Conbud LES Browser Scraper - Network Intercept Approach
 * 
 * This scraper uses Playwright to:
 * 1. Launch a browser and navigate to the store
 * 2. Intercept GraphQL API requests to api.dutchie.com
 * 3. Extract product data from network responses
 * 4. Capture actual GraphQL queries for api-scraper.mjs
 * 
 * Advantages:
 * - Most reliable (executes real JavaScript)
 * - Captures all API calls automatically
 * - No need to reverse-engineer queries upfront
 * - Handles dynamic content and lazy loading
 * 
 * Disadvantages:
 * - Slower than direct API
 * - Higher resource usage (requires Chromium)
 * - CAPTCHA may require manual intervention
 * - May not work in restricted sandbox environments
 * 
 * Use this scraper to:
 * 1. Extract the actual GraphQL queries used by the site
 * 2. Validate product data structure
 * 3. Debug when direct API fails
 */

import { chromium } from 'playwright';
import { writeFile } from 'fs/promises';
import {
  CONBUD_CONFIG,
  normalizeProduct,
  extractQueryInfo
} from './queries.mjs';

export class ConbudBrowserScraper {
  constructor(options = {}) {
    this.options = {
      headless: true,
      timeout: 60000,
      captchaWaitTime: 30000,
      scrollSteps: 5,
      scrollDelay: 1000,
      ...options
    };
    
    this.browser = null;
    this.page = null;
    this.products = [];
    this.graphqlRequests = [];
    this.graphqlResponses = [];
  }

  /**
   * Initialize browser with stealth settings
   */
  async init() {
    console.log('🚀 Launching browser...');
    
    this.browser = await chromium.launch({
      headless: this.options.headless,
      args: [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-setuid-sandbox'
      ]
    });

    const context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      extraHTTPHeaders: {
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
      }
    });

    this.page = await context.newPage();
    
    // Set up network interception
    await this.setupNetworkIntercept();
    
    console.log('✅ Browser initialized');
  }

  /**
   * Set up network request/response interception
   */
  async setupNetworkIntercept() {
    console.log('📡 Setting up network interception...');

    // Intercept requests
    this.page.on('request', request => {
      const url = request.url();
      
      // Capture GraphQL requests to Dutchie API
      if (url.includes('api.dutchie.com') && request.method() === 'POST') {
        const postData = request.postData();
        
        if (postData) {
          try {
            const payload = JSON.parse(postData);
            const queryInfo = {
              url,
              timestamp: Date.now(),
              query: payload.query,
              variables: payload.variables,
              operationName: payload.operationName
            };
            
            this.graphqlRequests.push(queryInfo);
            console.log(`📤 GraphQL Request: ${payload.operationName || 'unnamed'}`);
          } catch (e) {
            // Not JSON, skip
          }
        }
      }
    });

    // Intercept responses
    this.page.on('response', async response => {
      const url = response.url();
      
      // Capture GraphQL responses
      if (url.includes('api.dutchie.com') && response.status() === 200) {
        try {
          const json = await response.json();
          this.graphqlResponses.push({
            url,
            timestamp: Date.now(),
            data: json
          });
          
          console.log(`📥 GraphQL Response received`);
          
          // Extract products from this response
          this.extractProductsFromResponse(json);
        } catch (e) {
          // Not JSON or failed to parse
        }
      }
    });

    console.log('✅ Network interception ready');
  }

  /**
   * Extract product data from GraphQL response
   */
  extractProductsFromResponse(json) {
    // Dutchie returns products in various paths depending on query
    const possiblePaths = [
      json?.data?.menu?.products,
      json?.data?.filteredProducts?.products,
      json?.data?.products,
      json?.data?.dispensaryProducts,
      json?.data?.menu?.sections?.[0]?.products
    ];

    for (const products of possiblePaths) {
      if (Array.isArray(products) && products.length > 0) {
        console.log(`  ✨ Found ${products.length} products in response`);
        
        products.forEach(product => {
          const normalized = normalizeProduct(product, 'conbud-les-browser');
          if (normalized) {
            this.products.push(normalized);
          }
        });
        
        break;
      }
    }
  }

  /**
   * Navigate to store and wait for content to load
   */
  async navigateAndWait() {
    console.log(`🌐 Navigating to ${CONBUD_CONFIG.storeUrl}...`);
    
    await this.page.goto(CONBUD_CONFIG.storeUrl, {
      waitUntil: 'networkidle',
      timeout: this.options.timeout
    });

    console.log('✅ Page loaded');

    // Wait for React app to hydrate
    console.log('⏳ Waiting for app to initialize...');
    await this.page.waitForTimeout(5000);

    // Check for CAPTCHA
    await this.handleCaptcha();

    // Wait for initial GraphQL requests
    await this.page.waitForTimeout(3000);
  }

  /**
   * Handle Turnstile CAPTCHA if present
   */
  async handleCaptcha() {
    const captchaFrame = this.page.frameLocator('iframe[src*="turnstile"]');
    const hasCaptcha = await captchaFrame.locator('body').count() > 0;
    
    if (hasCaptcha) {
      console.warn('⚠️  Turnstile CAPTCHA detected!');
      
      if (this.options.headless) {
        console.log('💡 Run with headless=false to solve CAPTCHA manually');
        console.log(`⏳ Waiting ${this.options.captchaWaitTime}ms...`);
        await this.page.waitForTimeout(this.options.captchaWaitTime);
      } else {
        console.log('🖱️  Please solve the CAPTCHA in the browser window');
        console.log(`⏳ Waiting ${this.options.captchaWaitTime}ms for manual solve...`);
        await this.page.waitForTimeout(this.options.captchaWaitTime);
      }
    }
  }

  /**
   * Scroll through page to trigger lazy loading
   */
  async scrollToLoadAll() {
    console.log('📜 Scrolling to load all products...');
    
    for (let i = 0; i < this.options.scrollSteps; i++) {
      await this.page.evaluate(() => {
        window.scrollBy(0, window.innerHeight);
      });
      console.log(`  Scroll ${i + 1}/${this.options.scrollSteps}`);
      await this.page.waitForTimeout(this.options.scrollDelay);
    }

    // Scroll back to top
    await this.page.evaluate(() => window.scrollTo(0, 0));
    
    console.log('✅ Scrolling complete');
  }

  /**
   * Try to navigate categories to load all products
   */
  async navigateCategories() {
    console.log('📂 Attempting to navigate categories...');
    
    // Common category selectors for Dutchie sites
    const categorySelectors = [
      'button[data-testid*="category"]',
      'a[href*="category"]',
      '[role="tab"]',
      'button:has-text("Flower")',
      'button:has-text("Vapes")',
      'button:has-text("Edibles")',
      'button:has-text("Concentrates")',
      'button:has-text("Pre-Rolls")'
    ];

    for (const selector of categorySelectors) {
      try {
        const elements = await this.page.locator(selector).all();
        
        if (elements.length > 0) {
          console.log(`  Found ${elements.length} category elements with selector: ${selector}`);
          
          for (const element of elements) {
            try {
              const text = await element.textContent();
              console.log(`    → Clicking: ${text?.trim()}`);
              
              await element.click();
              await this.page.waitForTimeout(2000);
              await this.scrollToLoadAll();
            } catch (e) {
              // Element not clickable or navigation failed
            }
          }
          
          break; // Found and clicked categories, stop looking
        }
      } catch (e) {
        // Selector not found, try next
      }
    }
    
    console.log('✅ Category navigation complete');
  }

  /**
   * Deduplicate products by ID
   */
  deduplicateProducts() {
    const seen = new Set();
    const unique = this.products.filter(p => {
      if (seen.has(p.id)) return false;
      seen.add(p.id);
      return true;
    });
    
    console.log(`🔄 Deduplicated: ${this.products.length} → ${unique.length} products`);
    return unique;
  }

  /**
   * Save all collected data
   */
  async saveData() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    // Deduplicate products
    const uniqueProducts = this.deduplicateProducts();

    console.log(`💾 Saving ${uniqueProducts.length} products...`);

    // Save products
    const productsFile = `conbud-products-browser-${timestamp}.json`;
    await writeFile(
      productsFile,
      JSON.stringify({
        metadata: {
          source: 'conbud-les-browser',
          scrapedAt: new Date().toISOString(),
          productCount: uniqueProducts.length,
          config: CONBUD_CONFIG
        },
        products: uniqueProducts
      }, null, 2)
    );

    // Save GraphQL requests (for query extraction)
    const requestsFile = `conbud-graphql-requests-${timestamp}.json`;
    await writeFile(
      requestsFile,
      JSON.stringify(this.graphqlRequests, null, 2)
    );

    // Save GraphQL responses (for debugging)
    const responsesFile = `conbud-graphql-responses-${timestamp}.json`;
    await writeFile(
      responsesFile,
      JSON.stringify(this.graphqlResponses, null, 2)
    );

    console.log('✅ Data saved successfully');
    console.log(`  Products: ${productsFile}`);
    console.log(`  Requests: ${requestsFile}`);
    console.log(`  Responses: ${responsesFile}`);
    
    return {
      productCount: uniqueProducts.length,
      requestCount: this.graphqlRequests.length,
      responseCount: this.graphqlResponses.length,
      files: {
        products: productsFile,
        requests: requestsFile,
        responses: responsesFile
      }
    };
  }

  /**
   * Extract and save GraphQL queries for api-scraper
   */
  async extractQueries() {
    console.log('🔍 Extracting GraphQL queries...');
    
    // Group by operation name
    const queries = {};
    
    this.graphqlRequests.forEach(request => {
      const opName = request.operationName || 'unnamed';
      
      if (!queries[opName]) {
        queries[opName] = {
          query: request.query,
          variables: request.variables,
          count: 0
        };
      }
      
      queries[opName].count++;
    });

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `conbud-extracted-queries-${timestamp}.mjs`;
    
    const content = `/**
 * Extracted GraphQL Queries from Conbud Network Traffic
 * Generated: ${new Date().toISOString()}
 * 
 * Use these queries in api-scraper.mjs for direct API access
 */

export const EXTRACTED_QUERIES = ${JSON.stringify(queries, null, 2)};
`;

    await writeFile(filename, content);
    console.log(`✅ Queries extracted to ${filename}`);
    
    return queries;
  }

  /**
   * Main scraping workflow
   */
  async scrape() {
    const startTime = Date.now();
    
    try {
      console.log('🚀 Starting Conbud browser scraper...\n');
      
      await this.init();
      await this.navigateAndWait();
      await this.scrollToLoadAll();
      await this.navigateCategories();
      
      const stats = await this.saveData();
      await this.extractQueries();
      
      const duration = ((Date.now() - startTime) / 1000).toFixed(2);
      
      console.log('\n📊 Scraping Summary:');
      console.log(`  Products: ${stats.productCount}`);
      console.log(`  GraphQL Requests: ${stats.requestCount}`);
      console.log(`  GraphQL Responses: ${stats.responseCount}`);
      console.log(`  Duration: ${duration}s`);
      
      return {
        success: true,
        ...stats,
        duration
      };
      
    } catch (error) {
      console.error('❌ Scraping failed:', error);
      throw error;
    } finally {
      if (this.browser) {
        await this.browser.close();
        console.log('🔒 Browser closed');
      }
    }
  }
}

/**
 * CLI runner
 */
export async function main() {
  const scraper = new ConbudBrowserScraper({
    headless: process.env.HEADLESS !== 'false',
    timeout: 60000,
    captchaWaitTime: 30000
  });
  
  try {
    const result = await scraper.scrape();
    console.log('\n✅ SUCCESS!');
    process.exit(0);
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}
