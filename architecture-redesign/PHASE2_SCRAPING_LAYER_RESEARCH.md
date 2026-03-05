# Phase 2: Scraping Layer Research - Production Architecture

**Date:** 2026-03-05  
**Focus:** Stealth scraping at scale for hundreds of stores

---

## Executive Summary

This phase designs a **production-grade scraping layer** capable of handling **hundreds of stores × hundreds of products** with:
- **Stealth first:** Fingerprint evasion, proxy rotation, anti-detection
- **Distributed architecture:** Worker queues, horizontal scaling, fault isolation
- **Platform flexibility:** Plugin system for Dutchie, Jane, WordPress, custom sites
- **Failure resilience:** Retries, circuit breakers, graceful degradation
- **Cost efficiency:** Smart scheduling, caching, differential scraping

---

## 1. Stealth Scraping at Scale

### Current Approach (Phase 1)
- Basic Playwright automation
- Age gate cookie bypass
- Some rate limiting awareness
- **Lacks:** Fingerprinting defense, proxy rotation, detection evasion

### Production Requirements

| Threat | Detection Method | Mitigation Strategy |
|--------|------------------|---------------------|
| **Bot Detection** | Playwright/Puppeteer signatures | Stealth plugins, undetected-chromedriver |
| **Fingerprinting** | Canvas, WebGL, fonts, timezone | Randomization, spoofing |
| **IP Tracking** | Request origin, rate patterns | Proxy rotation, residential IPs |
| **Session Analysis** | Cookie patterns, localStorage | Session recycling, realistic profiles |
| **CAPTCHA** | Cloudflare, reCAPTCHA | 2Captcha API, human fallback, avoid triggers |
| **Rate Limiting** | Too many requests | Exponential backoff, per-store limits |
| **User-Agent** | Outdated or bot signatures | Real browser UA strings, rotation |

### Recommended Stealth Stack

#### Browser Automation
```typescript
// Stealth configuration
import { chromium } from 'playwright-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

// Option 1: Playwright-extra with stealth (Node.js)
chromium.use(StealthPlugin());

// Option 2: Undetected ChromeDriver (Python)
import undetected_chromedriver as uc
driver = uc.Chrome()

// Option 3: Selenium with custom patches
// - Random viewport sizes
// - WebGL/Canvas noise injection
// - Timezone spoofing
```

#### Fingerprint Randomization
```typescript
const browserConfig = {
  viewport: randomViewport(), // 1920x1080, 1366x768, etc.
  userAgent: rotateBrowserUA(), // Real Chrome/Firefox UAs
  locale: 'en-US',
  timezone: 'America/New_York',
  permissions: ['geolocation'], // Look more human
  webgl: injectNoise(), // Unique fingerprint per session
  canvas: injectNoise(),
  fonts: loadRandomFonts()
};
```

#### Proxy Strategy

**Tier 1: Residential Proxies (High Stealth)**
- Provider: BrightData, Oxylabs, Smartproxy
- Use case: Hard targets (Curaleaf, Rise with CAPTCHA)
- Cost: $3-15 per GB
- Rotation: Per-request or per-session

**Tier 2: Datacenter Proxies (Medium Stealth)**
- Provider: ProxyScrape, WebShare
- Use case: Medium-complexity sites
- Cost: $1-3 per GB
- Rotation: Per-store or per-scrape

**Tier 3: No Proxy (Low Risk)**
- Use case: Easy targets (WordPress sites, public APIs)
- Cost: $0
- Mitigation: Rate limiting, user-agent rotation

**Smart Proxy Selection:**
```typescript
function selectProxy(store: Store): ProxyConfig | null {
  if (store.protection === 'cloudflare') return residentialProxy();
  if (store.platform === 'dutchie') return datacenterProxy();
  if (store.platform === 'wordpress') return null; // Direct
  return datacenterProxy(); // Default
}
```

#### Rate Limiting Strategy

**Per-Store Limits:**
```typescript
const rateLimits = {
  // Easy targets (WordPress, static)
  easy: { requestsPerMinute: 30, concurrency: 3 },
  
  // Medium targets (Blaze, Jane)
  medium: { requestsPerMinute: 10, concurrency: 1 },
  
  // Hard targets (Dutchie, Cloudflare)
  hard: { requestsPerMinute: 5, concurrency: 1, delayMs: 2000 }
};
```

