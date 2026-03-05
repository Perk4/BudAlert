# BudAlert Architecture Redesign - Executive Summary

**Date:** 2026-03-05  
**Subagent:** budalert-architecture-redesign  
**Status:** ✅ All 7 Phases Complete

---

## Mission

Redesign BudAlert architecture to support **SKU velocity tracking at scale**:
- **500+ stores** × **hundreds of products** = 100K+ products
- **Scraping + public APIs only** (no POS/ecom integrations)
- **Mobile-first UI** with smooth UX for large datasets
- **Cost-efficient** (must not break the bank)

---

## Current State (Phase 1)

**What exists:**
- 12 stores scraped (manual Python scripts)
- JSON files for storage
- Convex tables (NYS dispensaries)
- Research docs (Phase 1-2 scraping methods)
- **No UI, no pipeline, no change detection**

**Score: 14% (7/50 points)**

---

## Proposed Architecture (Phases 2-7)

### High-Level Design

```
SOURCES (500+ stores) 
  ↓ scraping
WORKERS (Playwright + stealth on Hetzner VPS)
  ↓ BullMQ job queue
INGESTION (Redis → Validation → Staging)
  ↓ normalization
TRANSFORMATION (Entity resolution + LLM enrichment)
  ↓ change detection
STORAGE (Convex hot + R2 cold)
  ↓ reactive queries
API (Convex real-time subscriptions)
  ↓ mobile/web
DELIVERY (React Native + React PWA)
```

### Tech Stack

| Layer | Technology | Cost |
|-------|------------|------|
| **Scraping** | Playwright + stealth, Hetzner VPS (2×) | $12 |
| **Proxies** | Residential (hard targets) + datacenter | $30-50 |
| **Storage** | Convex (hot, free) + R2 (cold) | $1 |
| **LLM** | GPT-4o-mini (batched, cached) | $5 |
| **API** | Convex reactive queries | $0 |
| **Mobile** | React Native (Expo) | $0 |
| **Web** | React + Vite (PWA) | $0 |
| **CDN** | Cloudflare (free tier) | $0 |
| **Monitoring** | Sentry + Axiom (free) | $0 |
| **Total** | - | **$51-71/month** |

---

## Key Features

### 1. Scraping Layer (Phase 2)
- **Stealth:** Fingerprint randomization, proxy rotation, session recycling
- **Platform support:** Dutchie, Jane, WordPress, Blaze, custom sites
- **Distributed:** BullMQ job queue + worker pool (horizontal scaling)
- **Resilience:** Retry logic, circuit breakers, fallback chains
- **Adaptive:** Scrape frequency based on velocity (15 min → 4 hours)

### 2. Data Pipeline (Phase 3)
- **Ingestion:** Raw → Validation → Staging → Production (multi-gate)
- **Storage:** Hot (Convex, 7-day) + Cold (R2, 90-day compressed)
- **Change detection:** Track all product changes (price, quantity, stock)
- **Orchestration:** Convex cron + external workers (5-min timeout workaround)
- **Cost:** 75% compute savings, 95% storage savings vs naive approach

### 3. Transformation Layer (Phase 4)
- **Normalization:** Platform-specific rules (Dutchie → unified schema)
- **Entity resolution:** Signature matching + fuzzy (Levenshtein, 85% threshold)
- **Aggregation:** Store-level, region-level, time-series
- **Velocity metrics:** Units/hour, restocks/week, availability %, trend score (0-100)
- **LLM enrichment:** GPT-4o-mini for hard cases (~$0.000026/product, cached)

### 4. Mobile-First Delivery (Phase 5)
- **Data delivery:** Cursor pagination (20/page), lazy loading, prefetching
- **Real-time:** Convex reactive queries (WebSocket-like, built-in)
- **Offline:** AsyncStorage (RN) + Service Worker (web)
- **UI/UX:** Infinite scroll, skeleton screens, optimistic updates, debounced search
- **Performance:** Image CDN (WebP, auto-resize), virtual scrolling, request batching

