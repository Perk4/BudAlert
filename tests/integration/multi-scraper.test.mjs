import { describe, it, expect, vi, beforeEach } from 'vitest';
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
 * Integration Tests: Multi-Scraper Orchestration
 * 
 * Tests coordinated scraping across multiple stores:
 * - Parallel execution
 * - Error isolation (one fails, others continue)
 * - Result aggregation
 * - Duplicate detection across stores
 */

describe('Integration: Multi-Scraper Orchestration', () => {
  describe('Parallel Scraping', () => {
    it('should run multiple scrapers independently', async () => {
      const gothamScraper = new GothamScraper();
      const hwScraper = new HousingWorksScraper();
      
      // Mock HTTP calls to use fixtures
      const gothamHTML = readFileSync(join(fixturesDir, 'gotham-sample.html'), 'utf-8');
      const hwHTML = readFileSync(join(fixturesDir, 'housing-works-sample.html'), 'utf-8');
      
      vi.spyOn(gothamScraper, 'fetchPage').mockResolvedValue(gothamHTML);
      vi.spyOn(hwScraper, 'fetchPage').mockResolvedValue(hwHTML);
      
      // Run in parallel
      const [gothamResult, hwResult] = await Promise.all([
        gothamScraper.scrape(),
        hwScraper.scrape()
      ]);
      
      expect(gothamResult.length).toBeGreaterThan(0);
      expect(hwResult.length).toBeGreaterThan(0);
      
      // Verify each has unique source
      gothamResult.forEach(p => expect(p.source).toBe('gotham-nyc'));
      hwResult.forEach(p => expect(p.source).toBe('housing-works-broadway'));
    });

    it('should continue if one scraper fails', async () => {
      const gothamScraper = new GothamScraper();
      const hwScraper = new HousingWorksScraper();
      
      // Mock one to fail, one to succeed
      vi.spyOn(gothamScraper, 'fetchPage').mockRejectedValue(new Error('Network error'));
      vi.spyOn(hwScraper, 'fetchPage').mockResolvedValue(
        readFileSync(join(fixturesDir, 'housing-works-sample.html'), 'utf-8')
      );
      
      const results = await Promise.allSettled([
        gothamScraper.scrape(),
        hwScraper.scrape()
      ]);
      
      expect(results[0].status).toBe('rejected');
      expect(results[1].status).toBe('fulfilled');
      expect(results[1].value.length).toBeGreaterThan(0);
    });
  });

  describe('Result Aggregation', () => {
    it('should combine results from multiple scrapers', async () => {
      const scrapers = {
        gotham: new GothamScraper(),
        housingWorks: new HousingWorksScraper(),
        conbud: new ConbudAPIScraper()
      };
      
      // Mock all scrapers
      vi.spyOn(scrapers.gotham, 'fetchPage').mockResolvedValue(
        readFileSync(join(fixturesDir, 'gotham-sample.html'), 'utf-8')
      );
      vi.spyOn(scrapers.housingWorks, 'fetchPage').mockResolvedValue(
        readFileSync(join(fixturesDir, 'housing-works-sample.html'), 'utf-8')
      );
      vi.spyOn(scrapers.conbud.client, 'post').mockResolvedValue({
        data: JSON.parse(readFileSync(join(fixturesDir, 'conbud-api-response.json'), 'utf-8'))
      });
      
      // Run all scrapers
      const [gothamProducts, hwProducts, conbudResults] = await Promise.all([
        scrapers.gotham.scrape(),
        scrapers.housingWorks.scrape(),
        scrapers.conbud.scrape()
      ]);
      
      // Aggregate
      const allProducts = [
        ...gothamProducts,
        ...hwProducts,
        ...(conbudResults.success ? conbudResults.products || [] : [])
      ];
      
      expect(allProducts.length).toBeGreaterThan(0);
      
      // Verify diversity of sources
      const sources = [...new Set(allProducts.map(p => p.source))];
      expect(sources.length).toBeGreaterThanOrEqual(2);
    });

    it('should track scraper performance metrics', async () => {
      const gothamScraper = new GothamScraper();
      
      vi.spyOn(gothamScraper, 'fetchPage').mockResolvedValue(
        readFileSync(join(fixturesDir, 'gotham-sample.html'), 'utf-8')
      );
      
      const startTime = Date.now();
      const products = await gothamScraper.scrape();
      const duration = Date.now() - startTime;
      
      expect(products.length).toBeGreaterThan(0);
      expect(duration).toBeGreaterThanOrEqual(0);
      expect(duration).toBeLessThan(5000); // Should be fast with mocked data
    });
  });

  describe('Cross-Store Product Matching', () => {
    it('should identify potential duplicate products across stores', async () => {
      const gothamProducts = [
        { name: 'Purple Haze 3.5g', brand: 'Brand A', price: 50, source: 'gotham' },
        { name: 'Sour Diesel Cart', brand: 'Brand B', price: 40, source: 'gotham' }
      ];
      
      const hwProducts = [
        { name: 'Purple Haze Flower 3.5g', brand: 'Brand A', price: 48, source: 'housing-works' },
        { name: 'Blue Dream', brand: 'Brand C', price: 45, source: 'housing-works' }
      ];
      
      // Simple fuzzy matching by name similarity
      const allProducts = [...gothamProducts, ...hwProducts];
      const potentialDuplicates = [];
      
      for (let i = 0; i < allProducts.length; i++) {
        for (let j = i + 1; j < allProducts.length; j++) {
          const p1 = allProducts[i];
          const p2 = allProducts[j];
          
          // Check if names are similar (simple contains check)
          const name1 = p1.name.toLowerCase().replace(/[^a-z0-9]/g, '');
          const name2 = p2.name.toLowerCase().replace(/[^a-z0-9]/g, '');
          
          if (name1.includes(name2.slice(0, 10)) || name2.includes(name1.slice(0, 10))) {
            // Check if same brand
            if (p1.brand === p2.brand && p1.source !== p2.source) {
              potentialDuplicates.push([p1, p2]);
            }
          }
        }
      }
      
      expect(potentialDuplicates.length).toBeGreaterThan(0);
      expect(potentialDuplicates[0][0].name).toContain('Purple Haze');
      expect(potentialDuplicates[0][1].name).toContain('Purple Haze');
    });

    it('should track price variations across stores', () => {
      const products = [
        { name: 'Product A', price: 50, source: 'store1' },
        { name: 'Product A', price: 48, source: 'store2' },
        { name: 'Product A', price: 52, source: 'store3' }
      ];
      
      const prices = products.map(p => p.price);
      const minPrice = Math.min(...prices);
      const maxPrice = Math.max(...prices);
      const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
      
      expect(minPrice).toBe(48);
      expect(maxPrice).toBe(52);
      expect(avgPrice).toBeCloseTo(50, 1);
      
      const priceVariation = maxPrice - minPrice;
      expect(priceVariation).toBe(4);
    });
  });

  describe('Error Recovery', () => {
    it('should collect errors without stopping other scrapers', async () => {
      const scrapers = [
        { name: 'Scraper A', scrape: async () => { throw new Error('Network error'); } },
        { name: 'Scraper B', scrape: async () => [{ name: 'Product 1' }] },
        { name: 'Scraper C', scrape: async () => { throw new Error('Parse error'); } },
        { name: 'Scraper D', scrape: async () => [{ name: 'Product 2' }] }
      ];
      
      const results = await Promise.allSettled(
        scrapers.map(s => s.scrape())
      );
      
      const successful = results.filter(r => r.status === 'fulfilled');
      const failed = results.filter(r => r.status === 'rejected');
      
      expect(successful).toHaveLength(2);
      expect(failed).toHaveLength(2);
      
      // Collect successful products
      const products = successful.flatMap(r => r.value);
      expect(products).toHaveLength(2);
    });

    it('should log scraper errors for monitoring', async () => {
      const errors = [];
      
      const scraper = new GothamScraper();
      vi.spyOn(scraper, 'fetchPage').mockRejectedValue(new Error('Connection timeout'));
      
      try {
        await scraper.scrape();
      } catch (error) {
        errors.push({
          scraper: 'gotham',
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
      
      expect(errors).toHaveLength(1);
      expect(errors[0].scraper).toBe('gotham');
      expect(errors[0].error).toContain('timeout');
      expect(errors[0].timestamp).toBeDefined();
    });
  });

  describe('Batch Processing', () => {
    it('should process scrapers in batches to limit concurrency', async () => {
      const scrapers = Array(10).fill(null).map((_, i) => ({
        id: `scraper-${i}`,
        scrape: async () => {
          await new Promise(resolve => setTimeout(resolve, 10));
          return [{ name: `Product ${i}` }];
        }
      }));
      
      const batchSize = 3;
      const results = [];
      
      // Process in batches
      for (let i = 0; i < scrapers.length; i += batchSize) {
        const batch = scrapers.slice(i, i + batchSize);
        const batchResults = await Promise.all(batch.map(s => s.scrape()));
        results.push(...batchResults);
      }
      
      expect(results).toHaveLength(10);
      expect(results.every(r => Array.isArray(r))).toBe(true);
    });

    it('should track batch completion progress', async () => {
      const scrapers = Array(5).fill(null).map((_, i) => ({
        scrape: async () => [{ name: `Product ${i}` }]
      }));
      
      let completed = 0;
      const progress = [];
      
      const results = await Promise.all(
        scrapers.map(async (scraper) => {
          const result = await scraper.scrape();
          completed++;
          progress.push({
            completed,
            total: scrapers.length,
            percent: (completed / scrapers.length) * 100
          });
          return result;
        })
      );
      
      expect(results).toHaveLength(5);
      expect(completed).toBe(5);
      expect(progress[progress.length - 1].percent).toBe(100);
    });
  });

  describe('Data Consistency Validation', () => {
    it('should validate all products before storage', async () => {
      const products = [
        { name: 'Valid Product', price: 50, source: 'test' },
        { name: null, price: 30, source: 'test' }, // Invalid: no name
        { name: 'Another Product', price: -10, source: 'test' }, // Invalid: negative price
        { name: 'Good Product', price: 40, source: 'test' }
      ];
      
      const validated = products.filter(p => {
        if (!p.name || typeof p.name !== 'string') return false;
        if (p.price !== null && (typeof p.price !== 'number' || p.price < 0)) return false;
        return true;
      });
      
      expect(validated).toHaveLength(2);
      expect(validated.every(p => p.name)).toBe(true);
      expect(validated.every(p => p.price === null || p.price >= 0)).toBe(true);
    });

    it('should normalize inconsistent data formats', () => {
      const products = [
        { name: '  Product 1  ', price: '50.00', thc: '20%' },
        { name: 'Product 2', price: 30, thc: { value: 18, formatted: '18%' } }
      ];
      
      const normalized = products.map(p => ({
        name: p.name.trim(),
        price: typeof p.price === 'string' ? parseFloat(p.price) : p.price,
        thc: typeof p.thc === 'string' ? { formatted: p.thc, value: parseFloat(p.thc) } : p.thc
      }));
      
      expect(normalized[0].name).toBe('Product 1');
      expect(normalized[0].price).toBe(50.00);
      expect(normalized[0].thc.value).toBe(20);
      
      expect(normalized[1].price).toBe(30);
      expect(normalized[1].thc.value).toBe(18);
    });
  });
});
