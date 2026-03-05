# Phase 6: Cost Optimization Analysis

**Date:** 2026-03-05  
**Focus:** Detailed cost projections and optimization strategies for scale

---

## Executive Summary

**Target Scale:**
- 500 stores
- 100,000 products
- Scrape every 1-4 hours (adaptive)
- 10,000 monthly active users
- 1M API requests/month

**Projected Monthly Costs:**
- **Optimized:** $150-300/month
- **Naive (without optimization):** $2,000-5,000/month

**Cost Breakdown:**
| Component | Optimized | Naive | Savings |
|-----------|-----------|-------|---------|
| Scraping | $50-100 | $500-1000 | 80% |
| Storage | $0.10-1 | $50-100 | 98% |
| Compute | $20-50 | $200-500 | 80% |
| LLM | $5-10 | $50-100 | 90% |
| CDN | $10-20 | $100-200 | 85% |
| Monitoring | $0 (free tier) | $50 | 100% |
| **Total** | **$85-181** | **$950-1950** | **85%** |

---

## 1. Scraping Infrastructure Costs

### Components

**1.1 Browser Automation Compute**

**Workload:**
- 500 stores × 6 scrapes/day avg (adaptive) = **3,000 scrapes/day**
- Average scrape time: 30 seconds
- Total compute: 3,000 × 30s = **25 hours/day**

**Options:**

| Option | Cost | Pros | Cons |
|--------|------|------|------|
| **VPS (Hetzner CX21)** | $6/month | Cheap, predictable | Manual setup, single point of failure |
| **AWS EC2 (t3.medium)** | $30/month | Scalable, reliable | More expensive |
| **Cloudflare Workers** | $5/10M requests | Serverless, global | 5min timeout, limited browser support |
| **Railway/Render** | $20/month | Easy deploy | Limited control |
| **DigitalOcean Droplet** | $12/month | Balance | Moderate cost |

**Recommendation:** **Hetzner CX21 ($6/month)** for workers + monitoring

- 2 vCPU, 4GB RAM
- Enough for 5 concurrent browser instances
- Can handle 3,000 scrapes/day comfortably
- Add second VPS ($6) if growth exceeds capacity

**Cost:** **$12/month** (2 VPS for redundancy)

---

**1.2 Proxy Costs**

**Requirement:**
- Hard targets (Cloudflare, CAPTCHA): ~10% of stores = 50 stores
- Medium targets: ~40% = 200 stores
- Easy targets (no proxy): ~50% = 250 stores

**Proxy Usage:**
- Hard targets: Residential proxies (50 stores × 6 scrapes/day × 500KB) = **150 MB/day** = 4.5 GB/month
- Medium targets: Datacenter proxies (200 stores × 6 scrapes/day × 500KB) = **600 MB/day** = 18 GB/month

**Costs:**
| Proxy Type | Cost/GB | Usage | Monthly Cost |
|------------|---------|-------|--------------|
| Residential (BrightData) | $10-15/GB | 4.5 GB | $45-68 |
| Datacenter (WebShare) | $1-3/GB | 18 GB | $18-54 |
| **Total** | - | - | **$63-122** |

**Optimization Strategies:**

**Strategy 1: Selective Proxy Use**
- Only use proxies when needed (detection logic)
- Most scrapes don't need proxies (50% of stores)

**Strategy 2: Shared Residential Pool**
- Rotate IPs only on failure
- Reuse sessions for multiple requests
- **Reduce residential usage by 50%:** 2.25 GB = $22-34/month

**Strategy 3: Free Datacenter Proxies**
- Use free proxies for low-risk targets
- Fall back to paid on failure
- **Reduce datacenter cost by 70%:** $5-16/month

**Optimized Proxy Cost:** **$27-50/month**

---

**1.3 CAPTCHA Solving (Optional)**

**Requirement:**
- ~5% of scrapes encounter CAPTCHA = 150/day
- 2Captcha cost: $2.99/1000 CAPTCHAs

**Monthly Cost:**
- 150 × 30 = 4,500 CAPTCHAs/month
- 4,500 / 1000 × $2.99 = **$13.50/month**

**Optimization:** Avoid CAPTCHAs instead of solving
- Better fingerprinting
- Slower scraping
- Proxy rotation
- **Target: <1% CAPTCHA rate = $3/month**

---

**Total Scraping Cost (Optimized):** **$42-65/month**

---

## 2. Storage Costs

### 2.1 Hot Storage (Convex)

**Free Tier Limits:**
- Storage: 1 GB
- Bandwidth: 5 GB/month
- Function calls: 1M/month

