# Phase 3: Data Pipeline Architecture

**Date:** 2026-03-05  
**Focus:** Ingestion, storage, change detection, orchestration at scale

---

## Executive Summary

This phase designs a **scalable data pipeline** to handle:
- **Ingestion:** Raw scraper output → validated → normalized → stored
- **Storage:** Hot (Convex) + Cold (R2) tiered strategy
- **Change Detection:** Track SKU velocity, price changes, stock changes
- **Orchestration:** Hybrid Convex actions + external workers
- **Scale:** Hundreds of stores × thousands of products × hourly updates = millions of records/month

**Key Principle:** Separate concerns (raw → staging → production) with validation gates to catch bad data early.

---

## 1. Ingestion Layer

### Current State (Phase 1 Analysis)
- Scrapers output JSON files (e.g., `alta_products.json`)
- Manual import scripts (`import-nys-dispensaries.js`)
- No validation before import
- No staging area

### Production Requirements

**Multi-Stage Pipeline:**
```
RAW SCRAPE → VALIDATION → STAGING → NORMALIZATION → PRODUCTION
```

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  SCRAPER WORKERS                         │
│  (Playwright, API clients, HTML parsers)                │
└────────────────────┬─────────────────────────────────────┘
                     │ Raw JSON
                     ▼
┌──────────────────────────────────────────────────────────┐
│               RAW DATA INGESTION                         │
│  • Redis queue (buffer for high-throughput)             │
│  • R2 bucket (raw-scrapes/{store}/{timestamp}.json)     │
│  • Schema-less (accept anything)                        │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│                 VALIDATION LAYER                         │
│  • Required fields present?                             │
│  • Data types correct?                                  │
│  • Values within expected ranges?                       │
│  • Duplicates detected?                                 │
│  • Invalid products flagged                             │
└────────────────────┬─────────────────────────────────────┘
                     │ Validated JSON
                     ▼
┌──────────────────────────────────────────────────────────┐
│              STAGING (Convex Table)                      │
│  • 24-hour retention                                    │
│  • Allows inspection before promotion                   │
│  • A/B comparison with production                       │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│              NORMALIZATION LAYER                         │
│  • Store-specific format → unified schema               │
│  • Price parsing ($55.00 → 55.0)                       │
│  • THC/CBD extraction (18.5% → 18.5)                   │
│  • Category mapping (flower/edibles/etc)               │
│  • Entity resolution (match products across stores)     │
└────────────────────┬─────────────────────────────────────┘
                     │ Normalized data
                     ▼
┌──────────────────────────────────────────────────────────┐
│           PRODUCTION (Convex Tables)                     │
│  • products: Current snapshot                           │
│  • productHistory: Change log                           │
│  • storeProducts: Junction table                        │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Storage Strategy

### Problem: Scale and Cost

**Data Growth Projection:**
- 500 stores × 200 products = **100,000 products**
- Scrape every hour = **2.4 million scrapes/day**
- Each product record = ~1KB = **2.4 GB/day raw data**
- 30 days = **72 GB/month**

**Without optimization:** Convex storage costs would explode.

### Solution: Hot/Cold Tiered Storage

#### Hot Storage (Convex)
**What:** Current product snapshot + recent history (7 days)

