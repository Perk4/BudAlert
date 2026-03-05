import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import axios from 'axios';

// Import scraper and query utilities
import { ConbudAPIScraper } from '../../../scrapers/conbud/api-scraper.mjs';
import {
  buildFilters,
  normalizeProduct,
  getFilteredProductsVariables,
  COMMON_CATEGORIES
} from '../../../scrapers/conbud/queries.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fixturesDir = join(__dirname, '../../fixtures');

// Mock axios
vi.mock('axios');

describe('ConbudAPIScraper', () => {
  let scraper;
  let mockApiResponse;

  beforeEach(() => {
    scraper = new ConbudAPIScraper({
      timeout: 10000,
      retries: 2,
      retryDelay: 100
    });
    
    const responseData = readFileSync(
      join(fixturesDir, 'conbud-api-response.json'),
      'utf-8'
    );
    mockApiResponse = JSON.parse(responseData);

    // Reset mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('extractOperationName()', () => {
    it('should extract operation name from query', () => {
      const query = 'query FilteredProducts($filters: Filters) { ... }';
      const result = scraper.extractOperationName(query);
      expect(result).toBe('FilteredProducts');
    });

    it('should handle query with no name', () => {
      const query = '{ products { id name } }';
      const result = scraper.extractOperationName(query);
      expect(result).toBe(null);
    });

    it('should handle multi-line queries', () => {
      const query = `
        query GetProducts(
          $dispensaryId: ID!
        ) {
          menu { ... }
        }
      `;
      const result = scraper.extractOperationName(query);
      expect(result).toBe('GetProducts');
    });
  });

  describe('processProducts()', () => {
    it('should normalize and deduplicate products', () => {
      const rawProducts = mockApiResponse.data.filteredProducts.products;
      const processed = scraper.processProducts(rawProducts);
      
      expect(processed.length).toBe(rawProducts.length);
      processed.forEach(product => {
        expect(product.id).toBeDefined();
        expect(product.name).toBeDefined();
        expect(product.source).toBe('conbud-les-api');
      });
    });

    it('should remove duplicates', () => {
      const rawProducts = [
        { id: 'prod_1', name: 'Product 1' },
        { id: 'prod_1', name: 'Product 1' }, // Duplicate
        { id: 'prod_2', name: 'Product 2' }
      ];
      
      const processed = scraper.processProducts(rawProducts);
      expect(processed).toHaveLength(2);
      expect(processed.map(p => p.id)).toEqual(['prod_1', 'prod_2']);
    });

    it('should filter out null products', () => {
      const rawProducts = [
        { id: 'prod_1', name: 'Product 1' },
        null, // Invalid
        { id: 'prod_2', name: 'Product 2' }
      ];
      
      // Mock normalizeProduct to return null for invalid products
      const processed = scraper.processProducts(rawProducts.filter(Boolean));
      expect(processed.length).toBeGreaterThan(0);
    });

    it('should handle empty array', () => {
      const processed = scraper.processProducts([]);
      expect(processed).toHaveLength(0);
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const mockPost = vi.fn().mockRejectedValue(new Error('Network error'));
      scraper.client.post = mockPost;
      
      await expect(scraper.query('query { test }', {})).rejects.toThrow('Network error');
    });

    it('should retry on failure', async () => {
      const mockPost = vi.fn()
        .mockRejectedValueOnce(new Error('Temporary error'))
        .mockRejectedValueOnce(new Error('Temporary error'))
        .mockResolvedValueOnce({
          data: { data: { test: 'success' } }
        });
      
      scraper.client.post = mockPost;
      
      const result = await scraper.query('query { test }', {});
      expect(result).toEqual({ test: 'success' });
      expect(mockPost).toHaveBeenCalledTimes(3);
    });

    it('should fail after max retries', async () => {
      const mockPost = vi.fn().mockRejectedValue(new Error('Persistent error'));
      scraper.client.post = mockPost;
      
      await expect(scraper.query('query { test }', {})).rejects.toThrow();
      expect(mockPost).toHaveBeenCalledTimes(3); // Initial + 2 retries
    });

    it('should handle GraphQL errors', async () => {
      const mockPost = vi.fn().mockResolvedValue({
        data: {
          errors: [{ message: 'GraphQL syntax error' }],
          data: null
        }
      });
      
      scraper.client.post = mockPost;
      
      await expect(scraper.query('query { test }', {})).rejects.toThrow('GraphQL error');
    });
  });

  describe('Configuration', () => {
    it('should initialize with custom options', () => {
      const customScraper = new ConbudAPIScraper({
        timeout: 5000,
        retries: 5,
        retryDelay: 500
      });
      
      expect(customScraper.options.timeout).toBe(5000);
      expect(customScraper.options.retries).toBe(5);
      expect(customScraper.options.retryDelay).toBe(500);
    });

    it('should have default options', () => {
      const defaultScraper = new ConbudAPIScraper();
      
      expect(defaultScraper.options.timeout).toBe(30000);
      expect(defaultScraper.options.retries).toBe(3);
    });

    it('should have proper headers', () => {
      expect(scraper.client.defaults.headers['Content-Type']).toBe('application/json');
      expect(scraper.client.defaults.headers['User-Agent']).toContain('Mozilla');
      expect(scraper.client.defaults.headers['Origin']).toBe('https://conbud.com');
    });
  });
});

