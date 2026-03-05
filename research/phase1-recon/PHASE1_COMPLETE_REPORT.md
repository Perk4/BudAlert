# Phase 1: Reconnaissance - Complete Report

**Date**: 2026-03-05
**Status**: ✅ COMPLETE

---

## Executive Summary

Reconnaissance completed for three NYC dispensaries. Two have existing Python-based scrapers; one (Conbud) requires new implementation.

| Dispensary | Platform | Existing Scraper | Complexity | Priority |
|------------|----------|------------------|------------|----------|
| **Conbud LES** | Dutchie (React SPA) | ❌ No | **High** | **P1** - New implementation needed |
| **Housing Works SoHo** | Blaze | ✅ Yes (Python) | Medium | P2 - Test & validate |
| **Gotham NYC** | WordPress/Dovetail | ✅ Yes (Python) | Low-Medium | P2 - Test & validate |

---

## 1. Conbud LES (Lower East Side)

### URLs
- **Store Page**: https://conbud.com/stores/conbud-les
- **Address**: 85 Delancey St, New York, NY 10002
- **Chain URLs**: https://shop.conbud.com/conbud/

### Platform Details
- **Type**: Dutchie Embedded (React SPA)
- **Framework**: Next.js
- **API**: https://api.dutchie.com (GraphQL)
- **Dispensary ID**: `6430f42042cf3c004e37f0f8`
- **Chain ID**: `conbud`
- **Retailer ID**: `7d9a369e-6b29-4ccb-84c8-e802e28ae23e`

### Technical Characteristics
- ✅ **JavaScript-heavy**: All content client-side rendered
- ✅ **GraphQL API**: Structured API with formal schema
- ⚠️  **CAPTCHA**: Turnstile protection present
- ✅ **React SPA**: Single page application with dynamic routing
- ❌ **No static HTML**: Empty `<div id="__next"></div>` in source

### Scraping Strategy
**Primary**: Browser automation with network interception
**Fallback**: Direct GraphQL API (if queries can be replicated)
**DO NOT**: Simple HTML parsing (will fail)

### Expected Data Fields
- Product ID, Name, Brand, Category
- Price (with variant support)
- THC %, CBD % (in potency objects)
- Image URL
- Inventory status (requires deeper inspection)

### Implementation Status
- ❌ No existing scraper
- 📝 Technical analysis complete
- 🔍 API structure documented (estimated)
- ⚠️  Browser environment issues (missing dependencies)
- 📋 Next: Implement browser-based network interception

---

## 2. Housing Works SoHo/Broadway

### URLs
- **Main Site**: https://hwcannabis.co
- **Menu**: https://hwcannabis.co/menu/broadway/
- **Locations**: Broadway, SoHo (confirm same platform)

### Platform Details
- **Type**: Blaze
- **Existing Scraper**: ✅ `memory/stealth-scraper/scrapers/blaze/housing_works.py`
- **Implementation**: Playwright-based (Python)
- **Features**: 
  - Product extraction
  - Quantity parser
  - Cart prober for inventory
  - Category navigation
  - Pagination/infinite scroll handling

### Scraper Features (from code review)
```python
class HousingWorksScraper:
    - Playwright browser automation
    - Stealth mode (user agent rotation, resource blocking)
    - Network request tracking
    - Quantity extraction (multiple methods)
    - Cart probing for stock levels
    - Category-based scraping
    - Pagination support
```

### Extractable Fields
- ✅ Product ID, Name, Price
- ✅ Product URL, Category
- ✅ Store name, scrape timestamp
- ⚠️  Quantity info (via quantity_parser)
- ⚠️  In-stock status (multiple detection methods)
- ⚠️  Max quantity (if available)

### Implementation Status
- ✅ Full scraper exists
- 📝 Well-documented code
- 🔄 Includes quantity detection tools
- ⏳ **Needs testing**: Python not available in current environment
- 📋 Next: Test in proper Python environment or port to Node.js

---

## 3. Gotham NYC

### URLs
- **Main Site**: https://gotham.nyc
- **Menu**: https://gotham.nyc/menu

### Platform Details
- **Type**: WordPress + Dovetail ecommerce plugin
- **Existing Scraper**: ✅ `memory/stealth-scraper/scrapers/custom-medium/gotham.py`
- **Implementation**: curl-based (Python)
- **Complexity**: Low-Medium

### Technical Characteristics
- ✅ **Server-rendered**: HTML content in source
- ✅ **WordPress**: Standard CMS with plugin
- ⚠️  **Age gate**: Potential age verification required
- ✅ **JSON-LD**: Structured data in page source
- ✅ **HTML product elements**: Multiple parsing fallbacks

### Scraper Features (from code review)
```python
class GothamScraper:
    - curl-based HTTP requests
    - HTML regex parsing for products
    - JSON-LD structured data extraction
    - Multiple product element patterns
    - Age gate detection/bypass attempts
    - Dovetail-specific class selectors (dt-*)
```

### Extractable Fields
- ✅ Product name, Price
- ✅ Category, Brand
- ✅ THC %, CBD %
- ✅ Image URL
- ✅ Stock status (from HTML or JSON-LD)
- ⚠️  URL (product detail pages)

