# Phase 4: Scraping Infrastructure for Velocity - Distributed Architecture

**Date:** 2026-03-05  
**Researcher:** sku-velocity-research subagent  
**Focus:** Design scraping architecture that captures velocity at scale

---

## Executive Summary

Velocity tracking requires **frequent, consistent snapshots** of inventory across hundreds of stores. This phase designs a **distributed scraping infrastructure** that:

- Scrapes **500 stores** every **15 minutes to 12 hours** (adaptive frequency)
- Handles **100K+ products** without overloading targets
- Detects changes in **<30 seconds** (for high-velocity items)
- Costs **<$70/month** at full scale
- Achieves **>95% uptime** with fault tolerance

**Architecture:** **Worker pool + job queue + change detection + adaptive scheduling**

---

## The Velocity Scraping Challenge

### Requirements

| Requirement | Target | Challenge |
|-------------|--------|-----------|
| **Stores** | 500+ | Each has different platform, protection, rate limits |
| **Products/store** | 100-300 | Must scrape entire menu, not just top items |
| **Scrape frequency** | 15 min - 12 hr | Too fast = banned, too slow = miss changes |
| **Change detection** | <1 min latency | Need real-time delta calculation |
| **Cost** | <$70/month | Can't just throw money at cloud compute |
| **Reliability** | >95% uptime | Single points of failure = data loss |
| **Stealth** | <1% ban rate | Bot detection is sophisticated |

### Why Basic Cron Jobs Don't Work

```javascript
// ❌ NAIVE APPROACH (doesn't scale)
// Run every store every 30 minutes
cron.schedule('*/30 * * * *', async () => {
  for (const store of stores) {
    await scrapeStore(store); // Sequential, slow
  }
});

// Problems:
// 1. Sequential = 500 stores × 30 sec = 4.1 hours (can't finish in 30 min)
// 2. No failure handling (one crash = whole batch fails)
// 3. No rate limiting per store
// 4. No adaptive frequency (wastes resources on slow movers)
// 5. No change detection (just overwrites data)
```

---

## Proposed Architecture: Distributed Worker Pool

```
┌──────────────────────────────────────────────────────────┐
│  SCHEDULER (Convex Cron)                                │
│  - Runs every 5 minutes                                  │
│  - Generates scrape jobs based on priority               │
│  - Adaptive: high-velocity stores → every 15 min         │
│             low-velocity stores → every 12 hours         │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  JOB QUEUE (BullMQ on Redis)                            │
│  - Stores pending scrape jobs                           │
│  - Priority: high-velocity stores first                  │
│  - Rate limiting: max N jobs/store/hour                  │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  WORKER POOL (2× Hetzner VPS)                           │
│  - Worker 1: Handles 250 stores                          │
│  - Worker 2: Handles 250 stores                          │
│  - Each worker: 4 concurrent scrapes                     │
│  - PM2 process manager (auto-restart)                   │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼ (scrape results)
┌──────────────────────────────────────────────────────────┐
│  INGESTION PIPELINE                                      │
│  - Validate scraped data                                 │
│  - Store in menuSnapshots (Convex)                       │
│  - Trigger change detection                              │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  CHANGE DETECTION ENGINE                                 │
│  - Compare current vs previous scrape                    │
│  - Calculate deltas (quantity, price, stock status)      │
│  - Generate events (restock, sold_out)                   │
│  - Update velocity scores                                │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  STORAGE (Convex + R2)                                   │
│  - Hot: Convex (last 7 days, fast queries)              │
│  - Cold: R2 (90+ days, compressed)                       │
└──────────────────────────────────────────────────────────┘
```

---

## Component 1: Adaptive Scheduler

### Frequency Calculation