```typescript
// Convex schema for hot storage
export default defineSchema({
  // Current products (latest snapshot)
  products: defineTable({
    externalId: v.string(), // store_productId
    storeId: v.id('stores'),
    name: v.string(),
    brand: v.optional(v.string()),
    category: v.string(),
    price: v.number(),
    thc: v.optional(v.number()),
    cbd: v.optional(v.number()),
    quantity: v.optional(v.number()),
    inStock: v.boolean(),
    imageUrl: v.optional(v.string()),
    url: v.string(),
    lastScraped: v.number(), // Unix timestamp
    lastChanged: v.number(), // Last time any field changed
  })
    .index('by_store', ['storeId'])
    .index('by_external_id', ['externalId'])
    .index('by_category', ['category'])
    .index('by_last_changed', ['lastChanged']),
  
  // Recent changes (7-day retention)
  productChanges: defineTable({
    productId: v.id('products'),
    field: v.string(), // 'price', 'quantity', 'inStock'
    oldValue: v.any(),
    newValue: v.any(),
    changedAt: v.number(),
  })
    .index('by_product', ['productId', 'changedAt'])
    .index('by_changed_at', ['changedAt']),
  
  // Stores
  stores: defineTable({
    name: v.string(),
    url: v.string(),
    platform: v.string(),
    lastScraped: v.number(),
    scrapeStatus: v.union(
      v.literal('success'),
      v.literal('failed'),
      v.literal('pending')
    ),
    scrapeFrequencyMinutes: v.number(),
  })
    .index('by_last_scraped', ['lastScraped']),
});
```

**Size Estimate:**
- 100K products × 1KB = **100 MB**
- 7 days of changes × ~10K changes/day × 200B = **14 MB**
- **Total hot storage: ~120 MB** (well within Convex limits)

#### Cold Storage (Cloudflare R2 / S3)
**What:** Historical scrapes, archived changes, raw data

```
r2://budalert-data/
├── raw-scrapes/           # Raw scraper output
│   ├── 2026-03/
│   │   ├── alta/
│   │   │   ├── 2026-03-05T12:00:00Z.json
│   │   │   └── 2026-03-05T13:00:00Z.json
│   │   └── conbud/
│   │       └── 2026-03-05T12:00:00Z.json
│   └── ...
├── snapshots/             # Daily product snapshots (compressed)
│   ├── 2026-03-05.json.gz  # All products at EOD
│   └── 2026-03-04.json.gz
├── changes/               # Change history (compressed)
│   ├── 2026-03/
│   │   ├── 2026-03-05-changes.jsonl.gz
│   │   └── 2026-03-04-changes.jsonl.gz
│   └── ...
└── archives/              # Long-term cold storage
    └── 2026-Q1-archive.parquet  # Columnar format for analytics
```

**Retention Policy:**
- **Raw scrapes:** 7 days (then delete)
- **Snapshots:** 90 days (daily) → 1 year (weekly) → delete
- **Changes:** 90 days (detailed) → 1 year (summarized) → archive to Parquet
- **Archives:** Indefinite (compressed, queryable via DuckDB/analytics)

**Cost Estimate (R2):**
- Storage: $0.015/GB/month
- 72 GB/month × $0.015 = **$1.08/month storage**
- Operations: Class A (writes) ~free, Class B (reads) ~free for this scale
- **Total R2 cost: ~$1-2/month**

---

## 3. Change Detection

### Problem: Core Feature Not Implemented

**Current State:** Only boolean `inStock` status, no historical tracking.

**Target:** Track every change to every product across all stores.

### Change Detection Architecture

```typescript
// Change detection flow
async function detectChanges(
  productId: string,
  newData: ProductData
): Promise<ProductChange[]> {
  const current = await ctx.db.get(productId);
  const changes: ProductChange[] = [];
  
  // Track all meaningful changes
  const fieldsToTrack = ['price', 'quantity', 'inStock', 'thc', 'cbd'];
  
  for (const field of fieldsToTrack) {
    if (current[field] !== newData[field]) {
      changes.push({
        productId,
        field,
        oldValue: current[field],
        newValue: newData[field],
        changedAt: Date.now()
      });
    }
  }
  
  return changes;
}
```

### SKU Velocity Calculation

**Definition:** Rate of product availability/quantity change over time.

