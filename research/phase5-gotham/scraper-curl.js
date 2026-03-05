/**
 * Gotham NYC Scraper - curl + HTML Parsing Method
 * URL: https://gotham.nyc/menu
 * Platform: WordPress + Dovetail
 * Complexity: Low-Medium
 * 
 * This scraper uses simple HTTP requests with HTML parsing:
 * 1. Fetch page with curl/axios (no browser needed)
 * 2. Parse HTML for product data
 * 3. Extract JSON-LD structured data if available
 * 4. Handle age gate if present
 * 
 * Advantages:
 * - Fast (no browser overhead)
 * - Low resource usage
 * - Easy to deploy anywhere
 * - Server-side rendered content
 * 
 * Disadvantages:
 * - May miss dynamic content
 * - Age gate might block access
 * - Less structured than API
 */

const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

const GOTHAM_CONFIG = {
  baseUrl: 'https://gotham.nyc',
  menuUrl: 'https://gotham.nyc/menu',
  storeName: 'gotham_nyc'
};

class GothamCurlScraper {
  constructor() {
    this.products = [];
    this.client = axios.create({
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Accept-Language': 'en-US,en;q=0.9',
        // Set age verification cookie if needed
        'Cookie': 'age_verified=1; age_gate_passed=true'
      },
      maxRedirects: 5,
      timeout: 30000
    });
  }

  /**
   * Fetch page HTML
   */
  async fetchPage(url) {
    console.log(`🌐 Fetching ${url}...`);
    
    try {
      const response = await this.client.get(url);
      console.log(`✅ Page fetched (${response.data.length} bytes)`);
      return response.data;
    } catch (error) {
      console.error(`❌ Failed to fetch ${url}:`, error.message);
      throw error;
    }
  }

  /**
   * Extract products from HTML
   */
  extractProductsFromHTML(html, url) {
    console.log('📦 Parsing HTML for products...');
    
    const $ = cheerio.load(html);
    const products = [];

    // Method 1: Look for JSON-LD structured data (best for WordPress)
    const jsonLdProducts = this.extractJsonLd($);
    if (jsonLdProducts.length > 0) {
      console.log(`  ✨ Found ${jsonLdProducts.length} products via JSON-LD`);
      products.push(...jsonLdProducts);
    }

    // Method 2: Parse HTML product elements (Dovetail classes)
    const htmlProducts = this.extractHtmlProducts($);
    if (htmlProducts.length > 0) {
      console.log(`  ✨ Found ${htmlProducts.length} products via HTML parsing`);
      products.push(...htmlProducts);
    }

    // Method 3: Look for WordPress WooCommerce patterns
    const wooProducts = this.extractWooCommerceProducts($);
    if (wooProducts.length > 0) {
      console.log(`  ✨ Found ${wooProducts.length} products via WooCommerce`);
      products.push(...wooProducts);
    }

    console.log(`✅ Total products extracted: ${products.length}`);
    
    // Add metadata
    products.forEach(p => {
      p.scrapedAt = new Date().toISOString();
      p.source = 'gotham-nyc';
      p.sourceUrl = url;
    });

    return products;
  }

  /**
   * Extract JSON-LD structured data
   */
  extractJsonLd($) {
    const products = [];

    $('script[type="application/ld+json"]').each((i, elem) => {
      try {
        const jsonText = $(elem).html();
        const data = JSON.parse(jsonText);

        // Handle single product
        if (data['@type'] === 'Product') {
          products.push(this.normalizeJsonLdProduct(data));
        }

        // Handle product list
        if (data['@type'] === 'ItemList' && data.itemListElement) {
          data.itemListElement.forEach(item => {
            if (item.item && item.item['@type'] === 'Product') {
              products.push(this.normalizeJsonLdProduct(item.item));
            }
          });
        }

        // Handle array of products
        if (Array.isArray(data)) {
          data.forEach(item => {
            if (item['@type'] === 'Product') {
              products.push(this.normalizeJsonLdProduct(item));
            }
          });
        }
      } catch (e) {
        // Invalid JSON or not a product
      }
    });

    return products;
  }

  /**
   * Normalize JSON-LD product
   */
  normalizeJsonLdProduct(data) {
    return {
      id: data.sku || data.productID,
      name: data.name,
      brand: data.brand?.name || data.brand,
      category: data.category || this.extractCategory(data.name),
      
      price: data.offers?.price || data.price,
      priceFormatted: data.offers?.priceCurrency 
        ? `${data.offers.priceCurrency} ${data.offers.price}`
        : `$${data.offers?.price || data.price}`,
      
      image: data.image?.url || data.image,
      images: Array.isArray(data.image) ? data.image : [data.image],
      
      description: data.description,
      url: data.url || data.offers?.url,
      
      inStock: data.offers?.availability === 'https://schema.org/InStock' || 
               data.offers?.availability === 'InStock',
      
      // Try to extract potency from description
      ...this.extractPotencyFromText(data.description || '')
    };
  }

  /**
   * Extract HTML products (Dovetail/WordPress patterns)
   */
  extractHtmlProducts($) {
    const products = [];

    // Dovetail-specific selectors (dt- prefix)
    const selectors = [
      '.dt-product',
      '.dt-product-item',
      '.product',
      '.product-item',
      'article.product',
      '[data-product-id]'
    ];

    for (const selector of selectors) {
      const elements = $(selector);
      
      if (elements.length > 0) {
        console.log(`  → Found ${elements.length} elements with selector: ${selector}`);
        
        elements.each((i, elem) => {
          const product = this.parseProductElement($, elem);
          if (product && product.name) {
            products.push(product);
          }
        });
        
        break; // Use first working selector
      }
    }

    return products;
  }

  /**
   * Parse individual product element
   */
  parseProductElement($, elem) {
    const $elem = $(elem);

    // Extract name
    const name = $elem.find('h1, h2, h3, h4, .product-name, .product-title, .dt-product-name')
      .first().text().trim();

    if (!name) return null;

    // Extract price
    const priceText = $elem.find('.price, .product-price, .dt-price, .cost')
      .first().text().trim();
    const price = this.parsePrice(priceText);

    // Extract URL
    const url = $elem.find('a').first().attr('href');
    const fullUrl = url ? new URL(url, GOTHAM_CONFIG.baseUrl).href : null;

    // Extract image
    const image = $elem.find('img').first().attr('src') || 
                  $elem.find('img').first().attr('data-src');

    // Extract THC/CBD from text
    const text = $elem.text();
    const potency = this.extractPotencyFromText(text);

    // Extract brand
    const brand = $elem.find('.brand, .product-brand, .dt-brand')
      .first().text().trim() || null;

    // Check stock status
    const inStock = !text.toLowerCase().includes('out of stock') &&
                    !text.toLowerCase().includes('sold out') &&
                    !$elem.hasClass('out-of-stock');

    return {
      name,
      brand,
      category: this.extractCategory(name),
      price,
      priceFormatted: priceText,
      url: fullUrl,
      image,
      ...potency,
      inStock
    };
  }

  /**
   * Extract WooCommerce products
   */
  extractWooCommerceProducts($) {
    const products = [];

    $('.woocommerce-product, .product-type-simple, .product-type-variable').each((i, elem) => {
      const $elem = $(elem);

      const name = $elem.find('.woocommerce-loop-product__title, h2.product-title')
        .first().text().trim();

      if (!name) return;

      const priceText = $elem.find('.price .amount, .woocommerce-Price-amount')
        .first().text().trim();
      const price = this.parsePrice(priceText);

      const url = $elem.find('a.woocommerce-LoopProduct-link').first().attr('href');
      const fullUrl = url ? new URL(url, GOTHAM_CONFIG.baseUrl).href : null;

      const image = $elem.find('img.attachment-woocommerce_thumbnail').first().attr('src');

      products.push({
        name,
        price,
        priceFormatted: priceText,
        url: fullUrl,
        image,
        category: this.extractCategory(name),
        inStock: !$elem.hasClass('outofstock')
      });
    });

    return products;
  }

  /**
   * Parse price from string
   */
  parsePrice(priceString) {
    if (!priceString) return null;
    
    const match = priceString.match(/[\d,]+\.?\d*/);
    return match ? parseFloat(match[0].replace(/,/g, '')) : null;
  }

  /**
   * Extract THC/CBD from text
   */
  extractPotencyFromText(text) {
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
   * Extract category from product name
   */
  extractCategory(name) {
    const nameLower = name.toLowerCase();
    
    if (nameLower.includes('flower') || nameLower.includes('bud')) return 'Flower';
    if (nameLower.includes('edible') || nameLower.includes('gummies')) return 'Edibles';
    if (nameLower.includes('vape') || nameLower.includes('cart')) return 'Vapes';
    if (nameLower.includes('concentrate') || nameLower.includes('wax') || nameLower.includes('shatter')) return 'Concentrates';
    if (nameLower.includes('pre-roll') || nameLower.includes('joint')) return 'Pre-Rolls';
    if (nameLower.includes('tincture') || nameLower.includes('oil')) return 'Tinctures';
    
    return 'Other';
  }

  /**
   * Check for age gate
   */
  checkAgeGate(html) {
    const $ = cheerio.load(html);
    
    const ageGateIndicators = [
      'age verification',
      'age gate',
      'confirm you are',
      'are you 21',
      'must be 21',
      'verify your age'
    ];

    const pageText = $('body').text().toLowerCase();
    
    for (const indicator of ageGateIndicators) {
      if (pageText.includes(indicator)) {
        console.warn('⚠️  Age gate detected on page');
        return true;
      }
    }

    return false;
  }

  /**
   * Main scraping workflow
   */
  async scrape() {
    try {
      // Fetch menu page
      const html = await this.fetchPage(GOTHAM_CONFIG.menuUrl);

      // Check for age gate
      if (this.checkAgeGate(html)) {
        console.log('💡 TIP: Age gate detected. Set appropriate cookies to bypass.');
        console.log('   Cookie: age_verified=1');
      }

      // Extract products
      this.products = this.extractProductsFromHTML(html, GOTHAM_CONFIG.menuUrl);

      // Deduplicate by name
      const uniqueProducts = Array.from(
        new Map(this.products.map(p => [p.name, p])).values()
      );

      // Save data
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `gotham-products-${timestamp}.json`;
      
      fs.writeFileSync(
        filename,
        JSON.stringify(uniqueProducts, null, 2)
      );

      console.log(`\n✅ Saved ${uniqueProducts.length} products to ${filename}`);
      
      return {
        productCount: uniqueProducts.length,
        filename
      };
    } catch (error) {
      console.error('❌ Scraping failed:', error);
      throw error;
    }
  }
}

// Export
module.exports = GothamCurlScraper;

// Run if executed directly
if (require.main === module) {
  const scraper = new GothamCurlScraper();
  
  scraper.scrape()
    .then(stats => {
      console.log('\n✅ SUCCESS!');
      console.log(`📊 Scraped ${stats.productCount} products`);
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ FAILED:', error.message);
      process.exit(1);
    });
}