```javascript
function calculateScrapeInterval(storeMetrics) {
  const velocityScore = storeMetrics.avgVelocityScore; // 0-100
  const lastChangeTime = Date.now() - storeMetrics.lastChangeAt;
  const errorRate = storeMetrics.recentErrorRate;
  
  // Base frequency by velocity
  let intervalMs;
  if (velocityScore >= 80) {
    intervalMs = 15 * 60 * 1000; // 15 minutes (very high velocity)
  } else if (velocityScore >= 60) {
    intervalMs = 30 * 60 * 1000; // 30 minutes (high velocity)
  } else if (velocityScore >= 40) {
    intervalMs = 60 * 60 * 1000; // 1 hour (medium velocity)
  } else if (velocityScore >= 20) {
    intervalMs = 4 * 60 * 60 * 1000; // 4 hours (low velocity)
  } else {
    intervalMs = 12 * 60 * 60 * 1000; // 12 hours (very low velocity)
  }
  
  // Backoff if no recent changes (stale inventory)
  if (lastChangeTime > 48 * 60 * 60 * 1000) { // 48 hours
    intervalMs *= 2; // Double the interval
  }
  
  // Backoff if high error rate (target is unstable/blocking)
  if (errorRate > 0.1) { // >10% errors
    intervalMs *= 1.5;
  }
  
  return intervalMs;
}
```

### Scheduler Implementation (Convex Cron)

```typescript
// convex/crons.ts
import { cronJobs } from 'convex/server';
import { internal } from './_generated/api';

const crons = cronJobs();

crons.interval(
  'generate-scrape-jobs',
  { minutes: 5 }, // Run every 5 minutes
  internal.scraping.generateJobs
);

export default crons;

// convex/scraping.ts
export const generateJobs = internalMutation({
  handler: async (ctx) => {
    const stores = await ctx.db.query('retailers').collect();
    const now = Date.now();
    
    for (const store of stores) {
      const metrics = await getStoreMetrics(ctx, store._id);
      const interval = calculateScrapeInterval(metrics);
      const lastScrape = metrics.lastScrapeAt || 0;
      
      if (now - lastScrape >= interval) {
        // Time to scrape!
        await queueScrapeJob(ctx, {
          storeId: store._id,
          priority: metrics.avgVelocityScore, // High velocity = high priority
          scheduledAt: now
        });
      }
    }
  }
});
```

**Why every 5 minutes?**
- Convex cron minimum is 1 minute
- 5 minutes balances responsiveness vs overhead
- Can still detect high-velocity changes within 15-20 minutes total

---

## Component 2: Job Queue (BullMQ)

### Why BullMQ?
- Distributed (Redis-backed, works across multiple workers)
- Priority queues (high-velocity stores processed first)
- Rate limiting (max N jobs/store/hour)
- Retry logic (exponential backoff)
- Job persistence (survives worker crashes)

### Queue Setup

```javascript
// workers/queue.js
import { Queue, Worker } from 'bullmq';
import Redis from 'ioredis';

const redis = new Redis({
  host: 'localhost', // Redis on same VPS
  port: 6379,
  maxRetriesPerRequest: null
});

const scrapeQueue = new Queue('scrape-jobs', {
  connection: redis,
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000 // 2s, 4s, 8s
    },
    removeOnComplete: 100, // Keep last 100 completed jobs
    removeOnFail: 500      // Keep last 500 failed jobs
  }
});

// Add job from Convex webhook/cron
export async function addScrapeJob(storeId, priority) {
  await scrapeQueue.add(
    `scrape-${storeId}`,
    { storeId },
    {
      priority: priority, // 0-100 (higher = processed first)
      jobId: `${storeId}-${Date.now()}`, // Unique ID
      removeOnComplete: true,
      removeOnFail: false
    }
  );
}
```

### Rate Limiting

```javascript
// Max 1 scrape per store per 10 minutes (safety)
const rateLimiter = {
  max: 1,
  duration: 10 * 60 * 1000, // 10 minutes
  groupKey: (job) => job.data.storeId
};

scrapeQueue.setRateLimiter(rateLimiter);
```

---

## Component 3: Worker Pool

### Worker Configuration

