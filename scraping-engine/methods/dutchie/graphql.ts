/**
 * Dutchie GraphQL Method
 * Direct GraphQL API approach - fast and lightweight
 * 
 * Based on ~/clawd/budalert/scrapers/conbud/api-scraper.mjs
 */

import axios, { AxiosInstance } from 'axios';
import {
  ScrapingMethod,
  ScrapeConfig,
  ScrapeResult,
  Product,
  calculateFieldCompleteness,
  sleep,
} from '../base.js';

interface DutchieConfig extends ScrapeConfig {
  apiUrl?: string;
  dispensaryId?: string;
}

export class DutchieGraphQLMethod implements ScrapingMethod {
  name = 'dutchie-graphql';
  provider = 'dutchie';
  type = 'api' as const;
  
  requirements = {
    chromium: false,
    proxy: false,
    cookies: true,
    javascript: false,
  };
  
  private client: AxiosInstance | null = null;
  
  /**
   * Initialize axios client
   */
  private initClient(config: DutchieConfig): AxiosInstance {
    const apiUrl = config.apiUrl || 'https://api.dutchie.com/graphql';
    
    return axios.create({
      baseURL: apiUrl,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': new URL(config.url).origin,
        'Referer': config.url,
      },
    });
  }
  
  /**
   * Make GraphQL query with retry logic
   */
  private async query(query: string, variables: any, retries = 3): Promise<any> {
    if (!this.client) {
      throw new Error('Client not initialized');
    }
    
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const response = await this.client.post('', {
          query,
          variables,
          operationName: this.extractOperationName(query),
        });
        
        if (response.data.errors) {
          throw new Error(`GraphQL error: ${response.data.errors[0]?.message}`);
        }
        
        return response.data.data;
      } catch (error: any) {
        if (attempt === retries - 1) throw error;
        await sleep(2000 * (attempt + 1));
      }
    }
  }
  
  /**
   * Extract operation name from query
   */
  private extractOperationName(query: string): string | null {
    const match = query.match(/query\s+(\w+)/);
    return match ? match[1] : null;
  }
  
  /**
   * Build filtered products query
   */
  private getFilteredProductsQuery(): string {
    return `
      query FilteredProducts($dispensaryId: ID!, $limit: Int, $offset: Int) {
        filteredProducts(
          dispensaryId: $dispensaryId
          limit: $limit
          offset: $offset
        ) {
          products {
            id
            name
            brand {
              name
              id
            }
            category
            variants {
              id
              priceMed
              priceRec
              option
            }
            potencyCbd {
              formatted
              range
            }
            potencyThc {
              formatted
              range
            }
            image
            description
            effects
          }
        }
      }
    `;
  }
  
  /**
   * Normalize Dutchie product to standard format
   */
  private normalizeProduct(raw: any, sourceUrl: string): Product {
    const variant = raw.variants?.[0];
    const price = variant?.priceRec || variant?.priceMed || null;
    
    return {
      id: raw.id,
      name: raw.name,
      price,
      priceRaw: price ? `$${price}` : null,
      brand: raw.brand?.name || null,
      category: raw.category || null,
      weight: variant?.option || null,
      thc: raw.potencyThc?.formatted
        ? {
            formatted: raw.potencyThc.formatted,
            value: parseFloat(raw.potencyThc.formatted) || 0,
          }
        : null,
      cbd: raw.potencyCbd?.formatted
        ? {
            formatted: raw.potencyCbd.formatted,
            value: parseFloat(raw.potencyCbd.formatted) || 0,
          }
        : null,
      inStock: true, // Dutchie API only returns in-stock products
      quantity: null,
      url: sourceUrl,
      imageUrl: raw.image || null,
      description: raw.description || null,
      metadata: {
        effects: raw.effects || [],
        variants: raw.variants || [],
      },
    };
  }
  
  /**
   * Main scrape function
   */
  async scrape(config: DutchieConfig): Promise<ScrapeResult> {
    const startTime = Date.now();
    const errors: string[] = [];
    let products: Product[] = [];
    
    try {
      this.client = this.initClient(config);
      
      // Extract dispensary ID from config or URL
      const dispensaryId = config.dispensaryId || this.extractDispensaryId(config.url);
      if (!dispensaryId) {
        throw new Error('Could not extract dispensaryId from URL');
      }
      
      // Fetch products
      const query = this.getFilteredProductsQuery();
      const variables = {
        dispensaryId,
        limit: 1000,
        offset: 0,
      };
      
      const data = await this.query(query, variables);
      
      if (!data?.filteredProducts?.products) {
        throw new Error('No products found in response');
      }
      
      // Normalize products
      products = data.filteredProducts.products.map((p: any) =>
        this.normalizeProduct(p, config.url)
      );
      
      const scrapeTimeMs = Date.now() - startTime;
      
      return {
        success: true,
        products,
        fieldCompleteness: calculateFieldCompleteness(products),
        metadata: {
          scrapeTimeMs,
          pagesVisited: 1,
          requestsMade: 1,
          method: this.name,
        },
      };
    } catch (error: any) {
      errors.push(error.message);
      
      return {
        success: false,
        products,
        fieldCompleteness: calculateFieldCompleteness(products),
        metadata: {
          scrapeTimeMs: Date.now() - startTime,
          pagesVisited: 0,
          requestsMade: 1,
          method: this.name,
        },
        errors,
      };
    }
  }
  
  /**
   * Extract dispensary ID from Dutchie URL
   */
  private extractDispensaryId(url: string): string | null {
    // Try to extract from URL patterns like:
    // https://dutchie.com/dispensary/conbud-les
    // https://conbud.com (embedded Dutchie)
    
    const match = url.match(/\/dispensary\/([^/]+)/);
    if (match) return match[1];
    
    // For embedded Dutchie, would need to fetch the page
    return null;
  }
  
  /**
   * Diagnose failure
   */
  async diagnose(error: Error, html?: string): Promise<any> {
    const message = error.message.toLowerCase();
    
    if (message.includes('graphql error')) {
      return {
        type: 'api_change',
        explanation: 'GraphQL API structure may have changed',
        suggestedFix: 'Update GraphQL query structure',
        confidence: 80,
      };
    }
    
    if (message.includes('timeout')) {
      return {
        type: 'network',
        explanation: 'Request timed out',
        suggestedFix: 'Increase timeout or check network connectivity',
        confidence: 90,
      };
    }
    
    return {
      type: 'other',
      explanation: error.message,
      suggestedFix: null,
      confidence: 50,
    };
  }
}
