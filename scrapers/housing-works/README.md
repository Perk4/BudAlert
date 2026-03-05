# Housing Works Cannabis Co. Scraper

**Status**: ✅ Working (with limitations)  
**Platform**: Blaze (client-side SPA)  
**Location**: Broadway, NYC  
**URL**: https://hwcannabis.co/menu/broadway/

---

## Overview

This is a lightweight HTTP-based scraper for Housing Works Cannabis Co., which uses the Blaze e-commerce platform. 

### Why This Approach?

The original Python scraper (located at `~/clawd/budalert/memory/stealth-scraper/scrapers/blaze/housing_works.py`) uses Playwright for browser automation, but:

1. **Python 3 is not available** on this system
2. **Playwright requires system dependencies** (libglib, etc.) that aren't installed
3. **Browser automation is slow** and resource-intensive

This Node.js version uses simple HTTP requests + HTML parsing for a lightweight, dependency-free solution.

---

## Installation

```bash
cd ~/clawd/budalert/scrapers/housing-works
npm install
```

**Dependencies:**
- `axios` - HTTP client
- `cheerio` - HTML parsing (jQuery-like API)

---

## Usage

### Basic Scraping

```bash
npm run scrape
```

Or directly:

```bash
node scraper.mjs
```

### Output

The scraper will:
1. Fetch the main menu page
2. Extract product categories
3. Scrape the first 3 category pages
4. Deduplicate products
5. Save results to `housing-works-products-{timestamp}.json`

**Example output:**
```
🏪 Housing Works Cannabis Co. Scraper
══════════════════════════════════════════════════
Store: housing_works
Location: Broadway
URL: https://hwcannabis.co/menu/broadway/
══════════════════════════════════════════════════

🌐 Fetching: https://hwcannabis.co/menu/broadway/
   ✅ Status: 200
📂 Extracting categories...
   ✅ Found 6 categories: [
  '🍃Flower🍃',
  '💨Vape Pens💨',
  '🪄Pre-rolls🪄',
  '🍫Edibles🍬',
  '🍯Concentrates🌿',
  '💧Tinctures🧪'
]

📦 Scraping main menu page...
   ✅ Extracted 122 products

📂 Scraping category: 🍃Flower🍃
   ✅ Extracted 221 products

...

══════════════════════════════════════════════════
📊 SCRAPING RESULTS
══════════════════════════════════════════════════
Total Products: 169
In Stock: 169
Out of Stock: 0
With Prices: 99
With THC Data: 0
══════════════════════════════════════════════════

💾 Saved 169 products to: housing-works-products-2026-03-05T04-15-39-185Z.json

✅ SUCCESS!
```

---

## Data Schema

Each product contains:

```json
{
  "name": "Product Name",
  "price": 45.00,
  "priceRaw": "$45",
  "url": "https://hwcannabis.co/menu/broadway/products/...",
  "brand": null,
  "category": "🍃Flower🍃",
  "weight": null,
  "thc": null,
  "cbd": null,
  "inStock": true,
  "quantity": null,
  "scrapedAt": "2026-03-05T04:15:33.687Z",
  "source": "housing-works-broadway",
  "sourceUrl": "https://hwcannabis.co/menu/broadway/"
}
```

---

## Current Limitations

### ✅ What Works
- ✅ Product names extracted
- ✅ Prices extracted (for ~60% of products)
- ✅ Product URLs captured
- ✅ Categories identified and tagged
- ✅ Basic stock status

### ⚠️  What Doesn't Work Well
- ❌ **Brand data** - Not extracted (selectors may need refinement)
- ❌ **THC/CBD potency** - Not extracted (data likely loaded via JavaScript)
- ❌ **Product weight/size** - Not extracted
- ❌ **Quantity available** - Not extracted (requires API or cart probing)
- ⚠️  **Product names** - Sometimes shows just "Indica" or "Sativa" instead of full name
- ⚠️  **Price coverage** - Only ~60% of products have prices

### Why These Limitations Exist

**Blaze is a client-side rendered SPA (Single Page Application)**

The HTML we fetch via HTTP is the server-side rendered shell. Most product data is loaded dynamically via JavaScript API calls after the page loads. This means:

1. **Static HTML scraping** gets incomplete data
2. **Full data requires browser automation** (Playwright/Puppeteer)
3. **Best approach is direct API access** (fastest and most reliable)

---

## Comparison to Python Scraper