```javascript
// workers/scraper-worker.js
import { Worker } from 'bullmq';
import { scrapeStore } from './scrapers/index.js';

const worker = new Worker(
  'scrape-jobs',
  async (job) => {
    const { storeId } = job.data;
    
    console.log(`[Worker ${process.env.WORKER_ID}] Scraping store ${storeId}`);
    
    try {
      const result = await scrapeStore(storeId);
      
      // Send to ingestion pipeline
      await ingestScrapeResult(result);
      
      return { success: true, products: result.products.length };
    } catch (error) {
      console.error(`[Worker ${process.env.WORKER_ID}] Error:`, error);
      throw error; // Trigger retry
    }
  },
  {
    connection: redis,
    concurrency: 4, // 4 concurrent scrapes per worker
    limiter: {
      max: 20,        // Max 20 jobs processed
      duration: 60000 // Per minute
    }
  }
);

worker.on('completed', (job, result) => {
  console.log(`✓ Job ${job.id} completed: ${result.products} products`);
});

worker.on('failed', (job, err) => {
  console.error(`✗ Job ${job.id} failed:`, err.message);
});
```

### Deployment (PM2)

```bash
# pm2.config.js
module.exports = {
  apps: [
    {
      name: 'scraper-worker-1',
      script: './workers/scraper-worker.js',
      instances: 1,
      exec_mode: 'fork',
      env: {
        WORKER_ID: 1,
        NODE_ENV: 'production'
      },
      error_file: './logs/worker-1-error.log',
      out_file: './logs/worker-1-out.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s'
    }
  ]
};

# Deploy
pm2 start pm2.config.js
pm2 save
pm2 startup # Auto-start on boot
```

### Horizontal Scaling (2 VPS)

**VPS 1:** Handles stores 1-250  
**VPS 2:** Handles stores 251-500

```javascript
// Route jobs to specific worker based on storeId
function getWorkerForStore(storeId) {
  const storeIndex = parseInt(storeId.slice(-3)); // Last 3 chars
  return storeIndex % 2 === 0 ? 'worker-1' : 'worker-2';
}
```

**Alternatively:** Use Redis queue (both workers pull from same queue, no routing needed)

---

## Component 4: Scraper Execution Layer

### Platform Adapter Pattern

```javascript
// scrapers/index.js
import DutchieScraper from './platforms/dutchie.js';
import WordPressScraper from './platforms/wordpress.js';
import BlazeScraper from './platforms/blaze.js';

const SCRAPERS = {
  dutchie: DutchieScraper,
  wordpress: WordPressScraper,
  blaze: BlazeScraper
};

export async function scrapeStore(storeId) {
  const store = await getStoreConfig(storeId);
  const ScraperClass = SCRAPERS[store.platform];
  
  if (!ScraperClass) {
    throw new Error(`Unsupported platform: ${store.platform}`);
  }
  
  const scraper = new ScraperClass(store);
  
  const startTime = Date.now();
  const result = await scraper.scrape();
  const duration = Date.now() - startTime;
  
  return {
    storeId,
    platform: store.platform,
    products: result.products,
    scrapedAt: Date.now(),
    duration,
    success: true
  };
}
```

### Base Scraper Class

```javascript
// scrapers/base.js
export class BaseScraper {
  constructor(storeConfig) {
    this.config = storeConfig;
    this.browser = null;
  }
  
  async scrape() {
    throw new Error('scrape() must be implemented by subclass');
  }
  
  async launchBrowser() {
    const { chromium } = await import('playwright');
    this.browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    return this.browser;
  }
  
  async closeBrowser() {
    if (this.browser) {
      await this.browser.close();
    }
  }
  
  async withRetry(fn, maxAttempts = 3) {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        return await fn();
      } catch (error) {
        if (i === maxAttempts - 1) throw error;
        await this.delay(Math.pow(2, i) * 1000);
      }
    }
  }
  
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### Dutchie Scraper Example

```javascript
// scrapers/platforms/dutchie.js
import { BaseScraper } from '../base.js';

