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
import { fileURLToPath } from 'url';
import { writeFileSync } from 'fs';
import {
  cookiesToHeader,
  defaultSessionFile,
  loadSessionFile,
  saveSessionFile
} from '../session-storage.mjs';
import { GothamScraper } from './scraper.mjs';

const GOTHAM_CONFIG = {
  baseUrl: 'https://gotham.nyc',
  menuUrl: 'https://gotham.nyc/menu'
};

const DEFAULT_SESSION_FILE = defaultSessionFile(import.meta.url, 'gotham-browser-session.json');

function parseBoolean(value, defaultValue) {
  if (value === undefined) {
    return defaultValue;
  }

  const normalized = String(value).trim().toLowerCase();
  if (['1', 'true', 'yes', 'y', 'on'].includes(normalized)) return true;
  if (['0', 'false', 'no', 'n', 'off'].includes(normalized)) return false;

  return defaultValue;
}

function parseNumber(value, defaultValue) {
  if (value === undefined) {
    return defaultValue;
  }

  const parsed = Number.parseInt(String(value), 10);
  return Number.isFinite(parsed) ? parsed : defaultValue;
}

export class GothamBrowserScraper extends GothamScraper {
  constructor(options = {}) {
    super();
    this.options = {
      headless: true,
      timeout: 60000,
      challengeWaitTime: 8000,
      manualSolve: false,
      manualSolveWaitTime: 120000,
      sessionFile: DEFAULT_SESSION_FILE,
      loadSession: true,
      saveSession: true,
      ...options
    };

    this.browser = null;
    this.context = null;
    this.page = null;
  }

  /**
   * Launch browser and solve Cloudflare challenge
   */
  async launchBrowser() {
    console.log('🌐 Launching browser...');
    
    this.browser = await chromium.launch({
      headless: this.options.headless,
      args: [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage'
      ]
    });

    this.context = await this.browser.newContext({
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      viewport: { width: 1920, height: 1080 },
      locale: 'en-US'
    });

    await this.loadPersistedSession();
    this.page = await this.context.newPage();
    
    // Remove webdriver flag
    await this.page.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', {
        get: () => false,
      });
    });

    console.log('✅ Browser launched');
  }

  /**
   * Load cookies from previous successful/manual browser session
   */
  async loadPersistedSession() {
    if (!this.options.loadSession) {
      console.log('🍪 Session load disabled by configuration');
      return;
    }

    const session = await loadSessionFile(this.options.sessionFile);
    if (!session) {
      console.log(`🍪 No persisted session found at ${this.options.sessionFile}`);
      return;
    }

    const cookies = Array.isArray(session.cookies) ? session.cookies : [];
    if (cookies.length === 0) {
      console.log(`🍪 Session file found but no cookies present: ${this.options.sessionFile}`);
      return;
    }

    await this.context.addCookies(cookies);
    console.log(`🍪 Loaded ${cookies.length} cookies from ${this.options.sessionFile}`);
  }

  /**
   * Persist cookies after manual or successful challenge handling
   */
  async persistSession(reason = 'run-update') {
    if (!this.options.saveSession || !this.context) {
      return;
    }

    const cookies = await this.context.cookies();
    await saveSessionFile(this.options.sessionFile, {
      metadata: {
        source: 'gotham-browser',
        updatedAt: new Date().toISOString(),
        reason,
        cookieCount: cookies.length
      },
      cookies,
      cookieHeader: cookiesToHeader(cookies),
      urls: {
        menu: GOTHAM_CONFIG.menuUrl
      }
    });

    console.log(`🍪 Session saved (${cookies.length} cookies) -> ${this.options.sessionFile}`);
  }

  /**
   * Wait for manual solve in visible mode and persist updated cookies
   */
  async waitForManualSolve(reason) {
    if (this.options.headless) {
      console.log('⚠️  Manual solve requested but browser is headless. Set HEADLESS=false.');
      return;
    }

    console.log('\n🧑‍💻 Operator action required');
    console.log(`  Reason: ${reason}`);
    console.log('  Action: complete the Cloudflare challenge in the browser window.');
    console.log(`  Waiting ${this.options.manualSolveWaitTime}ms before continuing...`);

    await this.page.waitForTimeout(this.options.manualSolveWaitTime);
    await this.persistSession('manual-solve');
    console.log('✅ Manual solve wait complete\n');
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
      await this.page.waitForTimeout(this.options.challengeWaitTime);

      const challengeText = await this.page.content();
      const challengePending = challengeText.includes('Please wait while your request is being verified') ||
        challengeText.includes('cf_chl_opt') ||
        challengeText.toLowerCase().includes('checking your browser');

      if (challengePending && !this.options.headless) {
        await this.waitForManualSolve('Cloudflare challenge still visible');
      } else if (this.options.manualSolve && !this.options.headless) {
        await this.waitForManualSolve('Optional manual gate validation before extraction');
      }
      
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

      await this.persistSession('fetch-page-success');
      
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
      await this.persistSession('scrape-complete');
      
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
if (fileURLToPath(import.meta.url) === process.argv[1]) {
  const headless = parseBoolean(process.env.HEADLESS, true);
  const manualSolve = parseBoolean(process.env.MANUAL_SOLVE, !headless);
  const challengeWaitTime = parseNumber(process.env.CHALLENGE_WAIT_MS, 8000);
  const manualSolveWaitTime = parseNumber(process.env.MANUAL_SOLVE_WAIT_MS, 120000);

  const scraper = new GothamBrowserScraper({
    headless,
    manualSolve,
    challengeWaitTime,
    manualSolveWaitTime,
    sessionFile: process.env.GOTHAM_SESSION_FILE || DEFAULT_SESSION_FILE,
    loadSession: parseBoolean(process.env.LOAD_SESSION, true),
    saveSession: parseBoolean(process.env.SAVE_SESSION, true)
  });

  console.log('🛠️  Runtime options:');
  console.log(`  HEADLESS=${headless}`);
  console.log(`  MANUAL_SOLVE=${manualSolve}`);
  console.log(`  CHALLENGE_WAIT_MS=${challengeWaitTime}`);
  console.log(`  MANUAL_SOLVE_WAIT_MS=${manualSolveWaitTime}`);
  console.log(`  SESSION_FILE=${scraper.options.sessionFile}`);

  scraper.scrape()
    .then(products => {
      console.log('\n✅ SUCCESS!');
      console.log(`📊 Scraped ${products.length} products`);

      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `gotham-products-${timestamp}.json`;
      writeFileSync(filename, JSON.stringify(products, null, 2));
      console.log(`💾 Saved to ${filename}`);

      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ FAILED:', error.message);
      process.exit(1);
    });
}
