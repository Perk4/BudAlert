# Phase 1: Reconnaissance Findings

## 1. Conbud LES (Lower East Side)

### URLs
- **Main site**: https://conbud.com/
- **LES Store page**: https://conbud.com/stores/conbud-les
- **Direct menu**: https://shop.conbud.com/conbud/ (chain-level)
- **Address**: 85 Delancey St, New York, NY 10002

### Platform: Dutchie (Embedded React SPA)
- **Framework**: Next.js / React
- **Type**: Dutchie embedded store (NOT iframe)
- **API Base**: https://api.dutchie.com
- **Retailer ID**: 7d9a369e-6b29-4ccb-84c8-e802e28ae23e
- **Dispensary ID**: 6430f42042cf3c004e37f0f8
- **Chain ID**: conbud
- **Chain CNames**: conbud-les, conbud-bronx, conbud-gerard-avenue

### Technical Details
- **Rendering**: Client-side React app, heavily JavaScript-dependent
- **Data Loading**: Uses Dutchie API with GraphQL endpoints
- **Authentication**: Turnstile CAPTCHA protection (0x4AAAAAAA1_LIO4cx5r-Yf4)
- **Analytics**: Google Analytics, Amplitude, LogRocket, LaunchDarkly
- **Assets**: Hosted on assets2.dutchie.com

### API Endpoints Observed
```javascript
window.reactEnv = {
  "apiUrl": "https://api.dutchie.com",
  "adminUrl": "https://admin.dutchie.com",
  "consumerUrl": "https://dutchie.com",
  "dispensaryId": "6430f42042cf3c004e37f0f8",
  "chainId": "conbud",
  "retailerId": "7d9a369e-6b29-4ccb-84c8-e802e28ae23e"
}
```

### Scraping Challenges
1. **JavaScript-heavy**: Requires browser automation or API interception
2. **Client-side rendering**: HTML source is empty `<div id="__next"></div>`
3. **CAPTCHA protection**: Turnstile might trigger on automated access
4. **Rate limiting**: Likely has API rate limits
5. **Dynamic content**: Products loaded via GraphQL queries

### Scraping Approaches to Test
1. ✅ **Headless browser** (Playwright/Puppeteer) - Most reliable
2. ✅ **API interception** - Monitor network calls to Dutchie API
3. ✅ **GraphQL query replication** - If we can extract query structure
4. ❌ **Direct HTML parsing** - Won't work, no products in static HTML
5. ⚠️ **Dutchie API direct access** - May require auth tokens

---

## 2. Housing Works SoHo

### URLs
- **Main site**: https://hwcannabis.co
- **Broadway menu**: https://hwcannabis.co/menu/broadway/
- **SoHo location**: Needs verification (may be same as Broadway)

### Platform: Blaze
- **Existing scraper**: ✅ `memory/stealth-scraper/scrapers/blaze/housing_works.py`
- **Status**: Already implemented with Playwright
- **Quantity extraction**: Includes quantity parser and cart prober

### Scraping Status
- **Implementation**: Already exists
- **Task**: Test existing scraper, verify data completeness, check for improvements

---

## 3. Gotham NYC

### URLs
- **Main site**: https://gotham.nyc
- **Menu**: https://gotham.nyc/menu

### Platform: WordPress + Dovetail ecommerce
- **Existing scraper**: ✅ `memory/stealth-scraper/scrapers/custom-medium/gotham.py`
- **Framework**: WordPress with Dovetail plugin
- **Status**: Already implemented with curl-based approach

### Technical Details
- **Rendering**: Server-side WordPress
- **Potential age gate**: May require verification bypass
- **Data format**: HTML product listings + JSON-LD structured data

### Scraping Status
- **Implementation**: Already exists
- **Task**: Test existing scraper, verify data completeness, check for improvements

---

## Summary

| Dispensary | Platform | URL | Existing Scraper | Priority |
|------------|----------|-----|------------------|----------|
| Conbud LES | Dutchie (React SPA) | conbud.com/stores/conbud-les | ❌ No | **High** - New implementation needed |
| Housing Works | Blaze | hwcannabis.co/menu/broadway/ | ✅ Yes | Medium - Test & improve |
| Gotham NYC | WordPress/Dovetail | gotham.nyc/menu | ✅ Yes | Medium - Test & improve |

## Next Steps (Phase 2)
1. Test existing Housing Works scraper
2. Test existing Gotham scraper
3. Design Conbud LES scraper architecture
4. Identify API endpoints for Dutchie platform
5. Plan multiple scraping methods for each