export default class DutchieScraper extends BaseScraper {
  async scrape() {
    const products = await this.withRetry(async () => {
      const response = await fetch('https://api.dutchie.com/graphql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `
            query GetMenu($dispensaryId: ID!) {
              menu(dispensaryId: $dispensaryId) {
                products {
                  id name price inStock quantity
                  brand { name }
                  category
                  potencyThc { formatted }
                }
              }
            }
          `,
          variables: { dispensaryId: this.config.dutchieId }
        })
      });
      
      const data = await response.json();
      return data.data.menu.products;
    });
    
    return {
      products: products.map(p => this.normalizeProduct(p)),
      count: products.length
    };
  }
  
  normalizeProduct(raw) {
    return {
      id: raw.id,
      name: raw.name,
      brand: raw.brand?.name,
      category: raw.category,
      price: raw.price,
      inStock: raw.inStock,
      quantity: raw.quantity, // Dutchie exposes this!
      thc: raw.potencyThc?.formatted,
      scrapedAt: Date.now(),
      source: this.config.slug
    };
  }
}
```

---

## Component 5: Ingestion Pipeline

### Validation Layer

```javascript
// ingestion/validator.js
export function validateProduct(product, store) {
  const errors = [];
  
  // Required fields
  if (!product.name) errors.push('Missing name');
  if (!product.category) errors.push('Missing category');
  if (typeof product.price !== 'number') errors.push('Invalid price');
  if (typeof product.inStock !== 'boolean') errors.push('Invalid inStock');
  
  // Data quality
  if (product.price < 0 || product.price > 1000) {
    errors.push(`Suspicious price: $${product.price}`);
  }
  
  if (product.quantity && (product.quantity < 0 || product.quantity > 10000)) {
    errors.push(`Suspicious quantity: ${product.quantity}`);
  }
  
  // Duplicates
  if (!product.id) {
    // Generate ID from name + store
    product.id = `${store.slug}-${slugify(product.name)}`;
  }
  
  if (errors.length > 0) {
    return { valid: false, errors };
  }
  
  return { valid: true, product };
}
```

### Storage in Convex

```javascript
// ingestion/store.js
export async function ingestScrapeResult(result) {
  const { storeId, products, scrapedAt } = result;
  
  // 1. Store raw snapshot
  const snapshotId = await storeSnapshot(storeId, products, scrapedAt);
  
  // 2. Update current inventory
  await updateCurrentInventory(storeId, products);
  
  // 3. Trigger change detection
  await detectChanges(storeId, snapshotId);
  
  return snapshotId;
}

async function storeSnapshot(storeId, products, scrapedAt) {
  // Convex mutation via HTTP
  const response = await fetch(`${CONVEX_URL}/api/mutations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      path: 'scraping/storeSnapshot',
      args: {
        retailerId: storeId,
        products: products,
        scrapedAt: scrapedAt
      }
    })
  });
  
  const result = await response.json();
  return result.snapshotId;
}
```

---

## Component 6: Change Detection Engine

### Delta Calculation

```javascript
// convex/changeDetection.ts
export const detectChanges = internalMutation({
  handler: async (ctx, { storeId, snapshotId }) => {
    const currentSnapshot = await ctx.db.get(snapshotId);
    const previousSnapshot = await getPreviousSnapshot(ctx, storeId);
    
    if (!previousSnapshot) {
      // First scrape, no comparison
      return { deltas: 0 };
    }
    
    const deltas = [];
    const events = [];
    
    // Build product maps for comparison
    const currentProducts = new Map(
      currentSnapshot.products.map(p => [p.id, p])
    );
    const previousProducts = new Map(
      previousSnapshot.products.map(p => [p.id, p])
    );
    
    // Compare each product
    for (const [productId, current] of currentProducts) {
      const previous = previousProducts.get(productId);
      
      if (!previous) {
        // New product
        events.push({
          type: 'new_product',
          productId,
          retailerId: storeId,
          timestamp: currentSnapshot.scrapedAt
        });
        continue;
      }
      
      // Calculate delta
      const delta = calculateDelta(previous, current);
      
      if (delta.hasChanges) {
        deltas.push({
          productId,
          retailerId: storeId,
          ...delta,
          scrapedAt: currentSnapshot.scrapedAt
        });
        
        // Generate events
        events.push(...generateEvents(delta, productId, storeId));
      }
    }
    
    // Check for removed products
    for (const [productId, previous] of previousProducts) {
      if (!currentProducts.has(productId)) {
        events.push({
          type: 'product_removed',
          productId,
          retailerId: storeId,
          timestamp: currentSnapshot.scrapedAt
        });
      }
    }
    
    // Store deltas and events
    await ctx.db.insert('inventoryDeltas', deltas);
    await ctx.db.insert('inventoryEvents', events);
    
    // Update velocity scores
    await updateVelocityScores(ctx, storeId, deltas);
    
    return { deltas: deltas.length, events: events.length };
  }
});