```typescript
interface VelocityMetrics {
  productId: string;
  storeId: string;
  
  // Stock velocity
  quantityChange24h: number; // Units sold in 24 hours
  quantityChange7d: number;  // Units sold in 7 days
  velocityPerHour: number;   // Units/hour
  
  // Availability velocity
  timeInStock: number;       // % of time in stock (last 7 days)
  restockFrequency: number;  // Restocks per week
  avgRestockQuantity: number; // Average restock size
  
  // Price velocity
  priceChanges7d: number;    // Number of price changes
  avgPriceChange: number;    // Average change %
  
  // Trend
  trend: 'hot' | 'steady' | 'slow' | 'dead';
  score: number;             // 0-100 velocity score
}

async function calculateVelocity(
  productId: string,
  windowDays = 7
): Promise<VelocityMetrics> {
  const changes = await getProductChanges(productId, windowDays);
  
  // Quantity-based velocity
  const quantityChanges = changes.filter(c => c.field === 'quantity');
  const totalSold = quantityChanges.reduce((sum, c) => 
    sum + (c.oldValue - c.newValue), 0
  );
  const velocityPerHour = totalSold / (windowDays * 24);
  
  // Stock availability
  const stockChanges = changes.filter(c => c.field === 'inStock');
  const restocks = stockChanges.filter(c => !c.oldValue && c.newValue);
  const restockFrequency = restocks.length / windowDays * 7;
  
  // Price volatility
  const priceChanges = changes.filter(c => c.field === 'price');
  
  // Calculate trend score
  const score = calculateTrendScore({
    velocityPerHour,
    restockFrequency,
    priceVolatility: priceChanges.length
  });
  
  return {
    productId,
    storeId: product.storeId,
    quantityChange24h: getSoldInWindow(quantityChanges, 1),
    quantityChange7d: totalSold,
    velocityPerHour,
    timeInStock: calculateUptime(stockChanges, windowDays),
    restockFrequency,
    avgRestockQuantity: calculateAvgRestock(restocks),
    priceChanges7d: priceChanges.length,
    avgPriceChange: calculateAvgPriceChange(priceChanges),
    trend: getTrend(score),
    score
  };
}

function calculateTrendScore(metrics: {
  velocityPerHour: number;
  restockFrequency: number;
  priceVolatility: number;
}): number {
  // Weighted score (0-100)
  const velocityScore = Math.min(metrics.velocityPerHour * 10, 50);
  const restockScore = Math.min(metrics.restockFrequency * 5, 30);
  const priceScore = Math.min(metrics.priceVolatility * 5, 20);
  
  return velocityScore + restockScore + priceScore;
}

function getTrend(score: number): 'hot' | 'steady' | 'slow' | 'dead' {
  if (score >= 70) return 'hot';
  if (score >= 40) return 'steady';
  if (score >= 10) return 'slow';
  return 'dead';
}
```

### Change Event Types

```typescript
type ChangeEvent = 
  | { type: 'new_product', product: Product }
  | { type: 'restock', product: Product, quantity: number }
  | { type: 'price_change', product: Product, oldPrice: number, newPrice: number }
  | { type: 'out_of_stock', product: Product }
  | { type: 'low_stock', product: Product, quantity: number }
  | { type: 'discontinued', product: Product }; // Not seen in 30 days

// Event emission
async function emitChangeEvents(changes: ProductChange[]): Promise<void> {
  for (const change of changes) {
    const event = mapToEvent(change);
    
    // Publish to event stream (for real-time updates)
    await publishEvent(event);
    
    // Trigger alerts if needed
    await checkAlertRules(event);
    
    // Update metrics
    await updateVelocityMetrics(event);
  }
}
```

### Historical Tracking

**Time-Series Storage for Analytics:**
```typescript
// Convex query to get historical price data
export const getPriceHistory = query({
  args: { productId: v.id('products'), days: v.number() },
  handler: async (ctx, args) => {
    const cutoff = Date.now() - (args.days * 86400000);
    
    const changes = await ctx.db
      .query('productChanges')
      .withIndex('by_product', q => 
        q.eq('productId', args.productId).gt('changedAt', cutoff)
      )
      .filter(q => q.eq(q.field('field'), 'price'))
      .collect();
    
    return changes.map(c => ({
      timestamp: c.changedAt,
      price: c.newValue
    }));
  }
});
```

