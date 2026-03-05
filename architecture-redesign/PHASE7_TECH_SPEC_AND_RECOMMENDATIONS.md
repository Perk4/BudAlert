# Phase 7: Technical Specification & Recommendations

**Date:** 2026-03-05  
**Project:** BudAlert Architecture Redesign  
**Target:** SKU velocity data product at scale (500+ stores, 100K+ products)

---

## 1. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       DATA SOURCES                              │
│   500+ Dispensary Websites (Dutchie, Jane, WordPress, Custom)  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SCRAPING LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Worker 1    │  │  Worker 2    │  │  Worker N    │        │
│  │  (Playwright)│  │  (Playwright)│  │  (Playwright)│        │
│  │  VPS/Hetzner │  │  VPS/Hetzner │  │  VPS/Hetzner │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │                 │
│         └──────────────────┴──────────────────┘                │
│                           │                                     │
│  ┌────────────────────────┴─────────────────────────┐         │
│  │  Job Queue (BullMQ / Convex Actions)            │         │
│  │  • Scheduling (adaptive frequency)               │         │
│  │  • Priority queuing                              │         │
│  │  • Retry logic + circuit breakers                │         │
│  └──────────────────────────────────────────────────┘         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Raw JSON
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ Raw Buffer  │→ │ Validation  │→ │ Staging     │           │
│  │ (Redis)     │  │ (Schema)    │  │ (Convex)    │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  TRANSFORMATION LAYER                           │
│  ┌─────────────────────────────────────────────────┐           │
│  │  Normalization (platform-specific rules)        │           │
│  │  Entity Resolution (signature + fuzzy match)    │           │
│  │  LLM Enrichment (GPT-4o-mini, batched)         │           │
│  │  Change Detection (diff current vs new)         │           │
│  └──────────────────────┬──────────────────────────┘           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                                │
│  ┌───────────────────────────────────────────────────┐         │
│  │  HOT STORAGE (Convex - Free Tier)                 │         │
│  │  • products (current snapshot) - 100 MB           │         │
│  │  • productChanges (7-day history) - 14 MB         │         │
│  │  • stores, users, watchlist - 10 MB               │         │
│  │  • TOTAL: ~130 MB                                 │         │
│  └───────────────────────────────────────────────────┘         │
│  ┌───────────────────────────────────────────────────┐         │
│  │  COLD STORAGE (Cloudflare R2 - $1/mo)            │         │
│  │  • Raw scrapes (7-day retention) - 1 GB           │         │
│  │  • Daily snapshots (90-day, compressed) - 9 GB    │         │
│  │  • Change logs (90-day, compressed) - 1.8 GB      │         │
│  │  • TOTAL: ~12 GB                                  │         │
│  └───────────────────────────────────────────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER                                  │
│  ┌─────────────────────────────────────────────────┐           │
│  │  Convex Reactive Queries (Real-time)            │           │
│  │  • Product listing (paginated, filtered)        │           │
│  │  • Product details (full data + related)        │           │
│  │  • Velocity metrics (calculated)                │           │
│  │  • Price comparisons (canonical products)       │           │
│  │  • Store stats (aggregated)                     │           │
│  └─────────────────────────────────────────────────┘           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DELIVERY LAYER                                │
│  ┌─────────────────────────────────────────────────┐           │
│  │  Mobile App (React Native)                      │           │
│  │  • Infinite scroll (FlatList)                   │           │
│  │  • Real-time updates (Convex subscriptions)     │           │
│  │  • Offline support (AsyncStorage)               │           │
│  │  • Push notifications (Expo)                    │           │
│  └─────────────────────────────────────────────────┘           │
│  ┌─────────────────────────────────────────────────┐           │
│  │  Web App (React + PWA)                          │           │
│  │  • Virtual scrolling (react-window)             │           │
│  │  • Service worker (offline caching)             │           │
│  │  • Responsive design (mobile-first)             │           │
│  └─────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CDN LAYER                                   │
│  Cloudflare (Free Tier)                                        │
│  • Static assets (JS, CSS, images)                             │
│  • Image optimization (WebP, resize)                           │
│  • API edge caching                                            │
│  • DDoS protection                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

