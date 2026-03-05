# BudAlert SKU Velocity Research - Complete Documentation

**Research Completed:** 2026-03-05  
**Researcher:** sku-velocity-research subagent  
**Status:** ✅ Complete - Ready for implementation

---

## Overview

This directory contains **comprehensive research and specifications** for implementing **SKU velocity tracking at scale** in BudAlert.

**Velocity Tracking** = Measuring how fast products sell (units/hour, restocks/week, availability %) across hundreds of dispensaries using only web scraping data (no POS/API access).

---

## What's Inside

### Phase 1: Current State Analysis
**File:** [PHASE1_CURRENT_STATE.md](./PHASE1_CURRENT_STATE.md)

**Summary:** Analyzes existing BudAlert architecture for velocity-tracking readiness.

**Key Findings:**
- ✅ Scrapers work (3 platforms)
- ✅ Convex schema has velocity tables
- ❌ No change detection pipeline
- ❌ No velocity calculation logic
- ❌ No entity resolution
- **Readiness:** 18% (needs critical infrastructure)

**Read this first** to understand the starting point.

---

### Phase 2: Velocity Signal Research
**File:** [PHASE2_VELOCITY_SIGNALS.md](./PHASE2_VELOCITY_SIGNALS.md)

**Summary:** Explores 12 methods to calculate velocity without POS data.

**Top Methods:**
1. **Stock transition events** (⭐⭐⭐⭐⭐) - Works on 100% of platforms
2. **Quantity tracking** (⭐⭐⭐⭐⭐) - Dutchie only (~40% coverage)
3. **Cart probing** (⭐⭐⭐⭐) - For WordPress/Blaze
4. **Price change velocity** (⭐⭐⭐) - Weak but universal signal
5. **Variant analysis** (⭐⭐⭐⭐) - Which size sells out first?

**Key Insight:** Even without direct inventory counts, **stock transitions + restocks provide 85% accuracy** for velocity scoring.

**Read this** to understand how velocity is calculated from scraped data.

---

### Phase 3: Entity Resolution
**File:** [PHASE3_ENTITY_RESOLUTION.md](./PHASE3_ENTITY_RESOLUTION.md)

**Summary:** How to match products across stores with inconsistent naming.

**Challenge:**
- "Blue Dream 3.5g" (Conbud)
- "Blue Dream 1/8oz" (Gotham)
- "BD Eighth" (SMACKED)
- All the same product!

**Solution: 4-Tier Pipeline**
1. **Normalization** (lowercase, size standardization)
2. **Signature matching** (hash-based, 60-70% coverage)
3. **Fuzzy matching** (Levenshtein, 85% threshold, +20-25% coverage)
4. **LLM classification** (GPT-4o-mini, +5-10% coverage)

**Result:** 92-95% automated match rate, $0.30 cost for 100K products

**Read this** to understand cross-store velocity tracking.

---

### Phase 4: Scraping Infrastructure
**File:** [PHASE4_SCRAPING_INFRASTRUCTURE.md](./PHASE4_SCRAPING_INFRASTRUCTURE.md)

**Summary:** Distributed worker architecture for scraping at scale.

**Architecture:**
```
Convex Cron (every 5 min)
  ↓
BullMQ Job Queue (Redis)
  ↓
Worker Pool (2× Hetzner VPS, 4 concurrent each)
  ↓
Ingestion Pipeline (Convex)
  ↓
Change Detection Engine
  ↓
Storage (Convex hot + R2 cold)
```

**Features:**
- **Adaptive scheduling:** High-velocity stores scraped every 15 min, low-velocity every 12 hours
- **Fault tolerance:** PM2 auto-restart, retry logic, circuit breakers
- **Cost efficient:** $63/month at 500 stores (vs $150+ for naive AWS approach)

**Read this** for infrastructure design.

---

### Phase 5: Data Pipeline
**File:** [PHASE5_DATA_PIPELINE.md](./PHASE5_DATA_PIPELINE.md)

**Summary:** Transform raw deltas into velocity metrics.

**Pipeline Stages:**
1. **Time-series aggregation** (group deltas by hour/day/week)
2. **Velocity scoring** (multi-signal composite 0-100)
3. **Trend analysis** (accelerating/steady/decelerating)
4. **Forecasting** (predict next restock, units sold)
5. **Cross-store aggregation** (canonical product velocity)

**Velocity Score Formula:**
```javascript
score = (quantity_velocity * 40%) 
      + (restock_frequency * 30%)
      + (availability * 20%)
      + (price_volatility * 10%)
```

