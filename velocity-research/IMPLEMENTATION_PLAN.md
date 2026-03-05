# SKU Velocity Tracking - Implementation Plan

**Project:** BudAlert Velocity Tracking  
**Date:** 2026-03-05  
**Status:** Ready for implementation  
**Estimated Timeline:** 4-6 weeks to MVP

---

## Executive Summary

This document provides a **step-by-step implementation plan** to add SKU velocity tracking to BudAlert. The plan is broken into **4 phases** with clear milestones, deliverables, and acceptance criteria.

**Goal:** Calculate and track product velocity (units sold per time period) across hundreds of stores using only web scraping data.

**Outcome:** 
- Velocity scores (0-100) for every product
- Units/hour metrics (where available)
- Restock frequency tracking
- Cross-store velocity comparison
- Trend analysis and forecasting

---

## Prerequisites

### Required Knowledge
- TypeScript/Node.js
- Convex database & mutations
- Web scraping (Playwright)
- Job queues (BullMQ)

### Infrastructure Requirements
- Hetzner VPS (CPX11, $6/month) or equivalent
- Redis (self-hosted on VPS)
- Convex account (free tier)
- Domain + SSL (optional, for webhooks)

### Time Commitment
- **Week 1-2:** Foundation (schema, scrapers, workers) - 20-30 hours
- **Week 3-4:** Velocity calculation & testing - 15-20 hours
- **Week 5-6:** Entity resolution & polish - 15-20 hours

**Total:** 50-70 hours (1-2 months part-time, 4-6 weeks full-time)

---

## Phase 1: Foundation (Week 1-2)

**Goal:** Set up infrastructure for distributed scraping with snapshot storage.

### Step 1.1: Update Convex Schema

**Duration:** 1-2 hours  
**File:** `convex/schema.ts`

**Tasks:**
1. Add `productVelocity` table (see Phase 6 spec)
2. Add `canonicalProducts` table
3. Update `products` table with `canonicalId` field
4. Run `npx convex dev` to apply schema changes

**Acceptance Criteria:**
- [ ] Schema compiles without errors
- [ ] All new tables visible in Convex dashboard
- [ ] Indexes created successfully

**Testing:**
```bash
npx convex dev
# Check dashboard for new tables
```

---

### Step 1.2: Migrate Scrapers to Node.js

**Duration:** 2-3 days  
**Files:** `scrapers/platforms/*.mjs`, `scrapers/index.mjs`

**Tasks:**
1. Create base scraper class (`scrapers/platforms/base.mjs`)
2. Migrate Dutchie scraper (see Phase 6 code)
3. Migrate WordPress scraper (Gotham)
4. Migrate Blaze scraper (Housing Works)
5. Create scraper index with store config

**Acceptance Criteria:**
- [ ] Each platform scraper can be run standalone
- [ ] Returns normalized product data
- [ ] Handles errors gracefully (retries)
- [ ] Scraped data includes all required fields (id, name, price, inStock, quantity)

**Testing:**
```bash
cd scrapers
node platforms/dutchie.mjs --store=conbud-les
# Should output JSON with products
```

---

### Step 1.3: Set Up Worker Infrastructure

**Duration:** 1-2 days  
**Files:** `workers/scraper-worker.mjs`, `workers/ingestion.mjs`, `pm2.config.js`

**Tasks:**
1. Install dependencies: `npm install bullmq ioredis pm2 playwright`
2. Install Redis on VPS: `sudo apt install redis-server`
3. Create worker script (see Phase 6 code)
4. Create ingestion pipeline
5. Configure PM2 for auto-restart

**Acceptance Criteria:**
- [ ] Redis running and accessible
- [ ] BullMQ worker starts without errors
- [ ] Worker can process test job
- [ ] PM2 auto-restarts worker on crash
- [ ] Logs written to `logs/worker-*.log`