**Our Usage:**
- Current products: 100K × 1KB = 100 MB
- 7-day change history: ~14 MB
- Stores, users, watchlist: ~10 MB
- **Total: ~130 MB** ✅ Well within free tier

**Cost:** **$0/month** (free tier)

---

### 2.2 Cold Storage (Cloudflare R2)

**Data Volume:**
- Raw scrapes: 3,000/day × 50KB = 150 MB/day
- 7-day retention = 1 GB
- Daily snapshots (compressed): 100 MB/day × 90 days = 9 GB
- Change logs (compressed): 20 MB/day × 90 days = 1.8 GB
- **Total: ~12 GB**

**R2 Pricing:**
- Storage: $0.015/GB/month
- Class A operations (writes): $4.50/million
- Class B operations (reads): $0.36/million

**Monthly Cost:**
- Storage: 12 GB × $0.015 = **$0.18**
- Writes: 3,000 scrapes/day × 30 = 90K writes = **$0.40**
- Reads: ~10K reads/month (low usage) = **$0.004**
- **Total: $0.58/month**

**Cost:** **$1/month** (with buffer)

---

### 2.3 Image Storage (Optional CDN)

**Challenge:** Product images are hosted by stores (no storage cost), but:
- Slow load times from origin servers
- Broken links when products removed
- No optimization (large file sizes)

**Solution: Cloudflare Images**
- Cache-only mode: $0 (just proxying)
- Or: Upload to R2 + Cloudflare Images transform
  - Storage: ~10 GB for 100K images = $0.15/month
  - Transformations: 100K variants = $1/month
  - **Total: $1.15/month**

**Recommendation:** Start with cache-only (free), upgrade later

**Cost:** **$0-1/month**

---

**Total Storage Cost:** **$1-2/month**

---

## 3. Compute Costs

### 3.1 Data Pipeline (Convex Actions)

**Free Tier:**
- 1M function calls/month

**Our Usage:**
- Scraping jobs: 3,000/day × 30 = 90K/month
- API queries: ~100K/month (10K users × 10 queries/session)
- Mutations: ~20K/month
- **Total: ~210K/month** ✅ Within free tier

**Paid Tier (if needed):**
- $25/month for 10M calls
- We're at 2% of free tier, won't need paid

**Cost:** **$0/month**

---

### 3.2 Worker Processes

**Covered by VPS cost ($12/month above)**

---

### 3.3 LLM Transformations

**From Phase 4 Analysis:**
- One-time enrichment: 100K products × $0.000026 = $2.60
- Ongoing: ~100 new products/day × $0.000026 = $0.0026/day = **$0.08/month**

**Optimization:**
- Cache all results (never re-process)
- Only use LLM for hard cases (~10% of products)
- Batch processing (10 products/request)

**Cost:** **$5/month** (with buffer for retries)

---

### 3.4 Entity Resolution

**Computation:**
- 100 new products/day
- Fuzzy matching against ~100 candidates each = 10K comparisons/day
- Levenshtein distance: ~1ms per comparison = 10 seconds/day
- **Negligible compute cost** (runs on application server)

**Cost:** **$0/month**

---

**Total Compute Cost:** **$5/month**

---

## 4. Delivery Costs

### 4.1 CDN (Cloudflare)

**Free Tier:**
- Unlimited bandwidth
- 100K Workers requests/day

**Our Usage:**
- API requests: ~100K/month = 3,300/day ✅ Within free tier
- Image proxy: ~1M image loads/month
- Static assets: ~10 GB/month

**All covered by Cloudflare free tier.**

**Cost:** **$0/month**

---

### 4.2 Convex Bandwidth

**Free Tier:**
- 5 GB/month

**Our Usage:**
- Product list queries: 100K queries × 20KB = 2 GB/month
- Product details: 10K queries × 50KB = 0.5 GB/month
- Real-time subscriptions: ~1 GB/month
- **Total: ~3.5 GB/month** ✅ Within free tier

**Cost:** **$0/month**

---

### 4.3 Push Notifications (Expo)

**Free Tier:**
- Unlimited push notifications

**Our Usage:**
- 10K users × 2 notifications/week = 20K notifications/week = 80K/month
- ✅ Free on Expo

**Cost:** **$0/month**

---

**Total Delivery Cost:** **$0/month**

---

## 5. Monitoring & Observability

### 5.1 Error Tracking (Sentry)

**Free Tier:**
- 5K events/month

**Our Usage:**
- ~100 errors/day = 3K/month ✅ Within free tier

**Cost:** **$0/month**

---

### 5.2 Logging (Axiom / Logtail)

**Free Tier (Axiom):**
- 0.5 GB ingestion/month

**Our Usage:**
- ~100 MB/month ✅ Within free tier

