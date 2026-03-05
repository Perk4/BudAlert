/**
 * Housing Works Cannabis Co. Scraper
 * Lightweight HTTP-based scraper for Blaze platform
 * 
 * Based on the Python scraper at memory/stealth-scraper/scrapers/blaze/housing_works.py
 * Adapted for Node.js without browser automation (Playwright unavailable due to system deps)
 */

import axios from 'axios';
import * as cheerio from 'cheerio';
import { writeFileSync } from 'fs';

const CONFIG = {
  storeName: 'housing_works',
  baseUrl: 'https://hwcannabis.co',
  menuUrl: 'https://hwcannabis.co/menu/broadway/',
  location: 'Broadway',
  timeout: 30000,
  headers: {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none'
  }
};

class HousingWorksScraper {
  constructor() {
    this.products = [];
    this.apiEndpoints = [];
  }

  /**
   * Fetch page HTML
   */
  async fetchPage(url) {
    console.log(`🌐 Fetching: ${url}`);
    
    try {
      const response = await axios.get(url, {
        headers: CONFIG.headers,
        timeout: CONFIG.timeout,
        maxRedirects: 5
      });
      
      console.log(`   ✅ Status: ${response.status}`);
      return response.data;
    } catch (error) {
      console.error(`   ❌ Failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Parse products from HTML
   */
  parseProducts(html) {
    console.log('📦 Parsing products from HTML...');

    if (typeof html !== 'string' || html.trim() === '') {
      console.warn('   ⚠️  Empty or invalid HTML provided');
      return [];
    }
    
    const $ = cheerio.load(html);
    const products = [];
    
    // Try multiple selector strategies for Blaze platform
    const productSelectors = [
      '.product',
      '.product-item',
      '.menu-item',
      '[data-product]',
      '.product-card',
      'article.product',
      'div[class*="product"]'
    ];

    const elements = [];
    const seenElements = new Set();

    for (const selector of productSelectors) {
      const matches = $(selector).toArray();
      if (matches.length > 0) {
        console.log(`   ✅ Found ${matches.length} products using: ${selector}`);
      }

      for (const elem of matches) {
        if (!seenElements.has(elem)) {
          seenElements.add(elem);
          elements.push(elem);
        }
      }
    }

    if (elements.length === 0) {
      console.warn('   ⚠️  No product elements found');
      
      // Debug: save HTML to file
      writeFileSync('debug-housing-works.html', html);
      console.log('   📄 Saved HTML to debug-housing-works.html for inspection');
      
      return products;
    }

    elements.forEach((elem, i) => {
      try {
        const product = this.extractProductData($, elem);
        if (product) {
          products.push(product);
        }
      } catch (error) {
        console.error(`   ⚠️  Failed to parse product ${i + 1}: ${error.message}`);
      }
    });

    console.log(`   ✅ Extracted ${products.length} products`);
    return products;
  }

  /**
   * Extract data from a single product element
   */
  extractProductData($, element) {
    const $elem = $(element);
    
    // Try multiple selectors for each field
    const name = this.trySelectors($, $elem, [
      '.product-name',
      '.product-title',
      'h3',
      'h2',
      '.name',
      '[data-product-name]',
      'a[href*="/product"]',
      'strong'
    ]);

    if (!name) {
      return null; // Skip if no name
    }

    const price = this.trySelectors($, $elem, [
      '.price',
      '.product-price',
      '.cost',
      '[data-price]',
      'span[class*="price"]',
      '.amount'
    ]);

    const url = this.tryAttribute($, $elem, 'a', 'href');
    const fullUrl = url ? new URL(url, CONFIG.baseUrl).href : null;

    // Extract THC/CBD
    const thc = this.trySelectors($, $elem, [
      '.thc',
      '.thc-content',
      '[data-thc]',
      '*[class*="thc"]'
    ]);

    const cbd = this.trySelectors($, $elem, [
      '.cbd',
      '.cbd-content',
      '[data-cbd]',
      '*[class*="cbd"]'
    ]);

    // Extract category/type
    const category = this.trySelectors($, $elem, [
      '.category',
      '.product-category',
      '.type',
      '[data-category]'
    ]);

    // Extract brand
    const brand = this.trySelectors($, $elem, [
      '.brand',
      '.product-brand',
      '[data-brand]'
    ]);

    // Extract weight/size
    const weight = this.trySelectors($, $elem, [
      '.weight',
      '.size',
      '.amount',
      '[data-weight]'
    ]);

    // Check stock status
    const inStock = this.checkInStock($, $elem);

    return {
      name: name.trim(),
      price: this.parsePrice(price),
      priceRaw: price?.trim() || null,
      url: fullUrl,
      brand: brand?.trim() || null,
      category: category?.trim() || null,
      weight: weight?.trim() || null,
      thc: this.parsePotency(thc),
      cbd: this.parsePotency(cbd),
      inStock: inStock,
      quantity: inStock ? null : 0, // 0 if out of stock, null if unknown
      scrapedAt: new Date().toISOString(),
      source: 'housing-works-broadway',
      sourceUrl: CONFIG.menuUrl
    };
  }

  /**
   * Try multiple selectors to find text content
   */
  trySelectors($, $elem, selectors) {
    for (const selector of selectors) {
      try {
        const text = $elem.find(selector).first().text();
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
  tryAttribute($, $elem, selector, attribute) {
    try {
      const value = $elem.find(selector).first().attr(attribute);
      return value || null;
    } catch (e) {
      return null;
    }
  }

  /**
   * Check if product is in stock
   */
  checkInStock($, $elem) {
    const text = $elem.text().toLowerCase();
    
    // Check for explicit out of stock indicators
    if (text.includes('out of stock') || 
        text.includes('sold out') ||
        text.includes('unavailable')) {
      return false;
    }
    
    // Check for disabled add to cart button
    const addToCart = $elem.find('.add-to-cart, button[data-add-to-cart]');
    if (addToCart.length > 0 && addToCart.attr('disabled')) {
      return false;
    }
    
    // Default to in stock
    return true;
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
   * Parse potency string (THC/CBD)
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
   * Extract categories from page
   */
  extractCategories($) {
    console.log('📂 Extracting categories...');
    
    const categories = [];
    const categorySelectors = [
      '.category-menu a',
      '.menu-nav a',
      'nav a',
      '.categories a',
      'a[href*="/categories/"]'
    ];

    for (const selector of categorySelectors) {
      $(selector).each((i, elem) => {
        const $elem = $(elem);
        const href = $elem.attr('href');
        const text = $elem.text();
        
        if (href && text) {
          const textLower = text.toLowerCase().trim();
          const keywords = ['flower', 'edible', 'vape', 'concentrate', 'pre-roll', 'tincture'];
          
          if (keywords.some(kw => textLower.includes(kw))) {
            const fullUrl = new URL(href, CONFIG.baseUrl).href;
            categories.push({
              name: text.trim(),
              url: fullUrl
            });
          }
        }
      });
      
      if (categories.length > 0) {
        break;
      }
    }

    if (categories.length === 0) {
      console.log('   ⚠️  No categories found, using defaults');
      categories.push({
        name: 'All Products',
        url: CONFIG.menuUrl
      });
    } else {
      console.log(`   ✅ Found ${categories.length} categories:`, categories.map(c => c.name));
    }

    return categories;
  }

  /**
   * Main scraping function
   */
  async scrape() {
    console.log('🏪 Housing Works Cannabis Co. Scraper');
    console.log('═'.repeat(50));
    console.log(`Store: ${CONFIG.storeName}`);
    console.log(`Location: ${CONFIG.location}`);
    console.log(`URL: ${CONFIG.menuUrl}`);
    console.log('═'.repeat(50));
    console.log('');

    try {
      // Fetch main menu page
      const html = await this.fetchPage(CONFIG.menuUrl);
      
      // Parse with cheerio
      const $ = cheerio.load(html);
      
      // Extract categories
      const categories = this.extractCategories($);
      
      // Scrape main page first
      console.log('\n📦 Scraping main menu page...');
      const mainProducts = this.parseProducts(html);
      this.products.push(...mainProducts);
      
      // Scrape category pages (limit to avoid long runtime)
      const maxCategories = 3;
      for (let i = 0; i < Math.min(categories.length, maxCategories); i++) {
        const category = categories[i];
        
        if (category.url === CONFIG.menuUrl) {
          continue; // Skip if same as main page
        }
        
        console.log(`\n📂 Scraping category: ${category.name}`);
        
        try {
          const categoryHtml = await this.fetchPage(category.url);
          const categoryProducts = this.parseProducts(categoryHtml);
          
          // Add category to products
          categoryProducts.forEach(p => {
            p.category = category.name;
          });
          
          this.products.push(...categoryProducts);
          
          // Add delay between requests to be polite
          if (i < Math.min(categories.length, maxCategories) - 1) {
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
        } catch (error) {
          console.error(`   ❌ Failed to scrape ${category.name}: ${error.message}`);
        }
      }
      
      // Deduplicate products by name+price
      const uniqueProducts = Array.from(
        new Map(this.products.map(p => [`${p.name}-${p.price}`, p])).values()
      );
      
      this.products = uniqueProducts;
      
      console.log('\n' + '═'.repeat(50));
      console.log('📊 SCRAPING RESULTS');
      console.log('═'.repeat(50));
      console.log(`Total Products: ${this.products.length}`);
      console.log(`In Stock: ${this.products.filter(p => p.inStock).length}`);
      console.log(`Out of Stock: ${this.products.filter(p => !p.inStock).length}`);
      console.log(`With Prices: ${this.products.filter(p => p.price).length}`);
      console.log(`With THC Data: ${this.products.filter(p => p.thc).length}`);
      console.log('═'.repeat(50));
      
      return this.products;
      
    } catch (error) {
      console.error('❌ Scraping failed:', error.message);
      throw error;
    }
  }

  /**
   * Save products to JSON file
   */
  saveProducts(filename = null) {
    if (!filename) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      filename = `housing-works-products-${timestamp}.json`;
    }
    
    const output = {
      store: CONFIG.storeName,
      location: CONFIG.location,
      scrapedAt: new Date().toISOString(),
      totalProducts: this.products.length,
      inStock: this.products.filter(p => p.inStock).length,
      products: this.products
    };
    
    writeFileSync(filename, JSON.stringify(output, null, 2));
    console.log(`\n💾 Saved ${this.products.length} products to: ${filename}`);
    
    return filename;
  }
}

// Export for use as module
export default HousingWorksScraper;

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const scraper = new HousingWorksScraper();
  
  scraper.scrape()
    .then(products => {
      scraper.saveProducts();
      console.log('\n✅ SUCCESS!\n');
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ FAILED:', error.message);
      process.exit(1);
    });
}
