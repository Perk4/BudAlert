import { describe, it, expect, vi, beforeEach } from 'vitest';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import * as cheerio from 'cheerio';

// Import scraper class
import { GothamScraper } from '../../../scrapers/gotham/scraper.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fixturesDir = join(__dirname, '../../fixtures');

describe('GothamScraper', () => {
  let scraper;
  let sampleHTML;

  beforeEach(() => {
    scraper = new GothamScraper();
    sampleHTML = readFileSync(join(fixturesDir, 'gotham-sample.html'), 'utf-8');
  });

  describe('parsePrice()', () => {
    it('should parse simple price', () => {
      expect(scraper.parsePrice('$45.00')).toBe(45.00);
    });

    it('should parse price with comma', () => {
      expect(scraper.parsePrice('$1,234.56')).toBe(1234.56);
    });

    it('should parse price without dollar sign', () => {
      expect(scraper.parsePrice('99.99')).toBe(99.99);
    });

    it('should parse integer price', () => {
      expect(scraper.parsePrice('$5')).toBe(5);
    });

    it('should return null for invalid price', () => {
      expect(scraper.parsePrice('N/A')).toBe(null);
      expect(scraper.parsePrice('')).toBe(null);
      expect(scraper.parsePrice(null)).toBe(null);
    });

    it('should handle price with text', () => {
      expect(scraper.parsePrice('Price: $45.00 USD')).toBe(45.00);
    });
  });

  describe('extractPotencyFromText()', () => {
    it('should extract THC percentage', () => {
      const result = scraper.extractPotencyFromText('THC: 24.5%');
      expect(result.thc).toEqual({
        formatted: 'THC: 24.5%',
        value: 24.5
      });
      expect(result.cbd).toBe(null);
    });

    it('should extract CBD percentage', () => {
      const result = scraper.extractPotencyFromText('CBD: 18.2%');
      expect(result.cbd).toEqual({
        formatted: 'CBD: 18.2%',
        value: 18.2
      });
      expect(result.thc).toBe(null);
    });

    it('should extract both THC and CBD', () => {
      const result = scraper.extractPotencyFromText('THC: 24.5% CBD: 0.3%');
      expect(result.thc.value).toBe(24.5);
      expect(result.cbd.value).toBe(0.3);
    });

    it('should handle lowercase', () => {
      const result = scraper.extractPotencyFromText('thc 20%');
      expect(result.thc.value).toBe(20);
    });

    it('should handle without percentage sign', () => {
      const result = scraper.extractPotencyFromText('THC 15.5');
      expect(result.thc.value).toBe(15.5);
    });

    it('should return null for no matches', () => {
      const result = scraper.extractPotencyFromText('No potency info');
      expect(result.thc).toBe(null);
      expect(result.cbd).toBe(null);
    });

    it('should handle null/undefined input', () => {
      expect(scraper.extractPotencyFromText(null)).toEqual({ thc: null, cbd: null });
      expect(scraper.extractPotencyFromText(undefined)).toEqual({ thc: null, cbd: null });
    });
  });

  describe('extractCategory()', () => {
    it('should classify flower', () => {
      expect(scraper.extractCategory('Purple Haze Flower')).toBe('Flower');
      expect(scraper.extractCategory('Premium Bud 3.5g')).toBe('Flower');
    });

    it('should classify edibles', () => {
      expect(scraper.extractCategory('THC Gummies 10mg')).toBe('Edibles');
      expect(scraper.extractCategory('Cannabis Edible Chocolate')).toBe('Edibles');
    });

    it('should classify vapes', () => {
      expect(scraper.extractCategory('Sour Diesel Vape Cart')).toBe('Vapes');
      expect(scraper.extractCategory('Cartridge 1g')).toBe('Vapes');
    });

    it('should classify concentrates', () => {
      expect(scraper.extractCategory('Live Resin Concentrate')).toBe('Concentrates');
      expect(scraper.extractCategory('Shatter 1g')).toBe('Concentrates');
      expect(scraper.extractCategory('Wax')).toBe('Concentrates');
    });

    it('should classify pre-rolls', () => {
      expect(scraper.extractCategory('OG Kush Pre-Roll')).toBe('Pre-Rolls');
      expect(scraper.extractCategory('Joint Pack')).toBe('Pre-Rolls');
    });

    it('should classify tinctures', () => {
      expect(scraper.extractCategory('CBD Tincture')).toBe('Tinctures');
      expect(scraper.extractCategory('THC Oil')).toBe('Tinctures');
    });

    it('should default to Other', () => {
      expect(scraper.extractCategory('Mystery Product')).toBe('Other');
    });

    it('should be case insensitive', () => {
      expect(scraper.extractCategory('FLOWER')).toBe('Flower');
      expect(scraper.extractCategory('VaPe')).toBe('Vapes');
    });
  });

  describe('extractJsonLd()', () => {
    it('should extract single product from JSON-LD', () => {
      const $ = cheerio.load(sampleHTML);
      const products = scraper.extractJsonLd($);
      
      expect(products).toHaveLength(1);
      expect(products[0].name).toBe('Purple Haze Premium Flower');
      expect(products[0].id).toBe('GTH-001');
      expect(products[0].price).toBe(45.00);
      expect(products[0].brand).toBe('Gotham Growers');
      expect(products[0].inStock).toBe(true);
    });

    it('should extract potency from JSON-LD description', () => {
      const $ = cheerio.load(sampleHTML);
      const products = scraper.extractJsonLd($);
      
      expect(products[0].thc).toBeDefined();
      expect(products[0].thc.value).toBe(24.5);
    });

    it('should handle invalid JSON gracefully', () => {
      const html = '<script type="application/ld+json">invalid json</script>';
      const $ = cheerio.load(html);
      const products = scraper.extractJsonLd($);
      
      expect(products).toHaveLength(0);
    });

    it('should handle missing JSON-LD', () => {
      const $ = cheerio.load('<html><body>No JSON-LD here</body></html>');
      const products = scraper.extractJsonLd($);
      
      expect(products).toHaveLength(0);
    });

    it('should extract from ItemList', () => {
      const html = `
        <script type="application/ld+json">
        {
          "@type": "ItemList",
          "itemListElement": [
            {
              "item": {
                "@type": "Product",
                "name": "Product 1",
                "sku": "P1",
                "offers": { "price": "10" }
              }
            },
            {
              "item": {
                "@type": "Product",
                "name": "Product 2",
                "sku": "P2",
                "offers": { "price": "20" }
              }
            }
          ]
        }
        </script>
      `;
      const $ = cheerio.load(html);
      const products = scraper.extractJsonLd($);
      
      expect(products).toHaveLength(2);
      expect(products[0].name).toBe('Product 1');
      expect(products[1].name).toBe('Product 2');
    });
  });

  describe('extractHtmlProducts()', () => {
    it('should extract products from HTML', () => {
      const $ = cheerio.load(sampleHTML);
      const products = scraper.extractHtmlProducts($);
      
      expect(products.length).toBeGreaterThan(0);
      
      const product = products.find(p => p.name?.includes('Purple Haze'));
      expect(product).toBeDefined();
      expect(product.price).toBe(45);
      expect(product.brand).toBe('Gotham Growers');
    });

    it('should extract stock status', () => {
      const $ = cheerio.load(sampleHTML);
      const products = scraper.extractHtmlProducts($);
      
      const inStock = products.find(p => p.name?.includes('Purple Haze'));
      expect(inStock?.inStock).toBe(true);
      
      const outOfStock = products.find(p => p.name?.includes('OG Kush'));
      expect(outOfStock?.inStock).toBe(false);
    });

    it('should handle missing products', () => {
      const $ = cheerio.load('<html><body>No products</body></html>');
      const products = scraper.extractHtmlProducts($);
      
      expect(products).toHaveLength(0);
    });

    it('should extract relative URLs correctly', () => {
      const $ = cheerio.load(sampleHTML);
      const products = scraper.extractHtmlProducts($);
      
      const product = products.find(p => p.url?.includes('/product/purple-haze'));
      expect(product).toBeDefined();
      expect(product.url).toContain('https://gotham.nyc');
    });
  });

  describe('normalizeJsonLdProduct()', () => {
    it('should normalize product with full data', () => {
      const data = {
        sku: 'TEST-001',
        name: 'Test Product',
        brand: { name: 'Test Brand' },
        category: 'Flower',
        description: 'THC: 20%',
        image: 'https://example.com/image.jpg',
        url: 'https://example.com/product',
        offers: {
          price: '50.00',
          priceCurrency: 'USD',
          availability: 'https://schema.org/InStock'
        }
      };
      
      const result = scraper.normalizeJsonLdProduct(data);
      
      expect(result.id).toBe('TEST-001');
      expect(result.name).toBe('Test Product');
      expect(result.brand).toBe('Test Brand');
      expect(result.price).toBe(50.00);
      expect(result.inStock).toBe(true);
      expect(result.thc.value).toBe(20);
    });

    it('should handle brand as string', () => {
      const data = {
        name: 'Test',
        brand: 'Simple Brand',
        offers: { price: '10' }
      };
      
      const result = scraper.normalizeJsonLdProduct(data);
      expect(result.brand).toBe('Simple Brand');
    });

    it('should handle out of stock', () => {
      const data = {
        name: 'Test',
        offers: {
          price: '10',
          availability: 'OutOfStock'
        }
      };
      
      const result = scraper.normalizeJsonLdProduct(data);
      expect(result.inStock).toBe(false);
    });

    it('should handle missing optional fields', () => {
      const data = {
        name: 'Minimal Product',
        offers: { price: '10' }
      };
      
      const result = scraper.normalizeJsonLdProduct(data);
      
      expect(result.name).toBe('Minimal Product');
      expect(result.price).toBe(10);
      expect(result.brand).toBeUndefined();
      expect(result.thc).toBe(null);
    });

    it('should extract category from name if not provided', () => {
      const data = {
        name: 'Purple Haze Flower',
        offers: { price: '10' }
      };
      
      const result = scraper.normalizeJsonLdProduct(data);
      expect(result.category).toBe('Flower');
    });
  });

  describe('checkAgeGate()', () => {
    it('should detect age verification keywords', () => {
      const html = '<html><body>Please verify your age. Are you 21 or older?</body></html>';
      expect(scraper.checkAgeGate(html)).toBe(true);
    });

    it('should detect "must be 21"', () => {
      const html = '<html><body>You must be 21 to enter</body></html>';
      expect(scraper.checkAgeGate(html)).toBe(true);
    });

    it('should detect "age gate"', () => {
      const html = '<html><body>Age gate verification required</body></html>';
      expect(scraper.checkAgeGate(html)).toBe(true);
    });

    it('should return false for normal content', () => {
      const html = '<html><body>Welcome to our store! Browse products.</body></html>';
      expect(scraper.checkAgeGate(html)).toBe(false);
    });

    it('should be case insensitive', () => {
      const html = '<html><body>AGE VERIFICATION REQUIRED</body></html>';
      expect(scraper.checkAgeGate(html)).toBe(true);
    });
  });

  describe('extractProducts()', () => {
    it('should extract and merge products from all strategies', () => {
      const products = scraper.extractProducts(sampleHTML, 'https://gotham.nyc/menu');
      
      expect(products.length).toBeGreaterThan(0);
      
      // Check metadata
      products.forEach(p => {
        expect(p.scrapedAt).toBeDefined();
        expect(p.source).toBe('gotham-nyc');
        expect(p.sourceUrl).toBe('https://gotham.nyc/menu');
      });
    });

    it('should add metadata to all products', () => {
      const products = scraper.extractProducts(sampleHTML, 'https://test.com');
      
      products.forEach(product => {
        expect(product.scrapedAt).toMatch(/^\d{4}-\d{2}-\d{2}T/);
        expect(product.source).toBe('gotham-nyc');
        expect(product.sourceUrl).toBe('https://test.com');
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle null HTML gracefully', () => {
      expect(() => scraper.extractProducts(null, 'url')).not.toThrow();
    });

    it('should handle empty HTML', () => {
      const products = scraper.extractProducts('', 'url');
      expect(products).toHaveLength(0);
    });

    it('should handle malformed HTML', () => {
      const html = '<div><p>Unclosed tags';
      const products = scraper.extractProducts(html, 'url');
      // Should not crash, may return empty array
      expect(Array.isArray(products)).toBe(true);
    });
  });

  describe('fetchPage() [integration-like]', () => {
    it('should have proper headers including age verification', () => {
      // Check that client is configured with age cookies
      const cookieHeader = scraper.client.defaults.headers.Cookie;
      expect(cookieHeader).toContain('age_verified=1');
      expect(cookieHeader).toContain('age_gate_passed=true');
    });

    it('should have timeout configured', () => {
      expect(scraper.client.defaults.timeout).toBe(30000);
    });

    it('should have user agent', () => {
      const userAgent = scraper.client.defaults.headers['User-Agent'];
      expect(userAgent).toBeDefined();
      expect(userAgent).toContain('Mozilla');
    });
  });
});