### Implementation Status
- ✅ Scraper exists
- ⚠️  Age gate handling (may need improvement)
- ⏳ **Needs testing**: Python not available
- 📋 Next: Test and verify data completeness

---

## Environment Constraints

### Current Environment
- ✅ Node.js v22.13.1
- ✅ npm 10.9.2
- ✅ Playwright installed
- ❌ Python 3 not available
- ❌ Chromium missing system dependencies (libglib-2.0.so.0)
- ⚠️  Limited browser automation capability

### Implications
1. **Cannot test Python scrapers** directly
2. **Cannot run Playwright in current container** (missing deps)
3. **Alternative approaches needed**:
   - Port scrapers to Node.js
   - Use curl-based approaches where possible
   - Test in different environment with Python/browser support

---

## Reconnaissance Findings Summary

### Platform Distribution
- **Dutchie (React SPA)**: 1 dispensary - Complex, requires browser automation
- **Blaze**: 1 dispensary - Medium complexity, existing solution
- **WordPress/Dovetail**: 1 dispensary - Low complexity, existing solution

### Scraping Method Requirements

#### Conbud LES (Dutchie)
1. ✅ Browser automation (required)
2. ✅ Network interception (required)
3. ⚠️  Direct API (optional, for speed)
4. ❌ HTML parsing (won't work)

#### Housing Works (Blaze)
1. ✅ Browser automation (required)
2. ⚠️  Quantity extraction (specialized techniques)
3. ⚠️  Cart probing (for inventory)
4. ❌ HTML parsing alone (insufficient)

#### Gotham (WordPress)
1. ✅ HTML parsing (works)
2. ✅ JSON-LD extraction (works)
3. ⚠️  Age gate handling (may be needed)
4. ⚠️  Browser automation (optional, for reliability)

---

## Key Technical Discoveries

### 1. Dutchie Platform Architecture
- GraphQL-based API at api.dutchie.com
- Structured data with formal schema
- IDs: dispensaryId, chainId, retailerId, enterpriseId
- Turnstile CAPTCHA protection
- Next.js SSG/SSR framework
- Client-side data hydration

### 2. Blaze Platform
- Product-based selectors
- Quantity detection challenges
- Multiple data extraction methods needed
- Infinite scroll/pagination support
- API endpoint tracking via network monitoring

### 3. WordPress/Dovetail
- Server-side rendering (easier scraping)
- JSON-LD structured data (bonus)
- HTML fallback patterns
- Age gate complications
- Dovetail-specific CSS classes (dt-*)

---

## Data Extraction Target Fields

### Common Fields (All Dispensaries)
- ✅ Product ID
- ✅ Product Name
- ✅ Brand Name
- ✅ Category
- ✅ Price
- ✅ THC %
- ✅ CBD %
- ✅ Image URL

### Platform-Specific Fields
- **Dutchie**: Variants, subcategory, strainType
- **Blaze**: Quantity available, max quantity, stock signals
- **WordPress**: Stock status (from JSON-LD)

### Challenging Fields (All Platforms)
- ⚠️  **Inventory count**: Requires cart probing or API inspection
- ⚠️  **Real-time stock**: May require frequent polling
- ⚠️  **Price variations**: Different weights/quantities
- ⚠️  **Product variants**: Color/size/potency options

---

## Recommendations for Phase 2

### Priority 1: Conbud LES
- **Action**: Implement browser-based network interception scraper
- **Environment**: Need proper Node.js + Playwright environment
- **Alternative**: Use OpenClaw browser tool or external server
- **Goal**: Extract GraphQL queries and product data structure

### Priority 2: Housing Works & Gotham
- **Action**: Test existing Python scrapers in proper environment
- **Alternative**: Port to Node.js for consistency
- **Goal**: Validate data completeness and reliability

### General Recommendations
1. **Environment**: Set up Python 3 + Playwright OR continue with Node.js
2. **Testing**: Use actual HTTP requests to validate approaches
3. **Comparison**: Create side-by-side tests for different methods
4. **Documentation**: Record actual API responses and HTML structures

---

## Phase 1 Deliverables

✅ **Completed**:
1. Identified all three dispensary URLs
2. Determined platform types (Dutchie, Blaze, WordPress)
3. Analyzed technical architectures
4. Reviewed existing scraper code
5. Documented API endpoints and IDs
6. Identified scraping challenges
7. Ranked scraping approaches by feasibility

📋 **Documentation Created**:
- `FINDINGS.md` - Overview and URLs
- `CONBUD_TECHNICAL_ANALYSIS.md` - Detailed Dutchie analysis
- `PHASE1_COMPLETE_REPORT.md` - This comprehensive report

---

## Next Phase: Method Planning

Phase 2 will focus on:
1. Designing multiple scraping approaches for each dispensary
2. Creating implementation plans
3. Identifying "hacky" techniques
4. Planning fallback strategies
5. Estimating effort and reliability

**Status**: Ready to proceed to Phase 2 ✅