**Exponential Backoff:**
```typescript
async function scrapeWithRetry(store: Store, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await scrape(store);
    } catch (error) {
      if (error.status === 429) { // Rate limited
        const backoffMs = Math.pow(2, i) * 1000; // 1s, 2s, 4s
        await sleep(backoffMs);
      } else if (error.isCaptcha) {
        // Human intervention or CAPTCHA solver
        return await handleCaptcha(store, error);
      } else {
        throw error; // Non-retryable
      }
    }
  }
  throw new Error(`Failed after ${maxRetries} retries`);
}
```

#### Session Management

**Session Recycling:**
- Keep browser sessions alive for 5-15 minutes
- Reuse sessions for multiple products from same store
- Simulate realistic browsing (scroll, hover, delays)

**Cookie Persistence:**
```typescript
// Save cookies after age gate
const cookies = await page.context().cookies();
await fs.writeFile(`sessions/${store.id}.json`, JSON.stringify(cookies));

// Restore on next scrape
const savedCookies = JSON.parse(await fs.readFile(`sessions/${store.id}.json`));
await page.context().addCookies(savedCookies);
```

---

## 2. Platform-Specific Strategies

### 2.1 Dutchie (React + GraphQL)

**Complexity:** ⭐⭐⭐⭐⭐ Very High  
**Used by:** Conbud LES, many national chains

#### Architecture
- Client-side React app
- GraphQL API (requires reverse engineering)
- Possible Cloudflare protection
- Dynamic product loading

#### Recommended Approach: **Hybrid**

**Method A: Direct GraphQL (Preferred)**
```graphql
# Extract queries from network tab
query MenuQuery($dispensaryId: ID!) {
  dispensary(id: $dispensaryId) {
    products {
      id
      name
      brand
      category
      pricing {
        price
        unit
      }
      potency {
        thc { value }
        cbd { value }
      }
      inStock
      images
    }
  }
}
```

**Implementation:**
```typescript
import { request } from 'graphql-request';

async function scrapeDutchie(store: DutchieStore) {
  const endpoint = 'https://dutchie.com/graphql';
  const query = getQueryForStore(store); // Pre-extracted query
  
  const data = await request(endpoint, query, {
    dispensaryId: store.dutchieId,
    ...getDutchieHeaders(store) // auth, x-api-key, etc.
  });
  
  return normalizeProducts(data.dispensary.products);
}
```

**Method B: Browser + Network Intercept (Fallback)**
```typescript
import { chromium } from 'playwright';

async function scrapeDutchieWithBrowser(store: DutchieStore) {
  const browser = await chromium.launch(stealthConfig);
  const page = await browser.newPage();
  
  // Intercept GraphQL responses
  const products = [];
  page.on('response', async (response) => {
    if (response.url().includes('/graphql')) {
      const json = await response.json();
      if (json.data?.products) {
        products.push(...json.data.products);
      }
    }
  });
  
  await page.goto(store.menuUrl);
  await page.waitForSelector('.product-card'); // Wait for products to load
  
  return normalizeProducts(products);
}
```

**Platform Detection:**
- Check for `dutchie` in page source
- Look for `__NEXT_DATA__` (Next.js)
- Detect GraphQL network calls

**Inventory Hacks:**
- Cart probing: Add max quantity, check error message
- `inStock` boolean from GraphQL (not actual quantity)
- Listen for WebSocket updates (some Dutchie sites use real-time)

---

### 2.2 Jane/iHeartJane (React + REST API)

**Complexity:** ⭐⭐⭐⭐ High  
**Used by:** Many California dispensaries

#### Architecture
- React SPA
- REST API (easier to reverse engineer than GraphQL)
- JSON responses with product data
- Age gate via cookie

#### Recommended Approach: **Direct API**

**Discovery Process:**
```bash
# Open browser DevTools → Network tab
# Navigate to menu page
# Filter by XHR/Fetch

# Typical endpoints:
GET /api/v1/products?store_id=123&category=flower
GET /api/v1/stores/123/menu
```

**Implementation:**
```typescript
async function scrapeJane(store: JaneStore) {
  const response = await axios.get(`${store.apiBase}/products`, {
    params: {
      store_id: store.janeId,
      category: 'all',
      limit: 1000
    },
    headers: {
      'User-Agent': randomUserAgent(),
      'Cookie': `age_verified=1; ${store.sessionCookie}` // Age gate bypass
    }
  });
  
  return response.data.products.map(normalizeProduct);
}
```