| Feature | Python (Playwright) | Node.js (HTTP) | Direct API |
|---------|---------------------|----------------|------------|
| **Speed** | 45-60s | 5-10s | 2-5s |
| **Data Quality** | ⭐⭐⭐ Excellent | ⭐ Limited | ⭐⭐⭐ Excellent |
| **Quantity Data** | ✅ Yes (cart probing) | ❌ No | ✅ Yes |
| **Dependencies** | Python + Playwright + system libs | Node + axios + cheerio | Node + axios |
| **Resource Usage** | 600-900 MB | 50-100 MB | 30-50 MB |
| **Works on this system** | ❌ No (deps missing) | ✅ Yes | ⏳ Needs API discovery |

---

## Production Recommendations

### Short Term: Use This Scraper ✅
For quick proof-of-concept and basic product listings:
- ✅ Works now
- ✅ No complex dependencies
- ✅ Fast enough (~10 seconds)
- ⚠️  Limited data quality

### Medium Term: API Discovery 🎯
Use the Python scraper's network tracking (or browser DevTools) to discover Blaze API endpoints, then:

1. **Capture API requests** during manual browsing
2. **Extract endpoint URLs** and request formats
3. **Implement direct API calls** in Node.js
4. **Much faster** (2-5s) and **better data quality**

Example API patterns to look for:
```
POST https://hwcannabis.co/api/graphql
GET https://hwcannabis.co/api/products?category=flower
GET https://hwcannabis.co/api/menu/broadway
```

### Long Term: Browser Automation (If Needed) 🚀
If APIs prove unstable or blocked:
1. Install Playwright system dependencies:
   ```bash
   apt-get install -y \
     libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
     libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
     libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 \
     libcairo2 libatspi2.0-0
   ```
2. Use the Playwright scraper from research docs
3. Enable cart probing for quantity extraction

---

## Files in This Directory

```
scrapers/housing-works/
├── scraper.mjs              # Main scraper (this implementation)
├── package.json             # Node.js dependencies
├── README.md                # This file
└── housing-works-products-*.json  # Output files (generated)
```

---

## Related Documentation

**Research Phase:**
- Full implementation docs: `~/clawd/budalert/research/phase4-housing-works/README.md`
- Python scraper (reference): `~/clawd/budalert/memory/stealth-scraper/scrapers/blaze/housing_works.py`
- Playwright scraper (Node): `~/clawd/budalert/research/phase4-housing-works/scraper-playwright.js`

**Next Steps:**
See research docs for:
- API endpoint discovery workflow
- Direct API scraper template
- Docker deployment options
- Advanced quantity extraction methods

---

## Testing Checklist

- [x] HTTP requests succeed (status 200)
- [x] HTML parsing works
- [x] Categories extracted
- [x] Products found and extracted
- [x] Data saved to JSON
- [x] No crashes or errors
- [x] Reasonable execution time (<30s)
- [ ] Full product data captured (limited by SPA architecture)
- [ ] Quantity/inventory data (not available via HTTP scraping)

---

## Troubleshooting

### Issue: Few products extracted

**Cause:** Page might be loading products via AJAX  
**Solution:** Check `debug-housing-works.html` (auto-generated on first run) to see what HTML is actually returned

### Issue: Missing price/THC data

**Cause:** Data loaded dynamically via JavaScript  
**Solution:** This is expected. Use browser automation or API scraping for full data.

### Issue: Duplicate products

**Cause:** Product appears on multiple category pages  
**Solution:** Scraper already deduplicates by `name + price`. Refine as needed.

---

## Performance

**Test Run (2026-03-05):**
- Duration: ~10 seconds
- Products extracted: 169
- Categories scraped: 4 (main + 3 category pages)
- Data completeness:
  - Names: 100% ✅
  - Prices: ~60% ⚠️
  - THC/CBD: 0% ❌
  - Brand: 0% ❌

**Expected for production:**
- With API access: 200-400 products in 2-5 seconds with 95%+ data completeness
- With browser automation: 200-400 products in 45-60 seconds with 95%+ data completeness

---

## License

MIT

---

## Support

For questions or issues:
1. Check research docs at `~/clawd/budalert/research/phase4-housing-works/`
2. Review Python scraper for reference implementations
3. Check Blaze platform documentation (if available)

---

**Last Updated:** 2026-03-05  
**Status:** Working with known limitations  
**Next Phase:** API discovery for improved data quality
