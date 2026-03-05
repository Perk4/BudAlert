/**
 * Housing Works Cannabis Co. - Direct API Scraper
 * Platform: Blaze
 * 
 * This scraper calls the Blaze API directly after discovering endpoints
 * from the browser-based scraper's network logs.
 * 
 * Prerequisites:
 * 1. Run scraper-playwright.js first to capture API endpoints
 * 2. Extract API URLs and request formats from logs
 * 3. Update this script with actual API details
 * 
 * Advantages:
 * - Much faster than browser automation
 * - Lower resource usage
 * - Can run in serverless environments
 * 
 * Disadvantages:
 * - Requires initial API discovery
 * - May need authentication tokens
 * - Can break if API changes
 */

const axios = require('axios');
const fs = require('fs');

const HOUSING_WORKS_CONFIG = {
  storeName: 'housing_works_broadway',
  baseUrl: 'https://hwcannabis.co',
  // These would be discovered from network logs:
  // Example API endpoints (MUST BE UPDATED from actual site):
  apiBaseUrl: 'https://api.blaze.me', // Placeholder
  storeId: 'housing-works-broadway', // Placeholder
  locationId: 'broadway' // Placeholder
};

class HousingWorksDirectAPIScraper {
  constructor() {
    this.products = [];
    this.client = axios.create({
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept': 'application/json',
        'Origin': HOUSING_WORKS_CONFIG.baseUrl,
        'Referer': `${HOUSING_WORKS_CONFIG.baseUrl}/menu/broadway/`
      }
    });
  }

  /**
   * Discover API endpoints from network logs
   * This should be run after scraper-playwright.js to extract actual endpoints
   */
  static discoverEndpoints(logFile) {
    console.log('🔍 Discovering API endpoints from network logs...');
    
    const data = JSON.parse(fs.readFileSync(logFile, 'utf8'));
    
    const endpoints = {
      products: [],
      menu: [],
      inventory: [],
      other: []
    };

    data.forEach(request => {
      const url = request.url;
      
      if (url.includes('product')) {
        endpoints.products.push({
          url,
          method: request.method,
          data: request.postData
        });
      } else if (url.includes('menu')) {
        endpoints.menu.push({
          url,
          method: request.method,
          data: request.postData
        });
      } else if (url.includes('inventory')) {
        endpoints.inventory.push({
          url,
          method: request.method,
          data: request.postData
        });
      } else {
        endpoints.other.push({
          url,
          method: request.method
        });
      }
    });

    // Save endpoint analysis
    fs.writeFileSync(
      'housing-works-api-endpoints.json',
      JSON.stringify(endpoints, null, 2)
    );

    console.log('✅ Endpoints saved to housing-works-api-endpoints.json');
    console.log(`📊 Found:`);
    console.log(`  Product endpoints: ${endpoints.products.length}`);
    console.log(`  Menu endpoints: ${endpoints.menu.length}`);
    console.log(`  Inventory endpoints: ${endpoints.inventory.length}`);
    console.log(`  Other endpoints: ${endpoints.other.length}`);
    
    return endpoints;
  }

  /**
   * Fetch products from API
   * This is a TEMPLATE - actual implementation depends on discovered API
   */
  async fetchProducts() {
    console.log('📡 Fetching products from Blaze API...');

    try {
      // Example request structure (MUST BE UPDATED):
      const response = await this.client.get(
        `${HOUSING_WORKS_CONFIG.apiBaseUrl}/stores/${HOUSING_WORKS_CONFIG.storeId}/products`,
        {
          params: {
            location: HOUSING_WORKS_CONFIG.locationId,
            limit: 1000,
            includeInventory: true
          }
        }
      );

      const products = response.data?.products || response.data?.data || [];
      console.log(`✅ Fetched ${products.length} products from API`);
      
      return products;
    } catch (error) {
      console.error('❌ API request failed:', error.message);
      console.error('You need to update API endpoints from network logs!');
      throw error;
    }
  }

  /**
   * Fetch products by category
   */
  async fetchByCategory(category) {
    console.log(`📂 Fetching ${category} products...`);

    try {
      const response = await this.client.get(
        `${HOUSING_WORKS_CONFIG.apiBaseUrl}/stores/${HOUSING_WORKS_CONFIG.storeId}/products`,
        {
          params: {
            location: HOUSING_WORKS_CONFIG.locationId,
            category: category,
            limit: 1000
          }
        }
      );

      return response.data?.products || [];
    } catch (error) {
      console.error(`Failed to fetch ${category}:`, error.message);
      return [];
    }
  }

  /**
   * Normalize product from API response
   */
  normalizeProduct(product) {
    return {
      id: product.id || product.productId,
      name: product.name || product.productName,
      brand: product.brand || product.brandName,
      category: product.category || product.productType,
      
      price: product.price || product.pricing?.price,
      pricePerUnit: product.pricePerUnit,
      
      thc: {
        formatted: product.thcContent || product.thc,
        value: product.thcPercent || this.extractNumber(product.thcContent)
      },
      cbd: {
        formatted: product.cbdContent || product.cbd,
        value: product.cbdPercent || this.extractNumber(product.cbdContent)
      },
      
      image: product.image || product.imageUrl || product.photos?.[0],
      images: product.images || product.photos || [],
      
      weight: product.weight || product.size,
      description: product.description,
      
      quantity: product.quantity || product.inventory?.quantity,
      inStock: product.inStock !== false && (product.quantity === undefined || product.quantity > 0),
      
      strainType: product.strainType || product.strain,
      effects: product.effects || [],
      
      scrapedAt: new Date().toISOString(),
      source: 'housing-works-api',
      sourceUrl: HOUSING_WORKS_CONFIG.baseUrl
    };
  }

  /**
   * Extract numeric value from string
   */
  extractNumber(str) {
    if (!str) return null;
    const match = str.toString().match(/(\d+\.?\d*)/);
    return match ? parseFloat(match[1]) : null;
  }

  /**
   * Main scraping workflow
   */
  async scrape() {
    try {
      // Fetch products
      const rawProducts = await this.fetchProducts();
      
      // Normalize
      this.products = rawProducts.map(p => this.normalizeProduct(p));

      // Save
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `housing-works-products-api-${timestamp}.json`;
      
      fs.writeFileSync(
        filename,
        JSON.stringify(this.products, null, 2)
      );

      console.log(`✅ Saved ${this.products.length} products to ${filename}`);
      
      return {
        productCount: this.products.length,
        filename
      };
    } catch (error) {
      console.error('❌ Scraping failed:', error);
      throw error;
    }
  }
}

// Export
module.exports = {
  HousingWorksDirectAPIScraper,
  discoverEndpoints: HousingWorksDirectAPIScraper.discoverEndpoints
};

// Run if executed directly
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args[0] === 'discover') {
    // Discover endpoints from network log
    const logFile = args[1] || 'housing-works-api-requests-*.json';
    HousingWorksDirectAPIScraper.discoverEndpoints(logFile);
  } else {
    // Run scraper
    const scraper = new HousingWorksDirectAPIScraper();
    
    scraper.scrape()
      .then(stats => {
        console.log('\n✅ SUCCESS!');
        console.log(`📊 Scraped ${stats.productCount} products`);
        process.exit(0);
      })
      .catch(error => {
        console.error('\n❌ FAILED:', error.message);
        console.error('\n💡 TIP: Run playwright scraper first to discover API endpoints!');
        console.error('  node scraper-playwright.js');
        console.error('  node scraper-api-direct.js discover housing-works-api-requests-*.json');
        process.exit(1);
      });
  }
}