**Platform Detection:**
- Domain: `*.iheartjane.com` or custom domain
- Look for `/api/v1/products` endpoint
- Check for Jane branding in source

**Inventory Hacks:**
- Jane API often returns `inventory_count` directly
- If not, check product detail endpoint: `/api/v1/products/{id}`
- Cart API: POST to `/api/cart/add` with high quantity, check response

---

### 2.3 WordPress + Dovetail/WooCommerce

**Complexity:** ⭐⭐ Low-Medium  
**Used by:** Gotham NYC, many small dispensaries

#### Architecture
- Server-side rendering (easy!)
- WordPress REST API (v2)
- WooCommerce product endpoints
- JSON-LD structured data
- RSS/XML feeds

#### Recommended Approach: **API First**

**Option 1: WordPress REST API**
```bash
# Standard WordPress endpoints
GET /wp-json/wp/v2/products
GET /wp-json/wc/v3/products  # WooCommerce

# Example response
{
  "id": 123,
  "name": "Blue Dream 3.5g",
  "price": "55.00",
  "categories": [{"name": "Flower"}],
  "stock_status": "instock",
  "meta_data": [
    {"key": "thc_content", "value": "18.5%"}
  ]
}
```

**Implementation:**
```typescript
async function scrapeWordPress(store: WordPressStore) {
  const response = await axios.get(`${store.baseUrl}/wp-json/wp/v2/products`, {
    params: { per_page: 100, page: 1 }
  });
  
  return response.data.map(product => ({
    id: product.id,
    name: product.title.rendered,
    price: parsePrice(product.meta.price),
    thc: extractTHC(product.meta_data),
    inStock: product.stock_status === 'instock'
  }));
}
```

**Option 2: JSON-LD Scraping**
```typescript
import * as cheerio from 'cheerio';

async function scrapeJSONLD(store: Store) {
  const html = await axios.get(store.menuUrl);
  const $ = cheerio.load(html.data);
  
  const jsonLdScripts = $('script[type="application/ld+json"]');
  const products = [];
  
  jsonLdScripts.each((i, el) => {
    const data = JSON.parse($(el).html());
    if (data['@type'] === 'Product') {
      products.push({
        name: data.name,
        price: data.offers?.price,
        availability: data.offers?.availability // "InStock", "OutOfStock"
      });
    }
  });
  
  return products;
}
```

**Platform Detection:**
- Check for `/wp-content/` in HTML
- Look for `<meta name="generator" content="WordPress" />`
- Probe `/wp-json/` endpoint

**Inventory Hacks:**
- WordPress: `stock_status` field (instock/outofstock)
- WooCommerce: `stock_quantity` field (actual number!)
- RSS feed: `<woocommerce:stock_status>` tag

---

### 2.4 Blaze (Server-Side + API)

**Complexity:** ⭐⭐⭐ Medium  
**Used by:** Housing Works SoHo, others

#### Architecture
- Mixed SSR + client-side JavaScript
- API endpoints for product data
- Age gate with session cookie
- Category-based navigation

#### Recommended Approach: **Hybrid (API + Browser)**

**API Discovery (from Phase 1 research):**
```bash
# Typical Blaze endpoints
GET /api/v1/store/{storeId}/products
GET /api/v1/store/{storeId}/categories
GET /api/v1/product/{productId}/details
```

**Implementation (Existing Python scraper):**
```python
# From memory/stealth-scraper/scrapers/blaze/housing_works.py
async def scrape_blaze(store):
    async with playwright.async_api() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Set age gate cookie
        await page.context.add_cookies([{
            'name': 'age_verified',
            'value': '1',
            'domain': store.domain
        }])
        
        await page.goto(store.menu_url)
        await page.wait_for_selector('.product-tile')
        
        products = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('.product-tile')).map(el => ({
                name: el.querySelector('.product-name').textContent,
                price: el.querySelector('.product-price').textContent,
                // Quantity detection from dropdown
                maxQuantity: el.querySelector('select[name="quantity"]')?.options?.length || 0
            }));
        }''')
        
        return products
```

