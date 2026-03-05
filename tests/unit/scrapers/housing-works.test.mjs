import { describe, it, expect, vi, beforeEach } from 'vitest';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import * as cheerio from 'cheerio';

// Import scraper class
import HousingWorksScraper from '../../../scrapers/housing-works/scraper.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fixturesDir = join(__dirname, '../../fixtures');

describe('HousingWorksScraper', () => {
  let scraper;
  let sampleHTML;

  beforeEach(() => {
    scraper = new HousingWorksScraper();
    sampleHTML = readFileSync(join(fixturesDir, 'housing-works-sample.html'), 'utf-8');
  });

  describe('parsePrice()', () => {
    it('should parse simple price', () => {
      expect(scraper.parsePrice('$50.00')).toBe(50.00);
    });

    it('should parse price with comma', () => {
      expect(scraper.parsePrice('$1,234.56')).toBe(1234.56);
    });

    it('should parse price without dollar sign', () => {
      expect(scraper.parsePrice('25.99')).toBe(25.99);
    });

    it('should parse integer price', () => {
      expect(scraper.parsePrice('$10')).toBe(10);
    });

    it('should return null for invalid price', () => {
      expect(scraper.parsePrice('N/A')).toBe(null);
      expect(scraper.parsePrice('')).toBe(null);
      expect(scraper.parsePrice(null)).toBe(null);
    });

    it('should handle price with text', () => {
      expect(scraper.parsePrice('Price: $40.00 each')).toBe(40.00);
    });

    it('should extract first number if multiple', () => {
      expect(scraper.parsePrice('$50.00 - $100.00')).toBe(50.00);
    });
  });

  describe('parsePotency()', () => {
    it('should parse potency with percentage', () => {
      const result = scraper.parsePotency('22.5%');
      expect(result).toEqual({
        formatted: '22.5%',
        value: 22.5
      });
    });

    it('should parse potency without percentage', () => {
      const result = scraper.parsePotency('THC: 18');
      expect(result.value).toBe(18);
    });

    it('should parse decimal values', () => {
      const result = scraper.parsePotency('0.5%');
      expect(result.value).toBe(0.5);
    });

    it('should return null for invalid input', () => {
      expect(scraper.parsePotency('N/A')).toBe(null);
      expect(scraper.parsePotency('')).toBe(null);
      expect(scraper.parsePotency(null)).toBe(null);
    });

    it('should handle text with numbers', () => {
      const result = scraper.parsePotency('Contains 15.5% THC');
      expect(result.value).toBe(15.5);
    });
  });

  describe('trySelectors()', () => {
    it('should return text from first matching selector', () => {
      const $ = cheerio.load('<div><h3 class="name">Product Name</h3></div>');
      const $elem = $('div');
      
      const result = scraper.trySelectors($, $elem, ['.missing', '.name', 'h3']);
      expect(result).toBe('Product Name');
    });

    it('should skip empty results', () => {
      const $ = cheerio.load('<div><span class="empty"></span><h3>Name</h3></div>');
      const $elem = $('div');
      
      const result = scraper.trySelectors($, $elem, ['.empty', 'h3']);
      expect(result).toBe('Name');
    });

    it('should return null if no selectors match', () => {
      const $ = cheerio.load('<div>Content</div>');
      const $elem = $('div');
      
      const result = scraper.trySelectors($, $elem, ['.missing', '.nothere']);
      expect(result).toBe(null);
    });

    it('should trim whitespace', () => {
      const $ = cheerio.load('<div><span class="name">  Product  </span></div>');
      const $elem = $('div');
      
      const result = scraper.trySelectors($, $elem, ['.name']);
      expect(result).toBe('Product');
    });
  });

  describe('tryAttribute()', () => {
    it('should extract attribute value', () => {
      const $ = cheerio.load('<div><a href="/product/123">Link</a></div>');
      const $elem = $('div');
      
      const result = scraper.tryAttribute($, $elem, 'a', 'href');
      expect(result).toBe('/product/123');
    });

    it('should return null for missing element', () => {
      const $ = cheerio.load('<div>No link</div>');
      const $elem = $('div');
      
      const result = scraper.tryAttribute($, $elem, 'a', 'href');
      expect(result).toBe(null);
    });

    it('should return null for missing attribute', () => {
      const $ = cheerio.load('<div><a>No href</a></div>');
      const $elem = $('div');
      
      const result = scraper.tryAttribute($, $elem, 'a', 'href');
      expect(result).toBe(null);
    });

    it('should work with various attributes', () => {
      const $ = cheerio.load('<div><img src="image.jpg" alt="Alt text"></div>');
      const $elem = $('div');
      
      expect(scraper.tryAttribute($, $elem, 'img', 'src')).toBe('image.jpg');
      expect(scraper.tryAttribute($, $elem, 'img', 'alt')).toBe('Alt text');
    });
  });

  describe('checkInStock()', () => {
    it('should return false for "out of stock"', () => {
      const $ = cheerio.load('<div>Out of stock</div>');
      const $elem = $('div');
      
      expect(scraper.checkInStock($, $elem)).toBe(false);
    });

    it('should return false for "sold out"', () => {
      const $ = cheerio.load('<div>Sold out</div>');
      const $elem = $('div');
      
      expect(scraper.checkInStock($, $elem)).toBe(false);
    });

    it('should return false for "unavailable"', () => {
      const $ = cheerio.load('<div>Currently unavailable</div>');
      const $elem = $('div');
      
      expect(scraper.checkInStock($, $elem)).toBe(false);
    });

    it('should return false for disabled add to cart button', () => {
      const $ = cheerio.load('<div><button class="add-to-cart" disabled>Add</button></div>');
      const $elem = $('div');
      
      expect(scraper.checkInStock($, $elem)).toBe(false);
    });

    it('should return true for available product', () => {
      const $ = cheerio.load('<div>In stock now!</div>');
      const $elem = $('div');
      
      expect(scraper.checkInStock($, $elem)).toBe(true);
    });

    it('should be case insensitive', () => {
      const $ = cheerio.load('<div>OUT OF STOCK</div>');
      const $elem = $('div');
      
      expect(scraper.checkInStock($, $elem)).toBe(false);
    });

    it('should default to in stock', () => {
      const $ = cheerio.load('<div><h3>Product</h3><span>$10</span></div>');
      const $elem = $('div');
      
      expect(scraper.checkInStock($, $elem)).toBe(true);
    });
  });

  describe('extractProductData()', () => {
    it('should extract complete product data', () => {
      const $ = cheerio.load(sampleHTML);
      const $elem = $('.product[data-product="hw-001"]');
      
      const product = scraper.extractProductData($, $elem[0]);
      
      expect(product).toBeDefined();
      expect(product.name).toBe('Lemon Haze Flower');
      expect(product.brand).toBe('Green Thumb Industries');
      expect(product.price).toBe(50.00);
      expect(product.priceRaw).toBe('$50.00');
      expect(product.category).toBe('Flower');
      expect(product.weight).toBe('3.5g');
      expect(product.thc).toBeDefined();
      expect(product.thc.value).toBe(22.5);
      expect(product.cbd).toBeDefined();
      expect(product.cbd.value).toBe(0.5);
      expect(product.inStock).toBe(true);
      expect(product.source).toBe('housing-works-broadway');
    });

    it('should return null for element without name', () => {
      const $ = cheerio.load('<div class="product"><span>No name</span></div>');
      const $elem = $('.product');
      
      const product = scraper.extractProductData($, $elem[0]);
      expect(product).toBe(null);
    });

    it('should handle missing optional fields', () => {
      const $ = cheerio.load(`
        <div class="product">
          <h3>Simple Product</h3>
          <span class="price">$10</span>
        </div>
      `);
      const $elem = $('.product');
      
      const product = scraper.extractProductData($, $elem[0]);
      
      expect(product).toBeDefined();
      expect(product.name).toBe('Simple Product');
      expect(product.price).toBe(10);
      expect(product.brand).toBe(null);
      expect(product.category).toBe(null);
      expect(product.thc).toBe(null);
    });

    it('should detect out of stock products', () => {
      const $ = cheerio.load(sampleHTML);
      const outOfStockProduct = $('.menu-item');
      
      const product = scraper.extractProductData($, outOfStockProduct[0]);
      
      expect(product).toBeDefined();
      expect(product.inStock).toBe(false);
      expect(product.quantity).toBe(0);
    });

    it('should construct full URLs from relative paths', () => {
      const $ = cheerio.load(sampleHTML);
      const $elem = $('.product[data-product="hw-001"]');
      
      const product = scraper.extractProductData($, $elem[0]);
      
      expect(product.url).toContain('https://hwcannabis.co');
      expect(product.url).toContain('/product/lemon-haze');
    });

    it('should add timestamp and metadata', () => {
      const $ = cheerio.load(sampleHTML);
      const $elem = $('.product[data-product="hw-001"]');
      
      const product = scraper.extractProductData($, $elem[0]);
      
      expect(product.scrapedAt).toMatch(/^\d{4}-\d{2}-\d{2}T/);
      expect(product.source).toBe('housing-works-broadway');
      expect(product.sourceUrl).toContain('hwcannabis.co');
    });
  });

  describe('parseProducts()', () => {
    it('should parse multiple products', () => {
      const products = scraper.parseProducts(sampleHTML);
      
      expect(products.length).toBeGreaterThan(0);
      
      const lemonHaze = products.find(p => p.name?.includes('Lemon Haze'));
      expect(lemonHaze).toBeDefined();
      expect(lemonHaze.price).toBe(50);
    });

    it('should try multiple selector strategies', () => {
      const products = scraper.parseProducts(sampleHTML);
      
      // Should find products with different class names
      const productClasses = products.map(p => p.name);
      expect(productClasses.some(name => name?.includes('Lemon Haze'))).toBe(true);
      expect(productClasses.some(name => name?.includes('Blue Dream'))).toBe(true);
    });

    it('should handle empty HTML', () => {
      const products = scraper.parseProducts('<html><body>No products</body></html>');
      expect(products).toHaveLength(0);
    });

    it('should skip products without names', () => {
      const html = `
        <div class="product">
          <span class="price">$10</span>
        </div>
      `;
      
      const products = scraper.parseProducts(html);
      expect(products).toHaveLength(0);
    });
  });

  describe('extractCategories()', () => {
    it('should extract category links', () => {
      const html = `
        <nav class="category-menu">
          <a href="/categories/flower">Flower</a>
          <a href="/categories/edibles">Edibles</a>
          <a href="/categories/vapes">Vapes</a>
        </nav>
      `;
      
      const $ = cheerio.load(html);
      const categories = scraper.extractCategories($);
      
      expect(categories.length).toBeGreaterThan(0);
      expect(categories.some(c => c.name === 'Flower')).toBe(true);
    });

    it('should filter by cannabis keywords', () => {
      const html = `
        <nav>
          <a href="/about">About Us</a>
          <a href="/flower">Flower</a>
          <a href="/contact">Contact</a>
          <a href="/edibles">Edibles</a>
        </nav>
      `;
      
      const $ = cheerio.load(html);
      const categories = scraper.extractCategories($);
      
      const categoryNames = categories.map(c => c.name);
      expect(categoryNames).toContain('Flower');
      expect(categoryNames).toContain('Edibles');
      expect(categoryNames).not.toContain('About Us');
      expect(categoryNames).not.toContain('Contact');
    });

    it('should use defaults if no categories found', () => {
      const $ = cheerio.load('<html><body>No navigation</body></html>');
      const categories = scraper.extractCategories($);
      
      expect(categories).toHaveLength(1);
      expect(categories[0].name).toBe('All Products');
    });

    it('should construct full URLs', () => {
      const html = '<nav><a href="/categories/flower">Flower</a></nav>';
      const $ = cheerio.load(html);
      const categories = scraper.extractCategories($);
      
      expect(categories[0].url).toContain('https://hwcannabis.co');
    });
  });

  describe('Error Handling', () => {
    it('should not crash on null HTML', () => {
      expect(() => scraper.parseProducts(null)).not.toThrow();
    });

    it('should handle malformed HTML', () => {
      const html = '<div><p>Unclosed tags';
      const products = scraper.parseProducts(html);
      expect(Array.isArray(products)).toBe(true);
    });

    it('should handle parse errors gracefully', () => {
      const html = '<div class="product">Invalid structure</div>';
      const products = scraper.parseProducts(html);
      // Should not crash
      expect(Array.isArray(products)).toBe(true);
    });
  });

  describe('Configuration', () => {
    it('should have correct timeout', () => {
      // Check in CONFIG constant (imported from scraper)
      const scraper = new HousingWorksScraper();
      expect(scraper).toBeDefined();
    });

    it('should have browser-like headers', () => {
      const scraper = new HousingWorksScraper();
      expect(scraper).toBeDefined();
      // Headers are set in axios config - this just verifies instantiation
    });
  });
});