### Backend

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Database** | Convex | Free tier, real-time subscriptions, TypeScript-first |
| **Job Queue** | BullMQ (Redis) | Reliable, retries, priority queuing |
| **Scraping** | Playwright (Node.js) | Cross-browser, stealth plugins, network interception |
| **HTTP Client** | Axios | Simple, retries, interceptors |
| **Cache** | Redis | In-memory for queue + session management |
| **Cold Storage** | Cloudflare R2 | S3-compatible, cheap ($0.015/GB), no egress fees |
| **LLM** | GPT-4o-mini (OpenAI) | Cheap ($0.15/1M tokens), fast, good enough |

### Frontend

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Mobile** | React Native (Expo) | Cross-platform, hot reload, rich ecosystem |
| **Web** | React + Vite | Fast builds, modern DX, code sharing with mobile |
| **State** | Convex React hooks | Built-in, real-time, no Redux needed |
| **UI Components** | React Native Paper | Material Design, accessible, customizable |
| **Navigation** | React Navigation | Standard for RN, deep linking support |
| **Forms** | React Hook Form | Performant, small bundle, validation |

### Infrastructure

| Component | Technology | Cost |
|-----------|------------|------|
| **Scraping Workers** | Hetzner CX21 VPS (2×) | $12/month |
| **Proxies** | BrightData + WebShare | $30-50/month |
| **CDN** | Cloudflare (free) | $0 |
| **Monitoring** | Sentry + Axiom (free) | $0 |
| **CI/CD** | GitHub Actions (free) | $0 |
| **Domain** | Cloudflare Registrar | $9/year |

### DevOps

| Tool | Purpose |
|------|---------|
| **Docker** | Consistent scraper environments |
| **PM2** | Process management on VPS |
| **GitHub Actions** | Automated testing + deployment |
| **Sentry** | Error tracking + performance monitoring |
| **Axiom** | Log aggregation |
| **UptimeRobot** | Uptime monitoring (free) |

---

## 3. Data Flow

### Scraping Flow

```
1. SCHEDULER (Convex Cron)
   ↓ Every 15-60 min (adaptive)
   
2. CREATE JOB (Convex Mutation)
   → Insert scrapeJob { storeId, status: 'pending', priority }
   ↓
   
3. TRIGGER WORKER (HTTP Webhook)
   → POST https://worker.budalert.com/scrape
   ↓
   
4. WORKER PICKS UP JOB (Node.js)
   → Fetch store details from Convex
   → Launch Playwright browser (with stealth config)
   → Navigate to store menu
   → Intercept network requests (GraphQL/REST APIs)
   → Extract product data
   ↓
   
5. VALIDATION (Worker)
   → Check required fields
   → Validate data types
   → Flag invalid products
   ↓
   
6. SAVE RAW DATA (Worker → R2)
   → Upload raw JSON to R2 bucket
   → Key: raw-scrapes/{store}/{timestamp}.json.gz
   ↓
   
7. SEND TO CONVEX (Worker → Convex Mutation)
   → convex.mutation(api.scraping.saveProducts, { storeId, products })
   ↓
   
8. NORMALIZATION (Convex Mutation)
   → Apply platform-specific extraction rules
   → Clean product names, parse prices
   → Standardize categories
   ↓
   
9. ENTITY RESOLUTION (Convex Mutation)
   → Generate signature (brand:name:variant:category)
   → Match against canonical products
   → Create or link to canonical entity
   ↓
   
10. CHANGE DETECTION (Convex Mutation)
    → Compare with existing product record
    → Detect changes (price, quantity, stock status)
    → Log changes to productChanges table
    → Emit events for real-time updates
    ↓
    
11. LLM ENRICHMENT (Optional, Async)
    → Queue hard-to-parse products
    → Batch 10 products per GPT-4o-mini call
    → Extract brand, category, variant
    → Update product records
    ↓
    
12. VELOCITY CALCULATION (Daily Batch)
    → Aggregate changes over 7-day window
    → Calculate units/hour, restocks/week
    → Assign velocity score (0-100)
    → Classify trend (hot/steady/slow/dead)
```

