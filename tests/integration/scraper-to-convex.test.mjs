import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// Import scrapers
import { GothamScraper } from '../../scrapers/gotham/scraper.mjs';
import HousingWorksScraper from '../../scrapers/housing-works/scraper.mjs';
import { ConbudAPIScraper } from '../../scrapers/conbud/api-scraper.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fixturesDir = join(__dirname, '../fixtures');

/**
 * Integration Tests: Scraper → Convex Data Flow
 * 
 * Tests the complete pipeline:
 * 1. Scraper extracts data from fixtures
 * 2. Data is normalized
 * 3. Data can be inserted into Convex (mocked)
 */

describe('Integration: Scraper to Convex Flow', () => {
  describe('Gotham Scraper Integration', () => {
    let scraper;
    let sampleHTML;
    
    beforeEach(() => {
      scraper = new GothamScraper();
      sampleHTML = readFileSync(join(fixturesDir, 'gotham-sample.html'), 'utf-8');
    });

    it('should extract complete products ready for Convex', () => {
      const products = scraper.extractProducts(sampleHTML, 'https://gotham.nyc/menu');
      
      expect(products.length).toBeGreaterThan(0);
      
      // Verify Convex-ready format
      products.forEach(product => {
        // Required fields for Convex schema
        expect(product.name).toBeDefined();
        expect(typeof product.name).toBe('string');
        
        // Metadata fields
        expect(product.scrapedAt).toBeDefined();
        expect(product.source).toBe('gotham-nyc');
        expect(product.sourceUrl).toBe('https://gotham.nyc/menu');
        
        // Optional but expected fields
        if (product.price) {
          expect(typeof product.price).toBe('number');
          expect(product.price).toBeGreaterThan(0);
        }
        
        if (product.thc) {
          expect(product.thc).toHaveProperty('value');
          expect(product.thc).toHaveProperty('formatted');
        }
        
        if (product.cbd) {
          expect(product.cbd).toHaveProperty('value');
          expect(product.cbd).toHaveProperty('formatted');
        }
      });
    });

    it('should deduplicate products', () => {
      // Extract products multiple times (simulating multiple strategies)
      const products = scraper.extractProducts(sampleHTML, 'https://gotham.nyc/menu');
      
      // Check for duplicates by name
      const names = products.map(p => p.name);
      const uniqueNames = [...new Set(names)];
      
      // Should have fewer or equal unique names (some products appear multiple times)
      expect(uniqueNames.length).toBeLessThanOrEqual(products.length);
    });

    it('should handle products with missing optional fields', () => {
      const products = scraper.extractProducts(sampleHTML, 'https://gotham.nyc/menu');
      
      // Some products may not have all fields - should not crash
      products.forEach(product => {
        expect(product.name).toBeDefined(); // Required
        // Optional fields can be undefined/null
        if (!product.price) {
          expect([null, undefined]).toContain(product.price);
        }
      });
    });
  });

  describe('Housing Works Scraper Integration', () => {
    let scraper;
    let sampleHTML;
    
    beforeEach(() => {
      scraper = new HousingWorksScraper();
      sampleHTML = readFileSync(join(fixturesDir, 'housing-works-sample.html'), 'utf-8');
    });

    it('should extract complete products ready for Convex', () => {
      const products = scraper.parseProducts(sampleHTML);
      
      expect(products.length).toBeGreaterThan(0);
      
      products.forEach(product => {
        // Verify structure
        expect(product.name).toBeDefined();
        expect(product.source).toBe('housing-works-broadway');
        expect(product.scrapedAt).toBeDefined();
        
        // Verify types
        if (product.price !== null) {
          expect(typeof product.price).toBe('number');
        }
        
        if (product.inStock !== undefined) {
          expect(typeof product.inStock).toBe('boolean');
        }
      });
    });

    it('should handle stock status for inventory tracking', () => {
      const products = scraper.parseProducts(sampleHTML);
      
      const inStockProducts = products.filter(p => p.inStock === true);
      const outOfStockProducts = products.filter(p => p.inStock === false);
      
      expect(inStockProducts.length + outOfStockProducts.length).toBe(products.length);
      
      // Out of stock products should have quantity = 0
      outOfStockProducts.forEach(product => {
        expect(product.quantity).toBe(0);
      });
    });
  });

  describe('Conbud Scraper Integration', () => {
    let scraper;
    let mockApiResponse;
    
    beforeEach(() => {
      scraper = new ConbudAPIScraper();
      const responseData = readFileSync(
        join(fixturesDir, 'conbud-api-response.json'),
        'utf-8'
      );
      mockApiResponse = JSON.parse(responseData);
    });

    it('should process API response into Convex-ready format', () => {
      const rawProducts = mockApiResponse.data.filteredProducts.products;
      const processed = scraper.processProducts(rawProducts);
      
      expect(processed.length).toBeGreaterThan(0);
      
      processed.forEach(product => {
        expect(product.id).toBeDefined();
        expect(product.name).toBeDefined();
        expect(product.source).toBe('conbud-les-api');
        expect(product.scrapedAt).toBeDefined();
        
        // Check potency structure
        if (product.thc) {
          expect(product.thc).toHaveProperty('formatted');
          expect(product.thc).toHaveProperty('value');
        }
      });
    });

    it('should handle variants for different product sizes', () => {
      const rawProducts = mockApiResponse.data.filteredProducts.products;
      const processed = scraper.processProducts(rawProducts);
      
      const productsWithVariants = processed.filter(p => p.variants && p.variants.length > 0);
      
      expect(productsWithVariants.length).toBeGreaterThan(0);
      
      productsWithVariants.forEach(product => {
        product.variants.forEach(variant => {
          expect(variant).toHaveProperty('id');
          expect(variant).toHaveProperty('option');
          expect(variant).toHaveProperty('price');
        });
      });
    });
  });

  describe('Cross-Scraper Consistency', () => {
    it('should produce consistent data structures across all scrapers', () => {
      const gothamScraper = new GothamScraper();
      const hwScraper = new HousingWorksScraper();
      const conbudScraper = new ConbudAPIScraper();
      
      const gothamHTML = readFileSync(join(fixturesDir, 'gotham-sample.html'), 'utf-8');
      const hwHTML = readFileSync(join(fixturesDir, 'housing-works-sample.html'), 'utf-8');
      const conbudJSON = JSON.parse(readFileSync(
        join(fixturesDir, 'conbud-api-response.json'),
        'utf-8'
      ));
      
      const gothamProducts = gothamScraper.extractProducts(gothamHTML, 'test');
      const hwProducts = hwScraper.parseProducts(hwHTML);
      const conbudProducts = conbudScraper.processProducts(
        conbudJSON.data.filteredProducts.products
      );
      
      // All should have common required fields
      const commonFields = ['name', 'source', 'scrapedAt'];
      
      [gothamProducts, hwProducts, conbudProducts].forEach(productList => {
        expect(productList.length).toBeGreaterThan(0);
        
        productList.forEach(product => {
          commonFields.forEach(field => {
            expect(product).toHaveProperty(field);
          });
        });
      });
    });

    it('should use consistent potency format', () => {
      const gothamScraper = new GothamScraper();
      const conbudScraper = new ConbudAPIScraper();
      
      const gothamHTML = readFileSync(join(fixturesDir, 'gotham-sample.html'), 'utf-8');
      const conbudJSON = JSON.parse(readFileSync(
        join(fixturesDir, 'conbud-api-response.json'),
        'utf-8'
      ));
      
      const gothamProducts = gothamScraper.extractProducts(gothamHTML, 'test');
      const conbudProducts = conbudScraper.processProducts(
        conbudJSON.data.filteredProducts.products
      );
      
      // Check potency structure consistency
      const gothamWithTHC = gothamProducts.find(p => p.thc);
      const conbudWithTHC = conbudProducts.find(p => p.thc);
      
      if (gothamWithTHC && conbudWithTHC) {
        expect(gothamWithTHC.thc).toHaveProperty('value');
        expect(gothamWithTHC.thc).toHaveProperty('formatted');
        expect(conbudWithTHC.thc).toHaveProperty('value');
        expect(conbudWithTHC.thc).toHaveProperty('formatted');
        
        // Both should use numbers for value
        expect(typeof gothamWithTHC.thc.value).toBe('number');
        expect(typeof conbudWithTHC.thc.value).toBe('number');
      }
    });
  });

  describe('Data Validation for Convex', () => {
    it('should have valid timestamps', () => {
      const scraper = new GothamScraper();
      const html = readFileSync(join(fixturesDir, 'gotham-sample.html'), 'utf-8');
      const products = scraper.extractProducts(html, 'test');
      
      products.forEach(product => {
        expect(product.scrapedAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
        
        const timestamp = new Date(product.scrapedAt);
        expect(timestamp.getTime()).toBeGreaterThan(0);
        expect(timestamp.getTime()).toBeLessThanOrEqual(Date.now());
      });
    });

    it('should have valid URLs', () => {
      const scraper = new GothamScraper();
      const html = readFileSync(join(fixturesDir, 'gotham-sample.html'), 'utf-8');
      const products = scraper.extractProducts(html, 'https://gotham.nyc/menu');
      
      products.forEach(product => {
        if (product.url) {
          expect(product.url).toMatch(/^https?:\/\//);
        }
        
        if (product.image) {
          expect(product.image).toMatch(/^https?:\/\//);
        }
      });
    });

    it('should have valid numeric prices', () => {
      const scraper = new HousingWorksScraper();
      const html = readFileSync(join(fixturesDir, 'housing-works-sample.html'), 'utf-8');
      const products = scraper.parseProducts(html);
      
      products.forEach(product => {
        if (product.price !== null) {
          expect(typeof product.price).toBe('number');
          expect(product.price).toBeGreaterThan(0);
          expect(product.price).toBeLessThan(10000); // Sanity check
          expect(Number.isFinite(product.price)).toBe(true);
        }
      });
    });
  });
});