---

## 4. Pipeline Orchestration

### Hybrid Approach: Convex + External Workers

**Problem:** Convex actions have 5-minute timeout, browser scraping can be slow.

**Solution:** Use Convex for orchestration, external workers for heavy lifting.

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│            CONVEX (Orchestration Layer)                  │
│  • Job scheduling (cron)                                │
│  • State management (job queue)                         │
│  • Data storage (products, changes)                     │
│  • Real-time queries (subscriptions)                    │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTP/Webhook
                     ▼
┌──────────────────────────────────────────────────────────┐
│          EXTERNAL WORKER POOL (Node.js)                  │
│  • Long-running scraping tasks                          │
│  • Browser automation (Playwright)                      │
│  • Heavy CPU work (normalization, entity resolution)    │
│  • Reports back to Convex via mutation                  │
└──────────────────────────────────────────────────────────┘
```

### Implementation

#### Convex: Job Scheduler
```typescript
// convex/crons.ts
import { cronJobs } from 'convex/server';
import { internal } from './_generated/api';

const crons = cronJobs();

// Schedule scraping for high-priority stores (every 15 min)
crons.interval(
  'scrape-tier1-stores',
  { minutes: 15 },
  internal.scraping.scheduleTier1
);

// Schedule scraping for normal stores (every hour)
crons.hourly(
  'scrape-tier2-stores',
  { minuteUTC: 0 },
  internal.scraping.scheduleTier2
);

export default crons;
```

#### Convex: Job Queue Management
```typescript
// convex/scraping.ts
export const scheduleTier1 = internalMutation({
  handler: async (ctx) => {
    const tier1Stores = await ctx.db
      .query('stores')
      .withIndex('by_tier', q => q.eq('tier', 1))
      .collect();
    
    for (const store of tier1Stores) {
      // Add to job queue
      await ctx.db.insert('scrapeJobs', {
        storeId: store._id,
        status: 'pending',
        priority: 1,
        scheduledAt: Date.now(),
        attempts: 0
      });
      
      // Trigger external worker via webhook
      await triggerWorker(store._id);
    }
  }
});

async function triggerWorker(storeId: string) {
  // Option 1: HTTP webhook to worker pool
  await fetch('https://workers.budalert.com/scrape', {
    method: 'POST',
    body: JSON.stringify({ storeId }),
    headers: { 'Authorization': `Bearer ${process.env.WORKER_SECRET}` }
  });
  
  // Option 2: Redis pub/sub
  // await redis.publish('scrape-jobs', JSON.stringify({ storeId }));
  
  // Option 3: Convex action (if job fits in 5 min)
  // await ctx.scheduler.runAfter(0, internal.scraping.runScrapeJob, { storeId });
}
```

#### External Worker: Job Processor
```typescript
// workers/scraper.ts
import express from 'express';
import { ConvexHttpClient } from 'convex/browser';

const app = express();
const convex = new ConvexHttpClient(process.env.CONVEX_URL);

app.post('/scrape', async (req, res) => {
  const { storeId } = req.body;
  
  // Acknowledge immediately (don't block)
  res.status(202).json({ status: 'accepted' });
  
  // Process asynchronously
  processJob(storeId);
});

async function processJob(storeId: string) {
  try {
    // Mark job as in-progress
    await convex.mutation(api.scraping.markJobStarted, { storeId });
    
    // Fetch store details
    const store = await convex.query(api.stores.get, { id: storeId });
    
    // Scrape (this can take minutes)
    const products = await scrapeStore(store);
    
    // Send results back to Convex
    await convex.mutation(api.scraping.saveProducts, {
      storeId,
      products,
      scrapedAt: Date.now()
    });
    
    // Mark job as complete
    await convex.mutation(api.scraping.markJobComplete, { storeId });
    
  } catch (error) {
    // Mark job as failed
    await convex.mutation(api.scraping.markJobFailed, {
      storeId,
      error: error.message
    });
  }
}