### API Flow

```
1. CLIENT REQUEST (Mobile/Web)
   → const products = useQuery(api.products.listProducts, { ... })
   ↓
   
2. CONVEX QUERY (Server)
   → Apply filters (category, store, inStockOnly)
   → Use cursor pagination (limit: 20)
   → Return minimal data (id, name, price, image, stock)
   ↓
   
3. CLIENT SUBSCRIPTION (Automatic)
   → Convex maintains WebSocket connection
   → Watches query dependencies
   ↓
   
4. DATA CHANGES (Product updated)
   → Convex detects change
   → Pushes update to subscribed clients
   ↓
   
5. CLIENT RE-RENDERS (Automatic)
   → React re-renders with new data
   → No manual polling needed
```

---

## 4. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Goal:** MVP with basic scraping + data storage

**Tasks:**
- [ ] Set up Convex project (schema, mutations, queries)
- [ ] Deploy 1× Hetzner VPS with Docker
- [ ] Implement scraper framework (Playwright + stealth)
- [ ] Build 5 platform adapters (Dutchie, Jane, WordPress, Blaze, custom)
- [ ] Manual scraping of 20 stores
- [ ] Data normalization pipeline
- [ ] Basic Convex queries (list products, get details)

**Deliverables:**
- Working scrapers for 20 stores
- Data in Convex (products table)
- Basic API (list + details)

**Budget:** $6/month (1 VPS, no proxies yet)

---

### Phase 2: Automation & Scale (Weeks 3-4)

**Goal:** Automated scraping + 100 stores

**Tasks:**
- [ ] Implement BullMQ job queue
- [ ] Convex cron scheduling (adaptive frequency)
- [ ] Add 80 more stores (100 total)
- [ ] Implement proxy rotation (datacenter proxies)
- [ ] Retry logic + circuit breakers
- [ ] Change detection system
- [ ] R2 cold storage integration
- [ ] Basic monitoring (Sentry, Axiom)

**Deliverables:**
- Automated scraping every 1-4 hours
- 100 stores scraped
- Change history tracked
- Monitoring dashboard

**Budget:** $31/month (VPS + datacenter proxies + LLM)

---

### Phase 3: Mobile App (Weeks 5-6)

**Goal:** Launch React Native app

**Tasks:**
- [ ] Set up React Native (Expo) project
- [ ] Implement product listing (FlatList + infinite scroll)
- [ ] Product detail view
- [ ] Search & filters (category, price, stock)
- [ ] Watchlist feature
- [ ] Push notifications setup (Expo)
- [ ] Offline support (AsyncStorage)
- [ ] iOS + Android builds

**Deliverables:**
- Mobile app (iOS + Android)
- App Store + Google Play submissions
- Real-time updates via Convex

**Budget:** $31/month (no additional infrastructure cost)

---

### Phase 4: Entity Resolution & Enrichment (Weeks 7-8)

**Goal:** Cross-store product matching + LLM enrichment

**Tasks:**
- [ ] Implement canonical product schema
- [ ] Entity resolution (signature + fuzzy matching)
- [ ] LLM enrichment pipeline (GPT-4o-mini, batched)
- [ ] Price comparison feature
- [ ] Availability trends
- [ ] Velocity metrics calculation
- [ ] Store-level aggregations

**Deliverables:**
- Products matched across stores
- Price comparisons
- Velocity scores
- Enhanced product data

**Budget:** $36/month (+$5 for LLM)

---

### Phase 5: Scale to 500 Stores (Weeks 9-12)

**Goal:** Full-scale deployment

