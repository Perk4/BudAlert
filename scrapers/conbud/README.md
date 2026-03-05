## Conbud LES Scraper

**Dispensary**: Conbud LES (Lower East Side)  
**Platform**: Dutchie (React SPA with GraphQL API)  
**Complexity**: ⭐⭐⭐⭐⭐ Very High  
**URL**: https://conbud.com/stores/conbud-les

---

## Overview

This scraper targets Conbud LES, which uses the Dutchie e-commerce platform. Dutchie is a sophisticated React-based single-page application with:

- **Client-side rendering** (empty HTML source)
- **GraphQL API** at `api.dutchie.com`
- **Turnstile CAPTCHA** protection
- **Dynamic content loading**

### Two Implementation Approaches

| Approach | File | Speed | Reliability | Prerequisites |
|----------|------|-------|-------------|---------------|
| **Browser Intercept** | `browser-scraper.mjs` | Medium | ⭐⭐⭐⭐⭐ | Chromium |
| **Direct API** | `api-scraper.mjs` | Fast | ⭐⭐⭐⭐ | Extracted queries |

**Recommended workflow:**

1. Run `browser-scraper.mjs` first to extract GraphQL queries
2. Use extracted queries to power `api-scraper.mjs` for production
3. Keep browser scraper as fallback/validation

---

## Quick Start

### Installation

```bash
cd ~/clawd/budalert/scrapers/conbud

# Install dependencies
npm install playwright axios

# Install Playwright browsers
npx playwright install chromium
```

### Run Browser Scraper (Primary)

```bash
# Headless mode (production)
node browser-scraper.mjs

# With visible browser (debug/CAPTCHA solving)
HEADLESS=false node browser-scraper.mjs
```

**Output files:**
- `conbud-products-browser-{timestamp}.json` - Scraped products
- `conbud-graphql-requests-{timestamp}.json` - Captured GraphQL queries
- `conbud-graphql-responses-{timestamp}.json` - Raw API responses
- `conbud-extracted-queries-{timestamp}.mjs` - Reusable query templates

### Run API Scraper (Fast)

```bash
# Direct API method (requires extracted queries first)
node api-scraper.mjs
```

**Output:**
- `conbud-products-api-{timestamp}.json` - Products from direct API

---

## File Structure

```
conbud/
├── queries.mjs              # GraphQL queries and schema
├── browser-scraper.mjs      # Playwright network intercept method
├── api-scraper.mjs          # Direct GraphQL API method
├── README.md               # This file
└── package.json            # Dependencies
```

---

## GraphQL Queries

### Primary Query Structure

The `filteredProducts` query is the main endpoint for fetching products:

```graphql
query FilteredProducts(
  $dispensaryId: ID!
  $filters: FilterInput
  $offset: Int
  $limit: Int
) {
  filteredProducts(
    dispensaryId: $dispensaryId
    filters: $filters
    offset: $offset
    limit: $limit
  ) {
    products {
      id
      name
      brand { name id }
      category
      subcategory
      price
      variants { id option price inStock }
      potencyThc { formatted range }
      potencyCbd { formatted range }
      image
      images
      strainType
      description
      effects
      inStock
      quantity
    }
    totalCount
  }
}
```

**Variables:**

```json
{
  "dispensaryId": "6430f42042cf3c004e37f0f8",
  "filters": null,
  "offset": 0,
  "limit": 1000
}
```

### Available Filters

```javascript
{
  category: ["Flower", "Vapes", "Edibles"],
  subcategory: ["Indica", "Sativa", "Hybrid"],
  strainType: ["indica", "sativa", "hybrid"],
  brand: ["Brand Name"],
  price: { min: 10, max: 50 },
  inStock: true
}
```

---

## Product Data Schema

### Expected Fields

```javascript
{
  // Core identification
  "id": "64a1b2c3d4e5f6a7b8c9d0e1",
  "name": "Blue Dream Pre-Roll 1g",
  "brand": "House of Wise",
  "category": "Pre-Rolls",
  "subcategory": "Sativa",
  
  // Pricing
  "price": 12.00,
  "priceRange": { "min": 12.00, "max": 12.00 },
  
  // Potency
  "thc": "22.5%",
  "thcPercent": 22.5,
  "cbd": "0.1%",
  "cbdPercent": 0.1,
  
  // Media
  "image": "https://dutchie.com/photos/...",
  "images": ["url1", "url2"],
  
  // Inventory
  "inStock": true,
  "inventoryCount": 47,
  
  // Classification
  "strainType": "sativa",
  "effects": ["creative", "energetic", "uplifted"],
  "description": "Uplifting and creative...",
  
  // Variants (different sizes/weights)
  "variants": [
    { "id": "v1", "option": "1g", "price": 12.00, "inStock": true }
  ],
  
  // Metadata
  "scrapedAt": "2026-03-05T12:00:00.000Z",
  "source": "conbud-les",
  "sourceUrl": "https://conbud.com/stores/conbud-les"
}
```

### Field Availability