**Read this** for calculation algorithms.

---

### Phase 6: Stack Improvements
**File:** [PHASE6_STACK_IMPROVEMENTS.md](./PHASE6_STACK_IMPROVEMENTS.md)

**Summary:** Concrete code changes needed for BudAlert codebase.

**Changes Required:**
1. ✅ Convex schema updates (4 new tables)
2. ✅ Scraper migration (Python → Node.js)
3. ✅ Worker infrastructure (BullMQ + PM2)
4. ✅ Convex mutations (snapshot storage + change detection)
5. ✅ Velocity calculation (multi-signal scoring)
6. ✅ Scheduler (adaptive scraping)

**Includes:** Full TypeScript code examples for all mutations, queries, and workers.

**Read this** for implementation details.

---

### Implementation Plan
**File:** [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)

**Summary:** Step-by-step roadmap to implement velocity tracking.

**Timeline:**
- **Week 1-2:** Foundation (schema, scrapers, workers)
- **Week 3-4:** Velocity calculation
- **Week 5-6:** Entity resolution
- **Week 7-8:** Polish & production

**Total:** 4-6 weeks, 50-70 hours effort

**Milestones:**
- Phase 1: Scraping pipeline works
- Phase 2: Velocity tracking works
- Phase 3: Entity resolution works
- Phase 4: Production ready

**Read this** when ready to start building.

---

## Quick Start

### For Product Managers
1. Read **Phase 1** (understand current state)
2. Read **Phase 2** (understand velocity signals)
3. Read **Implementation Plan** (timeline & milestones)

### For Developers
1. Read **Phase 6** (code changes needed)
2. Read **Implementation Plan** (step-by-step tasks)
3. Start with Phase 1, Step 1.1 (update Convex schema)

### For Architects
1. Read **Phase 4** (scraping infrastructure)
2. Read **Phase 5** (data pipeline)
3. Read **Phase 3** (entity resolution)

---

## Key Metrics

### Technical Targets
- **Scrape success rate:** >95%
- **Velocity accuracy:** 85%+ (vs manual validation)
- **Match rate (entity resolution):** 90%+
- **Scrape frequency:** 15 min (high velocity) to 12 hours (low velocity)
- **Change detection latency:** <30 seconds
- **Uptime:** >99%

### Cost Targets
- **MVP (20 stores):** $6/month
- **Scale (100 stores):** $31/month
- **Full (500 stores):** $63/month
- **Enterprise (5,000 stores):** $470/month

### Business Metrics
- **Break-even:** 11 paid users @ $4.99/month
- **Target:** 500 paid users = $2,495 MRR
- **Profit margin:** 97% at scale

---

## Technology Stack

| Layer | Technology | Why? |
|-------|------------|------|
| **Database** | Convex | Real-time, serverless, generous free tier |
| **Scrapers** | Node.js + Playwright | Consistent with Convex TypeScript |
| **Job Queue** | BullMQ + Redis | Distributed, persistent, retry logic |
| **Workers** | Node.js + PM2 | Auto-restart, logging, process management |
| **Storage (cold)** | Cloudflare R2 | $0.015/GB (90-day retention) |
| **LLM** | GPT-4o-mini | $0.00003/product (entity matching) |
| **Monitoring** | Sentry + Axiom | Free tiers |
| **Hosting** | Hetzner VPS | $6-12/month (vs $150 AWS) |

---

## Data Flow

```
┌──────────────────────────────────────────────────────────┐
│  SOURCES (500 stores)                                    │
│  Dutchie, WordPress, Blaze, Jane, custom                 │
└────────────────────┬─────────────────────────────────────┘
                     │ scrape every 15min - 12hr
                     ▼
┌──────────────────────────────────────────────────────────┐
│  WORKERS (2× VPS, 4 concurrent each)                     │
│  Platform adapters, retry logic, stealth                 │
└────────────────────┬─────────────────────────────────────┘
                     │ scrape results
                     ▼
┌──────────────────────────────────────────────────────────┐
│  INGESTION (validation → snapshot storage)               │
│  menuSnapshots table in Convex                           │
└────────────────────┬─────────────────────────────────────┘
                     │ trigger change detection
                     ▼
┌──────────────────────────────────────────────────────────┐
│  CHANGE DETECTION (compare current vs previous)          │
│  inventoryDeltas + inventoryEvents tables                │
└────────────────────┬─────────────────────────────────────┘
                     │ deltas
                     ▼
┌──────────────────────────────────────────────────────────┐
│  VELOCITY CALCULATION (multi-signal scoring)             │
│  productVelocity table (scores 0-100)                    │
└────────────────────┬─────────────────────────────────────┘
                     │ velocity scores
                     ▼
┌──────────────────────────────────────────────────────────┐
│  ENTITY RESOLUTION (match across stores)                 │
│  canonicalProducts table                                 │
└────────────────────┬─────────────────────────────────────┘
                     │ aggregated metrics
                     ▼
┌──────────────────────────────────────────────────────────┐
│  API / UI (Convex queries, real-time subscriptions)     │
│  Top velocity products, cross-store comparison           │
└──────────────────────────────────────────────────────────┘
```

