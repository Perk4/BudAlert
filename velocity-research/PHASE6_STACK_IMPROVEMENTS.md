# Phase 6: Stack Improvements - Concrete Changes to BudAlert Codebase

**Date:** 2026-03-05  
**Researcher:** sku-velocity-research subagent  
**Focus:** Specific code changes, schema updates, and infrastructure additions

---

## Executive Summary

This phase translates research into **actionable code changes** for the existing BudAlert codebase.

**Current Stack:**
- Scrapers: Python (Playwright) + Node.js (research)
- Database: Convex
- Storage: JSON files + Convex tables
- No pipeline, no velocity tracking

**Required Changes:**
1. Convex schema additions (4 new tables)
2. Scraper migration (Python → Node.js for workers)
3. Worker infrastructure (BullMQ + PM2)
4. Change detection pipeline (Convex mutations)
5. API additions (velocity queries)

**Implementation Priority:** P0 (critical) → P4 (nice-to-have)

---

## Change 1: Convex Schema Updates (P0 - Critical)

### Current Schema Issues

The existing `convex/schema.ts` already has tables for velocity tracking, but they're not being populated:
- `menuSnapshots` - Exists but unused
- `inventoryDeltas` - Exists but unused
- `inventoryEvents` - Exists but unused
- `productVelocity` - **Missing** (needs to be added)

### Add New Table: productVelocity

```typescript
// convex/schema.ts
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // ... existing tables ...
  
  // NEW TABLE: Product velocity metrics
  productVelocity: defineTable({
    // Identifiers
    productId: v.string(),
    retailerId: v.string(),
    canonicalId: v.optional(v.string()), // Linked to canonical product
    
    // Core velocity metrics
    velocityScore: v.number(), // 0-100 composite score
    unitsPerHour: v.optional(v.number()), // Only for Dutchie stores
    unitsPerDay: v.optional(v.number()),
    restocksPerWeek: v.number(),
    avgTimeInStock: v.optional(v.number()), // Hours
    availabilityPct: v.number(), // 0-100
    
    // Trend analysis
    trend: v.optional(v.string()), // ACCELERATING, STEADY, DECELERATING
    trendConfidence: v.optional(v.number()), // 0-1
    
    // Forecasting
    nextRestockPredicted: v.optional(v.number()), // Unix timestamp
    nextRestockConfidence: v.optional(v.number()), // 0-1
    
    // Data quality
    dataPoints: v.number(), // Number of deltas contributing
    lastUpdated: v.number(), // Unix timestamp
    confidence: v.number() // Overall confidence 0-1
  })
    .index('by_product_retailer', ['productId', 'retailerId'])
    .index('by_canonical', ['canonicalId'])
    .index('by_velocity_score', ['velocityScore'])
    .index('by_retailer', ['retailerId'])
    .index('by_last_updated', ['lastUpdated']),
  
  // ... existing tables ...
});
```

### Update Existing Table: products

Add canonical linking:

```typescript
// Add to existing products table
products: defineTable({
  // ... existing fields ...
  canonicalId: v.optional(v.string()), // Link to canonicalProducts
  normalizedName: v.optional(v.string()), // For entity matching
  normalizedBrand: v.optional(v.string()),
  size: v.optional(v.number()), // Grams
  // ... rest of fields ...
})
  .index('by_canonical', ['canonicalId']) // NEW INDEX
  .index('by_normalized_name', ['normalizedName']) // Already exists
```

### Add New Table: canonicalProducts

```typescript
canonicalProducts: defineTable({
  canonicalId: v.string(), // Unique ID (e.g., "blue-dream-3.5g-good-chemistry")
  
  // Normalized attributes
  strain: v.string(), // "blue dream"
  brand: v.optional(v.string()), // "good chemistry"
  size: v.number(), // 3.5 (grams)
  category: v.string(), // "flower"
  
  // Metadata
  aliases: v.array(v.string()), // All name variations
  firstSeenAt: v.number(),
  lastSeenAt: v.number(),
  
  // Aggregated metrics (from all stores)
  totalStores: v.number(),
  avgPrice: v.optional(v.number()),
  minPrice: v.optional(v.number()),
  maxPrice: v.optional(v.number()),
  
  // Aggregate velocity
  avgVelocityScore: v.optional(v.number()),
  totalRestocksPerWeek: v.optional(v.number())
})
  .index('by_canonical_id', ['canonicalId'])
  .index('by_strain_size', ['strain', 'size'])
  .index('by_velocity', ['avgVelocityScore']),
```