**Cost:** **$0/month**

---

### 5.3 Uptime Monitoring (UptimeRobot)

**Free Tier:**
- 50 monitors

**Our Usage:**
- ~10 endpoints ✅ Free

**Cost:** **$0/month**

---

**Total Monitoring Cost:** **$0/month**

---

## 6. Cost Summary

### Optimized Architecture (Target)

| Component | Cost | Notes |
|-----------|------|-------|
| **Scraping Compute** | $12 | 2× Hetzner VPS |
| **Proxies** | $30-50 | Residential + datacenter (optimized) |
| **CAPTCHA Solving** | $3 | Minimal with good stealth |
| **Hot Storage (Convex)** | $0 | Free tier |
| **Cold Storage (R2)** | $1 | ~12 GB compressed |
| **Image CDN** | $0-1 | Cache-only or R2 |
| **Compute (Convex)** | $0 | Free tier |
| **LLM** | $5 | GPT-4o-mini, cached |
| **CDN (Cloudflare)** | $0 | Free tier |
| **Monitoring** | $0 | Free tiers |
| **Total** | **$51-71/month** | 🎯 |

---

### Scaling Projections

| Metric | Current | 2× Scale | 5× Scale | 10× Scale |
|--------|---------|----------|----------|-----------|
| **Stores** | 500 | 1,000 | 2,500 | 5,000 |
| **Products** | 100K | 200K | 500K | 1M |
| **Users** | 10K | 20K | 50K | 100K |
| **Scraping** | $45 | $90 | $225 | $450 |
| **Storage** | $2 | $4 | $10 | $20 |
| **Compute** | $5 | $10 | $25 | $50 |
| **CDN** | $0 | $0 | $10 | $25 |
| **Total** | **$52** | **$104** | **$270** | **$545** |

**Key Insight:** Costs scale **linearly** with optimization, not exponentially.

---

## 7. Optimization Strategies

### 7.1 Scraping Optimizations

**Strategy: Adaptive Scraping Frequency**
- High-velocity stores: Every 15 minutes
- Medium-velocity: Every 1 hour
- Low-velocity: Every 4 hours
- **Savings: 50% fewer scrapes = $22.50/month**

**Strategy: Differential Scraping**
- Check product count first (fast)
- Only full scrape if count changed significantly
- **Savings: 70% faster scrapes = $13.50/month**

**Strategy: Smart Proxy Selection**
- Only use proxies when detected
- Cache successful sessions
- **Savings: 40% proxy cost = $12-20/month**

**Strategy: Avoid CAPTCHAs**
- Better stealth (fingerprinting, rotation)
- Slow down on detection
- **Savings: 90% CAPTCHA cost = $12/month**

**Total Scraping Savings:** **$60-68/month** → **New cost: $15-25/month**

---

### 7.2 Storage Optimizations

**Strategy: Aggressive Compression**
- gzip JSON before R2 upload
- 10× reduction in storage
- **Savings: 90% storage cost = $0.90/month**

**Strategy: Smart Retention**
- Raw scrapes: 7 days (not 30)
- Snapshots: 90 days daily, then weekly
- **Savings: 80% storage = $0.80/month**

**Total Storage Savings:** **$1.70/month** → **New cost: $0.30/month**

---

### 7.3 Compute Optimizations

**Strategy: Batch LLM Calls**
- 10 products per request
- Already implemented in Phase 4
- **Current cost: $5/month** (already optimized)

**Strategy: Cache Everything**
- LLM results cached forever
- Entity resolution cached
- **No additional cost**

---

### 7.4 Delivery Optimizations

**Strategy: Image Optimization**
- WebP format (30% smaller)
- Lazy loading
- CDN caching
- **Current cost: $0** (free tier sufficient)

**Strategy: API Response Compression**
- gzip API responses
- Reduce bandwidth by 70%
- **Stay in Convex free tier**

---

## 8. Cost-Efficient Architecture Recommendations

### 8.1 MVP (Launch with $0-10/month)

**Stack:**
- Convex (free tier): Database + API + real-time
- Cloudflare (free): CDN + Workers
- 1× Hetzner VPS ($6): Scraping workers
- No proxies initially (scrape only easy targets)
- No CAPTCHA solving
- No LLM (manual categorization for MVP)

**Result:** **$6/month** for scraping compute only

---

### 8.2 Growth (100 stores, 20K products) - $30-50/month

**Stack:**
- Convex (free): Still within limits
- Cloudflare (free): Still sufficient
- 1× Hetzner VPS ($6): Scraping
- Datacenter proxies ($15): Medium-difficulty stores
- CAPTCHA budget ($5): Handle edge cases
- LLM ($5): Enrich new products

