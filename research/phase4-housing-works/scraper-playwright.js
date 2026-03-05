/**
 * Housing Works Cannabis Co. Scraper (Blaze Platform)
 * URL: https://hwcannabis.co/menu/broadway/
 * Complexity: Medium
 * 
 * This is a Node.js port of the existing Python scraper with enhancements:
 * 1. Browser automation with Playwright
 * 2. Network request tracking for API discovery
 * 3. Quantity extraction from multiple sources
 * 4. Category-based navigation
 * 5. Stealth mode to avoid detection
 * 
 * Based on: memory/stealth-scraper/scrapers/blaze/housing_works.py
 */

const { chromium } = require('playwright');
const fs = require('fs');

const HOUSING_WORKS_CONFIG = {
  storeName: 'housing_works',
  baseUrl: 'https://hwcannabis.co',
  menuUrl: 'https://hwcannabis.co/menu/broadway/',
  location: 'Broadway'
};

class HousingWorksScraper {
  constructor() {
    this.browser = null;
    this.page = null;
    this.products = [];
    this.apiRequests = [];
    this.apiResponses = [];
    
    // Blaze platform selectors (refined from Python scraper)
    this.selectors = {
      categoryNav: '.category-menu, .menu-nav, nav, .categories',
      categoryLinks: 'a[href*="categories"], a[href*="category"], .category-link',
      productGrid: '.product, .product-item, .menu-item, [data-product]',
      productName: '.product-name, .product-title, h3, .name',
      productPrice: '.price, .product-price, .cost',
      productLink: 'a',
      productDescription: '.description, .product-description',
      productThc: '.thc, .thc-content, [data-thc]',
      productCbd: '.cbd, .cbd-content, [data-cbd]',
      productWeight: '.weight, .size, .amount',
      quantityDropdown: 'select[name*="quantity"], select[name*="qty"]',
      quantityInput: 'input[name*="quantity"], input[name*="qty"]',
      addToCart: '.add-to-cart, button[data-add-to-cart]',
      loadMore: '.load-more, .show-more',
      nextPage: '.next-page, .pagination-next'
    };
  }

  /**
   * Initialize browser with stealth settings
   */
  async init() {
    console.log('🚀 Launching browser for Housing Works...');
    
    this.browser = await chromium.launch({
      headless: false, // Set to true for production
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-web-security',
        '--disable-blink-features=AutomationControlled'
      ]
    });

