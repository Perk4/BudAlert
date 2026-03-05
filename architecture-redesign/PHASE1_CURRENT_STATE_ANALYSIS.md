# Phase 1: Current State Analysis - BudAlert

**Date:** 2026-03-05  
**Analyst:** Subagent (budalert-architecture-redesign)  
**Repo:** ~/clawd/budalert

---

## Executive Summary

BudAlert is an early-stage **SKU velocity tracking product** for the cannabis dispensary space, focused on tracking product availability and movement across hundreds of stores using **scraping + public APIs only** (no POS/ecom integrations). 

The project has completed **Phase 6** of an initial "stealth scraper bake-off" with 12+ working store scrapers, 126+ products extracted, and basic monitoring infrastructure. Phase 7 (inventory validation) is in progress.

**Current Stack:**
- **Backend:** Convex (serverless database/API)
- **Scraping:** Python (Playwright/Requests) + Node.js research
- **Data:** JSON files, Convex tables
- **Monitoring:** Basic polling scheduler (Phase 6)
- **UI:** Not yet implemented

---

## Architecture Overview

### Current Components

```
┌─────────────────────────────────────────────────────────┐
│                    DATA SOURCES                         │
│  (20+ NYC Dispensaries - Web Scraping Only)            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              SCRAPING LAYER (Python)                    │
│  • Platform-specific scrapers (42 .py files)           │
│  • Playwright browser automation                        │
│  • Request-based (for simple sites)                     │
│  • Validation & monitoring scripts                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            DATA STORAGE (Mixed)                         │
│  • JSON files (e.g., alta_products.json)               │
│  • Convex tables (nysDispensaries)                     │
│  • /tmp files (dispensaries.json)                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            API LAYER (Convex)                           │
│  • schema.ts - Database schema                         │
│  • nysDispensaries.ts - Mutations & queries            │
│  • loadDispensaries.ts - Bulk loader                   │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│               UI LAYER (Not Built)                      │
│  • Mobile-first design (planned)                       │
│  • Real-time updates needed                            │
└─────────────────────────────────────────────────────────┘
```

---

## Current Data Flow

### Scraping → Storage → API

1. **Scraping (Manual/Scheduled):**
   - Python scripts run on-demand
   - Extract products from dispensary websites
   - Save to JSON files or temp storage

2. **Data Preparation:**
   - JSON files enriched with timestamps
   - Prepared for Convex import

3. **Import to Convex:**
   - Node.js import scripts (e.g., `import-nys-dispensaries.js`)
   - Batch upsert (50 records at a time)
   - Duplicate prevention via unique keys

4. **Query/Delivery:**
   - Convex queries (list, count, getStats, filter by city/ZIP)
   - **No UI yet** — data only accessible via API/dashboard

---

## Scraping Approaches Documented

### Platform Coverage (Phase 2 Research)

| Platform | Stores | Complexity | Method | Status |
|----------|--------|------------|--------|--------|
| **Dutchie** | Conbud LES | ⭐⭐⭐⭐⭐ Very High | Browser + Network Intercept | 📋 Planned |
| **Blaze** | Housing Works SoHo | ⭐⭐⭐ Medium | Hybrid (Browser + API) | ✅ Existing scraper |
| **WordPress/Dovetail** | Gotham NYC | ⭐⭐ Low-Medium | JSON-LD / WordPress API | ✅ Existing scraper |
| **Joint eCommerce** | Alta, Stoops | ⭐⭐ Medium | Custom requests | ✅ Working (alta.py) |
| **Leafbridge** | Qube NYC | ⭐⭐⭐ Medium | Leafbridge base scraper | ✅ Working |
| **Hard Targets** | Curaleaf, Rise | ⭐⭐⭐⭐⭐ Very High | Protection analysis done | ⚠️ Blocked (CAPTCHA) |
| **Custom Sites** | Happy Munkey, Smacked | ⭐⭐ Low-Medium | HTML scraping | ✅ Working |

### Scraping Techniques Used

**Browser Automation:**
- Playwright (Python) for client-rendered sites
- Network interception to capture API calls
- Cookie/session management for age gates
- Cart probing for inventory detection

**Direct API Calls:**
- Reverse-engineered GraphQL (Dutchie)
- REST endpoints (Blaze, others)
- JSON-LD structured data (WordPress)

**Stealth Techniques:**
- User-agent rotation
- Rate limiting
- Session persistence
- Error retry logic

---

## Data Schema

### Products (Sample: alta_products.json)

```json
{
  "id": "alta_001",
  "name": "Blue Dream 3.5g",
  "price": 55.0,
  "price_raw": "$55.00",
  "url": "https://alta.nyc/products/blue-dream-35g",
  "store": "alta",
  "scraped_at": "2026-03-02T01:39:00.000000",
  "category": "flower",
  "description": "...",
  "thc_content": 18.5,
  "cbd_content": 0.8,
  "in_stock": true,
  "strain_type": "hybrid",
  "raw_thc": "18.5%",
  "raw_cbd": "0.8%"
}
```

