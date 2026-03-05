/**
 * Conbud LES Scraper - Direct GraphQL API Method
 * Platform: Dutchie (React SPA)
 * API: https://api.dutchie.com
 * Complexity: High (requires extracted queries)
 * 
 * This scraper directly calls the Dutchie GraphQL API.
 * Prerequisites:
 * 1. Extract GraphQL queries from network-intercept scraper
 * 2. Identify required variables and authentication
 * 3. Handle rate limiting and CAPTCHA tokens
 * 
 * Advantages:
 * - Much faster than browser automation
 * - Lower resource usage
 * - Easier to deploy at scale
 * 
 * Disadvantages:
 * - Requires reverse engineering
 * - May break if API changes
 * - May require CAPTCHA tokens
 */

const axios = require('axios');
const fs = require('fs');

// Conbud LES identifiers
const CONBUD_CONFIG = {
  apiUrl: 'https://api.dutchie.com/graphql',
  dispensaryId: '6430f42042cf3c004e37f0f8',
  chainId: 'conbud',
  retailerId: '7d9a369e-6b29-4ccb-84c8-e802e28ae23e',
  storeUrl: 'https://conbud.com/stores/conbud-les'
};

/**
 * Example GraphQL queries
 * These are templates - actual queries need to be extracted from network traffic
 */
const QUERIES = {
  // Query to get menu/products
  // This is a SAMPLE - you must extract the real query from network intercept
  GET_MENU: `
    query FilteredProducts(
      $dispensaryId: ID!
      $filters: FilterInput
      $offset: Int
      $limit: Int
    ) {
      filteredProducts(
        dispensaryId: $dispensaryId
        filters: $filters
        offset: $offset
        limit: $limit
      ) {
        products {
          id
          name
          brand {
            name
            id
          }
          category
          subcategory
          price
          variants {
            id
            option
            price
            inStock
          }
          potencyThc {
            formatted
            range
          }
          potencyCbd {
            formatted
            range
          }
          image
          images
          strainType
          description
          effects
          inStock
          quantity
        }
        totalCount
      }
    }
  `,

  // Alternative query structure (also a sample)
  GET_PRODUCTS: `
    query GetProducts($dispensaryId: ID!) {
      menu(dispensaryId: $dispensaryId) {
        id
        products {
          id
          name
          brandName
          category
          Price
          THCContent {
            unit
            range
          }
          CBDContent {
            unit
            range
          }
          image
          POSMetaData {
            quantity
          }
        }
      }
    }
  `
};

class ConbudDirectAPIScraper {
  constructor() {
    this.products = [];
    this.client = axios.create({
      baseURL: CONBUD_CONFIG.apiUrl,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://conbud.com',
        'Referer': CONBUD_CONFIG.storeUrl
      }
    });
  }

  /**
   * Make GraphQL query
   */
  async query(query, variables) {
    try {
      const response = await this.client.post('', {
        query,
        variables
      });

      if (response.data.errors) {
        console.error('❌ GraphQL errors:', response.data.errors);
        return null;
      }

      return response.data.data;
    } catch (error) {
      console.error('❌ Request failed:', error.message);
      
      if (error.response) {
        console.error('  Status:', error.response.status);
        console.error('  Data:', error.response.data);
      }
      
      throw error;
    }
  }

  /**
   * Fetch products using the menu query
   */
  async fetchProducts() {
    console.log('📡 Fetching products from Dutchie API...');

    // Try first query structure
    try {
      const data = await this.query(QUERIES.GET_MENU, {
        dispensaryId: CONBUD_CONFIG.dispensaryId,
        filters: null,
        offset: 0,
        limit: 1000
      });

      if (data?.filteredProducts?.products) {
        const products = data.filteredProducts.products;
        console.log(`✅ Found ${products.length} products (query 1)`);
        return products;
      }
    } catch (e) {
      console.warn('⚠️  First query structure failed, trying alternative...');
    }

    // Try second query structure
    try {
      const data = await this.query(QUERIES.GET_PRODUCTS, {
        dispensaryId: CONBUD_CONFIG.dispensaryId
      });

      if (data?.menu?.products) {
        const products = data.menu.products;
        console.log(`✅ Found ${products.length} products (query 2)`);
        return products;
      }
    } catch (e) {
      console.error('❌ Both query structures failed');
      console.error('You need to extract the real GraphQL query from network traffic!');
      throw new Error('GraphQL queries need to be updated from actual API');
    }

    return [];
  }

  /**
   * Fetch products by category
   */
  async fetchByCategory(category) {
    console.log(`📂 Fetching ${category} products...`);

    const data = await this.query(QUERIES.GET_MENU, {
      dispensaryId: CONBUD_CONFIG.dispensaryId,
      filters: {
        category: [category]
      },
      offset: 0,
      limit: 1000
    });

    return data?.filteredProducts?.products || [];
  }

  /**
   * Normalize product data
   */
  normalizeProduct(product) {
    return {
      id: product.id,
      name: product.name,
      brand: product.brand?.name || product.brandName,
      category: product.category,
      subcategory: product.subcategory,
      
      price: product.price || product.Price,
      variants: product.variants || [],
      
      thc: product.potencyThc?.formatted || product.THCContent?.range,
      cbd: product.potencyCbd?.formatted || product.CBDContent?.range,
      
      image: product.image,
      images: product.images || [],
      
      strainType: product.strainType,
      description: product.description,
      effects: product.effects || [],
      
      inStock: product.inStock !== false,
      quantity: product.quantity || product.POSMetaData?.quantity,
      
      scrapedAt: new Date().toISOString(),
      source: 'conbud-les-api',
      sourceUrl: CONBUD_CONFIG.storeUrl
    };
  }

  /**
   * Main scraping workflow
   */
  async scrape() {
    try {
      // Fetch all products
      const rawProducts = await this.fetchProducts();
      
      // Normalize
      this.products = rawProducts.map(p => this.normalizeProduct(p));

      // Save
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `conbud-products-direct-${timestamp}.json`;
      
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

/**
 * Helper: Extract GraphQL queries from network-intercept output
 */
function extractQueriesFromLog(logFile) {
  console.log('🔍 Extracting GraphQL queries from log...');
  
  const data = JSON.parse(fs.readFileSync(logFile, 'utf8'));
  
  // Group by operation name
  const queries = {};
  
  data.forEach(request => {
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

  // Output as reusable module
  const output = `/**
 * Extracted GraphQL queries from Conbud network traffic
 * Generated: ${new Date().toISOString()}
 */

module.exports = ${JSON.stringify(queries, null, 2)};
`;

  fs.writeFileSync('conbud-extracted-queries.js', output);
  console.log('✅ Queries saved to conbud-extracted-queries.js');
  
  return queries;
}

// Export
module.exports = {
  ConbudDirectAPIScraper,
  extractQueriesFromLog
};

// Run if executed directly
if (require.main === module) {
  const scraper = new ConbudDirectAPIScraper();
  
  scraper.scrape()
    .then(stats => {
      console.log('\n✅ SUCCESS!');
      console.log(`📊 Scraped ${stats.productCount} products`);
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ FAILED:', error.message);
      console.error('\n💡 TIP: Run the network-intercept scraper first to extract queries!');
      process.exit(1);
    });
}