---

## Change 2: Scraper Migration (P0 - Critical)

### Current State
- Python scrapers in `scrapers/` directory
- Each store has manual Python script
- No job queue, no scheduling

### Target State
- Node.js scrapers (consistent with Convex TypeScript)
- Platform adapters (Dutchie, WordPress, Blaze)
- Worker pool with BullMQ

### Migration Path

**Step 1: Create scraper framework**

```bash
# New structure
scrapers/
  platforms/
    dutchie.mjs
    wordpress.mjs
    blaze.mjs
    base.mjs
  index.mjs
  config.json
```

**Step 2: Base scraper class**

```javascript
// scrapers/platforms/base.mjs
import { chromium } from 'playwright';

export class BaseScraper {
  constructor(storeConfig) {
    this.config = storeConfig;
    this.browser = null;
  }
  
  async scrape() {
    throw new Error('scrape() must be implemented');
  }
  
  async launchBrowser(options = {}) {
    this.browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      ...options
    });
    return this.browser;
  }
  
  async closeBrowser() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }
  
  async withRetry(fn, maxAttempts = 3) {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        return await fn();
      } catch (error) {
        console.error(`Attempt ${i + 1} failed:`, error.message);
        if (i === maxAttempts - 1) throw error;
        await this.delay(Math.pow(2, i) * 1000);
      }
    }
  }
  
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  normalizeProduct(raw) {
    return {
      id: raw.id || this.generateId(raw),
      name: raw.name,
      brand: raw.brand || null,
      category: raw.category,
      price: parseFloat(raw.price),
      inStock: Boolean(raw.inStock),
      quantity: raw.quantity || null,
      thc: raw.thc || null,
      cbd: raw.cbd || null,
      image: raw.image || null,
      scrapedAt: Date.now(),
      source: this.config.slug
    };
  }
  
  generateId(product) {
    const slug = product.name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
    return `${this.config.slug}-${slug}`;
  }
}
```

**Step 3: Migrate existing scrapers**

```javascript
// scrapers/platforms/dutchie.mjs
import { BaseScraper } from './base.mjs';

export class DutchieScraper extends BaseScraper {
  async scrape() {
    const products = await this.withRetry(async () => {
      const response = await fetch('https://api.dutchie.com/graphql', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        body: JSON.stringify({
          query: this.getGraphQLQuery(),
          variables: { dispensaryId: this.config.dutchieId }
        })
      });
      
      if (!response.ok) {
        throw new Error(`GraphQL request failed: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.errors) {
        throw new Error(`GraphQL errors: ${JSON.stringify(data.errors)}`);
      }
      
      return data.data.filteredProducts.products;
    });
    
    return {
      storeId: this.config.slug,
      platform: 'dutchie',
      products: products.map(p => this.normalizeProduct(p)),
      scrapedAt: Date.now(),
      success: true,
      count: products.length
    };
  }
  
  getGraphQLQuery() {
    return `
      query FilteredProducts($dispensaryId: ID!) {
        filteredProducts(dispensaryId: $dispensaryId, limit: 1000) {
          products {
            id
            name
            brand { name }
            category
            price
            inStock
            quantity
            potencyThc { formatted }
            potencyCbd { formatted }
            image
          }
        }
      }
    `;
  }
  
  normalizeProduct(raw) {
    return super.normalizeProduct({
      id: raw.id,
      name: raw.name,
      brand: raw.brand?.name,
      category: raw.category,
      price: raw.price,
      inStock: raw.inStock,
      quantity: raw.quantity, // Dutchie exposes this!
      thc: raw.potencyThc?.formatted,
      cbd: raw.potencyCbd?.formatted,
      image: raw.image
    });
  }
}
```

**Step 4: Store configuration**

```json
// scrapers/config.json
{
  "stores": [
    {
      "slug": "conbud-les",
      "name": "Conbud Lower East Side",
      "platform": "dutchie",
      "dutchieId": "6430f42042cf3c004e37f0f8",
      "url": "https://dutchie.com/dispensary/conbud-les",
      "region": "nyc",
      "priority": 80
    },
    {
      "slug": "gotham-nyc",
      "name": "Gotham NYC",
      "platform": "wordpress",
      "url": "https://gotham.nyc/menu",
      "region": "nyc",
      "priority": 70
    }
  ]
}
```

---

## Change 3: Worker Infrastructure (P0 - Critical)

### Install Dependencies

```bash
cd ~/clawd/budalert
npm install bullmq ioredis pm2
npm install playwright
npx playwright install chromium
```

### Create Worker

```javascript
// workers/scraper-worker.mjs
import { Worker } from 'bullmq';
import { Redis } from 'ioredis';
import { scrapeStore } from '../scrapers/index.mjs';
import { ingestScrapeResult } from './ingestion.mjs';

