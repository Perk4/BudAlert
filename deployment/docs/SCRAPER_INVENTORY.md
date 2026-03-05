# Scraper Inventory & Requirements Analysis

**Generated:** 2026-03-05  
**Purpose:** Docker deployment planning for all BudAlert scrapers

---

## Executive Summary

| Scraper | Platform | Method | Browser Required | Dependencies |
|---------|----------|--------|------------------|--------------|
| **Gotham NYC** | WordPress + Dovetail | HTTP + Browser fallback | Optional (Cloudflare bypass) | axios, cheerio, playwright |
| **Housing Works** | Blaze | HTTP-only | No | axios, cheerio |
| **Conbud LES** | Dutchie GraphQL | API + Browser fallback | Optional (query extraction) | axios, playwright |

---

## 1. Gotham NYC Scraper

### Location
`~/clawd/budalert/scrapers/gotham/`

### Files
- `scraper.mjs` - HTTP-based scraper (primary)
- `scraper-browser.mjs` - Playwright-based scraper (Cloudflare bypass)
- `test.mjs` - Test runner

### Platform Details
- **Target Site:** https://gotham.nyc/menu
- **Technology:** WordPress + Dovetail menu system
- **Challenge:** Cloudflare protection (intermittent)
- **Data Format:** Server-rendered HTML + JSON-LD structured data