function calculateDelta(previous, current) {
  const delta = {
    hasChanges: false,
    quantityChange: null,
    priceChange: null,
    stockChange: null
  };
  
  // Quantity change
  if (previous.quantity !== undefined && current.quantity !== undefined) {
    if (previous.quantity !== current.quantity) {
      delta.quantityChange = current.quantity - previous.quantity;
      delta.hasChanges = true;
    }
  }
  
  // Price change
  if (previous.price !== current.price) {
    delta.priceChange = current.price - previous.price;
    delta.hasChanges = true;
  }
  
  // Stock status change
  if (previous.inStock !== current.inStock) {
    delta.stockChange = current.inStock ? 'restocked' : 'sold_out';
    delta.hasChanges = true;
  }
  
  return delta;
}

function generateEvents(delta, productId, storeId) {
  const events = [];
  
  if (delta.stockChange === 'sold_out') {
    events.push({
      type: 'sold_out',
      productId,
      retailerId: storeId,
      timestamp: Date.now()
    });
  }
  
  if (delta.stockChange === 'restocked') {
    events.push({
      type: 'restock',
      productId,
      retailerId: storeId,
      timestamp: Date.now()
    });
  }
  
  if (delta.priceChange && Math.abs(delta.priceChange) > 5) {
    events.push({
      type: delta.priceChange > 0 ? 'price_increase' : 'price_drop',
      productId,
      retailerId: storeId,
      priceChange: delta.priceChange,
      timestamp: Date.now()
    });
  }
  
  return events;
}
```

---

## Component 7: Data Retention & Archival

### Hot Storage (Convex - 7 days)

```javascript
// Keep last 7 days in Convex for fast queries
export const archiveOldSnapshots = internalMutation({
  handler: async (ctx) => {
    const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    const oldSnapshots = await ctx.db
      .query('menuSnapshots')
      .filter(q => q.lt(q.field('scrapedAt'), sevenDaysAgo))
      .collect();
    
    // Archive to R2
    for (const snapshot of oldSnapshots) {
      await archiveToR2(snapshot);
      await ctx.db.delete(snapshot._id);
    }
    
    return { archived: oldSnapshots.length };
  }
});
```

### Cold Storage (R2 - 90 days compressed)

```javascript
// workers/archival.js
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { gzip } from 'zlib';
import { promisify } from 'util';

const gzipAsync = promisify(gzip);

const r2 = new S3Client({
  region: 'auto',
  endpoint: process.env.R2_ENDPOINT,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY,
    secretAccessKey: process.env.R2_SECRET_KEY
  }
});