const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379,
  maxRetriesPerRequest: null
});

const worker = new Worker(
  'scrape-jobs',
  async (job) => {
    const { storeId } = job.data;
    
    console.log(`[${new Date().toISOString()}] Scraping ${storeId}...`);
    
    try {
      const result = await scrapeStore(storeId);
      
      // Send to Convex
      await ingestScrapeResult(result);
      
      console.log(`[${new Date().toISOString()}] ✓ ${storeId}: ${result.products.length} products`);
      
      return {
        success: true,
        storeId,
        products: result.products.length,
        duration: result.duration
      };
    } catch (error) {
      console.error(`[${new Date().toISOString()}] ✗ ${storeId}:`, error.message);
      throw error;
    }
  },
  {
    connection: redis,
    concurrency: 4, // 4 concurrent scrapes
    limiter: {
      max: 20,
      duration: 60000 // 20 jobs per minute max
    }
  }
);

worker.on('completed', (job, result) => {
  console.log(`Job ${job.id} completed:`, result);
});

worker.on('failed', (job, err) => {
  console.error(`Job ${job.id} failed:`, err.message);
});

console.log('Worker started, waiting for jobs...');
```

### Create Ingestion Pipeline

```javascript
// workers/ingestion.mjs
import { ConvexHttpClient } from 'convex/browser';

const client = new ConvexHttpClient(process.env.CONVEX_URL);

export async function ingestScrapeResult(result) {
  const { storeId, products, scrapedAt } = result;
  
  // 1. Store snapshot
  const snapshotId = await client.mutation('scraping:storeSnapshot', {
    retailerId: storeId,
    products: products,
    scrapedAt: scrapedAt
  });
  
  console.log(`Stored snapshot ${snapshotId} for ${storeId}`);
  
  // 2. Update current inventory
  await client.mutation('scraping:updateCurrentInventory', {
    retailerId: storeId,
    products: products
  });
  
  // 3. Trigger change detection
  await client.action('scraping:detectChanges', {
    retailerId: storeId,
    snapshotId: snapshotId
  });
  
  return snapshotId;
}
```

### PM2 Configuration

```javascript
// pm2.config.js
module.exports = {
  apps: [
    {
      name: 'scraper-worker',
      script: './workers/scraper-worker.mjs',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production',
        REDIS_HOST: 'localhost',
        REDIS_PORT: 6379,
        CONVEX_URL: process.env.CONVEX_URL
      },
      error_file: './logs/worker-error.log',
      out_file: './logs/worker-out.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s'
    }
  ]
};
```

---

## Change 4: Convex Mutations (P0 - Critical)

### Create scraping.ts

```typescript
// convex/scraping.ts
import { v } from 'convex/values';
import { mutation, internalMutation, action } from './_generated/server';

// Store raw snapshot
export const storeSnapshot = mutation({
  args: {
    retailerId: v.string(),
    products: v.array(v.any()),
    scrapedAt: v.number()
  },
  handler: async (ctx, { retailerId, products, scrapedAt }) => {
    // Store each product as a snapshot
    const snapshotIds = [];
    
    for (const product of products) {
      const id = await ctx.db.insert('menuSnapshots', {
        retailerId,
        productId: product.id,
        name: product.name,
        brand: product.brand,
        category: product.category,
        price: product.price,
        inStock: product.inStock,
        quantity: product.quantity,
        thc: product.thc,
        scrapedAt
      });
      snapshotIds.push(id);
    }
    
    return { snapshotId: snapshotIds[0], count: snapshotIds.length };
  }
});