**Testing:**
```bash
# Start Redis
sudo systemctl start redis

# Start worker
pm2 start pm2.config.js
pm2 logs scraper-worker

# Add test job
node -e "
const { Queue } = require('bullmq');
const queue = new Queue('scrape-jobs');
queue.add('test', { storeId: 'conbud-les' });
"

# Watch logs for successful scrape
```

---

### Step 1.4: Create Convex Mutations

**Duration:** 2 days  
**Files:** `convex/scraping.ts`

**Tasks:**
1. Create `storeSnapshot` mutation
2. Create `updateCurrentInventory` mutation
3. Create `detectChanges` action + internal mutation
4. Add proper error handling

**Acceptance Criteria:**
- [ ] Snapshot mutation stores products correctly
- [ ] Current inventory updates without duplicates
- [ ] Change detection compares snapshots
- [ ] All mutations compile and deploy

**Testing:**
```bash
npx convex dev

# In Convex dashboard, test mutation:
# scraping:storeSnapshot with test data
```

---

### Phase 1 Milestone: Scraping Pipeline Works

**Deliverables:**
- [ ] 3+ platform scrapers (Dutchie, WordPress, Blaze)
- [ ] Worker infrastructure running
- [ ] Snapshots stored in Convex
- [ ] Change detection identifies deltas

**Test:**
1. Manually scrape 1 store
2. Wait 15 minutes
3. Scrape again
4. Verify deltas detected (if inventory changed)

---

## Phase 2: Velocity Calculation (Week 3-4)

**Goal:** Calculate velocity scores from deltas and display them.

### Step 2.1: Implement Velocity Algorithm

**Duration:** 2 days  
**File:** `convex/velocity.ts`

**Tasks:**
1. Create `calculateVelocity` mutation (see Phase 5 & 6)
2. Implement multi-signal scoring (quantity, restocks, availability, price)
3. Store velocity in `productVelocity` table
4. Create query endpoints (`getVelocity`, `getTopVelocity`)

**Acceptance Criteria:**
- [ ] Velocity score calculated correctly (0-100)
- [ ] Units/hour calculated (when quantity available)
- [ ] Restocks/week tracked
- [ ] Confidence score included

**Testing:**
```javascript
// In Convex dashboard:
await runMutation('velocity:calculateVelocity', {
  productId: 'test-product',
  retailerId: 'conbud-les'
});

// Should return velocity score
```

---

### Step 2.2: Trigger Velocity Updates

**Duration:** 1 day  
**Files:** `convex/scraping.ts` (update), `convex/crons.ts`

**Tasks:**
1. Call `calculateVelocity` after change detection
2. Create nightly cron to recalculate all velocities
3. Add velocity recalculation to worker flow

**Acceptance Criteria:**
- [ ] Velocity updates after each scrape
- [ ] Cron runs nightly without errors
- [ ] Velocity scores visible in Convex dashboard

**Testing:**
```bash
# Check cron scheduled:
npx convex crons list

# Manually trigger:
npx convex run crons:recalculateVelocities
```

---

### Step 2.3: Create Scheduler

**Duration:** 1 day  
**Files:** `convex/scheduler.ts`, `convex/crons.ts`

**Tasks:**
1. Create job generator that runs every 5 minutes
2. Calculate adaptive scrape intervals (15 min - 12 hours)
3. Queue scrape jobs in BullMQ

**Acceptance Criteria:**
- [ ] High-velocity stores scraped every 15-30 minutes
- [ ] Low-velocity stores scraped every 4-12 hours
- [ ] No duplicate jobs queued
- [ ] Job queue doesn't back up

**Testing:**
```bash
# Watch queue depth:
redis-cli
> LLEN bull:scrape-jobs:wait

# Should stay under 50 jobs
```

---

### Phase 2 Milestone: Velocity Tracking Works

**Deliverables:**
- [ ] Velocity scores calculated for all products
- [ ] Adaptive scraping based on velocity
- [ ] Real-time velocity updates
- [ ] Top velocity products queryable