**Tasks:**
- [ ] Add 400 more stores (500 total)
- [ ] Deploy 2nd VPS for redundancy
- [ ] Add residential proxies for hard targets
- [ ] CAPTCHA solving integration (2Captcha)
- [ ] Daily snapshot archival
- [ ] Advanced monitoring (uptime, latency, success rates)
- [ ] Web app (PWA with React)
- [ ] Performance optimizations (image CDN, caching)

**Deliverables:**
- 500 stores scraped
- 100K+ products tracked
- Web + mobile apps
- High availability (99.9% uptime target)

**Budget:** $71/month (full-scale infrastructure)

---

### Phase 6: Monetization & Polish (Weeks 13-16)

**Goal:** Launch paid tier + polish UX

**Tasks:**
- [ ] Implement subscription system (Stripe)
- [ ] Free vs Pro feature gating
- [ ] Real-time alerts (restock, price drop)
- [ ] Advanced filters (potency, strain type)
- [ ] User preferences (favorite stores, categories)
- [ ] Onboarding flow
- [ ] Marketing website
- [ ] Analytics (Mixpanel or PostHog)

**Deliverables:**
- Paid subscription ($4.99/month)
- Polished UX
- Marketing site
- User analytics

**Budget:** $71/month + Stripe fees (2.9% + $0.30 per transaction)

---

## 5. Risk Assessment

### High-Risk Issues

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Scraper detection/blocking** | High (no data) | Medium | Stealth plugins, proxy rotation, adaptive rate limiting, circuit breakers |
| **Platform changes break scrapers** | High (partial outage) | High | Fallback methods (API → browser → cache), monitoring alerts, version detection |
| **CAPTCHA at scale** | High (scraping fails) | Medium | CAPTCHA solvers (2Captcha), human fallback, avoid triggers |
| **Legal (terms of service)** | Critical (shutdown) | Low | Public data only, robots.txt compliance, rate limiting, consult legal |
| **Data quality issues** | Medium (bad UX) | Medium | Validation gates, human review queue, user reporting |

### Medium-Risk Issues

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Convex free tier limits** | Medium (upgrade cost) | Low | Monitor usage, optimize queries, prepared to pay $25/month |
| **VPS downtime** | Medium (scraping stops) | Low | 2× VPS redundancy, health checks, auto-restart (PM2) |
| **LLM API rate limits** | Low (slow enrichment) | Low | Batch processing, caching, queue with backoff |
| **Image CDN costs** | Low (budget overrun) | Low | Start with cache-only (free), lazy load, compression |
| **User growth exceeds capacity** | Medium (slow app) | Medium | Horizontal scaling (add workers), CDN, pagination |

### Low-Risk Issues

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Storage costs spike** | Low (budget impact) | Low | Compression, retention policies, cold storage (R2) |
| **Proxy costs spike** | Medium (budget impact) | Low | Smart proxy selection, cache sessions, avoid CAPTCHAs |
| **App store rejection** | Low (launch delay) | Low | Follow guidelines, test thoroughly, content moderation |
| **Negative user feedback** | Medium (churn) | Medium | User testing, iterative UX improvements, support channel |

---

## 6. Cost Projections

### MVP (Launch) - $6/month
- 20 stores, 5K products
- 1× VPS (scraping)
- Convex free tier
- No proxies, no LLM
- Basic mobile app

### Growth (100 stores) - $31/month
- 100 stores, 20K products
- 1× VPS + datacenter proxies
- LLM enrichment ($5)
- Web + mobile apps
- 1K users

### Scale (500 stores) - $71/month
- 500 stores, 100K products
- 2× VPS + residential proxies
- Full feature set
- 10K users
- $2,495 MRR (500 paid users @ $4.99) = **$2,424/month profit (97% margin)**

### Enterprise (5,000 stores) - $470/month
- 5,000 stores, 1M products
- Dedicated servers + proxy pools
- Convex paid tier ($25)
- 100K users
- $24,950 MRR (5,000 paid users @ $4.99) = **$24,480/month profit (98% margin)**

---

## 7. Success Metrics