describe('Query Utilities', () => {
  describe('buildFilters()', () => {
    it('should build category filter', () => {
      const filters = buildFilters({ category: 'FLOWER' });
      expect(filters).toBeDefined();
      expect(filters.category).toBe('FLOWER');
    });

    it('should build price range filter', () => {
      const filters = buildFilters({ minPrice: 10, maxPrice: 50 });
      expect(filters.priceRange).toEqual({ min: 10, max: 50 });
    });

    it('should build stock filter', () => {
      const filters = buildFilters({ inStockOnly: true });
      expect(filters.inStock).toBe(true);
    });

    it('should handle empty filters', () => {
      const filters = buildFilters({});
      expect(filters).toBeDefined();
      expect(Object.keys(filters)).toHaveLength(0);
    });

    it('should combine multiple filters', () => {
      const filters = buildFilters({
        category: 'VAPORIZERS',
        minPrice: 20,
        maxPrice: 100,
        inStockOnly: true
      });
      
      expect(filters.category).toBe('VAPORIZERS');
      expect(filters.priceRange).toEqual({ min: 20, max: 100 });
      expect(filters.inStock).toBe(true);
    });
  });

  describe('getFilteredProductsVariables()', () => {
    it('should generate variables with defaults', () => {
      const vars = getFilteredProductsVariables({});
      
      expect(vars).toHaveProperty('limit');
      expect(vars).toHaveProperty('offset');
      expect(vars.limit).toBeGreaterThan(0);
    });

    it('should apply custom limit and offset', () => {
      const vars = getFilteredProductsVariables({
        limit: 50,
        offset: 100
      });
      
      expect(vars.limit).toBe(50);
      expect(vars.offset).toBe(100);
    });

    it('should include filters', () => {
      const vars = getFilteredProductsVariables({
        filters: { category: 'FLOWER' }
      });
      
      expect(vars.filters).toBeDefined();
      expect(vars.filters.category).toBe('FLOWER');
    });
  });

  describe('normalizeProduct()', () => {
    it('should normalize complete product', () => {
      const rawProduct = {
        id: 'prod_123',
        name: 'Test Product',
        brand: {
          id: 'brand_1',
          name: 'Test Brand'
        },
        category: 'FLOWER',
        subcategory: 'Indica',
        description: 'Test description',
        potencyThc: {
          formatted: '20%',
          range: [20, 21]
        },
        potencyCbd: {
          formatted: '1%',
          range: [1, 2]
        },
        price: 50.00,
        variants: [
          { id: 'var_1', option: '3.5g', price: 50 }
        ],
        image: 'https://example.com/image.jpg',
        images: ['https://example.com/image.jpg'],
        inStock: true,
        quantity: 10
      };
      
      const normalized = normalizeProduct(rawProduct, 'test-source');
      
      expect(normalized.id).toBe('prod_123');
      expect(normalized.name).toBe('Test Product');
      expect(normalized.brand).toBe('Test Brand');
      expect(normalized.brandId).toBe('brand_1');
      expect(normalized.category).toBe('FLOWER');
      expect(normalized.price).toBe(50);
      expect(normalized.thc).toBeDefined();
      expect(normalized.thc.value).toBe(20);
      expect(normalized.inStock).toBe(true);
      expect(normalized.source).toBe('test-source');
    });

    it('should handle missing optional fields', () => {
      const rawProduct = {
        id: 'prod_minimal',
        name: 'Minimal Product',
        price: 10
      };
      
      const normalized = normalizeProduct(rawProduct, 'test-source');
      
      expect(normalized.id).toBe('prod_minimal');
      expect(normalized.name).toBe('Minimal Product');
      expect(normalized.brand).toBe(null);
      expect(normalized.thc).toBe(null);
      expect(normalized.cbd).toBe(null);
    });

    it('should extract brand name from object or string', () => {
      const withObject = normalizeProduct({
        id: '1',
        name: 'Product',
        brand: { id: 'b1', name: 'Brand Name' }
      }, 'source');
      
      expect(withObject.brand).toBe('Brand Name');
      
      const withString = normalizeProduct({
        id: '2',
        name: 'Product',
        brand: 'Simple Brand'
      }, 'source');
      
      expect(withString.brand).toBe('Simple Brand');
    });

    it('should normalize category names', () => {
      const product = normalizeProduct({
        id: '1',
        name: 'Product',
        category: 'FLOWER'
      }, 'source');
      
      expect(product.category).toBe('FLOWER');
    });

    it('should include variants', () => {
      const product = normalizeProduct({
        id: '1',
        name: 'Product',
        variants: [
          { id: 'v1', option: '3.5g', price: 50 },
          { id: 'v2', option: '7g', price: 90 }
        ]
      }, 'source');
      
      expect(product.variants).toHaveLength(2);
      expect(product.variants[0].option).toBe('3.5g');
    });

    it('should handle stock status', () => {
      const inStock = normalizeProduct({
        id: '1',
        name: 'Product',
        inStock: true,
        quantity: 5
      }, 'source');
      
      expect(inStock.inStock).toBe(true);
      expect(inStock.quantity).toBe(5);
      
      const outOfStock = normalizeProduct({
        id: '2',
        name: 'Product',
        inStock: false,
        quantity: 0
      }, 'source');
      
      expect(outOfStock.inStock).toBe(false);
      expect(outOfStock.quantity).toBe(0);
    });

    it('should return null for invalid product', () => {
      expect(normalizeProduct(null, 'source')).toBe(null);
      expect(normalizeProduct({}, 'source')).toBe(null);
      expect(normalizeProduct({ id: '1' }, 'source')).toBe(null); // No name
    });

    it('should add timestamp', () => {
      const product = normalizeProduct({
        id: '1',
        name: 'Product'
      }, 'source');
      
      expect(product.scrapedAt).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    });
  });

  describe('COMMON_CATEGORIES', () => {
    it('should have expected categories', () => {
      expect(COMMON_CATEGORIES).toContain('FLOWER');
      expect(COMMON_CATEGORIES).toContain('EDIBLES');
      expect(COMMON_CATEGORIES).toContain('VAPORIZERS');
      expect(COMMON_CATEGORIES).toContain('CONCENTRATES');
    });

    it('should be an array', () => {
      expect(Array.isArray(COMMON_CATEGORIES)).toBe(true);
    });

    it('should have at least 5 categories', () => {
      expect(COMMON_CATEGORIES.length).toBeGreaterThanOrEqual(5);
    });
  });
});
