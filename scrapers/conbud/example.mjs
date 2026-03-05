#!/usr/bin/env node

/**
 * Example Usage of Conbud Scrapers
 * 
 * This file demonstrates how to use the scrapers programmatically.
 */

import { ConbudAPIScraper } from './api-scraper.mjs';
import { ConbudBrowserScraper } from './browser-scraper.mjs';
import {
  buildFilters,
  normalizeProduct,
  COMMON_CATEGORIES
} from './queries.mjs';

// ============================================================================
// Example 1: Basic API Scraping
// ============================================================================

async function example1_basicAPIScrape() {
  console.log('=== Example 1: Basic API Scrape ===\n');
  
  const scraper = new ConbudAPIScraper();
  const result = await scraper.scrape();
  
  if (result.success) {
    console.log(`✅ Scraped ${result.productCount} products`);
    console.log(`📄 Saved to: ${result.filename}`);
  } else {
    console.error(`❌ Failed: ${result.error}`);
  }
}

// ============================================================================
// Example 2: API Scraping with Custom Configuration
// ============================================================================

async function example2_customAPIConfig() {
  console.log('\n=== Example 2: Custom API Configuration ===\n');
  
  const scraper = new ConbudAPIScraper({
    timeout: 15000,      // 15 second timeout
    retries: 5,          // Retry up to 5 times
    retryDelay: 3000     // 3 seconds between retries
  });
  
  const result = await scraper.scrape();
  console.log('Result:', result);
}

// ============================================================================
// Example 3: Fetch Specific Category
// ============================================================================