**Quantity Detection (Cart Probing):**
```typescript
async function getMaxQuantity(page: Page, productId: string) {
  // Try adding high quantity to cart
  await page.fill(`#quantity-${productId}`, '999');
  await page.click(`#add-to-cart-${productId}`);
  
  // Check for error message
  const error = await page.textContent('.error-message');
  if (error?.includes('Only')) {
    const match = error.match(/Only (\d+) available/);
    return match ? parseInt(match[1]) : null;
  }
  
  // Check cart for actual quantity added
  const cartQty = await page.textContent('.cart-quantity');
  return cartQty ? parseInt(cartQty) : null;
}
```

**Platform Detection:**
- Look for `blaze` in page source or domain
- Check for `/shop` or `/menu` URL structure
- Detect age gate modal (`#age-gate-modal`)

---

### 2.5 Custom Platforms (Shopify, Wix, Custom)

**Complexity:** ⭐⭐ to ⭐⭐⭐⭐ (varies)

#### Detection Strategy
```typescript
async function detectPlatform(url: string): Promise<PlatformType> {
  const html = await axios.get(url);
  const $ = cheerio.load(html.data);
  
  // Check meta tags and scripts
  if ($('script[src*="shopify"]').length) return 'shopify';
  if ($('script[src*="wix"]').length) return 'wix';
  if ($('script[src*="dutchie"]').length) return 'dutchie';
  if ($('script[src*="iheartjane"]').length) return 'jane';
  if ($('meta[name="generator"][content*="WordPress"]').length) return 'wordpress';
  
  // Check API endpoints
  try {
    await axios.head(`${url}/wp-json/`);
    return 'wordpress';
  } catch {}
  
  return 'custom'; // Unknown platform
}
```

#### Shopify Strategy
- Product JSON: `/products/{handle}.json`
- Collections JSON: `/collections/{handle}/products.json`
- Inventory via variant `available` field

#### Wix Strategy
- Usually client-rendered (use browser automation)
- Look for `/_api/wix-ecommerce-storefront-web/api/v1/products`

---

## 3. Hacky Inventory Detection

### Problem
Most sites don't expose actual inventory counts. We need "sneaky" methods to detect:
- Actual quantity available (not just in/out of stock)
- Low stock warnings
- Restock alerts

### Approach Matrix

| Method | Reliability | Speed | Detectability | Use Case |
|--------|-------------|-------|---------------|----------|
| **Cart Probing** | ⭐⭐⭐⭐ High | ⭐⭐ Slow | ⭐⭐⭐ Medium | Exact quantities |
| **Dropdown Parsing** | ⭐⭐⭐ Medium | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐⭐ Low | Max available (10+) |
| **API Inspection** | ⭐⭐⭐⭐⭐ Very High | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐ Low | If inventory exposed |
| **Stock Labels** | ⭐⭐ Low | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐⭐ Low | Only low stock |
| **Out of Stock Detection** | ⭐⭐⭐⭐⭐ Very High | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐⭐ Low | Binary status |

### Implementation: Cart Probing

**Technique:** Add progressively higher quantities until error

```typescript
async function probeInventory(page: Page, productId: string): Promise<number> {
  let low = 1, high = 100;
  let maxAvailable = 0;
  
  // Binary search for max quantity
  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    
    const success = await tryAddToCart(page, productId, mid);
    
    if (success) {
      maxAvailable = mid;
      low = mid + 1; // Try higher
    } else {
      high = mid - 1; // Try lower
    }
    
    // Clear cart between attempts
    await clearCart(page);
    await sleep(500); // Don't hammer the site
  }
  
  return maxAvailable;
}

async function tryAddToCart(page: Page, productId: string, quantity: number): Promise<boolean> {
  await page.fill(`#quantity-${productId}`, quantity.toString());
  await page.click(`#add-to-cart-${productId}`);
  
  // Check for success
  const cartCount = await page.textContent('.cart-count');
  return parseInt(cartCount) === quantity;
}
```

**Optimization:** Cache results, only re-probe weekly

### Implementation: Dropdown Parsing

**Technique:** Parse `<select name="quantity">` options

```typescript
async function parseQuantityDropdown(page: Page, productId: string): Promise<number> {
  const options = await page.$$eval(
    `#quantity-${productId} option`,
    (opts) => opts.map(opt => parseInt(opt.value))
  );
  
  const maxOption = Math.max(...options);
  
  // If max is 10, actual inventory is likely 10+
  // If max is 3, actual inventory is exactly 3 (or less)
  return maxOption >= 10 ? 10 : maxOption;
}
```

### Implementation: Stock Label Detection

**Technique:** Look for "Only X left!" text

```typescript
async function detectStockLabels(page: Page): Promise<Map<string, number>> {
  const labels = await page.$$eval('.product-stock-label', (els) =>
    els.map(el => ({
      productId: el.dataset.productId,
      text: el.textContent
    }))
  );
  
  const inventory = new Map();
  
  for (const label of labels) {
    // "Only 3 left in stock"
    const match = label.text.match(/Only (\d+) left/i);
    if (match) {
      inventory.set(label.productId, parseInt(match[1]));
    }
  }
  
  return inventory;
}
```

### Velocity Calculation

**Change Detection Logic:**
```typescript
interface ProductSnapshot {
  id: string;
  quantity: number;
  timestamp: number;
}