### Dependencies
```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "cheerio": "^1.0.0",
    "playwright": "^1.40.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

### Runtime Requirements
- **Node.js:** >=18.0.0
- **Browser Required:** Optional
  - HTTP scraper works when no Cloudflare challenge
  - Browser scraper needed when Cloudflare blocks requests
- **System Dependencies (Browser mode):**
  - Chromium browser
  - System libraries for Playwright (libnss3, libatk-bridge2.0-0, etc.)

### Extraction Strategy
1. **JSON-LD** - Structured product data in `<script type="application/ld+json">`
2. **HTML parsing** - Dovetail/WordPress product elements
3. **WooCommerce** - E-commerce product cards
4. **Multi-strategy** - Falls through strategies for maximum reliability

### Docker Image Recommendation
**Hybrid approach:**
- Base: `Dockerfile.http` for lightweight HTTP scraping
- Extended: `Dockerfile.browser` when Cloudflare protection detected
- **Preferred:** `Dockerfile.browser` (handles both scenarios)

---

## 2. Housing Works Scraper

### Location
`~/clawd/budalert/scrapers/housing-works/`

### Files
- `scraper.mjs` - HTTP-based scraper
- `package.json` - Dependencies manifest

### Platform Details
- **Target Site:** https://hwcannabis.co/menu/broadway/
- **Technology:** Blaze e-commerce platform
- **Challenge:** None (simple HTTP)
- **Data Format:** Server-rendered HTML

### Dependencies
```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "cheerio": "^1.0.0"
  }
}
```

### Runtime Requirements
- **Node.js:** >=18.0.0
- **Browser Required:** No
- **System Dependencies:** None (HTTP-only)

### Extraction Strategy
1. **Product selectors** - Multiple CSS selector strategies for Blaze platform
2. **Category extraction** - Menu navigation analysis
3. **Field fallbacks** - Tries multiple selectors per field
4. **Stock detection** - Checks for out-of-stock indicators

### Docker Image Recommendation
**Lightweight:**
- Base: `Dockerfile.http` (Alpine Node.js)
- Minimal footprint
- Fast startup
- Low resource usage

---

## 3. Conbud LES Scraper

### Location
`~/clawd/budalert/scrapers/conbud/`

### Files
- `api-scraper.mjs` - GraphQL API scraper (primary)
- `browser-scraper.mjs` - Playwright scraper (query extraction)
- `queries.mjs` - GraphQL query templates
- `example.mjs` - Usage examples
- `package.json` - Dependencies manifest

### Platform Details
- **Target Site:** https://conbud.com/stores/conbud-les
- **Technology:** Dutchie GraphQL API
- **Challenge:** Query structure extraction
- **Data Format:** JSON (GraphQL responses)

### Dependencies
```json
{
  "dependencies": {
    "playwright": "^1.40.0",
    "axios": "^1.6.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

### Runtime Requirements
- **Node.js:** >=18.0.0
- **Browser Required:** Optional
  - API scraper (fast, lightweight)
  - Browser scraper for query extraction/updates
- **System Dependencies (Browser mode):**
  - Chromium browser
  - Playwright system libraries

### Extraction Strategy
1. **Direct GraphQL** - Posts to https://api.dutchie.com/graphql
2. **Query templates** - Predefined filteredProducts/menu queries
3. **Browser fallback** - Network traffic interception for query updates
4. **Normalization** - Consistent product schema

### Docker Image Recommendation
**Dual-purpose:**
- Primary: `Dockerfile.http` for API-based scraping
- Secondary: `Dockerfile.browser` for query extraction tasks
- **Deployment:** Use HTTP image for production, browser for maintenance

---

## System Requirements Matrix

### HTTP-Only Scrapers (Lightweight)
**Applies to:** Housing Works, Conbud API mode, Gotham HTTP mode

| Requirement | Specification |
|-------------|---------------|
| **Base Image** | `node:18-alpine` or `node:20-alpine` |
| **Image Size** | ~150-200 MB |
| **RAM** | 128-256 MB |
| **CPU** | 0.1-0.5 cores |
| **Startup Time** | 1-3 seconds |
| **Node Modules** | axios, cheerio |

### Browser-Based Scrapers (Full)
**Applies to:** Gotham browser mode, Conbud browser mode

| Requirement | Specification |
|-------------|---------------|
| **Base Image** | `mcr.microsoft.com/playwright:v1.40.0` |
| **Image Size** | ~1.2-1.5 GB |
| **RAM** | 512 MB - 1 GB |
| **CPU** | 0.5-1.0 cores |
| **Startup Time** | 5-15 seconds |
| **System Packages** | libnss3, libnspr4, libatk1.0-0, libatk-bridge2.0-0, libcups2, libdrm2, libdbus-1-3, libatspi2.0-0, libx11-6, libxcomposite1, libxdamage1, libxext6, libxfixes3, libxrandr2, libgbm1, libxcb1, libxkbcommon0, libpango-1.0-0, libcairo2, libasound2 |

---

## Deployment Architecture Recommendations

### Strategy 1: Separate Images (Recommended)
- **Light scrapers:** Single `Dockerfile.http` base
- **Heavy scrapers:** Single `Dockerfile.browser` base
- **Per-scraper configs:** Individual Dockerfiles extending base

**Pros:**
- Minimal image size for HTTP-only scrapers
- Clear separation of concerns
- Easy to scale independently

**Cons:**
- Need to maintain two base images
- Slightly more complex deployment

### Strategy 2: Universal Image
- Single `Dockerfile.browser` for all scrapers
- HTTP scrapers just don't use browser

**Pros:**
- Single image to maintain
- Works for all scenarios

**Cons:**
- Oversized for HTTP-only scrapers (~1.5 GB vs ~200 MB)
- Slower cold starts
- Higher resource usage

### Strategy 3: Multi-Stage Build
- Build stage with all tools
- Conditional runtime selection based on ENV var

**Pros:**
- Flexible
- Single build pipeline

**Cons:**
- Complex Dockerfile
- Harder to debug

---

## Next Steps (Phase 2)

1. Create `deployment/docker/Dockerfile.http`
   - Based on `node:20-alpine`
   - Install axios, cheerio
   - Health check endpoint
   - Production optimizations

2. Create `deployment/docker/Dockerfile.browser`
   - Based on `mcr.microsoft.com/playwright:v1.40.0-jammy`
   - Install Chromium
   - Optimize for container usage
   - Health check endpoint

3. Test builds locally
4. Validate each scraper works in container
5. Document image sizes and performance

---

## Notes

- **Node Version:** All scrapers compatible with Node.js 18+, recommend Node.js 20 for production
- **Missing package.json:** Gotham scraper has no package.json (create in Phase 3)
- **Module Type:** All scrapers use ES modules (`"type": "module"` in package.json)
- **File Extensions:** All scripts use `.mjs` (ES module JavaScript)
- **Environment Variables:** None currently required (hardcoded configs)

---

**Phase 1 Complete** ✅  
**Ready for:** Base Docker image creation
