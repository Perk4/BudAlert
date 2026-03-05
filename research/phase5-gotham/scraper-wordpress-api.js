/**
 * Gotham NYC Scraper - WordPress REST API Method
 * URL: https://gotham.nyc
 * Platform: WordPress + Dovetail/WooCommerce
 * Complexity: Low
 * 
 * WordPress sites often expose REST API endpoints:
 * - /wp-json/wp/v2/posts
 * - /wp-json/wp/v2/products (if WooCommerce)
 * - /wp-json/wc/v3/products (WooCommerce API)
 * - Custom Dovetail endpoints
 * 
 * This scraper:
 * 1. Discovers available WordPress/WooCommerce API endpoints
 * 2. Fetches products via REST API
 * 3. Falls back to other endpoints if primary fails
 * 
 * Advantages:
 * - Official API (stable and supported)
 * - Clean JSON data
 * - Fast and efficient
 * - No HTML parsing needed
 * 
 * Disadvantages:
 * - May require authentication
 * - Not all WordPress sites expose product APIs
 * - Pagination may be required
 */

const axios = require('axios');
const fs = require('fs');

const GOTHAM_CONFIG = {
  baseUrl: 'https://gotham.nyc',
  apiBase: 'https://gotham.nyc/wp-json',
  storeName: 'gotham_nyc'
};

class GothamWordPressAPIScraper {
  constructor() {
    this.products = [];
    this.client = axios.create({
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept': 'application/json'
      },
      timeout: 30000
    });
    