export async function archiveToR2(snapshot) {
  const json = JSON.stringify(snapshot);
  const compressed = await gzipAsync(Buffer.from(json));
  
  const key = `snapshots/${snapshot.retailerId}/${snapshot.scrapedAt}.json.gz`;
  
  await r2.send(new PutObjectCommand({
    Bucket: 'budalert-snapshots',
    Key: key,
    Body: compressed,
    ContentType: 'application/json',
    ContentEncoding: 'gzip'
  }));
  
  console.log(`Archived ${key} (${compressed.length} bytes)`);
}
```

**Cost:** R2 storage = $0.015/GB/month  
**Estimate:** 100K products × 2KB/product × 90 days = 18GB = **$0.27/month**

---

## Performance Targets

| Metric | Target | How Measured |
|--------|--------|--------------|
| **Scrape duration** | <30s per store | Worker logs |
| **Queue latency** | <5 min (high priority) | Time from enqueue → start |
| **Success rate** | >95% | Successful jobs / total jobs |
| **Change detection latency** | <30s | Time from scrape → delta stored |
| **Uptime** | >99% | Worker health checks |
| **Cost** | <$70/month at 500 stores | Infrastructure spend |

---

## Monitoring & Alerting

### Metrics to Track

```javascript
// Send to monitoring service (Axiom, Sentry, etc.)
const metrics = {
  scraping: {
    jobsEnqueued: counter(),
    jobsCompleted: counter(),
    jobsFailed: counter(),
    scrapeDuration: histogram(),
    productsScraped: counter()
  },
  changeDetection: {
    deltasDetected: counter(),
    eventsGenerated: counter(),
    restockEvents: counter(),
    soldOutEvents: counter()
  },
  system: {
    workerUptime: gauge(),
    queueDepth: gauge(),
    redisMemory: gauge()
  }
};
```

### Alerts

```javascript
// Alert if:
// - Worker down for >5 minutes
// - Error rate >10%
// - Queue depth >100 jobs
// - No scrapes completed in last 15 minutes
// - Convex storage >80% of free tier

const alerts = [
  {
    name: 'worker-down',
    condition: 'workerUptime === 0 for 5 minutes',
    channel: 'email'
  },
  {
    name: 'high-error-rate',
    condition: 'errorRate > 0.10',
    channel: 'email'
  },
  {
    name: 'queue-backlog',
    condition: 'queueDepth > 100',
    channel: 'slack'
  }
];
```

---

## Cost Breakdown (500 Stores at Scale)

| Component | Cost/Month | Notes |
|-----------|-----------|-------|
| **2× Hetzner VPS** (CPX21) | $12 | 3 vCPU, 4GB RAM each |
| **Redis** (on VPS) | $0 | Self-hosted |
| **Residential proxies** | $30 | For hard targets (~10% of stores) |
| **Datacenter proxies** | $20 | For medium targets (~30% of stores) |
| **Convex** | $0 | Free tier (1GB, 1M calls) |
| **R2 storage** | $1 | 18GB compressed snapshots |
| **Monitoring** (Axiom) | $0 | Free tier |
| **Domain/SSL** | $0 | Cloudflare free |
| **Total** | **$63/month** | At 500 stores, 100K products |

**Per-store cost:** $0.126/month (~12.6 cents)

**Scaling:**
- 1,000 stores: Add 2 more VPS ($12) = $75/month
- 5,000 stores: 10× VPS ($60) + proxies ($100) = $160/month

**Linear scaling, not exponential!**

---

## Implementation Phases

### Phase 1: MVP (Weeks 1-2)
- Set up 1 VPS + Redis
- Implement BullMQ queue
- Build 3 platform scrapers (Dutchie, WordPress, Blaze)
- Basic change detection
- Scrape 20 stores manually
- **Cost: $6/month**

### Phase 2: Automation (Weeks 3-4)
- Convex cron scheduler
- Adaptive frequency logic
- Delta calculation pipeline
- Scale to 100 stores
- **Cost: $31/month**

### Phase 3: Scale (Weeks 5-8)
- Add 2nd VPS
- Implement archival (R2)
- Add monitoring
- Scale to 500 stores
- **Cost: $63/month**

---

## Next Phase Preview

**Phase 5 will design the data pipeline** that transforms raw scrape data into velocity metrics:
- Aggregation algorithms
- Velocity scoring formulas
- Time-series analysis
- Forecasting models

---

## Conclusion

A **distributed worker pool** architecture enables velocity tracking at scale:
- ✅ Handles 500 stores without overload
- ✅ Adaptive scraping (15 min - 12 hr based on velocity)
- ✅ Change detection in <30 seconds
- ✅ <$70/month at full scale
- ✅ >95% uptime with fault tolerance

**Key insight:** Don't scrape everything all the time. Scrape **smart** (adaptive frequency) and **distributed** (worker pool).

---

**Phase 4 Complete.** Proceeding to Phase 5: Data Pipeline for Velocity Calculation.