// Update current inventory (latest state)
export const updateCurrentInventory = mutation({
  args: {
    retailerId: v.string(),
    products: v.array(v.any())
  },
  handler: async (ctx, { retailerId, products }) => {
    for (const product of products) {
      // Check if exists
      const existing = await ctx.db
        .query('currentInventory')
        .withIndex('by_retailer_product', q =>
          q.eq('retailerId', retailerId).eq('productId', product.id)
        )
        .first();
      
      if (existing) {
        // Update
        await ctx.db.patch(existing._id, {
          price: product.price,
          inStock: product.inStock,
          quantity: product.quantity,
          lastSeenAt: Date.now()
        });
      } else {
        // Insert
        await ctx.db.insert('currentInventory', {
          retailerId,
          productId: product.id,
          name: product.name,
          brand: product.brand,
          category: product.category,
          price: product.price,
          inStock: product.inStock,
          quantity: product.quantity,
          firstSeenAt: Date.now(),
          lastSeenAt: Date.now()
        });
      }
    }
    
    return { updated: products.length };
  }
});

// Detect changes (compare current vs previous snapshot)
export const detectChanges = action({
  args: {
    retailerId: v.string(),
    snapshotId: v.string()
  },
  handler: async (ctx, { retailerId, snapshotId }) => {
    // This will call the internal mutation
    return await ctx.runMutation('scraping:_detectChangesInternal', {
      retailerId,
      snapshotId
    });
  }
});

export const _detectChangesInternal = internalMutation({
  args: {
    retailerId: v.string(),
    snapshotId: v.string()
  },
  handler: async (ctx, { retailerId, snapshotId }) => {
    // Get current snapshot
    const currentProducts = await ctx.db
      .query('menuSnapshots')
      .withIndex('by_retailer_time', q => q.eq('retailerId', retailerId))
      .order('desc')
      .take(500);
    
    // Get previous snapshot (before current)
    const previousProducts = await ctx.db
      .query('menuSnapshots')
      .withIndex('by_retailer_time', q => q.eq('retailerId', retailerId))
      .order('desc')
      .filter(q => q.lt(q.field('scrapedAt'), currentProducts[0]?.scrapedAt || 0))
      .take(500);
    
    if (previousProducts.length === 0) {
      // No previous data, skip comparison
      return { deltas: 0, events: 0 };
    }
    
    // Build maps
    const currentMap = new Map(currentProducts.map(p => [p.productId, p]));
    const previousMap = new Map(previousProducts.map(p => [p.productId, p]));
    
    let deltasCount = 0;
    let eventsCount = 0;
    
    // Compare
    for (const [productId, current] of currentMap) {
      const previous = previousMap.get(productId);
      
      if (!previous) continue; // New product, skip for now
      
      // Detect changes
      const hasQuantityChange = previous.quantity !== current.quantity;
      const hasPriceChange = previous.price !== current.price;
      const hasStockChange = previous.inStock !== current.inStock;
      
      if (hasQuantityChange || hasPriceChange || hasStockChange) {
        // Store delta
        await ctx.db.insert('inventoryDeltas', {
          retailerId,
          productId,
          quantityChange: hasQuantityChange ? (current.quantity || 0) - (previous.quantity || 0) : null,
          priceChange: hasPriceChange ? current.price - previous.price : null,
          stockChange: hasStockChange ? (current.inStock ? 'restocked' : 'sold_out') : null,
          scrapedAt: current.scrapedAt,
          timeSinceLast: current.scrapedAt - previous.scrapedAt
        });
        deltasCount++;
        
        // Generate events
        if (hasStockChange) {
          await ctx.db.insert('inventoryEvents', {
            type: current.inStock ? 'restock' : 'sold_out',
            retailerId,
            productId,
            timestamp: current.scrapedAt,
            notified: false
          });
          eventsCount++;
        }
      }
    }
    
    return { deltas: deltasCount, events: eventsCount };
  }
});
```

---

## Change 5: Velocity Calculation (P1 - High Priority)

```typescript
// convex/velocity.ts
import { v } from 'convex/values';
import { query, internalMutation } from './_generated/server';

