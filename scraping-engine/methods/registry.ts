/**
 * Method Registry
 * Central registry of all scraping methods
 */

import { ScrapingMethod } from './base.js';

// Method imports will be added as we create them
// import { DutchieGraphQLMethod } from './dutchie/graphql.js';
// import { DutchieBrowserMethod } from './dutchie/browser.js';
// etc.

const methodRegistry: Map<string, ScrapingMethod[]> = new Map();

/**
 * Register a method for a provider
 */
export function registerMethod(provider: string, method: ScrapingMethod): void {
  if (!methodRegistry.has(provider)) {
    methodRegistry.set(provider, []);
  }
  
  const methods = methodRegistry.get(provider)!;
  
  // Check if method with this name already exists
  const existing = methods.findIndex(m => m.name === method.name);
  if (existing !== -1) {
    methods[existing] = method;
    console.log(`[Registry] Updated existing method: ${provider}/${method.name}`);
  } else {
    methods.push(method);
    console.log(`[Registry] Registered new method: ${provider}/${method.name}`);
  }
}

/**
 * Get all methods for a provider
 */
export function getMethodsForProvider(provider: string): ScrapingMethod[] {
  const specific = methodRegistry.get(provider) || [];
  const universal = methodRegistry.get('universal') || [];
  return [...specific, ...universal];
}

/**
 * Get a specific method by name
 */
export function getMethod(provider: string, methodName: string): ScrapingMethod | null {
  const methods = methodRegistry.get(provider) || [];
  return methods.find(m => m.name === methodName) || null;
}

/**
 * Get all registered methods
 */
export function getAllMethods(): Map<string, ScrapingMethod[]> {
  return new Map(methodRegistry);
}

/**
 * Initialize and register all methods
 */
export async function initializeRegistry(): Promise<void> {
  console.log('[Registry] Initializing method registry...');
  
  // Methods will be registered here as we create them
  // For now, this is a placeholder
  
  console.log('[Registry] Registry initialized');
  console.log(`[Registry] Total providers: ${methodRegistry.size}`);
  
  for (const [provider, methods] of methodRegistry.entries()) {
    console.log(`[Registry]   ${provider}: ${methods.length} methods`);
  }
}