    this.discoveredEndpoints = [];
  }

  /**
   * Discover available WordPress API endpoints
   */
  async discoverEndpoints() {
    console.log('🔍 Discovering WordPress API endpoints...');

    const endpointsToTry = [
      // WordPress default
      '/wp-json',
      '/wp-json/wp/v2',
      
      // WooCommerce
      '/wp-json/wc/v3/products',
      '/wp-json/wc/v2/products',
      '/wp-json/wc/store/products',
      
      // Custom product endpoints
      '/wp-json/wp/v2/products',
      '/wp-json/wp/v2/product',
      '/wp-json/products',
      
      // Dovetail (if custom)
      '/wp-json/dovetail/v1/products',
      '/wp-json/dt/v1/products',
      
      // Other common patterns
      '/api/products',
      '/rest/products'
    ];

    for (const endpoint of endpointsToTry) {
      try {
        const url = `${GOTHAM_CONFIG.baseUrl}${endpoint}`;
        const response = await this.client.get(url, {
          validateStatus: status => status < 500 // Accept 404, just not 5xx
        });

        if (response.status === 200 && response.data) {
          console.log(`  ✅ Found working endpoint: ${endpoint}`);
          this.discoveredEndpoints.push({
            url,
            endpoint,
            dataType: this.detectDataType(response.data)
          });
        }
      } catch (e) {
        // Endpoint doesn't exist or requires auth
      }
    }

    console.log(`✅ Discovered ${this.discoveredEndpoints.length} working endpoints`);
    return this.discoveredEndpoints;
  }

  /**
   * Detect what type of data an endpoint returns
   */
  detectDataType(data) {
    if (Array.isArray(data) && data.length > 0) {
      if (data[0].name || data[0].title) return 'product_list';
      if (data[0].routes) return 'api_index';
    }

    if (data.routes) return 'api_index';
    if (data.products) return 'product_wrapper';
    
    return 'unknown';
  }

  /**
   * Fetch products from WooCommerce API
   */
  async fetchWooCommerceProducts() {
    console.log('📡 Fetching from WooCommerce API...');

    const endpoints = [
      '/wp-json/wc/store/products',
      '/wp-json/wc/v3/products',
      '/wp-json/wc/v2/products'
    ];

    for (const endpoint of endpoints) {
      try {
        const products = [];
        let page = 1;
        let hasMore = true;

        while (hasMore && page <= 10) { // Max 10 pages
          const url = `${GOTHAM_CONFIG.baseUrl}${endpoint}`;
          const response = await this.client.get(url, {
            params: {
              per_page: 100,
              page: page
            }
          });

          if (response.data && Array.isArray(response.data)) {
            products.push(...response.data);
            console.log(`  → Fetched page ${page}: ${response.data.length} products`);
            
            // Check if there's another page
            hasMore = response.data.length === 100;
            page++;
          } else {
            hasMore = false;
          }
        }

        if (products.length > 0) {
          console.log(`✅ Found ${products.length} products via WooCommerce`);
          return products.map(p => this.normalizeWooCommerceProduct(p));
        }
      } catch (e) {
        // Try next endpoint
      }
    }

    return [];
  }

  /**
   * Fetch products from WordPress custom post type
   */
  async fetchWordPressProducts() {
    console.log('📡 Fetching from WordPress custom post type...');

    const endpoints = [
      '/wp-json/wp/v2/products',
      '/wp-json/wp/v2/product'
    ];

    for (const endpoint of endpoints) {
      try {
        const products = [];
        let page = 1;
        let hasMore = true;

        while (hasMore && page <= 10) {
          const url = `${GOTHAM_CONFIG.baseUrl}${endpoint}`;
          const response = await this.client.get(url, {
            params: {
              per_page: 100,
              page: page
            }
          });

          if (response.data && Array.isArray(response.data)) {
            products.push(...response.data);
            console.log(`  → Fetched page ${page}: ${response.data.length} products`);
            
            hasMore = response.data.length === 100;
            page++;
          } else {
            hasMore = false;
          }
        }

        if (products.length > 0) {
          console.log(`✅ Found ${products.length} products via WordPress`);
          return products.map(p => this.normalizeWordPressProduct(p));
        }
      } catch (e) {
        // Try next endpoint
      }
    }

    return [];
  }

  /**
   * Normalize WooCommerce product
   */
  normalizeWooCommerceProduct(product) {
    return {
      id: product.id,
      name: product.name,
      slug: product.slug,
      
      brand: product.brands?.[0]?.name || this.extractBrand(product.name),
      category: product.categories?.[0]?.name || 'Unknown',
      
      price: parseFloat(product.price || product.regular_price),
      priceFormatted: product.price_html,
      
      image: product.images?.[0]?.src || product.image?.src,
      images: product.images?.map(img => img.src) || [],
      
      description: product.description || product.short_description,
      url: product.permalink,
      
      sku: product.sku,
      inStock: product.stock_status === 'instock',
      quantity: product.stock_quantity,
      
      // Extract potency from description/meta
      ...this.extractPotencyFromText(product.description + ' ' + product.short_description),
      
      // Metadata
      scrapedAt: new Date().toISOString(),
      source: 'gotham-woocommerce-api',
      sourceUrl: GOTHAM_CONFIG.baseUrl
    };
  }

  /**
   * Normalize WordPress custom post product
   */
  normalizeWordPressProduct(product) {
    return {
      id: product.id,
      name: product.title?.rendered || product.title,
      slug: product.slug,
      
      brand: product.acf?.brand || this.extractBrand(product.title?.rendered),
      category: this.extractCategory(product.title?.rendered),
      
      price: product.acf?.price || null,
      
      image: product.featured_media_url || product.acf?.image,
      
      description: product.content?.rendered || product.excerpt?.rendered,
      url: product.link,
      
      inStock: product.acf?.in_stock !== false,
      
      thc: product.acf?.thc_content ? {
        formatted: product.acf.thc_content,
        value: parseFloat(product.acf.thc_content)
      } : null,
      cbd: product.acf?.cbd_content ? {
        formatted: product.acf.cbd_content,
        value: parseFloat(product.acf.cbd_content)
      } : null,
      
      scrapedAt: new Date().toISOString(),
      source: 'gotham-wordpress-api',
      sourceUrl: GOTHAM_CONFIG.baseUrl
    };
  }

  /**
   * Extract potency from text
   */
  extractPotencyFromText(text) {
    if (!text) return {};
    
    const thcMatch = text.match(/THC[:\s]*([0-9.]+)%?/i);
    const cbdMatch = text.match(/CBD[:\s]*([0-9.]+)%?/i);

    return {
      thc: thcMatch ? {
        formatted: thcMatch[0],
        value: parseFloat(thcMatch[1])
      } : null,
      cbd: cbdMatch ? {
        formatted: cbdMatch[0],
        value: parseFloat(cbdMatch[1])
      } : null
    };
  }

  /**
   * Extract brand from product name
   */
  extractBrand(name) {
    if (!name) return null;
    
    // Common pattern: "Brand - Product Name"
    const dashMatch = name.match(/^([^-]+)-/);
    if (dashMatch) {
      return dashMatch[1].trim();
    }
    
    return null;
  }

  /**
   * Extract category from name
   */
  extractCategory(name) {
    if (!name) return 'Unknown';
    
    const nameLower = name.toLowerCase();
    
    if (nameLower.includes('flower')) return 'Flower';
    if (nameLower.includes('edible')) return 'Edibles';
    if (nameLower.includes('vape')) return 'Vapes';
    if (nameLower.includes('concentrate')) return 'Concentrates';
    if (nameLower.includes('pre-roll')) return 'Pre-Rolls';
    if (nameLower.includes('tincture')) return 'Tinctures';
    
    return 'Other';
  }

  /**
   * Main scraping workflow
   */
  async scrape() {
    try {
      // Discover endpoints
      await this.discoverEndpoints();

      // Try WooCommerce first (most common for dispensaries)
      let products = await this.fetchWooCommerceProducts();

      // Fallback to WordPress custom post types
      if (products.length === 0) {
        products = await this.fetchWordPressProducts();
      }

      // If still no products, API might not be available
      if (products.length === 0) {
        console.warn('⚠️  No products found via API');
        console.warn('💡 TIP: WordPress API might not be enabled for products');
        console.warn('   Try the curl scraper instead: scraper-curl.js');
      }

      this.products = products;

      // Save data
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `gotham-products-api-${timestamp}.json`;
      
      fs.writeFileSync(
        filename,
        JSON.stringify(this.products, null, 2)
      );

      // Save discovered endpoints for reference
      fs.writeFileSync(
        `gotham-api-endpoints-${timestamp}.json`,
        JSON.stringify(this.discoveredEndpoints, null, 2)
      );

      console.log(`\n✅ Saved ${this.products.length} products to ${filename}`);
      
      return {
        productCount: this.products.length,
        endpointCount: this.discoveredEndpoints.length,
        filename
      };
    } catch (error) {
      console.error('❌ Scraping failed:', error);
      throw error;
    }
  }
}

// Export
module.exports = GothamWordPressAPIScraper;

// Run if executed directly
if (require.main === module) {
  const scraper = new GothamWordPressAPIScraper();
  
  scraper.scrape()
    .then(stats => {
      console.log('\n✅ SUCCESS!');
      console.log(`📊 Scraped ${stats.productCount} products`);
      console.log(`🔍 Discovered ${stats.endpointCount} API endpoints`);
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ FAILED:', error.message);
      process.exit(1);
    });
}