| Field | Availability | Notes |
|-------|--------------|-------|
| `id` | ✅ Always | Dutchie product ID |
| `name` | ✅ Always | Product name |
| `brand` | ✅ Always | Brand name (nested) |
| `category` | ✅ Always | Main category |
| `subcategory` | ⚠️  Usually | Subtype classification |
| `price` | ✅ Always | Base price |
| `thc` / `cbd` | ⚠️  Usually | Potency strings |
| `image` | ✅ Always | Main image URL |
| `inStock` | ✅ Always | Availability flag |
| `inventoryCount` | ⚠️  Sometimes | Exact quantity |
| `variants` | ⚠️  Sometimes | Different weights/options |

---

## Browser Scraper Details

### How It Works

1. **Launch Chromium** with stealth settings
2. **Navigate** to Conbud store URL
3. **Intercept network** requests to `api.dutchie.com`
4. **Capture GraphQL** queries and responses
5. **Extract products** from response payloads
6. **Scroll & navigate** to trigger lazy loading
7. **Save data** and extracted queries

### Features

- ✅ Automatic query extraction
- ✅ CAPTCHA detection (manual solve)
- ✅ Lazy loading support
- ✅ Category navigation
- ✅ Request/response logging
- ✅ Deduplication

### Configuration Options

```javascript
const scraper = new ConbudBrowserScraper({
  headless: true,           // Run without UI
  timeout: 60000,           // Page load timeout (ms)
  captchaWaitTime: 30000,   // Time to solve CAPTCHA
  scrollSteps: 5,           // Number of scroll iterations
  scrollDelay: 1000         // Delay between scrolls (ms)
});
```

### Handling CAPTCHA

**Option 1: Manual (Development)**

```bash
# Run with visible browser
HEADLESS=false node browser-scraper.mjs

# Solve CAPTCHA in the browser window
```

**Option 2: Automated (Production)**