**Fields Extracted:**
- ✅ Product ID, name, price
- ✅ Category, description
- ✅ THC/CBD content (when available)
- ✅ Stock status (boolean)
- ⚠️ **Quantity available** (Phase 7 in progress)
- ⚠️ Brand (inconsistent)
- ⚠️ Images (inconsistent)

### Dispensaries (Convex: nysDispensaries)

```typescript
{
  entity_name: string,
  address?: string,
  city: string,
  zip_code?: string,
  website?: string,
  is_microbusiness: boolean,
  is_delivery_only: boolean,
  scraped_at: number  // Unix timestamp
}
```

**Data Source:** NYS Cannabis Control Board  
**Records:** 599 dispensaries  
**Coverage:** Statewide NY

---

## Strengths

### ✅ What's Working Well

1. **Platform Diversity**
   - Multiple scraper types (Playwright, requests, hybrid)
   - Proven methods for 5+ major platforms
   - Documented approaches for hard targets

2. **Research Rigor**
   - Comprehensive Phase 1/2 planning docs
   - 20 methods analyzed across 3 dispensaries
   - Scoring framework (reliability, speed, maintainability)

3. **Data Quality Focus**
   - Validation infrastructure (accuracy reports)
   - Ground truth verification planned
   - Structured schemas for products and stores

4. **Convex Integration**
   - Clean schema design
   - Upsert logic for duplicate prevention
   - Indexed queries for performance
   - Batch processing for reliability

5. **Stealth Awareness**
   - Age gate bypass
   - Rate limiting considerations
   - Multiple fallback methods
   - Cart probing for inventory

---

## Weaknesses & Gaps

### ❌ Critical Issues

1. **No UI/Delivery Layer**
   - Data exists but no way for users to access it
   - No mobile-first interface
   - No real-time updates or push notifications
   - **Impact:** Can't validate product-market fit

2. **Inventory Data Incomplete**
   - Only boolean `in_stock` status
   - No actual quantity tracking
   - Phase 7 attempting to fix, but not complete
   - **Impact:** Can't track SKU velocity properly

3. **No Pipeline Orchestration**
   - Scraping is manual or ad-hoc
   - No scheduling infrastructure (mentioned but not built)
   - No coordinated scraping across stores
   - **Impact:** Stale data, missed changes

4. **Storage Is Fragmented**
   - JSON files in multiple locations
   - Some data in Convex, some in /tmp
   - No clear "source of truth"
   - **Impact:** Hard to scale, data integrity issues

5. **No Change Detection**
   - Phase 7B planned (24-hour polling test) but not done
   - No historical tracking of product changes
   - No "velocity" calculation
   - **Impact:** Core feature (SKU velocity) is missing

6. **Scalability Concerns**
   - 42 Python files, no shared framework
   - Each scraper is standalone
   - No distributed scraping
   - Manual deployment/management
   - **Impact:** Can't scale to hundreds of stores

7. **No Error Handling at Scale**
   - Individual scrapers have retries
   - No system-wide monitoring
   - No alerting for failures
   - No circuit breakers
   - **Impact:** Silent failures, stale data

8. **No Entity Resolution**
   - Same product at different stores = different IDs
   - No normalization across platforms
   - No brand/product matching
   - **Impact:** Can't do cross-store analysis

---

## Technical Debt

### Code Quality

- **Language Mix:** Python scrapers + Node.js tooling + TypeScript Convex
- **No Framework:** Each scraper is custom, no shared base
- **No Tests:** No automated testing infrastructure
- **Documentation:** Good planning docs, but code lacks comments
- **Version Control:** Good git hygiene, but no CI/CD

### Infrastructure

- **Single Machine:** No distributed scraping
- **No Queuing:** No job queue for scraping tasks
- **No Caching:** Re-scrape everything every time
- **No CDN:** No optimization for data delivery
- **No Backup:** R2 backups mentioned but implementation unclear

### Data

- **No Versioning:** Can't rollback to previous scrapes
- **No Deduplication:** Manual upsert logic in each scraper
- **No Validation:** Schemas exist but no enforcement
- **No Compression:** JSON files are uncompressed

---

## Scale Analysis

### Current Scale
- **Stores:** 12+ working scrapers (20+ researched)
- **Products:** 126+ extracted
- **Data Size:** ~170KB (nys_dispensaries_prepared.json)
- **Scraping Frequency:** Manual/ad-hoc

### Target Scale (Per Requirements)
- **Stores:** Hundreds of stores
- **Products:** Hundreds per store = **tens of thousands** total
- **Data Size:** ~1GB+ (with full product details, images, history)
- **Scraping Frequency:** Continuous (every 15-60 minutes per store)

### Bottlenecks at Scale

| Component | Current | Target | Bottleneck |
|-----------|---------|--------|------------|
| **Scraping** | 12 stores manual | 500+ stores automated | No orchestration |
| **Storage** | JSON files | Structured DB | File I/O, deduplication |
| **Queries** | Convex (good) | High-frequency mobile | Real-time updates needed |
| **Bandwidth** | Minimal | High (images, history) | No CDN, no compression |
| **Cost** | Near-zero | Unknown | Browser automation at scale |