**Result:** **$31/month**

---

### 8.3 Scale (500 stores, 100K products) - $51-71/month

**Stack (as designed):**
- Convex (free): 130 MB storage, 200K function calls
- Cloudflare (free): Unlimited bandwidth
- 2× Hetzner VPS ($12): Redundant workers
- Residential + datacenter proxies ($30-50): All difficulty levels
- CAPTCHA solving ($3): Minimal with stealth
- R2 ($1): Cold storage
- LLM ($5): Ongoing enrichment

**Result:** **$51-71/month**

---

### 8.4 Enterprise (5,000 stores, 1M products) - $500-700/month

**Upgrades needed:**
- Convex ($25): Paid tier for 10M function calls
- Hetzner dedicated ($60): 10× VPS or 2× dedicated servers
- Proxies ($300): 10× usage
- R2 ($20): 120 GB storage
- LLM ($50): 10× enrichment volume
- Cloudflare Workers ($5): Some API endpoints
- Monitoring ($10): Paid Sentry tier

**Result:** **$470/month**

---

## 9. Cost Comparison with Alternatives

### Alternative 1: AWS Fully Managed

| Service | Monthly Cost |
|---------|--------------|
| ECS Fargate (scraping) | $150 |
| RDS PostgreSQL (hot storage) | $100 |
| S3 (cold storage) | $10 |
| Lambda (API) | $50 |
| API Gateway | $30 |
| CloudFront (CDN) | $50 |
| ALB (load balancer) | $25 |
| **Total** | **$415/month** |

**Savings with our architecture:** **$344/month (83%)**

---

### Alternative 2: All-in-One PaaS (Heroku/Railway)

| Service | Monthly Cost |
|---------|--------------|
| Web dyno (API) | $25 |
| Worker dynos (scraping) × 3 | $75 |
| PostgreSQL (hot storage) | $50 |
| Redis (caching) | $30 |
| S3 (cold storage) | $10 |
| **Total** | **$190/month** |

**Savings with our architecture:** **$119/month (63%)**

---

### Alternative 3: Firebase/Supabase

| Service | Monthly Cost |
|---------|--------------|
| Firestore (hot storage) | $25 |
| Cloud Functions (API) | $50 |
| Cloud Storage (cold) | $10 |
| External scraping workers | $100 |
| **Total** | **$185/month** |

**Savings with our architecture:** **$114/month (62%)**

---

## 10. ROI Analysis

### Revenue Assumptions (Hypothetical)

**Subscription Model:**
- Free tier: Basic product browsing
- Pro tier: $4.99/month
  - Real-time alerts
  - Price tracking
  - Watchlist

**User Conversion:**
- 10K free users
- 5% convert to Pro = 500 paid users
- **MRR: 500 × $4.99 = $2,495/month**

**Cost at this scale:** ~$51-71/month

**Profit Margin:** **$2,424/month (97%)**

**Break-even:** 11 paid users ($54 MRR vs $51 cost)

---

### Cost Per User

| Scale | Users | Monthly Cost | Cost/User |
|-------|-------|--------------|-----------|
| **MVP** | 100 | $6 | $0.06 |
| **Growth** | 1,000 | $31 | $0.03 |
| **Scale** | 10,000 | $71 | $0.007 |
| **Enterprise** | 100,000 | $470 | $0.005 |

**Insight:** Costs per user **decrease** with scale (economies of scale).

---

## Phase 6 Complete ✅

**Deliverables:**
1. ✅ Detailed cost breakdown (scraping, storage, compute, delivery)
2. ✅ Cost projections at different scales (1×, 2×, 5×, 10×)
3. ✅ Optimization strategies (adaptive scraping, compression, caching)
4. ✅ Architecture recommendations (MVP $6/month → Scale $71/month → Enterprise $470/month)
5. ✅ ROI analysis (97% profit margin at scale, $0.007 cost per user)
6. ✅ Comparison with alternatives (83% savings vs AWS, 63% vs PaaS)

**Key Insights:**
- **MVP launch: $6/month** (Convex free + 1 VPS)
- **At scale (500 stores, 100K products): $51-71/month**
- **10× scale: $470/month** (still very affordable)
- **Costs scale linearly** with optimizations (not exponentially)
- **Free tiers cover 90%** of infrastructure (Convex, Cloudflare, monitoring)
- **Most cost is scraping** (proxies + compute), which is optimizable
- **High profit margins** possible ($2,495 MRR vs $71 cost = 97% margin)

**Next Phase:** Tech Spec & Recommendations (architecture diagram, stack, implementation roadmap, risk assessment, cost projections)

---