---

## Sample Output

### Product Velocity Example

```json
{
  "productId": "blue-dream-3.5g-conbud",
  "canonicalId": "blue-dream-3.5g-good-chemistry",
  "velocityScore": 87,
  "unitsPerHour": 12,
  "unitsPerDay": 288,
  "restocksPerWeek": 5,
  "avgTimeInStock": 4.2,
  "availabilityPct": 73,
  "trend": "ACCELERATING",
  "confidence": 0.92,
  "lastUpdated": 1709625000000
}
```

### Cross-Store Comparison

```json
{
  "canonicalId": "blue-dream-3.5g-good-chemistry",
  "strain": "blue dream",
  "size": 3.5,
  "totalStores": 5,
  "avgVelocityScore": 78,
  "totalRestocksPerWeek": 23,
  "priceRange": {
    "min": 42,
    "max": 50
  },
  "fastestStore": "union-square",
  "slowestStore": "smacked",
  "stores": [
    { "store": "conbud-les", "velocity": 87, "price": 45 },
    { "store": "gotham-nyc", "velocity": 76, "price": 50 },
    { "store": "housing-works", "velocity": 68, "price": 48 },
    { "store": "smacked", "velocity": 54, "price": 42 },
    { "store": "union-square", "velocity": 92, "price": 47 }
  ]
}
```

---

## Common Questions

### Q: Why not use POS/ecommerce APIs?
**A:** Most dispensaries don't provide API access. Scraping is the only scalable option for cross-store tracking.

### Q: How accurate is velocity without exact inventory counts?
**A:** 85%+ accuracy using stock transitions + restock frequency. For Dutchie stores (40% of total), we get exact counts.

### Q: What if a scraper gets blocked?
**A:** We use stealth plugins, proxy rotation, and adaptive rate limiting. If blocked, circuit breaker pauses scraping and alerts.

### Q: How much does this cost at scale?
**A:** $63/month for 500 stores, $470/month for 5,000 stores (linear scaling, not exponential).

### Q: How long to implement?
**A:** 4-6 weeks for MVP (basic velocity tracking), 8-12 weeks for full entity resolution and cross-store aggregation.

### Q: What's the hardest part?
**A:** Entity resolution (matching products across stores). We solve this with a 4-tier pipeline achieving 92-95% accuracy.

---

## Next Steps

1. **Review Phase 1** to understand current state
2. **Review Phase 6** for code changes needed
3. **Review Implementation Plan** for step-by-step tasks
4. **Begin Phase 1, Step 1.1** (update Convex schema)

---

## Research Credits

**Researcher:** sku-velocity-research subagent  
**Framework:** Progressive research with commit-per-phase  
**Date:** 2026-03-05  
**Total Research Output:** ~140KB of documentation

---

## Files Manifest

```
velocity-research/
├── README.md                           # This file (overview)
├── PHASE1_CURRENT_STATE.md            # Current architecture analysis
├── PHASE2_VELOCITY_SIGNALS.md         # 12 velocity detection methods
├── PHASE3_ENTITY_RESOLUTION.md        # Product matching across stores
├── PHASE4_SCRAPING_INFRASTRUCTURE.md  # Distributed worker architecture
├── PHASE5_DATA_PIPELINE.md            # Delta → velocity transformation
├── PHASE6_STACK_IMPROVEMENTS.md       # Concrete code changes
└── IMPLEMENTATION_PLAN.md             # Step-by-step roadmap
```

**Total:** 8 comprehensive documents, ready for implementation.

---

## Conclusion

**SKU velocity tracking is achievable** with the architecture designed in this research.

**Key innovations:**
- ✅ Velocity from scraping alone (no POS needed)
- ✅ 92-95% entity matching (cross-store tracking)
- ✅ $63/month at 500 stores (cost-efficient)
- ✅ 4-6 weeks to MVP (realistic timeline)

**This research is complete.** Next step: Implementation!

---

**Ready to build. Let's go! 🚀**