app.listen(3000);
```

#### Convex: Result Handler
```typescript
// convex/scraping.ts
export const saveProducts = mutation({
  args: {
    storeId: v.id('stores'),
    products: v.array(v.any()),
    scrapedAt: v.number()
  },
  handler: async (ctx, args) => {
    const results = {
      new: 0,
      updated: 0,
      unchanged: 0,
      errors: []
    };
    
    for (const productData of args.products) {
      try {
        // Validate
        const validated = validateProduct(productData);
        
        // Check if exists
        const existing = await ctx.db
          .query('products')
          .withIndex('by_external_id', q => 
            q.eq('externalId', `${args.storeId}_${validated.id}`)
          )
          .first();
        
        if (!existing) {
          // New product
          await ctx.db.insert('products', {
            ...validated,
            storeId: args.storeId,
            lastScraped: args.scrapedAt,
            lastChanged: args.scrapedAt
          });
          results.new++;
        } else {
          // Detect changes
          const changes = await detectChanges(existing._id, validated);
          
          if (changes.length > 0) {
            // Update product
            await ctx.db.patch(existing._id, {
              ...validated,
              lastScraped: args.scrapedAt,
              lastChanged: args.scrapedAt
            });
            
            // Log changes
            for (const change of changes) {
              await ctx.db.insert('productChanges', change);
            }
            
            // Emit events
            await emitChangeEvents(changes);
            
            results.updated++;
          } else {
            // Just update lastScraped
            await ctx.db.patch(existing._id, {
              lastScraped: args.scrapedAt
            });
            results.unchanged++;
          }
        }
      } catch (error) {
        results.errors.push({
          product: productData.name,
          error: error.message
        });
      }
    }
    
    // Update store status
    await ctx.db.patch(args.storeId, {
      lastScraped: args.scrapedAt,
      scrapeStatus: 'success'
    });
    
    return results;
  }
});
```

---

## 5. Scalability Patterns

### Challenge: Linear Cost Growth

**Naive Approach:** Scrape every store every hour = 500 stores × 24 hours = 12,000 scrapes/day

**Problem:** Most products don't change hourly. Wasting 90%+ of scrapes.

### Pattern 1: Differential Scraping

**Concept:** Only re-scrape when likely to have changed.

```typescript
function shouldScrapeStore(store: Store): boolean {
  const hoursSinceLastScrape = (Date.now() - store.lastScraped) / 3600000;
  
  // Priority-based scheduling
  if (store.tier === 1) return hoursSinceLastScrape >= 0.25; // 15 min
  if (store.tier === 2) return hoursSinceLastScrape >= 1;    // 1 hour
  if (store.tier === 3) return hoursSinceLastScrape >= 4;    // 4 hours
  
  // Adaptive: scrape more if high velocity
  const velocity = store.avgVelocityScore || 0;
  const multiplier = Math.max(0.5, 1 / (velocity / 50));
  
  return hoursSinceLastScrape >= (1 * multiplier);
}
```

### Pattern 2: Incremental Scraping

**Concept:** Don't scrape entire menu if only checking for changes.

```typescript
async function incrementalScrape(store: Store): Promise<Product[]> {
  // 1. Quick check: count products on page
  const currentCount = await getProductCount(store);
  const cachedCount = store.lastProductCount || 0;
  
  if (Math.abs(currentCount - cachedCount) < 5) {
    // No significant changes, sample a few products
    return await sampleProducts(store, 10);
  } else {
    // Significant change detected, full scrape
    return await fullScrape(store);
  }
}
```

### Pattern 3: Caching & ETags

**Concept:** Use HTTP caching when available.

```typescript
async function scrapeWithCache(store: Store): Promise<Product[]> {
  const cacheKey = `scrape:${store.id}`;
  const cached = await redis.get(cacheKey);
  
  if (cached) {
    const { etag, data } = JSON.parse(cached);
    
    // Make conditional request
    const response = await axios.get(store.menuUrl, {
      headers: { 'If-None-Match': etag }
    });
    
    if (response.status === 304) {
      // Not modified, return cached data
      return data;
    }
    
    // Modified, cache new data
    await redis.set(cacheKey, JSON.stringify({
      etag: response.headers.etag,
      data: response.data
    }), 'EX', 3600);
    
    return response.data;
  }
  
  // First scrape, no cache
  return await fullScrape(store);
}
```

### Pattern 4: Smart Batching

**Concept:** Batch operations to reduce overhead.

```typescript
// Bad: One mutation per product
for (const product of products) {
  await ctx.db.insert('products', product); // Many round-trips
}