async function example3_fetchCategory() {
  console.log('\n=== Example 3: Fetch Specific Category ===\n');
  
  const scraper = new ConbudAPIScraper();
  
  try {
    // Fetch only flower products
    const flowerProducts = await scraper.fetchByCategory('Flower');
    console.log(`🌸 Found ${flowerProducts.length} flower products`);
    
    // Process and normalize
    const normalized = flowerProducts
      .map(p => normalizeProduct(p))
      .filter(p => p !== null);
    
    console.log(`✅ Normalized ${normalized.length} products`);
    
    // Show first product
    if (normalized.length > 0) {
      console.log('\nFirst product:');
      console.log(JSON.stringify(normalized[0], null, 2));
    }
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

// ============================================================================
// Example 4: Fetch All Categories
// ============================================================================

async function example4_fetchAllCategories() {
  console.log('\n=== Example 4: Fetch All Categories ===\n');
  
  const scraper = new ConbudAPIScraper();
  
  try {
    const allProducts = await scraper.fetchAllCategories();
    console.log(`📦 Total products: ${allProducts.length}`);
    
    // Group by category
    const byCategory = {};
    allProducts.forEach(product => {
      const cat = product.category || 'Unknown';
      if (!byCategory[cat]) byCategory[cat] = [];
      byCategory[cat].push(product);
    });
    
    console.log('\nProducts by category:');
    Object.entries(byCategory).forEach(([category, products]) => {
      console.log(`  ${category}: ${products.length}`);
    });
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

// ============================================================================
// Example 5: Using Filters
// ============================================================================

async function example5_usingFilters() {
  console.log('\n=== Example 5: Using Filters ===\n');
  
  const scraper = new ConbudAPIScraper();
  
  // Build custom filters
  const filters = buildFilters({
    category: 'Flower',
    strainType: 'indica',
    priceMin: 10,
    priceMax: 50,
    inStockOnly: true
  });
  
  console.log('Filters:', JSON.stringify(filters, null, 2));
  
  // Note: This requires updating api-scraper to accept custom filters
  // For now, this is just an example of the filter structure
}

// ============================================================================
// Example 6: Browser Scraper (Headless)
// ============================================================================

async function example6_browserScraper() {
  console.log('\n=== Example 6: Browser Scraper (Headless) ===\n');
  
  // Note: This will only work in environments with Chromium available
  
  try {
    const scraper = new ConbudBrowserScraper({
      headless: true,
      timeout: 60000,
      captchaWaitTime: 30000,
      scrollSteps: 3
    });
    
    const result = await scraper.scrape();
    
    if (result.success) {
      console.log(`✅ Scraped ${result.productCount} products`);
      console.log(`📡 Captured ${result.requestCount} GraphQL requests`);
      console.log(`📥 Captured ${result.responseCount} GraphQL responses`);
      console.log(`⏱️  Duration: ${result.duration}s`);
    }
    
  } catch (error) {
    if (error.message.includes('browserType.launch')) {
      console.log('⚠️  Browser scraper requires Chromium');
      console.log('💡 Run: npx playwright install chromium');
    } else {
      console.error('❌ Error:', error.message);
    }
  }
}

// ============================================================================
// Example 7: Browser Scraper (Visible, for debugging)
// ============================================================================

async function example7_browserScraperVisible() {
  console.log('\n=== Example 7: Browser Scraper (Visible) ===\n');
  
  try {
    const scraper = new ConbudBrowserScraper({
      headless: false,  // Show browser window
      captchaWaitTime: 60000  // Extra time for manual CAPTCHA solving
    });
    
    const result = await scraper.scrape();
    console.log('Result:', result);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

// ============================================================================
// Example 8: Custom Product Processing
// ============================================================================

async function example8_customProcessing() {
  console.log('\n=== Example 8: Custom Product Processing ===\n');
  
  const scraper = new ConbudAPIScraper();
  
  try {
    const rawProducts = await scraper.fetchAllProducts();
    
    // Custom processing: Find high-THC products under $50
    const highThcDeals = rawProducts
      .map(p => normalizeProduct(p))
      .filter(p => {
        return p && 
               p.price < 50 && 
               p.thcPercent && 
               p.thcPercent > 20 &&
               p.inStock;
      })
      .sort((a, b) => b.thcPercent - a.thcPercent);
    
    console.log(`🔥 Found ${highThcDeals.length} high-THC deals`);
    
    // Show top 5
    console.log('\nTop 5 high-THC deals:');
    highThcDeals.slice(0, 5).forEach((product, i) => {
      console.log(`${i + 1}. ${product.name}`);
      console.log(`   THC: ${product.thc} | Price: $${product.price}`);
      console.log(`   Brand: ${product.brand} | Category: ${product.category}`);
    });
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

// ============================================================================
// Example 9: Error Handling
// ============================================================================

async function example9_errorHandling() {
  console.log('\n=== Example 9: Error Handling ===\n');
  
  const scraper = new ConbudAPIScraper({
    timeout: 5000,   // Short timeout to trigger errors
    retries: 1
  });
  
  try {
    const result = await scraper.scrape();
    
    if (result.success) {
      console.log('✅ Success');
    } else {
      console.log('⚠️  Partial failure');
      console.log(`Errors encountered: ${result.errorCount}`);
      
      // Errors are stored in scraper.errors
      scraper.errors.forEach(err => {
        console.log(`  - ${err.type}: ${err.error}`);
      });
    }
    
  } catch (error) {
    console.error('❌ Complete failure:', error.message);
  }
}

// ============================================================================
// Example 10: Integration with BudAlert
// ============================================================================

async function example10_budAlertIntegration() {
  console.log('\n=== Example 10: BudAlert Integration ===\n');
  
  const scraper = new ConbudAPIScraper();
  
  try {
    const rawProducts = await scraper.fetchAllProducts();
    const products = rawProducts.map(p => normalizeProduct(p));
    
    // Example: Detect price drops
    // (In real implementation, compare with previous scrape)
    console.log('Products ready for BudAlert pipeline:');
    console.log(`  Total: ${products.length}`);
    console.log(`  In stock: ${products.filter(p => p.inStock).length}`);
    console.log(`  With THC data: ${products.filter(p => p.thc).length}`);
    
    // Group by category for stats
    const categories = {};
    products.forEach(p => {
      const cat = p.category || 'Unknown';
      categories[cat] = (categories[cat] || 0) + 1;
    });
    
    console.log('\nCategory breakdown:');
    Object.entries(categories)
      .sort((a, b) => b[1] - a[1])
      .forEach(([cat, count]) => {
        console.log(`  ${cat}: ${count}`);
      });
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

// ============================================================================
// Main: Run Examples
// ============================================================================

async function main() {
  const args = process.argv.slice(2);
  const exampleNumber = args[0] ? parseInt(args[0]) : null;
  
  const examples = [
    example1_basicAPIScrape,
    example2_customAPIConfig,
    example3_fetchCategory,
    example4_fetchAllCategories,
    example5_usingFilters,
    example6_browserScraper,
    example7_browserScraperVisible,
    example8_customProcessing,
    example9_errorHandling,
    example10_budAlertIntegration
  ];
  
  if (exampleNumber && exampleNumber >= 1 && exampleNumber <= examples.length) {
    // Run specific example
    await examples[exampleNumber - 1]();
  } else {
    // Show usage
    console.log('Conbud Scraper Examples\n');
    console.log('Usage: node example.mjs [example_number]\n');
    console.log('Available examples:');
    console.log('  1 - Basic API scrape');
    console.log('  2 - Custom API configuration');
    console.log('  3 - Fetch specific category');
    console.log('  4 - Fetch all categories');
    console.log('  5 - Using filters');
    console.log('  6 - Browser scraper (headless)');
    console.log('  7 - Browser scraper (visible)');
    console.log('  8 - Custom product processing');
    console.log('  9 - Error handling');
    console.log(' 10 - BudAlert integration');
    console.log('\nExample: node example.mjs 1');
    console.log('\nNote: Examples 6-7 require Chromium (npx playwright install chromium)');
  }
}

// Run
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
