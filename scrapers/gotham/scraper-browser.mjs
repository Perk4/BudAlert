/**
 * Gotham NYC Scraper - Browser Version
 * 
 * This version uses Playwright to bypass Cloudflare protection
 * then uses the same extraction logic from scraper.mjs
 * 
 * USAGE:
 *   npm install playwright
 *   npx playwright install chromium
 *   node scraper-browser.mjs
 */

import { chromium } from 'playwright';
import { GothamScraper } from './scraper.mjs';

const GOTHAM_CONFIG = {
  baseUrl: 'https://gotham.nyc',
  menuUrl: 'https://gotham.nyc/menu'
};

export class GothamBrowserScraper extends GothamScraper {
  constructor() {
    super();
    this.browser = null;
    this.page = null;
  }

  /**
   * Launch browser and solve Cloudflare challenge
   */
  async launchBrowser() {
    console.log('🌐 Launching browser...');
    
    this.browser = await chromium.launch({
      headless: true, // Set to false to debug
      args: [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage'
      ]
    });

    const context = await this.browser.newContext({
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      viewport: { width: 1920, height: 1080 },
      locale: 'en-US'
    });

    this.page = await context.newPage();
    
    // Remove webdriver flag
    await this.page.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', {
        get: () => false,
      });
    });

    console.log('✅ Browser launched');
  }

  /**
   * Fetch page HTML by solving Cloudflare challenge
   */
  async fetchPage(url) {
    console.log(`🌐 Navigating to ${url}...`);
    
    try {
      // Navigate to page
      await this.page.goto(url, {
        waitUntil: 'domcontentloaded',
        timeout: 60000
      });

      console.log('⏳ Waiting for Cloudflare challenge...');
      
      // Wait for challenge to complete
      // Option 1: Wait for specific time
      await this.page.waitForTimeout(8000);
      
      // Option 2: Wait for products to appear (more reliable)
      try {
        await this.page.waitForSelector('.product, .dt-product, article.product', {
          timeout: 15000
        });
        console.log('✅ Products detected on page');
      } catch (e) {
        console.warn('⚠️  Product selector not found, proceeding anyway...');
      }

      // Get final HTML after challenge
      const html = await this.page.content();
      
      console.log(`✅ Page loaded (${html.length} bytes)`);
      
      // Check if we're still on challenge page
      if (html.includes('Please wait while your request is being verified')) {
        throw new Error('Cloudflare challenge not solved - still on challenge page');
      }
      
      return html;
      
    } catch (error) {
      console.error(`❌ Failed to load ${url}:`, error.message);
      throw error;
    }
  }

  /**
   * Main scraping workflow with browser
   */
  async scrape() {
    try {
      // Launch browser
      await this.launchBrowser();

      // Fetch page HTML (solving Cloudflare challenge)
      const html = await this.fetchPage(GOTHAM_CONFIG.menuUrl);

      // Use existing extraction logic from parent class
      const allProducts = this.extractProducts(html, GOTHAM_CONFIG.menuUrl);

      // Deduplicate
      const uniqueProducts = Array.from(
        new Map(allProducts.map(p => [p.name, p])).values()
      );

      console.log(`\n✅ Scraped ${uniqueProducts.length} unique products`);
      
      return uniqueProducts;
      
    } catch (error) {
      console.error('❌ Scraping failed:', error);
      throw error;
      
    } finally {
      // Always close browser
      if (this.browser) {
        await this.browser.close();
        console.log('🔒 Browser closed');
      }
    }
  }
}

export default GothamBrowserScraper;

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const scraper = new GothamBrowserScraper();
  
  scraper.scrape()
    .then(products => {
      console.log('\n✅ SUCCESS!');
      console.log(`📊 Scraped ${products.length} products`);
      
      // Save to file
      import('fs').then(fs => {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `gotham-products-${timestamp}.json`;
        fs.default.writeFileSync(filename, JSON.stringify(products, null, 2));
        console.log(`💾 Saved to ${filename}`);
      });
      
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ FAILED:', error.message);
      process.exit(1);
    });
}