**Test:**
1. Let system run for 48 hours
2. Query top 20 velocity products
3. Verify scores make sense (high-velocity products have higher scores)

---

## Phase 3: Entity Resolution (Week 5-6)

**Goal:** Match products across stores (cross-store velocity).

### Step 3.1: Implement Normalization

**Duration:** 1 day  
**File:** `convex/entityResolution.ts`

**Tasks:**
1. Create normalization functions (see Phase 3)
2. Normalize product names, brands, sizes
3. Generate signature hashes

**Acceptance Criteria:**
- [ ] "Blue Dream 3.5g" = "Blue Dream 1/8oz" (after normalization)
- [ ] Brand aliases work ("Good Chemistry" = "GC")
- [ ] Size conversions work (1/8oz = 3.5g)

**Testing:**
```javascript
normalizeProduct({
  name: "Blue Dream 1/8oz",
  brand: "GC"
});
// Should return normalized signature
```

---

### Step 3.2: Implement Signature Matching

**Duration:** 1-2 days  
**File:** `convex/entityResolution.ts`

**Tasks:**
1. Create signature matching function
2. Build canonical product on first match
3. Link subsequent products to canonical

**Acceptance Criteria:**
- [ ] Exact matches create canonical products
- [ ] 60-70% of products match via signature

**Testing:**
```javascript
matchBySignature(newProduct, existingCanonicals);
// Should return canonicalId if match found
```

---

### Step 3.3: Implement Fuzzy Matching

**Duration:** 1-2 days  
**File:** `convex/entityResolution.ts`

**Tasks:**
1. Implement Levenshtein distance
2. Set threshold at 85% similarity
3. Match remaining products

**Acceptance Criteria:**
- [ ] Typos matched ("Blue Deram" → "Blue Dream")
- [ ] 80-95% total match rate

**Testing:**
```javascript
similarityScore("blue dream", "blu dream");
// Should return ~90
```

---

### Step 3.4: Cross-Store Aggregation

**Duration:** 1 day  
**File:** `convex/velocity.ts`

**Tasks:**
1. Create `calculateCanonicalVelocity` query
2. Aggregate velocity across all stores for canonical product
3. Return fastest/slowest stores

**Acceptance Criteria:**
- [ ] Canonical velocity = sum of all store velocities
- [ ] Price range shown (min/max across stores)
- [ ] Fastest/slowest stores identified

**Testing:**
```javascript
await runQuery('velocity:getCanonicalVelocity', {
  canonicalId: 'blue-dream-3.5g-good-chemistry'
});
// Should return aggregated metrics from all stores
```

---

### Phase 3 Milestone: Entity Resolution Complete

**Deliverables:**
- [ ] Canonical products created
- [ ] 90%+ of products matched
- [ ] Cross-store velocity metrics
- [ ] Price comparison across stores

**Test:**
1. Find a popular product (e.g., "Blue Dream")
2. Check how many stores carry it
3. Compare velocity across stores
4. Verify price range accurate

---

## Phase 4: Polish & Production (Week 7-8)

**Goal:** Production-ready deployment.

### Step 4.1: Monitoring & Alerting

**Duration:** 1 day  
**Tools:** Sentry (errors), Axiom (logs), PM2 (uptime)

**Tasks:**
1. Add Sentry error tracking
2. Set up log aggregation
3. Create health check endpoint
4. Configure alerts (worker down, high error rate)

**Acceptance Criteria:**
- [ ] Errors logged to Sentry
- [ ] Logs searchable in Axiom
- [ ] Alerts sent when worker crashes

---

### Step 4.2: API Documentation

**Duration:** 1 day  
**File:** `docs/API.md`

**Tasks:**
1. Document all Convex queries
2. Provide example requests/responses
3. Create Postman collection

**Acceptance Criteria:**
- [ ] All endpoints documented
- [ ] Examples tested and working

---

### Step 4.3: Performance Testing

**Duration:** 2 days  
**Tools:** Artillery, k6, or manual