function calculateVelocity(
  previous: ProductSnapshot,
  current: ProductSnapshot
): VelocityMetric {
  const timeDiff = current.timestamp - previous.timestamp;
  const qtyDiff = previous.quantity - current.quantity;
  
  // Velocity = units sold per hour
  const velocityPerHour = (qtyDiff / timeDiff) * 3600;
  
  return {
    velocity: velocityPerHour,
    unitsSold: qtyDiff,
    timeWindow: timeDiff,
    percentageChange: (qtyDiff / previous.quantity) * 100,
    trend: qtyDiff > 0 ? 'decreasing' : qtyDiff < 0 ? 'restocked' : 'stable'
  };
}
```

---

## 4. Distributed Scraping Architecture

### Requirements
- **Horizontal scaling:** Add workers to increase capacity
- **Fault isolation:** One store failure doesn't crash everything
- **Priority queuing:** Scrape important stores more frequently
- **Rate limiting:** Per-store, per-IP, per-platform
- **Monitoring:** Track success rates, latency, errors

### Architecture: Worker Queue System

```
┌─────────────────────────────────────────────────────────┐
│               SCHEDULER (Convex Cron)                   │
│  • Every 15-60 min per store                           │
│  • Priority-based (popular stores more frequent)       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            JOB QUEUE (BullMQ / Convex)                  │
│  • Store scraping jobs                                 │
│  • Priority levels (high/normal/low)                   │
│  • Retry logic built-in                                │
└────────────────────┬────────────────────────────────────┘
                     │
           ┌─────────┴─────────┬─────────┐
           ▼                   ▼         ▼
    ┌─────────────┐     ┌─────────────┐ ┌─────────────┐
    │  WORKER 1   │     │  WORKER 2   │ │  WORKER N   │
    │  (Chromium) │     │  (Chromium) │ │  (Chromium) │
    └──────┬──────┘     └──────┬──────┘ └──────┬──────┘
           │                   │               │
           └───────────────────┴───────────────┘
                             │
                             ▼
           ┌─────────────────────────────────────┐
           │       RAW DATA STORAGE              │
           │  • Redis (hot cache)                │
           │  • Convex (structured)              │
           │  • R2 (cold archive)                │
           └─────────────────────────────────────┘
```

### Implementation: Convex-Based Queue

**Option 1: Pure Convex (Serverless)**

```typescript
// convex/scraping.ts
import { mutation, action } from './_generated/server';

// Schedule scraping job
export const scheduleStoreScrape = mutation({
  args: { storeId: v.id('stores'), priority: v.number() },
  handler: async (ctx, args) => {
    await ctx.db.insert('scrapeJobs', {
      storeId: args.storeId,
      status: 'pending',
      priority: args.priority,
      scheduledAt: Date.now()
    });
  }
});

// Worker action (runs in Node.js environment)
export const runScrapeJob = action({
  args: { jobId: v.id('scrapeJobs') },
  handler: async (ctx, args) => {
    const job = await ctx.runQuery(api.scraping.getJob, { jobId: args.jobId });
    const store = await ctx.runQuery(api.stores.get, { id: job.storeId });
    
    try {
      // Run scraper (browser automation here)
      const products = await scrapeStore(store);
      
      // Save results
      await ctx.runMutation(api.scraping.saveResults, {
        jobId: args.jobId,
        products,
        status: 'success'
      });
    } catch (error) {
      await ctx.runMutation(api.scraping.markFailed, {
        jobId: args.jobId,
        error: error.message
      });
    }
  }
});
```

**Option 2: BullMQ (More Control)**

```typescript
// worker.ts
import { Queue, Worker } from 'bullmq';
import Redis from 'ioredis';