export const calculateVelocity = internalMutation({
  args: {
    productId: v.string(),
    retailerId: v.string()
  },
  handler: async (ctx, { productId, retailerId }) => {
    // Get deltas from last 7 days
    const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    
    const deltas = await ctx.db
      .query('inventoryDeltas')
      .withIndex('by_product_retailer', q =>
        q.eq('productId', productId).eq('retailerId', retailerId)
      )
      .filter(q => q.gte(q.field('scrapedAt'), sevenDaysAgo))
      .collect();
    
    if (deltas.length === 0) {
      return { velocityScore: 0, dataAvailable: false };
    }
    
    // Calculate metrics
    let totalUnitsSold = 0;
    let totalTimeMs = 0;
    let restockCount = 0;
    
    for (const delta of deltas) {
      if (delta.quantityChange && delta.quantityChange < 0) {
        totalUnitsSold += Math.abs(delta.quantityChange);
        totalTimeMs += delta.timeSinceLast || 0;
      }
      
      if (delta.stockChange === 'restocked') {
        restockCount++;
      }
    }
    
    const totalHours = totalTimeMs / (60 * 60 * 1000);
    const unitsPerHour = totalHours > 0 ? totalUnitsSold / totalHours : null;
    const unitsPerDay = unitsPerHour ? unitsPerHour * 24 : null;
    const restocksPerWeek = (restockCount / 7) * 7; // Normalize to per-week
    
    // Calculate velocity score (0-100)
    let score = 0;
    
    if (unitsPerDay) {
      score += Math.min(unitsPerDay / 100, 1) * 40;
    }
    
    if (restocksPerWeek >= 7) score += 30;
    else if (restocksPerWeek >= 5) score += 27;
    else if (restocksPerWeek >= 3) score += 21;
    else if (restocksPerWeek >= 1) score += 12;
    
    score += 30; // Baseline for having data
    
    // Store or update
    const existing = await ctx.db
      .query('productVelocity')
      .withIndex('by_product_retailer', q =>
        q.eq('productId', productId).eq('retailerId', retailerId)
      )
      .first();
    
    const velocityData = {
      productId,
      retailerId,
      velocityScore: Math.round(score),
      unitsPerHour,
      unitsPerDay,
      restocksPerWeek,
      dataPoints: deltas.length,
      lastUpdated: Date.now(),
      confidence: deltas.length >= 50 ? 0.9 : (deltas.length / 50) * 0.9
    };
    
    if (existing) {
      await ctx.db.patch(existing._id, velocityData);
    } else {
      await ctx.db.insert('productVelocity', velocityData);
    }
    
    return velocityData;
  }
});

// Query: Get velocity for a product
export const getVelocity = query({
  args: {
    productId: v.string(),
    retailerId: v.string()
  },
  handler: async (ctx, { productId, retailerId }) => {
    const velocity = await ctx.db
      .query('productVelocity')
      .withIndex('by_product_retailer', q =>
        q.eq('productId', productId).eq('retailerId', retailerId)
      )
      .first();
    
    return velocity || { velocityScore: 0, dataAvailable: false };
  }
});

// Query: Top velocity products
export const getTopVelocity = query({
  args: {
    limit: v.optional(v.number())
  },
  handler: async (ctx, { limit = 20 }) => {
    return await ctx.db
      .query('productVelocity')
      .withIndex('by_velocity_score')
      .order('desc')
      .take(limit);
  }
});
```

---

## Change 6: Scheduler (P1 - High Priority)

```typescript
// convex/crons.ts
import { cronJobs } from 'convex/server';
import { internal } from './_generated/api';

const crons = cronJobs();

// Run every 5 minutes
crons.interval(
  'generate-scrape-jobs',
  { minutes: 5 },
  internal.scheduler.generateJobs
);

// Recalculate velocities nightly
crons.cron(
  'recalculate-velocities',
  '0 2 * * *', // 2 AM daily
  internal.velocity.recalculateAll
);

export default crons;
```

```typescript
// convex/scheduler.ts
import { v } from 'convex/values';
import { internalMutation } from './_generated/server';
import { Queue } from 'bullmq';
import { Redis } from 'ioredis';

const redis = new Redis(/* config */);
const queue = new Queue('scrape-jobs', { connection: redis });