// Good: Batch insert
await batchInsert(ctx, 'products', products, { batchSize: 50 });

// Helper
async function batchInsert<T>(
  ctx: MutationCtx,
  table: string,
  items: T[],
  options: { batchSize: number }
): Promise<void> {
  const batches = chunk(items, options.batchSize);
  
  for (const batch of batches) {
    await Promise.all(
      batch.map(item => ctx.db.insert(table, item))
    );
  }
}
```

### Pattern 5: Data Compression

**Concept:** Compress large payloads before storage.

```typescript
import { gzip, gunzip } from 'zlib';
import { promisify } from 'util';

const gzipAsync = promisify(gzip);
const gunzipAsync = promisify(gunzip);

// Save to R2 with compression
async function saveToR2(key: string, data: any): Promise<void> {
  const json = JSON.stringify(data);
  const compressed = await gzipAsync(json);
  
  await r2.put(key, compressed, {
    httpMetadata: { contentEncoding: 'gzip' }
  });
  
  // Original: 1MB → Compressed: ~100KB (10x reduction)
}
```

---

## Cost Optimization Summary

### Scraping Costs

| Strategy | Saves | Impact |
|----------|-------|--------|
| **Adaptive scheduling** | 50% fewer scrapes | High velocity only |
| **Incremental scraping** | 70% faster | Sample vs full scrape |
| **Caching (ETags)** | 90% for static sites | WordPress, etc. |
| **Smart batching** | Reduce DB overhead | Fewer transactions |

**Projected Savings:**
- Naive: 12,000 scrapes/day × 30s avg = **100 hours/day compute**
- Optimized: 6,000 scrapes/day × 15s avg = **25 hours/day compute**
- **75% cost reduction**

### Storage Costs

| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| **Hot/cold tiering** | 95% storage costs | 7-day hot window |
| **Compression (gzip)** | 90% for JSON | CPU overhead (minimal) |
| **Retention policies** | 80% long-term | Delete old raw data |
| **Columnar archives** | 99% for analytics | Parquet vs JSON |

**Projected Costs:**
- Convex (hot): ~120 MB = **$0** (free tier)
- R2 (cold): ~72 GB compressed to ~7 GB = **$0.10/month**
- **Total storage: ~$0.10/month**

---

## Phase 3 Complete ✅

**Deliverables:**
1. ✅ Ingestion layer design (raw → validation → staging → production)
2. ✅ Storage strategy (hot Convex + cold R2 tiering)
3. ✅ Change detection system (SKU velocity calculation, historical tracking)
4. ✅ Pipeline orchestration (Convex + external workers hybrid)
5. ✅ Scalability patterns (differential scraping, caching, batching, compression)
6. ✅ Cost optimization (75% compute savings, 95% storage savings)

**Next Phase:** Transformation Layer (normalization, entity resolution, derived metrics, LLM assistance)

---