**Tasks:**
1. Load test with 100 stores
2. Verify scrape duration <30s
3. Ensure queue doesn't back up
4. Check Convex stays in free tier

**Acceptance Criteria:**
- [ ] >95% scrape success rate
- [ ] Queue depth <100
- [ ] Convex usage <80% of free tier

---

### Phase 4 Milestone: Production Ready

**Deliverables:**
- [ ] Monitoring live
- [ ] API documented
- [ ] Performance tested
- [ ] Production deployed

**Test:**
1. Run for 1 week in production
2. Monitor uptime, error rates
3. Verify data quality
4. Collect user feedback (if applicable)

---

## Success Criteria (Final)

### Technical Metrics
- [ ] **Scrape success rate:** >95%
- [ ] **Velocity calculation accuracy:** 85%+ (vs manual validation)
- [ ] **Match rate (entity resolution):** 90%+
- [ ] **Uptime:** >99%
- [ ] **Cost:** <$70/month at 500 stores

### Data Quality
- [ ] All products have velocity scores
- [ ] Deltas detected within 30 minutes
- [ ] No duplicate products
- [ ] Historical data retained (7 days hot, 90 days cold)

### User Experience (if UI built)
- [ ] Velocity scores visible on product cards
- [ ] Top velocity products shown
- [ ] Cross-store comparison works
- [ ] Real-time updates (via Convex subscriptions)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **Scraper detection** | Stealth plugins, proxy rotation, adaptive rate limiting |
| **Convex free tier exceeded** | Monitor usage, upgrade if needed ($25/month) |
| **Worker crashes** | PM2 auto-restart, health checks, alerts |
| **Poor match accuracy** | Manual review queue, iterative improvement |
| **Slow velocity calculation** | Batch processing, caching, incremental updates |

---

## Rollback Plan

If issues arise:

1. **Disable scheduler:** Stop queuing new scrape jobs
2. **Pause workers:** `pm2 stop scraper-worker`
3. **Revert schema:** Use Convex dashboard to remove new tables
4. **Restore from backup:** Use Convex export/import

---

## Post-Launch

### Week 1-2 After Launch
- Monitor error rates daily
- Fix critical bugs
- Gather user feedback
- Tune scrape frequencies

### Month 2-3
- Implement cart probing (for WordPress stores)
- Add LLM entity matching (for hard cases)
- Build UI for velocity insights
- Scale to 500 stores

### Month 4-6
- Launch mobile app
- Add push notifications (restocks, price drops)
- Implement monetization (Pro tier)
- Target 500 paid users

---

## Resources

### Documentation
- [Phase 1: Current State](./PHASE1_CURRENT_STATE.md)
- [Phase 2: Velocity Signals](./PHASE2_VELOCITY_SIGNALS.md)
- [Phase 3: Entity Resolution](./PHASE3_ENTITY_RESOLUTION.md)
- [Phase 4: Scraping Infrastructure](./PHASE4_SCRAPING_INFRASTRUCTURE.md)
- [Phase 5: Data Pipeline](./PHASE5_DATA_PIPELINE.md)
- [Phase 6: Stack Improvements](./PHASE6_STACK_IMPROVEMENTS.md)

### Code Examples
- All code snippets in Phase 6
- Existing scrapers in `scrapers/` directory

### Support
- Convex Discord: https://convex.dev/discord
- BullMQ Docs: https://docs.bullmq.io
- Playwright Docs: https://playwright.dev

---

## Conclusion

**SKU velocity tracking is achievable in 4-6 weeks** with the roadmap above.

**Key milestones:**
- Week 2: Scraping pipeline works
- Week 4: Velocity calculation works
- Week 6: Entity resolution works
- Week 8: Production ready

**Total cost:** $6-70/month (depending on scale)  
**Total effort:** 50-70 hours

**Next step:** Begin Phase 1, Step 1.1 (Update Convex Schema)

---

**Implementation plan complete. Ready to begin development!** 🚀
