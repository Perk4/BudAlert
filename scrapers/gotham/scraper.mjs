/**
 * Gotham NYC Scraper
 * Platform: WordPress + Dovetail
 * Method: curl + HTML Parsing (no browser needed)
 * 
 * Extracts product data from Gotham NYC's server-rendered HTML
 * Uses multiple extraction strategies for maximum reliability
 */

import axios from 'axios';
import * as cheerio from 'cheerio';
import { writeFileSync } from 'fs';

const GOTHAM_CONFIG = {
  baseUrl: 'https://gotham.nyc',
  menuUrl: 'https://gotham.nyc/menu',
  storeName: 'gotham_nyc'
};

export class GothamScraper {
  constructor() {
    this.client = axios.create({
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Accept-Language': 'en-US,en;q=0.9',
        // Age verification cookie
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
   * Extract products from HTML using multiple strategies
   */
  extractProducts(html, url) {
    console.log('📦 Parsing HTML for products...');

    if (typeof html !== 'string' || html.trim() === '') {
      console.warn('  ⚠️  Empty or invalid HTML provided, returning no products');
      return [];
    }
    
    const $ = cheerio.load(html);
    const products = [];

    // Strategy 1: JSON-LD structured data (best for WordPress/SEO)
    const jsonLdProducts = this.extractJsonLd($);
    if (jsonLdProducts.length > 0) {
      console.log(`  ✨ Found ${jsonLdProducts.length} products via JSON-LD`);
      products.push(...jsonLdProducts);
    }

    // Strategy 2: HTML product elements (Dovetail/WordPress classes)
    const htmlProducts = this.extractHtmlProducts($);
    if (htmlProducts.length > 0) {
      console.log(`  ✨ Found ${htmlProducts.length} products via HTML parsing`);
      products.push(...htmlProducts);
    }

    // Strategy 3: WooCommerce patterns
    const wooProducts = this.extractWooCommerceProducts($);
    if (wooProducts.length > 0) {
      console.log(`  ✨ Found ${wooProducts.length} products via WooCommerce`);
      products.push(...wooProducts);
    }

    console.log(`✅ Total products extracted: ${products.length}`);
    
    // Add metadata to all products
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
        // Invalid JSON or not a product schema
      }
    });

    return products;
  }

  /**
   * Normalize JSON-LD product data
   */
  normalizeJsonLdProduct(data) {
    const potency = this.extractPotencyFromText(data.description || '');
    
    return {
      id: data.sku || data.productID,
      name: data.name,
      brand: data.brand?.name || data.brand,
      category: data.category || this.extractCategory(data.name),
      
      price: parseFloat(data.offers?.price || data.price),
      priceFormatted: data.offers?.priceCurrency 
        ? `${data.offers.priceCurrency} ${data.offers.price}`
        : `$${data.offers?.price || data.price}`,
      
      image: data.image?.url || data.image,
      images: Array.isArray(data.image) ? data.image : [data.image].filter(Boolean),
      
      description: data.description,
      url: data.url || data.offers?.url,
      
      inStock: data.offers?.availability === 'https://schema.org/InStock' || 
               data.offers?.availability === 'InStock',
      
      ...potency
    };
  }

  /**
   * Extract HTML products (Dovetail/WordPress patterns)
   */
  extractHtmlProducts($) {
    const products = [];

    // Common WordPress/Dovetail selectors
    const selectors = [
      '.dt-product',
      '.dt-product-item',
      '.product',
      '.product-item',
      'article.product',
      '[data-product-id]'
    ];

    const elements = [];
    const seenElements = new Set();

    for (const selector of selectors) {
      const matches = $(selector).toArray();

      if (matches.length > 0) {
        console.log(`  → Found ${matches.length} elements with selector: ${selector}`);
      }

      for (const elem of matches) {
        if (!seenElements.has(elem)) {
          seenElements.add(elem);
          elements.push(elem);
        }
      }
    }

    elements.forEach((elem) => {
      const product = this.parseProductElement($, elem);
      if (product && product.name) {
        products.push(product);
      }
    });

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

    // Extract potency from element text
    const text = $elem.text();
    const potency = this.extractPotencyFromText(text);

    // Extract brand
    const brand = $elem.find('.brand, .product-brand, .dt-brand')
      .first().text().trim() || null;

    // Check stock status
    const lowerText = text.toLowerCase();
    const classNames = ($elem.attr('class') || '').toLowerCase();
    const hasOutOfStockText = lowerText.includes('out of stock') ||
      lowerText.includes('sold out') ||
      lowerText.includes('unavailable');
    const hasOutOfStockClass = classNames.includes('out-of-stock') ||
      classNames.includes('outofstock') ||
      classNames.includes('sold-out') ||
      classNames.includes('soldout');
    const inStock = !hasOutOfStockText && !hasOutOfStockClass;

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
   * Extract THC/CBD potency from text
   */
  extractPotencyFromText(text) {
    if (!text) return { thc: null, cbd: null };
    
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
        console.log('💡 TIP: Age gate detected. Using age verification cookies.');
      }

      // Extract products
      const allProducts = this.extractProducts(html, GOTHAM_CONFIG.menuUrl);

      // Deduplicate by name
      const uniqueProducts = Array.from(
        new Map(allProducts.map(p => [p.name, p])).values()
      );

      console.log(`\n✅ Scraped ${uniqueProducts.length} unique products`);
      
      return uniqueProducts;
    } catch (error) {
      console.error('❌ Scraping failed:', error);
      throw error;
    }
  }
}

export default GothamScraper;

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const scraper = new GothamScraper();

  scraper.scrape()
    .then(products => {
      console.log('\n✅ SUCCESS!');
      console.log(`📊 Scraped ${products.length} products`);

      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `gotham-products-${timestamp}.json`;
      writeFileSync(filename, JSON.stringify(products, null, 2));
      console.log(`💾 Saved to ${filename}`);

      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ FAILED:', error.message);
      process.exit(1);
    });
}