### Scraping Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Success Rate** | >95% | Successful scrapes / total attempts |
| **Avg Scrape Time** | <30s | Time from job start to completion |
| **Data Completeness** | >90% | Products with all required fields |
| **Uptime** | >99% | Worker availability |
| **False Positives** | <1% | Invalid products flagged / total |

### Product Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **DAU** | 1,000 | Daily active users |
| **Session Duration** | 3-5 min | Avg time in app per session |
| **Products Viewed** | 10-20 | Products viewed per session |
| **Conversion Rate** | 5% | Free → Pro conversion |
| **Retention (D7)** | 40% | Users active 7 days after signup |
| **Churn Rate** | <5%/month | Cancelled subscriptions / total subs |

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **API Latency (p95)** | <500ms | 95th percentile response time |
| **Error Rate** | <0.1% | Failed requests / total requests |
| **Cache Hit Rate** | >80% | Cached responses / total requests |
| **Storage Growth** | <10 GB/month | R2 storage increase |

---

## 8. Comparison with Current State

### Before (Phase 1 Analysis)

| Aspect | Current State | Score |
|--------|---------------|-------|
| **Scraping** | 12 stores, manual, Python scripts | ⭐⭐ |
| **Data** | JSON files, fragmented | ⭐ |
| **Pipeline** | None (manual import) | ⭐ |
| **Change Detection** | None | ❌ |
| **Entity Resolution** | None | ❌ |
| **UI** | None | ❌ |
| **Real-time** | None | ❌ |
| **Cost** | ~$0/month | ⭐⭐⭐⭐⭐ |
| **Scalability** | Cannot scale | ❌ |

**Total:** 7/50 points (14%)

### After (Proposed Architecture)

| Aspect | Proposed State | Score |
|--------|----------------|-------|
| **Scraping** | 500 stores, automated, adaptive scheduling | ⭐⭐⭐⭐⭐ |
| **Data** | Hot/cold tiered, compressed, indexed | ⭐⭐⭐⭐⭐ |
| **Pipeline** | Multi-stage (raw → validation → staging → prod) | ⭐⭐⭐⭐⭐ |
| **Change Detection** | Full history, velocity metrics | ⭐⭐⭐⭐⭐ |
| **Entity Resolution** | Signature + fuzzy matching | ⭐⭐⭐⭐ |
| **UI** | Mobile-first (React Native) + Web (PWA) | ⭐⭐⭐⭐⭐ |
| **Real-time** | Convex reactive queries | ⭐⭐⭐⭐⭐ |
| **Cost** | $71/month at scale | ⭐⭐⭐⭐ |
| **Scalability** | Horizontal scaling, 10× growth ready | ⭐⭐⭐⭐⭐ |

**Total:** 44/50 points (88%)

---

## 9. Recommendations

### Short-Term (Weeks 1-4)

1. **Start with MVP** ($6/month)
   - 20 easy-to-scrape stores (WordPress, no CAPTCHA)
   - Manual validation of data quality
   - Basic mobile app (product listing + details)
   - Launch to friends/family for feedback

2. **Validate Product-Market Fit**
   - Is velocity data valuable?
   - Do users want cross-store price comparisons?
   - Which features drive engagement?

3. **Iterate Quickly**
   - Weekly deploys
   - User feedback → immediate fixes
   - A/B test UI changes

### Medium-Term (Weeks 5-12)

1. **Scale to 100 Stores**
   - Automate scraping (BullMQ + Convex cron)
   - Add medium-difficulty stores (Blaze, custom platforms)
   - Implement change detection

2. **Build Core Features**
   - Entity resolution (cross-store matching)
   - Velocity scores
   - Price comparisons
   - Watchlist + alerts

3. **Polish UX**
   - Skeleton screens
   - Offline support
   - Push notifications
   - Search & filters

### Long-Term (Months 4-6)

1. **Scale to 500 Stores**
   - Add hard targets (Dutchie, Jane, CAPTCHA sites)
   - Residential proxies for stealth
   - 2nd VPS for redundancy