const connection = new Redis();
const scrapeQueue = new Queue('scraping', { connection });

// Add jobs to queue
export async function scheduleScrape(store: Store) {
  await scrapeQueue.add('scrape', 
    { storeId: store.id },
    {
      priority: store.priority,
      attempts: 3,
      backoff: { type: 'exponential', delay: 1000 },
      removeOnComplete: { age: 3600 },
      removeOnFail: { age: 86400 }
    }
  );
}

// Worker processes jobs
const worker = new Worker('scraping', async (job) => {
  const { storeId } = job.data;
  const store = await getStore(storeId);
  
  const products = await scrapeStore(store);
  
  // Save to Convex
  await saveToConvex(products);
  
  return { productCount: products.length };
}, { connection, concurrency: 5 });

worker.on('completed', (job) => {
  console.log(`✅ Store ${job.data.storeId} scraped successfully`);
});

worker.on('failed', (job, err) => {
  console.error(`❌ Store ${job.data.storeId} failed:`, err);
});
```

### Scheduling Strategy

**Frequency Tiers:**
```typescript
const scrapingSchedule = {
  tier1: { 
    frequency: '15min', // High-traffic stores
    stores: ['conbud', 'housingworks', 'gotham'] 
  },
  tier2: { 
    frequency: '1hour', // Medium-traffic
    stores: ['alta', 'qube', 'smacked'] 
  },
  tier3: { 
    frequency: '4hour', // Low-traffic
    stores: ['delivery-only', 'new-stores'] 
  }
};
```

**Adaptive Scheduling:**
```typescript
function calculateNextScrapeTime(store: Store, history: ScrapeHistory[]): number {
  // Scrape more frequently if:
  // - High velocity (products selling fast)
  // - Frequent restocks
  // - User interest (pageviews)
  
  const velocity = calculateVelocity(history);
  const userInterest = store.pageviews / 100;
  
  const baseInterval = 3600; // 1 hour
  const multiplier = Math.max(0.25, 1 / (velocity + userInterest));
  
  return Date.now() + (baseInterval * multiplier * 1000);
}
```

---

## 5. Failure Handling & Resilience

### Failure Types

| Failure | Cause | Mitigation |
|---------|-------|------------|
| **Network Timeout** | Slow site, network issues | Retry with exponential backoff |
| **CAPTCHA** | Bot detection | Human solver, delay, proxy rotation |
| **Age Gate** | Missing cookie | Persistent session management |
| **Rate Limit (429)** | Too many requests | Per-store rate limiting, backoff |
| **Site Down (5xx)** | Maintenance | Circuit breaker, skip for 1 hour |
| **Data Missing** | Site structure changed | Fallback parsers, alert for manual fix |
| **Browser Crash** | Memory leak, timeout | Restart browser, worker auto-recovery |

### Circuit Breaker Pattern

```typescript
class CircuitBreaker {
  private failureCount = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  private lastFailureTime = 0;
  
  constructor(
    private threshold = 5,
    private timeoutMs = 60000 // 1 minute
  ) {}
  
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime > this.timeoutMs) {
        this.state = 'half-open';
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }
    
    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  private onSuccess() {
    this.failureCount = 0;
    this.state = 'closed';
  }
  
  private onFailure() {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    
    if (this.failureCount >= this.threshold) {
      this.state = 'open';
    }
  }
}

// Usage
const breakers = new Map<string, CircuitBreaker>();

async function scrapeWithCircuitBreaker(store: Store) {
  if (!breakers.has(store.id)) {
    breakers.set(store.id, new CircuitBreaker());
  }
  
  const breaker = breakers.get(store.id);
  return breaker.execute(() => scrapeStore(store));
}
```

### Retry Strategy

```typescript
interface RetryConfig {
  maxAttempts: number;
  baseDelayMs: number;
  maxDelayMs: number;
  retryableErrors: string[];
}

