/**
 * Base Scraping Method Interface
 * All scraping methods must implement this interface
 */

export interface ScrapeConfig {
  dispensaryId: string;
  url: string;
  menuUrl?: string;
  timeout?: number;
  retries?: number;
  proxy?: string;
  sessionData?: Record<string, unknown>;
}

export interface Product {
  id: string;
  name: string;
  price: number | null;
  priceRaw: string | null;
  brand: string | null;
  category: string | null;
  weight: string | null;
  thc: {
    formatted: string;
    value: number;
  } | null;
  cbd: {
    formatted: string;
    value: number;
  } | null;
  inStock: boolean;
  quantity: number | null;
  url: string | null;
  imageUrl: string | null;
  description: string | null;
  metadata: Record<string, unknown>;
}

export interface ScrapeResult {
  success: boolean;
  products: Product[];
  fieldCompleteness: {
    overall: number;
    name: number;
    price: number;
    brand: number;
    category: number;
    thc: number;
    inStock: number;
  };
  metadata: {
    scrapeTimeMs: number;
    pagesVisited: number;
    requestsMade: number;
    method: string;
  };
  errors?: string[];
  rawData?: unknown;
}

export interface InventoryResult {
  method: 'cart_probe' | 'api' | 'dropdown' | 'badge' | 'none';
  confidence: number;
  inventoryData?: Map<string, number>;
  notes?: string;
}

export interface Diagnosis {
  type: 'cloudflare' | 'age_gate' | 'api_change' | 'wrong_provider' | 'network' | 'structure_change' | 'auth_required' | 'other';
  explanation: string;
  suggestedFix: string | null;
  confidence: number;
}

/**
 * Base interface that all scraping methods must implement
 */
export interface ScrapingMethod {
  /** Unique identifier for this method */
  name: string;
  
  /** Provider this method works for */
  provider: string;
  
  /** Type of scraping approach */
  type: 'http' | 'browser' | 'api' | 'hybrid';
  
  /** Requirements for this method */
  requirements: {
    chromium?: boolean;
    proxy?: boolean;
    cookies?: boolean;
    javascript?: boolean;
  };
  
  /**
   * Main scraping function
   * @param config - Configuration for the scrape
   * @returns Result of the scrape
   */
  scrape(config: ScrapeConfig): Promise<ScrapeResult>;
  
  /**
   * Optional: Detect inventory levels
   * @param config - Configuration for the scrape
   * @returns Inventory detection result
   */
  detectInventory?(config: ScrapeConfig): Promise<InventoryResult>;
  
  /**
   * Optional: Diagnose why a scrape failed
   * @param error - The error that occurred
   * @param html - HTML content if available
   * @returns Diagnosis of the issue
   */
  diagnose?(error: Error, html?: string): Promise<Diagnosis>;
  
  /**
   * Optional: Apply a patch/fix to the method
   * @param patchCode - Code or configuration to apply
   */
  applyPatch?(patchCode: string): void;
}

/**
 * Calculate field completeness from products
 */
export function calculateFieldCompleteness(products: Product[]): ScrapeResult['fieldCompleteness'] {
  if (products.length === 0) {
    return {
      overall: 0,
      name: 0,
      price: 0,
      brand: 0,
      category: 0,
      thc: 0,
      inStock: 0,
    };
  }

  const counts = {
    name: products.filter(p => p.name).length,
    price: products.filter(p => p.price !== null).length,
    brand: products.filter(p => p.brand).length,
    category: products.filter(p => p.category).length,
    thc: products.filter(p => p.thc !== null).length,
    inStock: products.filter(p => typeof p.inStock === 'boolean').length,
  };

  const percentages = {
    name: (counts.name / products.length) * 100,
    price: (counts.price / products.length) * 100,
    brand: (counts.brand / products.length) * 100,
    category: (counts.category / products.length) * 100,
    thc: (counts.thc / products.length) * 100,
    inStock: (counts.inStock / products.length) * 100,
  };

  const overall = Object.values(percentages).reduce((sum, val) => sum + val, 0) / Object.keys(percentages).length;

  return {
    overall: Math.round(overall),
    name: Math.round(percentages.name),
    price: Math.round(percentages.price),
    brand: Math.round(percentages.brand),
    category: Math.round(percentages.category),
    thc: Math.round(percentages.thc),
    inStock: Math.round(percentages.inStock),
  };
}

/**
 * Sleep utility
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
