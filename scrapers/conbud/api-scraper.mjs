/**
 * Conbud LES API Scraper - Direct GraphQL Approach
 * 
 * This scraper directly calls the Dutchie GraphQL API without browser automation.
 * 
 * Advantages:
 * - Fast (no browser overhead)
 * - Low resource usage
 * - Easy to deploy
 * - Scalable
 * 
 * Disadvantages:
 * - Requires extracted GraphQL queries (run browser-scraper.mjs first)
 * - May break if API changes
 * - May require CAPTCHA tokens in production
 * 
 * Prerequisites:
 * 1. Extract real queries using browser-scraper.mjs
 * 2. Update queries.mjs with actual query structures
 * 3. Test with live API
 */

import axios from 'axios';
import { writeFile } from 'fs/promises';
import {
  CONBUD_CONFIG,
  FILTERED_PRODUCTS_QUERY,
  MENU_PRODUCTS_QUERY,
  getFilteredProductsVariables,
  buildFilters,
  normalizeProduct,
  COMMON_CATEGORIES
} from './queries.mjs';

export class ConbudAPIScraper {
  constructor(options = {}) {
    this.options = {
      timeout: 30000,
      retries: 3,
      retryDelay: 2000,
      ...options
    };
    
    this.products = [];
    this.errors = [];
    
    // Create axios client
    this.client = axios.create({
      baseURL: CONBUD_CONFIG.apiUrl,
      timeout: this.options.timeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://conbud.com',
        'Referer': CONBUD_CONFIG.storeUrl,
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site'
      }
    });
  }

  /**
   * Make GraphQL query with retry logic
   */
  async query(query, variables, retryCount = 0) {
    try {
      console.log(`📡 GraphQL Request (attempt ${retryCount + 1}/${this.options.retries + 1})...`);
      
      const response = await this.client.post('', {
        query,
        variables,
        operationName: this.extractOperationName(query)
      });

      // Check for GraphQL errors
      if (response.data.errors) {
        console.error('❌ GraphQL errors:', response.data.errors);
        throw new Error(`GraphQL error: ${response.data.errors[0]?.message}`);
      }

      return response.data.data;
      
    } catch (error) {
      console.error(`❌ Request failed: ${error.message}`);
      
      if (error.response) {
        console.error(`  Status: ${error.response.status}`);
        console.error(`  Data:`, error.response.data);
      }
      
      // Retry on network errors
      if (retryCount < this.options.retries) {
        console.log(`⏳ Retrying in ${this.options.retryDelay}ms...`);
        await this.sleep(this.options.retryDelay);
        return this.query(query, variables, retryCount + 1);
      }
      
      throw error;
    }
  }

  /**
   * Extract operation name from query string
   */
  extractOperationName(query) {
    const match = query.match(/query\s+(\w+)/);
    return match ? match[1] : null;
  }

  /**
   * Fetch all products using filteredProducts query
   */
  async fetchAllProducts() {
    console.log('📦 Fetching all products...');
    
    const variables = getFilteredProductsVariables({
      limit: 1000,
      offset: 0
    });
    
    try {
      const data = await this.query(FILTERED_PRODUCTS_QUERY, variables);
      
      if (data?.filteredProducts?.products) {
        const products = data.filteredProducts.products;
        console.log(`✅ Found ${products.length} products`);
        return products;
      }
      
      console.warn('⚠️  No products found in response');
      return [];
      
    } catch (error) {
      this.errors.push({
        type: 'fetch_all',
        error: error.message,
        timestamp: new Date().toISOString()
      });
      
      // Try alternative query structure
      return this.fetchAllProductsAlternative();
    }
  }

  /**
   * Fallback: Try alternative menu query structure
   */
  async fetchAllProductsAlternative() {
    console.log('🔄 Trying alternative query structure...');
    
    try {
      const data = await this.query(MENU_PRODUCTS_QUERY, {
        dispensaryId: CONBUD_CONFIG.dispensaryId
      });
      
      if (data?.menu?.products) {
        const products = data.menu.products;
        console.log(`✅ Found ${products.length} products (alternative query)`);
        return products;
      }
      
      console.error('❌ Both query structures failed');
      console.error('💡 You need to extract real queries using browser-scraper.mjs first!');
      return [];
      
    } catch (error) {
      this.errors.push({
        type: 'fetch_alternative',
        error: error.message,
        timestamp: new Date().toISOString()
      });
      throw new Error('All query methods failed. Run browser-scraper.mjs to extract queries.');
    }
  }

  /**
   * Fetch products by category
   */
  async fetchByCategory(category) {
    console.log(`📂 Fetching ${category} products...`);
    
    const filters = buildFilters({ category });
    const variables = getFilteredProductsVariables({ filters });
    
    try {
      const data = await this.query(FILTERED_PRODUCTS_QUERY, variables);
      
      if (data?.filteredProducts?.products) {
        const products = data.filteredProducts.products;
        console.log(`  ✅ ${products.length} products`);
        return products;
      }
      
      return [];
      
    } catch (error) {
      console.error(`  ❌ Failed: ${error.message}`);
      this.errors.push({
        type: 'fetch_category',
        category,
        error: error.message,
        timestamp: new Date().toISOString()
      });
      return [];
    }
  }

  /**
   * Fetch products for all categories
   */
  async fetchAllCategories() {
    console.log('📚 Fetching all categories...');
    
    const allProducts = [];
    
    for (const category of COMMON_CATEGORIES) {
      const products = await this.fetchByCategory(category);
      allProducts.push(...products);
      
      // Rate limiting
      await this.sleep(1000);
    }
    
    console.log(`✅ Total products from categories: ${allProducts.length}`);
    return allProducts;
  }

  /**
   * Normalize and deduplicate products
   */
  processProducts(rawProducts) {
    console.log('🔄 Processing products...');
    
    const normalized = rawProducts
      .map(p => normalizeProduct(p, 'conbud-les-api'))
      .filter(p => p !== null);
    
    // Deduplicate by ID
    const seen = new Set();
    const unique = normalized.filter(p => {
      if (seen.has(p.id)) return false;
      seen.add(p.id);
      return true;
    });
    
    console.log(`✅ ${unique.length} unique products (${normalized.length - unique.length} duplicates removed)`);
    
    return unique;
  }

  /**
   * Save scraped data
   */
  async saveData(products) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `conbud-products-api-${timestamp}.json`;
    
    console.log(`💾 Saving to ${filename}...`);
    
    const data = {
      metadata: {
        source: 'conbud-les-api',
        scrapedAt: new Date().toISOString(),
        productCount: products.length,
        errorCount: this.errors.length,
        config: CONBUD_CONFIG
      },
      products,
      errors: this.errors
    };
    
    await writeFile(filename, JSON.stringify(data, null, 2));
    console.log('✅ Saved successfully');
    
    return filename;
  }

  /**
   * Sleep helper
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Main scraping workflow
   */
  async scrape() {
    const startTime = Date.now();
    
    try {
      console.log('🚀 Starting Conbud API scraper...\n');
      
      // Fetch products
      const rawProducts = await this.fetchAllProducts();
      
      // Process and normalize
      this.products = this.processProducts(rawProducts);
      
      // Save
      const filename = await this.saveData(this.products);
      
      const duration = ((Date.now() - startTime) / 1000).toFixed(2);
      
      console.log('\n📊 Scraping Summary:');
      console.log(`  Products: ${this.products.length}`);
      console.log(`  Errors: ${this.errors.length}`);
      console.log(`  Duration: ${duration}s`);
      console.log(`  File: ${filename}`);
      
      return {
        success: true,
        productCount: this.products.length,
        errorCount: this.errors.length,
        duration,
        filename
      };
      
    } catch (error) {
      console.error('\n❌ Scraping failed:', error.message);
      
      return {
        success: false,
        error: error.message,
        productCount: this.products.length,
        errorCount: this.errors.length
      };
    }
  }
}

/**
 * CLI runner
 */
export async function main() {
  const scraper = new ConbudAPIScraper({
    timeout: 30000,
    retries: 3
  });
  
  const result = await scraper.scrape();
  
  if (result.success) {
    console.log('\n✅ SUCCESS!');
    process.exit(0);
  } else {
    console.error('\n❌ FAILED!');
    console.error('💡 TIP: Run browser-scraper.mjs first to extract GraphQL queries');
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