async function scrapeWithRetry(
  store: Store,
  config: RetryConfig
): Promise<Product[]> {
  let lastError: Error;
  
  for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
    try {
      return await scrapeStore(store);
    } catch (error) {
      lastError = error;
      
      // Don't retry non-retryable errors
      if (!isRetryable(error, config.retryableErrors)) {
        throw error;
      }
      
      // Calculate backoff delay
      const delay = Math.min(
        config.baseDelayMs * Math.pow(2, attempt - 1),
        config.maxDelayMs
      );
      
      console.log(`Retry ${attempt}/${config.maxAttempts} for ${store.id} in ${delay}ms`);
      await sleep(delay);
    }
  }
  
  throw lastError;
}

function isRetryable(error: Error, retryableErrors: string[]): boolean {
  return retryableErrors.some(pattern => 
    error.message.includes(pattern) || 
    error.name.includes(pattern)
  );
}
```

### Graceful Degradation

**Fallback Chain:**
```typescript
async function scrapeStoreRobust(store: Store): Promise<Product[]> {
  // Try primary method (fastest)
  try {
    return await scrapeViaAPI(store);
  } catch (error) {
    console.warn(`API scraping failed for ${store.id}:`, error);
  }
  
  // Try secondary method (browser automation)
  try {
    return await scrapeViaBrowser(store);
  } catch (error) {
    console.warn(`Browser scraping failed for ${store.id}:`, error);
  }
  
  // Try tertiary method (cached data)
  try {
    return await getCachedProducts(store);
  } catch (error) {
    console.error(`All methods failed for ${store.id}`);
  }
  
  // Return empty array rather than crashing
  return [];
}
```

### Monitoring & Alerting

**Metrics to Track:**
```typescript
interface ScrapingMetrics {
  storeId: string;
  successRate: number; // % of successful scrapes
  avgLatencyMs: number; // Average scrape time
  productsFound: number; // Product count
  errorRate: number; // % of errors
  lastSuccessAt: number; // Unix timestamp
  failureStreak: number; // Consecutive failures
}

function shouldAlert(metrics: ScrapingMetrics): boolean {
  return (
    metrics.successRate < 0.8 || // Less than 80% success
    metrics.failureStreak >= 5 || // 5 consecutive failures
    metrics.productsFound === 0 || // No products found
    Date.now() - metrics.lastSuccessAt > 86400000 // 24 hours since last success
  );
}
```

**Alert Destinations:**
- Discord webhook for immediate alerts
- Email for daily summaries
- Convex dashboard for historical view

---

## Summary: Recommended Stack

### Scraping Layer
```typescript
{
  browserAutomation: 'Playwright with stealth plugin',
  httpClient: 'Axios with retry logic',
  proxies: 'BrightData residential (hard targets) + WebShare datacenter (medium)',
  fingerprinting: 'Randomized viewport/UA/timezone',
  sessionManagement: 'Persistent cookies, 5-15min session reuse'
}
```

### Orchestration
```typescript
{
  scheduling: 'Convex cron + adaptive timing',
  queuing: 'BullMQ (Redis-backed) or Convex actions',
  workers: '3-10 Node.js processes with browser pools',
  rateLimit: 'Per-store limits, exponential backoff',
  failureHandling: 'Circuit breakers, retry with backoff, fallback chains'
}
```

### Platform Support
```typescript
{
  dutchie: 'Direct GraphQL + browser fallback',
  jane: 'REST API + browser fallback',
  wordpress: 'WordPress API + JSON-LD',
  blaze: 'Hybrid (API discovery + browser)',
  shopify: 'Product JSON endpoints',
  custom: 'Browser automation + HTML parsing'
}
```

### Inventory Detection
```typescript
{
  primary: 'API inspection for inventory_count',
  secondary: 'Dropdown parsing (fast, non-invasive)',
  tertiary: 'Cart probing (slow, accurate)',
  labels: 'Stock label text extraction'
}
```

---

## Phase 2 Complete ✅

**Deliverables:**
1. ✅ Stealth scraping strategies (fingerprinting, proxies, session management)
2. ✅ Platform-specific approaches (Dutchie, Jane, WordPress, Blaze, custom)
3. ✅ Inventory detection techniques (cart probing, dropdowns, API, labels)
4. ✅ Distributed architecture (worker queues, scheduling, horizontal scaling)
5. ✅ Failure handling (retries, circuit breakers, graceful degradation)

**Next Phase:** Data Pipeline Architecture (ingestion, storage, change detection, orchestration)

---