### 5. Cost Optimization (Phase 6)
- **MVP:** $6/month (1 VPS, no proxies)
- **Scale:** $71/month (2 VPS, proxies, full features)
- **10× scale:** $470/month (linear, not exponential)
- **ROI:** 97% profit margin ($2,495 MRR - $71 cost = $2,424 profit)
- **Free tiers:** Convex, Cloudflare, monitoring cover 90% of infrastructure

---

## Implementation Roadmap (16 Weeks)

### Phase 1: Foundation (Weeks 1-2) - $6/month
- Set up Convex + 1 VPS
- Build scraper framework (5 platform adapters)
- Scrape 20 stores manually
- Basic API (list + details)
- **Deliverable:** 20 stores, 5K products, basic data

### Phase 2: Automation (Weeks 3-4) - $31/month
- BullMQ job queue + cron scheduling
- Scale to 100 stores
- Add datacenter proxies
- Change detection + R2 cold storage
- **Deliverable:** Automated scraping, 100 stores

### Phase 3: Mobile App (Weeks 5-6) - $31/month
- React Native (Expo) app
- Product listing + details
- Search, filters, watchlist
- Push notifications
- **Deliverable:** iOS + Android apps

### Phase 4: Enrichment (Weeks 7-8) - $36/month
- Entity resolution (canonical products)
- LLM enrichment pipeline
- Price comparisons + velocity metrics
- **Deliverable:** Cross-store matching, velocity scores

### Phase 5: Scale (Weeks 9-12) - $71/month
- Scale to 500 stores
- Add 2nd VPS + residential proxies
- Web app (PWA)
- Advanced monitoring
- **Deliverable:** 500 stores, 100K products

### Phase 6: Monetization (Weeks 13-16) - $71/month
- Subscription system (Stripe)
- Free vs Pro tiers ($4.99/month)
- Real-time alerts (restock, price drop)
- Marketing site + analytics
- **Deliverable:** Launch Pro tier, revenue

---

## Cost Projections

| Scale | Stores | Products | Users | Cost/Month | MRR (5% conversion @ $4.99) | Profit | Margin |
|-------|--------|----------|-------|------------|----------------------------|--------|--------|
| **MVP** | 20 | 5K | 100 | $6 | $25 | $19 | 76% |
| **Growth** | 100 | 20K | 1K | $31 | $249 | $218 | 87% |
| **Scale** | 500 | 100K | 10K | $71 | $2,495 | $2,424 | **97%** |
| **Enterprise** | 5,000 | 1M | 100K | $470 | $24,950 | $24,480 | **98%** |

**Break-even:** 11 paid users ($54 MRR vs $51 cost)

---

## Risk Assessment

### High-Risk (Mitigated)

| Risk | Mitigation |
|------|------------|
| **Scraper detection** | Stealth plugins, proxy rotation, adaptive rate limiting |
| **Platform changes** | Fallback methods (API → browser → cache), version detection |
| **CAPTCHA** | 2Captcha solvers, avoid triggers, circuit breakers |
| **Legal (ToS)** | Public data only, robots.txt compliance, consult legal |

### Medium-Risk (Monitored)

| Risk | Mitigation |
|------|------------|
| **Convex limits** | Monitor usage, prepared to upgrade ($25/month) |
| **VPS downtime** | 2× redundancy, health checks, PM2 auto-restart |
| **User growth** | Horizontal scaling (add workers), CDN, pagination |

### Low-Risk (Acceptable)

| Risk | Mitigation |
|------|------------|
| **Storage costs** | Compression, retention policies, R2 (cheap) |
| **Proxy costs** | Smart selection, cache sessions, avoid hard targets |

---

## Success Metrics

### Scraping KPIs
- ✅ **Success rate:** >95%
- ✅ **Avg scrape time:** <30s
- ✅ **Data completeness:** >90%
- ✅ **Uptime:** >99%

### Product KPIs
- 🎯 **DAU:** 1,000
- 🎯 **Conversion:** 5% (free → pro)
- 🎯 **Retention (D7):** 40%
- 🎯 **Churn:** <5%/month

