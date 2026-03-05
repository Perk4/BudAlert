/**
 * GraphQL Queries for Conbud/Dutchie API
 * 
 * These are template queries based on Dutchie's GraphQL schema.
 * Actual queries should be extracted from network traffic using browser-scraper.mjs
 * 
 * API Endpoint: https://api.dutchie.com/graphql
 */

export const CONBUD_CONFIG = {
  storeUrl: 'https://conbud.com/stores/conbud-les',
  apiUrl: 'https://api.dutchie.com/graphql',
  dispensaryId: '6430f42042cf3c004e37f0f8',
  chainId: 'conbud',
  retailerId: '7d9a369e-6b29-4ccb-84c8-e802e28ae23e'
};

/**
 * Primary query structure for fetching products
 * This uses the filteredProducts query which is common in Dutchie's API
 */
export const FILTERED_PRODUCTS_QUERY = `
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
          description
          imageUrl
        }
        category
        subcategory
        price
        variants {
          id
          option
          price
          inStock
          quantity
        }
        potencyThc {
          formatted
          range
          unit
        }
        potencyCbd {
          formatted
          range
          unit
        }
        image
        images
        strainType
        description
        effects
        inStock
        quantity
        
        # Additional fields that may be available
        weight
        manualWeight
        staffPick
        featured
        special
        specialData {
          name
          description
          type
        }
        
        # Product metadata
        productType
        cannabinoidType
        
        # Menu metadata
        menuType
        
        # Timestamps
        createdAt
        updatedAt
      }
      totalCount
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }
    }
  }
`;

/**
 * Alternative query structure using menu endpoint
 */
export const MENU_PRODUCTS_QUERY = `
  query GetMenu($dispensaryId: ID!) {
    menu(dispensaryId: $dispensaryId) {
      id
      name
      products {
        id
        name
        brandName
        category
        subcategory
        Price
        THCContent {
          unit
          range
          formatted
        }
        CBDContent {
          unit
          range
          formatted
        }
        image
        images
        type
        strain
        effects
        POSMetaData {
          id
          quantity
          canonicalID
          canonicalEffectivePotency {
            formatted
          }
        }
      }
    }
  }
`;

/**
 * Query for specific product details
 */
export const PRODUCT_DETAIL_QUERY = `
  query GetProduct($productId: ID!, $dispensaryId: ID!) {
    product(id: $productId, dispensaryId: $dispensaryId) {
      id
      name
      brand {
        name
        id
        description
      }
      category
      subcategory
      description
      price
      variants {
        id
        option
        price
        inStock
        quantity
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
      effects
      inStock
      quantity
      weight
      
      # Reviews
      reviewCount
      reviewRating
      
      # Lab results
      labResults {
        thcPercent
        cbdPercent
        terpenes {
          name
          percentage
        }
      }
    }
  }
`;

/**
 * Query for categories/menu structure
 */
export const CATEGORIES_QUERY = `
  query GetCategories($dispensaryId: ID!) {
    menu(dispensaryId: $dispensaryId) {
      id
      categories {
        id
        name
        type
        subcategories
      }
    }
  }
`;

/**
 * Default variables for filteredProducts query
 */
export function getFilteredProductsVariables(options = {}) {
  return {
    dispensaryId: CONBUD_CONFIG.dispensaryId,
    filters: options.filters || null,
    offset: options.offset || 0,
    limit: options.limit || 1000
  };
}

/**
 * Filter builder helpers
 */
export function buildFilters(options = {}) {
  const filters = {};
  
  if (options.category) {
    filters.category = Array.isArray(options.category) 
      ? options.category 
      : [options.category];
  }
  
  if (options.subcategory) {
    filters.subcategory = Array.isArray(options.subcategory)
      ? options.subcategory
      : [options.subcategory];
  }
  
  if (options.strainType) {
    filters.strainType = Array.isArray(options.strainType)
      ? options.strainType
      : [options.strainType];
  }
  
  if (options.brand) {
    filters.brand = Array.isArray(options.brand)
      ? options.brand
      : [options.brand];
  }
  
  if (options.priceMin !== undefined || options.priceMax !== undefined) {
    filters.price = {
      min: options.priceMin,
      max: options.priceMax
    };
  }
  
  if (options.inStockOnly) {
    filters.inStock = true;
  }
  
  return Object.keys(filters).length > 0 ? filters : null;
}

/**
 * Common categories for iteration
 */
export const COMMON_CATEGORIES = [
  'Flower',
  'Vapes',
  'Edibles',
  'Concentrates',
  'Pre-Rolls',
  'Topicals',
  'Tinctures',
  'Accessories'
];

/**
 * Extract queries from captured network traffic
 * Used by browser-scraper to document actual queries
 */
export function extractQueryInfo(graphqlRequest) {
  return {
    operationName: graphqlRequest.operationName,
    query: graphqlRequest.query,
    variables: graphqlRequest.variables,
    timestamp: graphqlRequest.timestamp
  };
}

/**
 * Normalize product data from various query responses
 */
export function normalizeProduct(product, source = 'conbud-les') {
  try {
    return {
      // Basic info
      id: product.id || product._id || product.productId,
      name: product.name || product.Name,
      brand: product.brand?.name || product.brandName || product.brand,
      category: product.category || product.type,
      subcategory: product.subcategory || product.subtype,
      
      // Pricing
      price: product.price || product.Price || product.variants?.[0]?.price,
      priceRange: {
        min: product.priceMin || product.price || product.Price,
        max: product.priceMax || product.price || product.Price
      },
      
      // Potency
      thc: product.potencyThc?.formatted || product.THCContent?.formatted || product.thc || null,
      thcPercent: product.potencyThc?.range?.[0] || product.THCContent?.range?.[0] || null,
      cbd: product.potencyCbd?.formatted || product.CBDContent?.formatted || product.cbd || null,
      cbdPercent: product.potencyCbd?.range?.[0] || product.CBDContent?.range?.[0] || null,
      
      // Media
      image: product.image || product.imageUrl || product.images?.[0],
      images: product.images || [],
      
      // Inventory
      inStock: product.inStock !== false,
      inventoryCount: product.quantity || product.POSMetaData?.quantity || null,
      
      // Metadata
      strainType: product.strainType || product.strain,
      description: product.description,
      effects: product.effects || [],
      
      // Variants (different weights/sizes)
      variants: product.variants?.map(v => ({
        id: v.id,
        option: v.option,
        price: v.price,
        inStock: v.inStock,
        quantity: v.quantity
      })) || [],
      
      // Scrape metadata
      scrapedAt: new Date().toISOString(),
      source,
      sourceUrl: CONBUD_CONFIG.storeUrl
    };
  } catch (error) {
    console.error('Failed to normalize product:', error.message);
    return null;
  }
}
