/**
 * Conbud LES Scraper - Browser + Network Intercept Method
 * Platform: Dutchie (React SPA)
 * URL: https://conbud.com/stores/conbud-les
 * Complexity: High
 * 
 * This scraper uses Playwright to:
 * 1. Launch a browser and navigate to the store
 * 2. Intercept GraphQL API requests to api.dutchie.com
 * 3. Extract product data from network responses
 * 4. Handle Turnstile CAPTCHA (manual bypass or wait)
 */

const { chromium } = require('playwright');
const fs = require('fs');

// Conbud LES identifiers (from Phase 1 recon)
const CONBUD_CONFIG = {
  storeUrl: 'https://conbud.com/stores/conbud-les',
  dispensaryId: '6430f42042cf3c004e37f0f8',
  chainId: 'conbud',
  retailerId: '7d9a369e-6b29-4ccb-84c8-e802e28ae23e',
  apiUrl: 'https://api.dutchie.com'
};

class ConbudScraper {
  constructor() {
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
      headless: false, // Set to true for production, false for debugging
      args: [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox'
      ]
    });

    const context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      // Add extra HTTP headers to appear more human
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
   * Captures all GraphQL queries and responses to api.dutchie.com
   */
  async setupNetworkIntercept() {
    console.log('📡 Setting up network interception...');

    // Intercept requests
    this.page.on('request', request => {
      const url = request.url();
      
      // Capture GraphQL requests to Dutchie API
      if (url.includes('api.dutchie.com') && request.method() === 'POST') {
        const postData = request.postData();
        
        try {
          const payload = JSON.parse(postData);
          this.graphqlRequests.push({
            url,
            timestamp: Date.now(),
            query: payload.query,
            variables: payload.variables,
            operationName: payload.operationName
          });
          
          console.log(`📤 GraphQL Request: ${payload.operationName || 'unnamed'}`);
        } catch (e) {
          // Not JSON, skip
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
          
          // Extract products if this response contains them
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
    // Dutchie typically returns products in data.menu.products or similar
    // The exact path depends on the query structure
    
    // Check common paths
    const possiblePaths = [
      json?.data?.menu?.products,
      json?.data?.filteredProducts?.products,
      json?.data?.products,
      json?.data?.dispensaryProducts
    ];

    for (const products of possiblePaths) {
      if (Array.isArray(products) && products.length > 0) {
        console.log(`✨ Found ${products.length} products in response`);
        
        products.forEach(product => {
          // Normalize product data
          const normalized = this.normalizeProduct(product);
          if (normalized) {
            this.products.push(normalized);
          }
        });
        
        break;
      }
    }
  }

  /**
   * Normalize product data to standard format
   */
  normalizeProduct(product) {
    try {
      return {
        // Basic info
        id: product.id || product._id || product.productId,
        name: product.name || product.Name,
        brand: product.brand?.name || product.brandName || product.brand,
        category: product.category || product.type,
        subcategory: product.subcategory || product.subtype,
        
        // Pricing
        price: product.price || product.variants?.[0]?.price,
        priceRange: {
          min: product.priceMin || product.price,
          max: product.priceMax || product.price
        },
        
        // Potency
        thc: product.potencyThc?.formatted || product.thc || null,
        thcPercent: product.potencyThc?.range?.[0] || null,
        cbd: product.potencyCbd?.formatted || product.cbd || null,
        cbdPercent: product.potencyCbd?.range?.[0] || null,
        
        // Media
        image: product.image || product.imageUrl || product.images?.[0],
        images: product.images || [],
        
        // Inventory
        inStock: product.inStock !== false, // Default true unless explicitly false
        inventoryCount: product.quantity || null,
        
        // Metadata
        strainType: product.strainType || product.strain,
        description: product.description,
        effects: product.effects || [],
        
        // Variants (for different weights/sizes)
        variants: product.variants?.map(v => ({
          id: v.id,
          option: v.option, // e.g., "1g", "3.5g", "7g"
          price: v.price,
          inStock: v.inStock
        })) || [],
        
        // Scrape metadata
        scrapedAt: new Date().toISOString(),
        source: 'conbud-les',
        sourceUrl: CONBUD_CONFIG.storeUrl
      };
    } catch (e) {
      console.error('❌ Failed to normalize product:', e.message);
      return null;
    }
  }

  /**
   * Navigate to store and wait for products to load
   */
  async navigateAndWait() {
    console.log(`🌐 Navigating to ${CONBUD_CONFIG.storeUrl}...`);
    
    await this.page.goto(CONBUD_CONFIG.storeUrl, {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    console.log('✅ Page loaded');

    // Wait for React app to hydrate and make API calls
    console.log('⏳ Waiting for GraphQL requests...');
    await this.page.waitForTimeout(5000);

    // Check if CAPTCHA is present
    const hasCaptcha = await this.page.locator('iframe[src*="turnstile"]').count() > 0;
    if (hasCaptcha) {
      console.warn('⚠️  Turnstile CAPTCHA detected!');
      console.log('Please solve the CAPTCHA manually, or implement automated bypass.');
      console.log('Waiting 30 seconds for manual intervention...');
      await this.page.waitForTimeout(30000);
    }

    // Scroll to trigger lazy loading
    await this.scrollToLoadAll();
  }

  /**
   * Scroll through the page to trigger lazy loading
   */
  async scrollToLoadAll() {
    console.log('📜 Scrolling to load all products...');
    
    const scrollSteps = 5;
    for (let i = 0; i < scrollSteps; i++) {
      await this.page.evaluate(() => {
        window.scrollBy(0, window.innerHeight);
      });
      await this.page.waitForTimeout(1000);
    }

    // Scroll back to top
    await this.page.evaluate(() => window.scrollTo(0, 0));
    
    console.log('✅ Scrolling complete');
  }

  /**
   * Try to navigate through categories if available
   */
  async navigateCategories() {
    console.log('📂 Attempting to navigate categories...');
    
    // Look for category buttons/links
    const categorySelectors = [
      'button:has-text("Flower")',
      'button:has-text("Vapes")',
      'button:has-text("Edibles")',
      'button:has-text("Concentrates")',
      'button:has-text("Pre-Rolls")',
      'a[href*="category"]'
    ];

    for (const selector of categorySelectors) {
      try {
        const elements = await this.page.locator(selector).all();
        
        for (const element of elements) {
          const text = await element.textContent();
          console.log(`  → Clicking category: ${text}`);
          
          await element.click();
          await this.page.waitForTimeout(2000); // Wait for new products to load
          await this.scrollToLoadAll();
        }
      } catch (e) {
        // Category not found or not clickable
      }
    }
    
    console.log('✅ Category navigation complete');
  }

  /**
   * Save collected data to files
   */
  async saveData() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    // Deduplicate products by ID
    const uniqueProducts = Array.from(
      new Map(this.products.map(p => [p.id, p])).values()
    );

    console.log(`💾 Saving ${uniqueProducts.length} unique products...`);

    // Save products
    fs.writeFileSync(
      `conbud-products-${timestamp}.json`,
      JSON.stringify(uniqueProducts, null, 2)
    );

    // Save raw GraphQL data for analysis
    fs.writeFileSync(
      `conbud-graphql-requests-${timestamp}.json`,
      JSON.stringify(this.graphqlRequests, null, 2)
    );

    fs.writeFileSync(
      `conbud-graphql-responses-${timestamp}.json`,
      JSON.stringify(this.graphqlResponses, null, 2)
    );

    console.log('✅ Data saved successfully');
    
    return {
      productCount: uniqueProducts.length,
      requestCount: this.graphqlRequests.length,
      responseCount: this.graphqlResponses.length
    };
  }

  /**
   * Main scraping workflow
   */
  async scrape() {
    try {
      await this.init();
      await this.navigateAndWait();
      await this.navigateCategories();
      
      const stats = await this.saveData();
      
      console.log('\n📊 Scraping Summary:');
      console.log(`  Products: ${stats.productCount}`);
      console.log(`  GraphQL Requests: ${stats.requestCount}`);
      console.log(`  GraphQL Responses: ${stats.responseCount}`);
      
      return stats;
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

// Export for use in other scripts
module.exports = ConbudScraper;

// Run if executed directly
if (require.main === module) {
  const scraper = new ConbudScraper();
  scraper.scrape()
    .then(stats => {
      console.log('\n✅ SUCCESS!');
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ FAILED:', error.message);
      process.exit(1);
    });
}
