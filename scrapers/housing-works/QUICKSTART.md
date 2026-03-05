# Housing Works Scraper - Quick Start

Get scraping in 30 seconds! 🚀

---

## One-Time Setup

```bash
cd ~/clawd/budalert/scrapers/housing-works
npm install
```

**That's it!** No Python, no system libraries, no browser required.

---

## Run the Scraper

```bash
npm run scrape
```

Or:

```bash
node scraper.mjs
```

---

## What You'll Get

**Output file:** `housing-works-products-{timestamp}.json`

**Contains:**
- 150-200+ products
- Product names
- Prices (for ~60% of products)
- Product URLs
- Categories
- Stock status

**Takes:** ~10 seconds

---

## View Results

```bash
# Count products
cat housing-works-products-*.json | jq '.totalProducts'

# See first product
cat housing-works-products-*.json | jq '.products[0]'

# List all product names
cat housing-works-products-*.json | jq '.products[].name'

# Filter by category
cat housing-works-products-*.json | jq '.products[] | select(.category == "🍃Flower🍃")'

# Products with prices
cat housing-works-products-*.json | jq '.products[] | select(.price != null) | {name, price}'
```

---

## What's Missing?

This scraper is **POC-ready** but **not production-ready**.

**Limitations:**
- ❌ THC/CBD potency (0% extraction)
- ❌ Brand info (0% extraction)
- ❌ Quantity/inventory (not available)
- ⚠️  Prices (only ~60% coverage)

**Why?** Housing Works uses Blaze (client-side SPA). Static HTML scraping gets incomplete data.

**Solution?** See README.md for production recommendations (API discovery).

---

## Quick Troubleshooting

**Problem:** `Cannot find module`  
**Fix:** Run `npm install`

**Problem:** No products extracted  
**Fix:** Check `debug-housing-works.html` - might be site structure change

**Problem:** Error connecting to site  
**Fix:** Check internet connection, verify URL still works

---

## More Info

- **Full docs:** `README.md`
- **Findings report:** `FINDINGS.md`
- **Research docs:** `~/clawd/budalert/research/phase4-housing-works/README.md`

---

**Last Updated:** 2026-03-05  
**Status:** Working ✅