    const context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      locale: 'en-US',
      timezoneId: 'America/New_York',
      extraHTTPHeaders: {
        'Accept-Language': 'en-US,en;q=0.9',
      }
    });

    this.page = await context.newPage();
    
    // Block unnecessary resources for speed
    await this.page.route('**/*.{png,jpg,jpeg,gif,svg,woff,woff2,mp4,mp3}', 
      route => route.abort()
    );
    
    // Set up network tracking for API discovery
    await this.setupNetworkTracking();
    
    console.log('✅ Browser initialized');
  }

  /**
   * Track API requests and responses for potential data sources
   */
  async setupNetworkTracking() {
    console.log('📡 Setting up network tracking...');

    // Track requests
    this.page.on('request', request => {
      const url = request.url();
      const keywords = ['api', 'graphql', 'inventory', 'products', 'cart', 'menu'];
      
      if (keywords.some(k => url.toLowerCase().includes(k))) {
        this.apiRequests.push({
          url,
          method: request.method(),
          postData: request.postData(),
          timestamp: Date.now()
        });
        
        console.log(`📤 API Request: ${request.method()} ${url.substring(0, 80)}...`);
      }
    });

    // Track responses
    this.page.on('response', async response => {
      const url = response.url();
      const keywords = ['api', 'graphql', 'inventory', 'products', 'cart', 'menu'];
      
      if (keywords.some(k => url.toLowerCase().includes(k)) && response.status() === 200) {
        try {
          const contentType = response.headers()['content-type'] || '';
          
          if (contentType.includes('application/json')) {
            const json = await response.json();
            
            this.apiResponses.push({
              url,
              status: response.status(),
              data: json,
              timestamp: Date.now()
            });
            
            console.log(`📥 API Response: ${url.substring(0, 80)}...`);
            
            // Try to extract products from response
            this.extractProductsFromApiResponse(json);
          }
        } catch (e) {
          // Not JSON or failed to parse
        }
      }
    });
    
    console.log('✅ Network tracking ready');
  }

  /**
   * Extract products from API responses
   */
  extractProductsFromApiResponse(json) {
    // Check common API response structures
    const possiblePaths = [
      json?.data?.products,
      json?.products,
      json?.data?.menu?.products,
      json?.menu?.items,
      json?.items,
      json?.results
    ];

    for (const products of possiblePaths) {
      if (Array.isArray(products) && products.length > 0) {
        console.log(`✨ Found ${products.length} products in API response`);
        
        products.forEach(product => {
          const normalized = this.normalizeProduct(product, 'api');
          if (normalized) {
            this.products.push(normalized);
          }
        });
        
        break;
      }
    }
  }

  /**
   * Navigate to menu page
   */
  async navigateToMenu() {
    console.log(`🌐 Navigating to ${HOUSING_WORKS_CONFIG.menuUrl}...`);
    
    await this.page.goto(HOUSING_WORKS_CONFIG.menuUrl, {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    console.log('✅ Menu page loaded');
    
    // Wait for content to render (Blaze is SPA)
    await this.page.waitForTimeout(5000);

    // Try to wait for products
    try {
      await this.page.waitForSelector(this.selectors.productGrid, { timeout: 10000 });
      console.log('✅ Products found on page');
    } catch (e) {
      console.warn('⚠️  Products selector not found, but continuing...');
    }
  }

  /**
   * Extract categories from navigation
   */
  async extractCategories() {
    console.log('📂 Extracting categories...');
    
    const categories = [];
    const navSelectors = [
      '.category-menu a',
      '.menu-nav a',
      'nav a',
      '.categories a',
      'a[href*="categories"]',
      '.category-link'
    ];

    for (const selector of navSelectors) {
      try {
        const links = await this.page.locator(selector).all();
        
        for (const link of links) {
          const href = await link.getAttribute('href');
          const text = await link.textContent();
          
          if (href && text) {
            const textLower = text.toLowerCase().trim();
            const categoryKeywords = ['flower', 'edible', 'vape', 'concentrate', 'pre-roll', 'tincture'];
            
            if (categoryKeywords.some(kw => textLower.includes(kw))) {
              const fullUrl = new URL(href, HOUSING_WORKS_CONFIG.baseUrl).href;
              categories.push({
                name: text.trim(),
                url: fullUrl
              });
            }
          }
        }
        
        if (categories.length > 0) {
          break;
        }
      } catch (e) {
        // Try next selector
      }
    }

    // Default categories if none found
    if (categories.length === 0) {
      categories.push(
        { name: 'Flower', url: `${HOUSING_WORKS_CONFIG.menuUrl}categories/flower/` },
        { name: 'Edibles', url: `${HOUSING_WORKS_CONFIG.menuUrl}categories/edibles/` },
        { name: 'Vapes', url: `${HOUSING_WORKS_CONFIG.menuUrl}categories/vapes/` },
        { name: 'Pre-rolls', url: `${HOUSING_WORKS_CONFIG.menuUrl}categories/pre-rolls/` },
        { name: 'All Products', url: HOUSING_WORKS_CONFIG.menuUrl }
      );
    }

    console.log(`✅ Found ${categories.length} categories:`, categories.map(c => c.name));
    return categories;
  }

  /**
   * Extract products from current page
   */
  async extractProductsFromPage() {
    console.log('📦 Extracting products from page...');
    
    const products = [];
    const productSelectors = [
      '.product',
      '.product-item',
      '.menu-item',
      '[data-product]',
      '.product-card'
    ];

    let productElements = [];
    for (const selector of productSelectors) {
      productElements = await this.page.locator(selector).all();
      if (productElements.length > 0) {
        console.log(`  Found ${productElements.length} products with selector: ${selector}`);
        break;
      }
    }

    if (productElements.length === 0) {
      console.warn('⚠️  No product elements found on page');
      return products;
    }

    for (const element of productElements) {
      try {
        const product = await this.extractProductData(element);
        if (product) {
          products.push(product);
        }
      } catch (e) {
        console.error('Error extracting product:', e.message);
      }
    }

    console.log(`✅ Extracted ${products.length} products from page`);
    return products;
  }

  /**
   * Extract data from a single product element
   */
  async extractProductData(element) {
    try {
      // Extract basic info using multiple selector strategies
      const name = await this.trySelectors(element, [
        '.product-name',
        '.product-title',
        'h3',
        '.name',
        '[data-product-name]'
      ]);

      if (!name) {
        return null; // Skip if no name found
      }

      const price = await this.trySelectors(element, [
        '.price',
        '.product-price',
        '.cost',
        '[data-price]'
      ]);

      const url = await this.tryAttribute(element, 'a', 'href');
      const fullUrl = url ? new URL(url, HOUSING_WORKS_CONFIG.baseUrl).href : null;

      // Extract potency
      const thc = await this.trySelectors(element, [
        '.thc',
        '.thc-content',
        '[data-thc]'
      ]);

      const cbd = await this.trySelectors(element, [
        '.cbd',
        '.cbd-content',
        '[data-cbd]'
      ]);

      // Try to extract quantity/availability
      const quantity = await this.extractQuantity(element);

      return {
        name: name.trim(),
        price: this.parsePrice(price),
        url: fullUrl,
        thc: this.parsePotency(thc),
        cbd: this.parsePotency(cbd),
        quantity: quantity,
        inStock: quantity === null || quantity > 0,
        scrapedAt: new Date().toISOString(),
        source: 'housing-works-broadway',
        sourceUrl: HOUSING_WORKS_CONFIG.menuUrl
      };
    } catch (e) {
      console.error('Failed to extract product data:', e);
      return null;
    }
  }

  /**
   * Try multiple selectors to find content
   */
  async trySelectors(element, selectors) {
    for (const selector of selectors) {
      try {
        const child = await element.locator(selector).first();
        const text = await child.textContent();
        if (text && text.trim()) {
          return text.trim();
        }
      } catch (e) {
        // Try next selector
      }
    }
    return null;
  }

  /**
   * Try to get attribute from element
   */
  async tryAttribute(element, selector, attribute) {
    try {
      const child = await element.locator(selector).first();
      return await child.getAttribute(attribute);
    } catch (e) {
      return null;
    }
  }

  /**
   * Extract quantity from element (multiple methods)
   */
  async extractQuantity(element) {
    // Method 1: Check for quantity dropdown/input
    try {
      const dropdown = await element.locator('select[name*="quantity"]').first();
      const options = await dropdown.locator('option').all();
      if (options.length > 0) {
        const lastOption = options[options.length - 1];
        const value = await lastOption.getAttribute('value');
        return parseInt(value) || null;
      }
    } catch (e) {
      // No dropdown
    }

    // Method 2: Check for data attributes
    try {
      const qty = await element.getAttribute('data-quantity');
      if (qty) {
        return parseInt(qty);
      }
    } catch (e) {
      // No data attribute
    }

    // Method 3: Look for "out of stock" indicators
    try {
      const text = await element.textContent();
      if (text.toLowerCase().includes('out of stock') || 
          text.toLowerCase().includes('sold out')) {
        return 0;
      }
    } catch (e) {
      // Can't check text
    }

    return null; // Quantity unknown
  }

  /**
   * Parse price string to number
   */
  parsePrice(priceString) {
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
  parsePotency(potencyString) {
    if (!potencyString) return null;
    
    const match = potencyString.match(/(\d+\.?\d*)%?/);
    if (match) {
      return {
        formatted: potencyString.trim(),
        value: parseFloat(match[1])
      };
    }
    
    return null;
  }

  /**
   * Normalize product from any source (API or page)
   */
  normalizeProduct(product, source = 'page') {
    return {
      id: product.id || product.productId,
      name: product.name,
      brand: product.brand || product.brandName,
      category: product.category || product.type,
      price: product.price,
      url: product.url,
      thc: product.thc,
      cbd: product.cbd,
      quantity: product.quantity,
      inStock: product.inStock !== false,
      scrapedAt: new Date().toISOString(),
      source: `housing-works-${source}`,
      sourceUrl: HOUSING_WORKS_CONFIG.menuUrl
    };
  }

  /**
   * Scroll to load all products (lazy loading)
   */
  async scrollToLoadAll() {
    console.log('📜 Scrolling to trigger lazy loading...');
    
    const scrollSteps = 5;
    for (let i = 0; i < scrollSteps; i++) {
      await this.page.evaluate(() => window.scrollBy(0, window.innerHeight));
      await this.page.waitForTimeout(1500);
    }

    // Scroll back to top
    await this.page.evaluate(() => window.scrollTo(0, 0));
    
    console.log('✅ Scrolling complete');
  }

  /**
   * Navigate through categories and extract all products
   */
  async scrapeAllCategories() {
    const categories = await this.extractCategories();
    const allProducts = [];

    for (const category of categories) {
      try {
        console.log(`\n📂 Scraping category: ${category.name}`);
        
        await this.page.goto(category.url, { 
          waitUntil: 'networkidle',
          timeout: 30000 
        });
        
        await this.page.waitForTimeout(3000);
        await this.scrollToLoadAll();
        
        const products = await this.extractProductsFromPage();
        
        // Add category to products
        products.forEach(p => {
          p.category = category.name;
          allProducts.push(p);
        });
        
      } catch (e) {
        console.error(`❌ Failed to scrape category ${category.name}:`, e.message);
      }
    }

    return allProducts;
  }

  /**
   * Save data to files
   */
  async saveData() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    // Deduplicate by name+price (no reliable ID)
    const uniqueProducts = Array.from(
      new Map(this.products.map(p => [`${p.name}-${p.price}`, p])).values()
    );

    console.log(`💾 Saving ${uniqueProducts.length} unique products...`);

    // Save products
    fs.writeFileSync(
      `housing-works-products-${timestamp}.json`,
      JSON.stringify(uniqueProducts, null, 2)
    );

    // Save API data for analysis
    fs.writeFileSync(
      `housing-works-api-requests-${timestamp}.json`,
      JSON.stringify(this.apiRequests, null, 2)
    );

    fs.writeFileSync(
      `housing-works-api-responses-${timestamp}.json`,
      JSON.stringify(this.apiResponses, null, 2)
    );

    console.log('✅ Data saved successfully');
    
    return {
      productCount: uniqueProducts.length,
      apiRequestCount: this.apiRequests.length,
      apiResponseCount: this.apiResponses.length
    };
  }

  /**
   * Main scraping workflow
   */
  async scrape() {
    try {
      await this.init();
      await this.navigateToMenu();
      
      // Option 1: Scrape all categories
      const categoryProducts = await this.scrapeAllCategories();
      this.products.push(...categoryProducts);
      
      // Option 2: Also try API products (from network tracking)
      // API products are already added via extractProductsFromApiResponse()
      
      const stats = await this.saveData();
      
      console.log('\n📊 Scraping Summary:');
      console.log(`  Products: ${stats.productCount}`);
      console.log(`  API Requests: ${stats.apiRequestCount}`);
      console.log(`  API Responses: ${stats.apiResponseCount}`);
      
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

// Export
module.exports = HousingWorksScraper;

// Run if executed directly
if (require.main === module) {
  const scraper = new HousingWorksScraper();
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