2. **Monetize**
   - Launch Pro tier ($4.99/month)
   - Target 5% conversion (500 paid users)
   - Break-even at 11 paid users

3. **Expand**
   - Add more regions (CA, CO, MA)
   - Advanced features (trends, recommendations)
   - Partnerships with dispensaries?

---

## 10. Final Thoughts

### Why This Architecture?

**1. Cost-Efficient**
- Free tiers cover 90% of infrastructure
- $71/month at scale (500 stores, 100K products)
- 97% profit margin with subscription model

**2. Scalable**
- Horizontal scaling (add workers, not re-architect)
- 10× growth = 2× cost (linear, not exponential)
- Convex handles real-time without custom WebSocket code

**3. Fast to Market**
- Convex eliminates backend boilerplate
- React Native = one codebase, two platforms
- Free tiers = launch with minimal risk

**4. Maintainable**
- TypeScript end-to-end (type safety)
- Clear separation of concerns (scraping → pipeline → storage → API → UI)
- Monitoring built-in (Sentry, Axiom)

**5. Future-Proof**
- Platform-agnostic scraping (adapters for each platform)
- Entity resolution enables multi-store analytics
- Cold storage (R2) allows unlimited historical analysis

### What Could Go Wrong?

**Legal Risks:**
- Scraping violates ToS → Talk to lawyer, focus on public data only
- Copyright claims → Don't store images long-term, hotlink or use CDN

**Technical Risks:**
- Mass CAPTCHA deployment → Need human solvers or pivot to partnerships
- Platform consolidation (all sites use one provider) → Would actually help (one adapter!)

**Business Risks:**
- Low user interest → Validate PMF early, pivot features if needed
- Competition → First-mover advantage, build moat with data (historical trends)

### Success Factors

1. **Data Quality:** Accurate, up-to-date data is #1 priority
2. **Performance:** Fast load times, smooth scrolling, real-time updates
3. **Reliability:** 99.9% uptime, alerts when scraping fails
4. **User Experience:** Mobile-first, offline support, push notifications
5. **Cost Control:** Stay lean, optimize early, don't overspend on infrastructure

---

## Phase 7 Complete ✅

**Deliverables:**
1. ✅ System architecture diagram (high-level + data flow)
2. ✅ Technology stack (backend, frontend, infrastructure, devops)
3. ✅ Implementation roadmap (6 phases, 16 weeks)
4. ✅ Risk assessment (high/medium/low risks + mitigations)
5. ✅ Cost projections (MVP $6 → Scale $71 → Enterprise $470)
6. ✅ Success metrics (scraping, product, technical KPIs)
7. ✅ Before/after comparison (14% → 88% score)
8. ✅ Recommendations (short/medium/long-term)

---

## All Phases Complete! 🎉

**Summary:**
- **Phase 1:** Current state analysis (12 stores, manual scraping, no pipeline)
- **Phase 2:** Scraping layer research (stealth, platform strategies, distributed architecture)
- **Phase 3:** Data pipeline (hot/cold storage, change detection, orchestration)
- **Phase 4:** Transformation layer (normalization, entity resolution, LLM enrichment)
- **Phase 5:** Mobile-first delivery (pagination, real-time, offline, UI/UX)
- **Phase 6:** Cost optimization ($6 MVP → $71 scale, 97% profit margin)
- **Phase 7:** Tech spec & recommendations (complete architecture, roadmap, risks)

**Final Architecture:**
- **Scraping:** Playwright + stealth on Hetzner VPS, BullMQ job queue, adaptive scheduling
- **Storage:** Convex (hot, free) + R2 (cold, $1/month)
- **Pipeline:** Multi-stage validation, normalization, entity resolution
- **API:** Convex reactive queries (real-time, no WebSocket setup)
- **UI:** React Native (mobile) + React (web PWA)
- **Cost:** $71/month at scale (500 stores, 100K products, 10K users)
- **Margin:** 97% with $4.99/month Pro tier

**Ready for implementation!** 🚀

---