export const generateJobs = internalMutation({
  handler: async (ctx) => {
    const stores = await ctx.db.query('retailers').collect();
    const now = Date.now();
    
    for (const store of stores) {
      // Get last scrape time
      const lastScrape = await ctx.db
        .query('scrapeJobs')
        .withIndex('by_retailer_time', q => q.eq('retailerId', store._id))
        .order('desc')
        .first();
      
      const timeSinceLast = lastScrape ? now - lastScrape.startedAt : Infinity;
      
      // Determine scrape interval based on priority
      const interval = calculateInterval(store.priority || 50);
      
      if (timeSinceLast >= interval) {
        // Time to scrape!
        await queue.add(`scrape-${store.slug}`, {
          storeId: store.slug
        }, {
          priority: store.priority || 50
        });
        
        console.log(`Queued scrape for ${store.slug}`);
      }
    }
  }
});

function calculateInterval(priority) {
  // priority 80-100: every 15 min
  // priority 60-79: every 30 min
  // priority 40-59: every 1 hour
  // priority 20-39: every 4 hours
  // priority 0-19: every 12 hours
  
  if (priority >= 80) return 15 * 60 * 1000;
  if (priority >= 60) return 30 * 60 * 1000;
  if (priority >= 40) return 60 * 60 * 1000;
  if (priority >= 20) return 4 * 60 * 60 * 1000;
  return 12 * 60 * 60 * 1000;
}
```

---

## Implementation Priority & Timeline

| Change | Priority | Effort | Timeline | Blockers |
|--------|----------|--------|----------|----------|
| **Schema updates** | P0 | 1-2 hours | Week 1 Day 1 | None |
| **Scraper migration** | P0 | 2-3 days | Week 1 | Schema |
| **Worker infrastructure** | P0 | 1-2 days | Week 1 | Scrapers |
| **Convex mutations** | P0 | 2-3 days | Week 1-2 | Schema |
| **Velocity calculation** | P1 | 2 days | Week 2 | Mutations |
| **Scheduler** | P1 | 1 day | Week 2 | Workers |
| **Entity resolution** | P2 | 1 week | Week 3-4 | Velocity |
| **API endpoints** | P2 | 2 days | Week 4 | All above |
| **Monitoring** | P3 | 1 day | Week 4 | Workers |

**Total MVP:** 2-3 weeks for basic velocity tracking

---

## Cost Impact

| Component | Before | After | Increase |
|-----------|--------|-------|----------|
| Convex | $0 (free tier) | $0 (still in free tier) | $0 |
| VPS | $0 | $6-12 (Hetzner) | +$6-12 |
| Redis | $0 | $0 (self-hosted on VPS) | $0 |
| Proxies | $0 | $0 (optional, for hard targets) | $0 |
| **Total** | **$0** | **$6-12/month** | +$6-12 |

**At 100 stores:** ~$31/month  
**At 500 stores:** ~$63/month

---

## Testing Plan

1. **Unit tests** (Phase 7 / test coverage subagent will handle)
2. **Integration tests**
   - Scrape → Snapshot → Delta → Velocity flow
   - Worker queue processing
3. **Manual testing**
   - Scrape 1 store, verify snapshot stored
   - Scrape again, verify deltas detected
   - Check velocity calculated correctly

---

## Next Phase Preview

**Phase 7 will create comprehensive deliverables:**
- SKU_VELOCITY_SPEC.md (technical specification)
- IMPLEMENTATION_PLAN.md (step-by-step guide)
- All finalized design documents

---

## Conclusion

**6 critical changes** enable velocity tracking:

1. ✅ Schema: Add `productVelocity`, `canonicalProducts` tables
2. ✅ Scrapers: Migrate Python → Node.js, create platform adapters
3. ✅ Workers: BullMQ + PM2 for distributed scraping
4. ✅ Mutations: Snapshot storage + change detection
5. ✅ Velocity: Multi-signal scoring algorithm
6. ✅ Scheduler: Adaptive scraping based on priority

**Cost:** $6-63/month (depending on scale)  
**Timeline:** 2-3 weeks for MVP  
**Complexity:** Medium (manageable with existing team)

---

**Phase 6 Complete.** Proceeding to Phase 7: Final Recommendations & Deliverables.