Integrate a CAPTCHA solving service:
- [2captcha.com](https://2captcha.com)
- [Anti-Captcha](https://anti-captcha.com)
- [CapSolver](https://www.capsolver.com)

---

## API Scraper Details

### How It Works

1. **Load GraphQL queries** from `queries.mjs`
2. **Make direct HTTP POST** to `api.dutchie.com/graphql`
3. **Parse JSON responses**
4. **Normalize product data**
5. **Save to file**

### Features

- ✅ Very fast (no browser overhead)
- ✅ Low resource usage
- ✅ Retry logic with exponential backoff
- ✅ Multiple query fallbacks
- ✅ Error tracking

### Configuration Options

```javascript
const scraper = new ConbudAPIScraper({
  timeout: 30000,      // Request timeout (ms)
  retries: 3,          // Number of retry attempts
  retryDelay: 2000     // Delay between retries (ms)
});
```

### Prerequisites

The API scraper requires valid GraphQL queries. Options:

1. **Extract from browser scraper** (recommended)
   ```bash
   node browser-scraper.mjs
   # Use queries from conbud-extracted-queries-*.mjs
   ```

2. **Use provided templates** in `queries.mjs`
   - May work but could be outdated
   - Update if API returns errors

3. **Manually inspect network traffic**
   - Open https://conbud.com/stores/conbud-les in browser
   - Open DevTools → Network → Filter by "graphql"
   - Copy query from request payload

---

## Troubleshooting

### Issue: Browser won't launch

**Error:** `browserType.launch: Host system is missing dependencies`

**Solution:** Install Playwright system dependencies

```bash
# Ubuntu/Debian
sudo apt-get install -y \
  libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
  libxdamage1 libxfixes3 libxrandr2 libgbm1 \
  libasound2 libwayland-client0

# Or use Playwright's installer
npx playwright install-deps chromium
```

**Alternative:** Use Docker (see below)

---

### Issue: CAPTCHA blocking scraper

**Error:** Turnstile CAPTCHA appears, scraper hangs

**Solution 1: Manual solve**

```bash
HEADLESS=false node browser-scraper.mjs
# Browser window opens, solve CAPTCHA manually
```

**Solution 2: Increase wait time**

```javascript
const scraper = new ConbudBrowserScraper({
  captchaWaitTime: 60000  // 60 seconds
});
```

**Solution 3: Automated solving**

Integrate a CAPTCHA API service (requires API key)

---

### Issue: No products in output

**Check:**

1. Were GraphQL requests captured?
   ```bash
   cat conbud-graphql-requests-*.json | jq 'length'
   ```

2. Are responses empty?
   ```bash
   cat conbud-graphql-responses-*.json | jq '.[0].data'
   ```

3. Is product extraction logic correct?
   - Update `normalizeProduct()` in `queries.mjs`
   - Check response structure in saved JSON files

**Debug:**

```javascript
// Add logging to extractProductsFromResponse
console.log('Response keys:', Object.keys(json));
console.log('Data structure:', json.data);
```

---

### Issue: API queries return errors

**Error:** GraphQL returns `"errors": [...]`

**Cause:** Query structure doesn't match current API

**Solution:**

1. Run browser scraper to capture real queries
   ```bash
   node browser-scraper.mjs
   ```

2. Check extracted queries
   ```bash
   cat conbud-extracted-queries-*.mjs
   ```

3. Update `queries.mjs` with actual query structure

4. Test with `api-scraper.mjs`

---

### Issue: Sandbox environment restrictions

**Error:** `playwright` or `chromium` not available

**Context:** Running in restricted sandbox (e.g., OpenClaw sandbox, AWS Lambda)

**Solutions:**

1. **Use API scraper only** (no browser needed)
   ```bash
   node api-scraper.mjs
   ```

2. **Run browser scraper locally first**
   - Extract queries on your machine
   - Deploy API scraper to production

3. **Use a proxy service**
   - [BrowserStack](https://www.browserstack.com/)
   - [Puppeteer as a Service](https://puppeteer.cloudflare.workers.dev/)

---

## Performance Benchmarks

### Expected Performance

| Metric | Browser Scraper | API Scraper |
|--------|-----------------|-------------|
| **Products** | 100-300 | 100-300 |
| **Duration** | 30-60 seconds | 2-5 seconds |
| **Memory** | 500-800 MB | 50-100 MB |
| **CPU** | Medium-High | Low |
| **Reliability** | 95%+ | 98%+ (after setup) |

### Optimization Tips

**Browser Scraper:**
- Reduce `scrollSteps` if products load quickly
- Increase `scrollDelay` if API is rate-limited
- Skip category navigation if not needed

**API Scraper:**
- Implement request caching
- Use connection pooling for multiple requests
- Batch requests if scraping multiple stores

---

## Production Deployment

### Recommended Setup

1. **Development:** Use browser scraper to extract queries
2. **Production:** Use API scraper for speed
3. **Fallback:** Keep browser scraper for validation

### Deployment Options

| Platform | Browser Scraper | API Scraper |
|----------|-----------------|-------------|
| **Local cron** | ✅ Works | ✅ Works |
| **GitHub Actions** | ✅ Works (with setup) | ✅ Works |
| **AWS Lambda** | ⚠️  Complex (Playwright Layer) | ✅ Perfect |
| **Docker** | ✅ Works | ✅ Works |
| **Vercel/Netlify** | ❌ No browser | ✅ Works |

### Docker Example

```dockerfile
FROM mcr.microsoft.com/playwright:v1.40.0-jammy

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Run browser scraper
CMD ["node", "browser-scraper.mjs"]
```

```bash
# Build and run
docker build -t conbud-scraper .
docker run -v $(pwd):/app/output conbud-scraper
```

### Scheduled Scraping

**Cron (Linux/Mac):**

```bash
# Add to crontab (crontab -e)
0 */6 * * * cd /path/to/scrapers/conbud && node api-scraper.mjs
```

**GitHub Actions:**

```yaml
name: Scrape Conbud
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install
      - run: node api-scraper.mjs
```

---

## Rate Limiting & Ethics

### Best Practices

- ✅ **Respect robots.txt** (if applicable)
- ✅ **Rate limit requests** (max 1-2 per second)
- ✅ **Use realistic user agents**
- ✅ **Avoid peak hours** (scrape during off-peak)
- ✅ **Cache responses** (don't re-scrape unnecessarily)
- ❌ **Don't hammer the API** (causes IP bans)
- ❌ **Don't scrape personally identifiable info**

### Recommended Schedule

```
Every 6 hours (4x per day)
- 00:00 UTC (8pm EST)
- 06:00 UTC (2am EST) ← Best (lowest traffic)
- 12:00 UTC (8am EST)
- 18:00 UTC (2pm EST)
```

---

## Next Steps

1. ✅ **Run browser scraper** to extract queries
   ```bash
   node browser-scraper.mjs
   ```

2. ✅ **Validate extracted queries**
   ```bash
   cat conbud-extracted-queries-*.mjs
   ```

3. ✅ **Test API scraper**
   ```bash
   node api-scraper.mjs
   ```

4. ⏳ **Integrate into BudAlert pipeline**
   - Parse product data
   - Detect price drops
   - Send alerts

5. ⏳ **Set up monitoring**
   - Track scrape success/failure
   - Alert on API changes
   - Log errors

6. ⏳ **Deploy to production**
   - Choose deployment platform
   - Set up scheduled runs
   - Configure error notifications

---

## Support & Resources

### Documentation

- [Playwright Docs](https://playwright.dev/docs/intro)
- [Axios Docs](https://axios-http.com/docs/intro)
- [GraphQL Docs](https://graphql.org/learn/)

### Related Files

- **Research:** `~/clawd/budalert/research/phase3-conbud/`
- **Main project:** `~/clawd/budalert/`

### Common Issues

- **CAPTCHA:** Use headless=false or automated solver
- **Empty responses:** Update queries from browser scraper
- **Sandbox restrictions:** Use API scraper only
- **Rate limiting:** Add delays between requests

---

**Status:** ✅ Ready for testing  
**Last Updated:** 2026-03-05  
**Maintainer:** BudAlert Project
