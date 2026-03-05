# BudAlert Codebase Map

**Generated:** 2026-03-05  
**Purpose:** Comprehensive mapping of codebase structure, data flows, and relationships for test coverage planning

---

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Dependencies & Technologies](#dependencies--technologies)
6. [Critical Paths](#critical-paths)
7. [Integration Points](#integration-points)

---

## Overview

BudAlert is a cannabis dispensary product scraping and alerting system built on:
- **Scrapers**: Extract product data from dispensary websites (Gotham, Housing Works, Conbud)
- **Convex Backend**: Serverless database and functions for data storage
- **Data Pipeline**: Transform scraped data → normalized products → inventory tracking → alerts

---

## Directory Structure

```
budalert/
├── scrapers/                    # Production scrapers (3 dispensaries)
│   ├── gotham/                  # Gotham NYC scraper
│   │   ├── scraper.mjs          # Main scraper (WordPress + Dovetail)
│   │   ├── scraper-browser.mjs  # Browser-based fallback
│   │   └── test.mjs             # Test script with validation
│   ├── housing-works/           # Housing Works scraper
│   │   ├── scraper.mjs          # Blaze platform scraper
│   │   └── package.json         # Dependencies (axios, cheerio)
│   └── conbud/                  # Conbud LES scraper
│       ├── api-scraper.mjs      # Direct GraphQL API approach
│       ├── browser-scraper.mjs  # Browser-based approach
│       ├── queries.mjs          # GraphQL query definitions
│       └── example.mjs          # Usage examples
│
├── convex/                      # Convex backend (database + functions)
│   ├── schema.ts                # Full database schema (20+ tables)
│   ├── nysDispensaries.ts       # NYS dispensary CRUD operations
│   ├── loadDispensaries.ts      # Bulk import logic
│   └── _generated/              # Auto-generated Convex types
│
├── scripts/                     # Utility scripts
│   └── import-nys-dispensaries.js  # CSV import for NYS data
│
├── research/                    # Research & prototypes (6 phases)
│   ├── phase1-recon/            # Initial reconnaissance
│   ├── phase2-planning/         # Planning docs
│   ├── phase3-conbud/           # Conbud research
│   ├── phase4-housing-works/    # Housing Works research
│   ├── phase5-gotham/           # Gotham research
│   └── phase6-scorecard/        # Evaluation metrics
│
├── architecture-redesign/       # Architecture documentation
│   ├── 00_EXECUTIVE_SUMMARY.md
│   ├── PHASE1_CURRENT_STATE_ANALYSIS.md
│   ├── PHASE2_SCRAPING_LAYER_RESEARCH.md
│   └── ... (7 phases total)
│
├── velocity-research/           # SKU velocity & entity resolution
│   ├── PHASE1_CURRENT_STATE.md
│   ├── PHASE2_VELOCITY_SIGNALS.md
│   ├── PHASE3_ENTITY_RESOLUTION.md
│   └── ... (6 phases + implementation plan)
│
├── deployment/                  # Deployment artifacts (new)
├── memory/                      # Stealth scraper history
└── skills/                      # OpenClaw skills

```

---

## Core Components

### 1. Scrapers (`/scrapers`)

#### Gotham NYC Scraper (`scrapers/gotham/scraper.mjs`)

**Type:** HTTP-based (no browser)  
**Platform:** WordPress + Dovetail  
**Strategy:** Multi-level extraction

**Key Methods:**
- `fetchPage(url)` - HTTP GET with age verification cookies
- `extractProducts(html, url)` - Orchestrates 3 extraction strategies:
  1. **JSON-LD** structured data (Schema.org Product)
  2. **HTML parsing** (Dovetail/WordPress classes)
  3. **WooCommerce** patterns
- `normalizeJsonLdProduct(data)` - Converts JSON-LD to standard format
- `extractHtmlProducts($)` - Parses DOM elements
- `extractWooCommerceProducts($)` - WooCommerce-specific extraction
- `checkAgeGate(html)` - Detects age verification requirements
- `scrape()` - Main workflow

**Data Extracted:**
```javascript
{
  id, name, brand, category,
  price, priceFormatted,
  image, images[],
  description, url,
  inStock,
  thc: { formatted, value },
  cbd: { formatted, value },
  scrapedAt, source, sourceUrl
}
```

**Dependencies:**
- `axios` - HTTP client
- `cheerio` - HTML parsing (jQuery-like)

---

#### Housing Works Scraper (`scrapers/housing-works/scraper.mjs`)

**Type:** HTTP-based  
**Platform:** Blaze e-commerce  
**Strategy:** Multi-selector HTML parsing

**Key Methods:**
- `fetchPage(url)` - HTTP GET with browser headers
- `parseProducts(html)` - Try multiple selector strategies
- `extractProductData($, element)` - Extract from single product element
- `trySelectors($, $elem, selectors)` - Fallback selector matching
- `extractCategories($)` - Find category navigation
- `checkInStock($, $elem)` - Stock status detection
- `scrape()` - Main workflow with category crawling

**Features:**
- **Adaptive selectors**: Falls back through multiple CSS selector strategies
- **Category crawling**: Discovers and scrapes category pages
- **Debug mode**: Saves HTML to file if parsing fails
- **Rate limiting**: 2s delay between category requests

**Dependencies:**
- `axios`
- `cheerio`

---

#### Conbud Scraper (`scrapers/conbud/api-scraper.mjs`)

**Type:** GraphQL API client  
**Platform:** Dutchie (headless e-commerce)  
**Strategy:** Direct API queries

**Key Methods:**
- `query(query, variables, retryCount)` - GraphQL with retry logic
- `fetchAllProducts()` - Bulk product query
- `fetchByCategory(category)` - Category-filtered queries
- `processProducts(rawProducts)` - Normalize + deduplicate

**Features:**
- **Retry logic**: 3 attempts with exponential backoff
- **Fallback queries**: Multiple query structures
- **Category filtering**: Can scrape by cannabis category
- **Deduplication**: By product ID

**Query Module (`queries.mjs`):**
- `FILTERED_PRODUCTS_QUERY` - Main GraphQL query
- `MENU_PRODUCTS_QUERY` - Alternative structure
- `buildFilters()` - Dynamic filter construction
- `normalizeProduct()` - API → standard format
- `COMMON_CATEGORIES` - Predefined category list

**Dependencies:**
- `axios` (GraphQL client)

---

### 2. Convex Backend (`/convex`)

#### Schema (`convex/schema.ts`)

**20+ Tables** organized into groups:

**Core Data:**
- `nysDispensaries` - NYS licensed dispensaries (strict schema)
- `retailers` - Dispensary/store records (flexible)
- `products` - Product catalog (flexible)
- `brands` - Brand directory (flexible)

**Inventory Tracking:**
- `currentInventory` - Latest stock levels
- `menuSnapshots` - Historical menu captures
- `inventoryDeltas` - Stock change events
- `inventoryEvents` - Product lifecycle events

**Scraping Infrastructure:**
- `scrapeBatches` - Batch job tracking
- `scrapeBatchChunks` - Chunk processing
- `scrapeJobs` - Individual scraper runs
- `scraperAlerts` - Error/warning notifications
- `deadLetterQueue` - Failed scrape recovery

**User & Subscriptions:**
- `users` - User accounts
- `subscriptions` - Payment/tier management
- `watchlists` - User product watches
- `productWatches` - Individual product alerts
- `alerts` - User notifications

**B2B Features:**
- `retailerAccounts` - Business accounts
- `b2bAlerts` - Business notifications
- `b2bPriceCache` - Competitor pricing
- `competitorMonitors` - Price tracking

**Analytics:**
- `brandAnalytics` - Brand performance
- `statsCache` - Cached statistics

**Payments:**
- `paymentEvents` - Stripe webhooks

**Key Indexes:**
- Most tables indexed by `retailerId`, `productId`, `brandId`
- Time-series indexes: `scrapedAt`, `timestamp`, `createdAt`
- Composite indexes for common queries

---

#### NYS Dispensaries Module (`convex/nysDispensaries.ts`)

**Mutations:**
- `upsert(dispensary)` - Insert or update by `entity_name`
- `batchUpsert(dispensaries[])` - Bulk import with error handling

**Queries:**
- `list()` - Get all dispensaries
- `getByCity(city)` - City filter
- `getByZip(zip_code)` - ZIP filter
- `count()` - Total count
- `getStats()` - Summary statistics (microbusiness, delivery-only, top cities)

---

#### Load Dispensaries (`convex/loadDispensaries.ts`)

**Purpose:** Import script for NYS dispensary CSV data

---

### 3. Scripts (`/scripts`)

#### `import-nys-dispensaries.js`

**Purpose:** Parse NYS CSV data and bulk upload to Convex  
**Usage:** Node script for one-time or periodic imports

---

## Data Flow

### Primary Flow: Scrape → Store → Notify

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SCRAPING LAYER                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Gotham     │  │ Housing Works│  │   Conbud     │    │
│  │  Scraper     │  │   Scraper    │  │  Scraper     │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                  │             │
│         └─────────────────┴──────────────────┘             │
│                           │                                │
│                  Raw Product Data                          │
│              {name, price, thc, url...}                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. TRANSFORMATION LAYER (Future)                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  • Normalize product formats                               │
│  • Entity resolution (match products across stores)        │
│  • Brand extraction/matching                               │
│  • Category classification                                 │
│  • Data validation & enrichment                            │
│                                                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. STORAGE LAYER (Convex)                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐      ┌──────────────┐                    │
│  │  products   │──┬───│ currentInv   │                    │
│  └─────────────┘  │   └──────────────┘                    │
│                   │                                        │
│  ┌─────────────┐  │   ┌──────────────┐                    │
│  │   brands    │──┘   │menuSnapshots │                    │
│  └─────────────┘      └──────────────┘                    │
│                                                             │
│  ┌─────────────┐      ┌──────────────┐                    │
│  │  retailers  │      │invDeltas     │                    │
│  └─────────────┘      └──────────────┘                    │
│                                                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. ANALYSIS LAYER                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  • Inventory change detection                              │
│  • Velocity calculation (SKU sales rate)                   │
│  • Price change tracking                                   │
│  • Stock alerts (in/out)                                   │
│  • Brand analytics                                         │
│                                                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. DELIVERY LAYER                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Webhooks   │  │    Email     │  │    Push      │    │
│  │  (Discord,   │  │ (Subscribed  │  │ (Mobile App) │    │
│  │   Slack)     │  │   Users)     │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Current Implementation Status

✅ **Complete:**
- Scraping Layer (3 scrapers operational)
- Storage Layer (Convex schema defined)
- Basic data insertion

⚠️ **Partial:**
- Transformation Layer (some normalization in scrapers)
- Analysis Layer (schema exists, logic incomplete)

❌ **Not Implemented:**
- Delivery Layer (notification infrastructure)
- Entity resolution
- Velocity calculation
- User subscriptions

---

## Dependencies & Technologies

### Core Stack

**Backend:**
- **Convex** - Serverless backend (DB + functions + real-time)
- **Node.js v22+** - Runtime
- **TypeScript** - Convex functions

**Scraping:**
- **axios** - HTTP client
- **cheerio** - HTML parsing (jQuery API for Node)
- **GraphQL** - API queries (Conbud/Dutchie)

**Utilities:**
- **fs/promises** - File I/O

### Package Dependencies

```json
{
  "dependencies": {
    "axios": "^1.13.6",
    "cheerio": "^1.2.0",
    "convex": "^1.32.0"
  }
}
```

### Sub-project Dependencies

**Housing Works** (`scrapers/housing-works/package.json`):
- `axios`
- `cheerio`

**Conbud** (`scrapers/conbud/package.json`):
- `axios`

---

## Critical Paths

### 1. **Scraper Execution → Data Extraction**

**Flow:**
```
fetchPage() → parseHTML/queryAPI() → extractData() → normalize() → return products[]
```

**Failure Points:**
- Network errors (timeout, DNS, SSL)
- HTTP errors (404, 403, 503)
- HTML structure changes (selector mismatch)
- Age gates / CAPTCHA challenges
- API changes (GraphQL schema drift)

**Currently Handled:**
- Retries with backoff (Conbud)
- Multiple selector strategies (all scrapers)
- Age verification cookies (Gotham)

**Not Handled:**
- CAPTCHA solving
- Dynamic content (JavaScript rendering)
- Rate limiting / IP bans

---

### 2. **Data Transformation → Storage**

**Flow:**
```
Raw Data → Validate → Normalize → Match Entities → Store
```

**Failure Points:**
- Missing required fields
- Data type mismatches
- Duplicate detection failures
- Entity resolution errors
- Database connection issues

**Currently Handled:**
- Basic normalization in scrapers
- Convex schema validation

**Not Handled:**
- Cross-store product matching
- Brand resolution
- Price history tracking

---

### 3. **Inventory Change Detection → Alerting**

**Flow:**
```
New Snapshot → Compare with Previous → Detect Changes → Generate Events → Send Notifications
```

**Status:** Schema exists, logic not implemented

---

## Integration Points

### External Services

1. **Dispensary Websites**
   - Gotham NYC: `https://gotham.nyc`
   - Housing Works: `https://hwcannabis.co`
   - Conbud LES: `https://conbud.com` (Dutchie API)

2. **Convex Cloud**
   - Backend deployment
   - Database hosting
   - Function runtime

3. **Future Integrations** (not yet implemented):
   - Stripe (payments)
   - SendGrid/Mailgun (email)
   - Twilio (SMS)
   - Discord/Slack webhooks
   - Push notification services

### Internal Interfaces

**Scraper → Convex:**
- Manual execution (CLI)
- Future: Scheduled runs (cron/Convex actions)
- Data format: Normalized JSON

**Convex → Frontend:**
- Real-time queries
- Subscriptions
- Mutations

---

## Testing Considerations

### Current Test Coverage

**Existing Tests:**
1. `scrapers/gotham/test.mjs` - Integration test with validation
2. `research/phase4-housing-works/test-quick.js` - Research test
3. `memory/stealth-scraper/scrapers/monitoring/test_runner.js` - Monitoring test

**Coverage:** ~5% (ad-hoc manual testing only)

### Critical Test Needs

**High Priority:**
1. Scraper data extraction accuracy
2. Data normalization consistency
3. Convex mutation logic
4. Error handling & recovery

**Medium Priority:**
5. Multi-scraper orchestration
6. Duplicate detection
7. Schema validation

**Low Priority:**
8. Analytics calculations
9. Alert generation
10. Notification delivery

---

## File Statistics

**Total Files by Type:**
- `.mjs` scrapers: 9
- `.ts` Convex: 3
- `.md` docs: 50+
- `.json` config/data: 15+

**Lines of Code (estimated):**
- Scrapers: ~1,500 LOC
- Convex: ~300 LOC
- Research/prototypes: ~2,000 LOC

**Test Code:** <200 LOC (needs expansion)

---

## Next Steps for Testing

See `TEST_GAP_ANALYSIS.md` for:
1. Detailed gap analysis
2. Prioritized test plan
3. Risk assessment
4. Implementation roadmap

---

**Document Version:** 1.0  
**Last Updated:** 2026-03-05  
**Maintainer:** BudAlert Testing Team