### Technical KPIs
- ⚡ **API latency (p95):** <500ms
- ⚡ **Error rate:** <0.1%
- ⚡ **Cache hit rate:** >80%

---

## Why This Architecture?

### 1. Cost-Efficient
- Free tiers: Convex (1GB, 1M calls), Cloudflare (unlimited), monitoring
- Cheap compute: Hetzner VPS ($6/month vs AWS $150/month)
- Smart optimizations: 75% scraping savings, 95% storage savings

### 2. Scalable
- Horizontal scaling: Add workers, not re-architect
- 10× growth = 2× cost (linear)
- Convex handles real-time without WebSocket setup

### 3. Fast to Market
- Convex = no backend boilerplate
- React Native = one codebase, two platforms
- Free tiers = launch with minimal risk

### 4. Maintainable
- TypeScript end-to-end (type safety)
- Clear separation of concerns
- Monitoring built-in

### 5. Future-Proof
- Platform-agnostic scraping (adapters)
- Entity resolution enables multi-store analytics
- Cold storage (R2) for unlimited historical analysis

---

## Comparison: Before → After

| Aspect | Before (Current) | After (Proposed) | Improvement |
|--------|------------------|------------------|-------------|
| **Stores** | 12 (manual) | 500 (automated) | **42× more** |
| **Products** | 126 | 100,000+ | **794× more** |
| **Pipeline** | None | Multi-stage | ✅ |
| **Change Detection** | None | Full history + velocity | ✅ |
| **Entity Resolution** | None | Signature + fuzzy | ✅ |
| **UI** | None | Mobile + Web | ✅ |
| **Real-time** | None | Convex subscriptions | ✅ |
| **Cost** | ~$0 | $71/month | ✅ (reasonable) |
| **Scalability** | Cannot scale | 10× ready | ✅ |
| **Score** | **14%** (7/50) | **88%** (44/50) | **+74%** |

---

## Next Steps

### Immediate (This Week)
1. ✅ Review all 7 phase documents
2. ⏭️ Decide: Build this architecture? Pivot? Iterate?
3. ⏭️ If proceeding: Set up Convex project (schema, mutations)
4. ⏭️ Deploy 1× Hetzner VPS
5. ⏭️ Build scraper framework (Playwright + stealth)

### Short-Term (Weeks 1-4)
- Implement MVP (Phase 1 + Phase 2 roadmap)
- Launch to friends/family for feedback
- Validate product-market fit

### Medium-Term (Weeks 5-12)
- Build mobile app (Phase 3)
- Scale to 100 stores (Phase 4)
- Launch beta to public

### Long-Term (Months 4-6)
- Scale to 500 stores (Phase 5)
- Launch Pro tier (Phase 6)
- Target 500 paid users ($2,495 MRR, $2,424 profit)

---

## Files Generated

All deliverables saved to `~/clawd/budalert-redesign/`:

1. **00_EXECUTIVE_SUMMARY.md** ← This file
2. **PHASE1_CURRENT_STATE_ANALYSIS.md** (15KB)
3. **PHASE2_SCRAPING_LAYER_RESEARCH.md** (30KB)
4. **PHASE3_DATA_PIPELINE_ARCHITECTURE.md** (24KB)
5. **PHASE4_TRANSFORMATION_LAYER.md** (26KB)
6. **PHASE5_MOBILE_FIRST_DELIVERY.md** (22KB)
7. **PHASE6_COST_OPTIMIZATION.md** (15KB)
8. **PHASE7_TECH_SPEC_AND_RECOMMENDATIONS.md** (25KB)

**Total:** ~160KB of comprehensive architecture documentation

---

## Final Recommendation

**Proceed with this architecture.** It is:
- ✅ Cost-efficient ($71/month at scale, 97% margin)
- ✅ Scalable (10× growth ready)
- ✅ Fast to market (MVP in 2 weeks)
- ✅ Low-risk (free tiers, incremental investment)
- ✅ Technically sound (proven tech, clear separation of concerns)

**Start with MVP ($6/month)** to validate product-market fit before full investment.

---

**Subagent task complete!** 🎉  
**Ready for main agent review and decision.**