---

## Cost Considerations (Current)

### Compute
- **Local scraping:** Free (developer machine)
- **Convex:** Free tier (599 records = trivial)
- **Monitoring:** None yet

### Storage
- **JSON files:** Negligible (<1MB)
- **Convex:** Free tier

### Data Transfer
- **Scraping:** ~10-50KB per store (text-based)
- **Images:** Not consistently downloaded/stored

**Current Monthly Cost:** ~$0  
**Estimated at Target Scale:** $500-2000/month (rough guess)

---

## Key Learnings from Research

### From Phase 2 Planning Docs

1. **Platform Complexity Varies Wildly**
   - WordPress sites = easy (curl + HTML)
   - Dutchie = very hard (React, GraphQL, potential CAPTCHA)

2. **Multiple Fallback Methods Are Critical**
   - Primary: Direct API
   - Fallback: Browser automation
   - Last resort: HTML scraping

3. **Inventory Detection Is Hard**
   - Cart probing works but is slow and detectable
   - Dropdown parsing is fragile
   - API responses are best but not always available

4. **Stealth Is Required**
   - Age gates are universal
   - Some sites have CAPTCHA (Curaleaf, Rise)
   - User-agent and rate limiting matter

5. **Data Normalization Is a Huge Lift**
   - Every platform has different product schemas
   - THC/CBD formats vary (18.5%, 18-20%, <20%, etc.)
   - Categories are inconsistent

---

## Recommendations for Phase 2+

### Immediate Priorities (Phase 2: Scraping Layer)

1. **Unified Scraper Framework**
   - Abstract common patterns (Playwright setup, rate limiting, retries)
   - Plugin architecture for platform-specific logic
   - Centralized configuration

2. **Distributed Scraping**
   - Worker queue system (BullMQ, Celery, Convex actions)
   - Horizontal scaling for hundreds of stores
   - Failure isolation

3. **Stealth Improvements**
   - Proxy rotation
   - Fingerprint randomization
   - CAPTCHA detection and handling

### Data Pipeline (Phase 3)

1. **Ingestion Layer**
   - Raw data → staging → production
   - Validation before commit
   - Schema enforcement

2. **Change Detection**
   - Track diffs between scrapes
   - Store historical data
   - Calculate velocity metrics

3. **Storage Strategy**
   - Hot: Recent data in Convex
   - Cold: Historical data in R2/S3
   - Compression for large datasets

### Transformation Layer (Phase 4)

1. **Entity Resolution**
   - Match products across stores
   - Normalize brands and categories
   - Handle duplicates

2. **Derived Metrics**
   - SKU velocity scores
   - Availability trends
   - Price comparisons

3. **LLM Assistance**
   - Product categorization
   - Brand extraction from names
   - Description normalization

### Delivery Layer (Phase 5)

1. **Mobile-First UI**
   - React Native or similar
   - Real-time updates via Convex subscriptions
   - Lazy loading for large datasets

2. **API Design**
   - GraphQL or REST
   - Pagination
   - Filtering and search

3. **Push Notifications**
   - New products
   - Price changes
   - Restocks

### Cost Optimization (Phase 6)

1. **Scraping Efficiency**
   - Cache unchanged pages
   - Differential scraping
   - Batch browser sessions

2. **Storage Efficiency**
   - Compress historical data
   - Archive old scrapes
   - CDN for static assets

3. **Compute Efficiency**
   - Serverless for scraping (Cloudflare Workers?)
   - Shared browser instances
   - Smart scheduling

---

## Phase 1 Deliverable Summary

### ✅ Completed

1. **Analyzed existing codebase**
   - 42 Python scraper files
   - Convex schema and mutations
   - Phase 1-6 research documentation

2. **Identified current scraping approaches**
   - Platform-specific strategies documented
   - 20 methods analyzed in Phase 2 research
   - Stealth techniques cataloged

3. **Documented data storage**
   - JSON files (products)
   - Convex tables (dispensaries)
   - Schema structures

4. **Assessed UI/delivery layer**
   - **Not implemented** (critical gap)

5. **Identified strengths**
   - Good research foundation
   - Platform diversity
   - Convex integration
   - Stealth awareness

6. **Identified weaknesses**
   - No UI
   - No pipeline orchestration
   - Incomplete inventory tracking
   - No change detection
   - Scalability concerns
   - Storage fragmentation
   - No entity resolution

7. **Scale analysis**
   - Current: 12 stores, 126 products
   - Target: Hundreds of stores, tens of thousands of products
   - Bottlenecks identified

8. **Cost baseline**
   - Current: ~$0/month
   - Estimated at scale: $500-2000/month

---

## Next Steps → Phase 2

Phase 2 will focus on **Scraping Layer Research** to recommend:
- Stealth scraping at scale
- Platform-specific strategies
- Distributed architecture
- Failure handling
- Circuit breakers

**Ready to proceed to Phase 2.** ✅
