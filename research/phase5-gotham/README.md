# Phase 5: Gotham NYC Implementation

**Dispensary**: Gotham NYC  
**Platform**: WordPress + Dovetail/WooCommerce  
**Complexity**: ⭐⭐ Low-Medium  
**Status**: ✅ Documentation Complete (Easiest Implementation)

---

## Overview

This phase implements scrapers for Gotham NYC, which uses WordPress with Dovetail ecommerce plugin. WordPress is the **easiest platform to scrape** due to:

- Server-side rendering (HTML in source)
- JSON-LD structured data (SEO-friendly)
- Optional REST API access
- No complex JavaScript frameworks

### Platform Characteristics

- **CMS**: WordPress
- **Ecommerce**: Dovetail plugin (or WooCommerce)
- **Rendering**: Server-side (full HTML in source)
- **Data**: Structured JSON-LD + HTML
- **Protection**: Possible age gate

### Key Advantages

1. ✅ **No browser needed** (simple HTTP requests work)
2. ✅ **Structured data available** (JSON-LD)
3. ✅ **Fast scraping** (no JavaScript execution)
4. ✅ **Low resource usage** (can run anywhere)
5. ✅ **Multiple fallback methods** (API → JSON-LD → HTML)

---

## Implementation Approaches

### Method #1: curl + HTML Parsing ⭐ **Primary**

**File**: `scraper-curl.js`  
**Score**: 18/25  
**Status**: Complete (documentation)

**How It Works**:
1. Fetch menu page with axios (no browser)
2. Parse HTML with cheerio
3. Extract JSON-LD structured data (if available)
4. Fall back to HTML element parsing
5. Handle age gate if present

**Advantages**:
- ✅ Very fast (1-5 seconds)
- ✅ Extremely low resource usage (50 MB RAM)
- ✅ Works anywhere (Node.js, serverless, cron)
- ✅ No browser dependencies
- ✅ Multiple extraction methods (JSON-LD, HTML, WooCommerce)

**Disadvantages**:
- ❌ May miss dynamic content (unlikely with WordPress)
- ❌ Age gate might block access (easily bypassed with cookie)

**Usage**:
```bash
npm install
node scraper-curl.js
```

**Output**:
- `gotham-products-{timestamp}.json`

---

### Method #2: WordPress REST API ⭐ **Best** (If Available)

**File**: `scraper-wordpress-api.js`  
**Score**: 21/25  
**Status**: Complete (documentation)

**How It Works**:
1. Discover WordPress API endpoints
2. Check for WooCommerce API (`/wp-json/wc/v3/products`)
3. Check for custom product endpoints
4. Fetch products as clean JSON
5. Handle pagination if needed

**Advantages**:
- ✅ Official API (most reliable)
- ✅ Clean, structured JSON
- ✅ No HTML parsing needed
- ✅ Supports pagination
- ✅ Product metadata included

**Disadvantages**:
- ❌ May not be enabled for all WordPress sites
- ❌ Might require authentication (rare for read-only)

**Usage**:
```bash
npm install
node scraper-wordpress-api.js
```

**Output**:
- `gotham-products-api-{timestamp}.json`
- `gotham-api-endpoints-{timestamp}.json` (discovered endpoints)

**Endpoint Discovery**:
```bash
# Run scraper to auto-discover endpoints
node scraper-wordpress-api.js

# Check what was discovered
cat gotham-api-endpoints-*.json | jq '.'
```

---

### Method #3: Browser Automation (Fallback Only)

If both Method #1 and #2 fail (which is unlikely for WordPress), use browser automation:

```javascript
const { chromium } = require('playwright');
// ... similar to Conbud/Housing Works scrapers
```

**When to use**:
- Only if age gate blocks curl requests
- Only if JavaScript is required (rare for WordPress)
- For debugging HTML structure

---

## Data Extraction Strategies

### Strategy A: JSON-LD (Best)

WordPress sites often include Schema.org JSON-LD for SEO:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Blue Dream 1/8oz",
  "brand": "Good Chemistry",
  "offers": {
    "@type": "Offer",
    "price": "45.00",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  },
  "image": "https://gotham.nyc/photos/blue-dream.jpg"
}
</script>
```

**Extraction**:
```javascript
$('script[type="application/ld+json"]').each((i, elem) => {
  const data = JSON.parse($(elem).html());
  if (data['@type'] === 'Product') {
    products.push(normalizeJsonLdProduct(data));
  }
});
```

### Strategy B: HTML Elements (Dovetail)

Dovetail uses `dt-` prefixed classes:

```html
<div class="dt-product" data-product-id="123">
  <h3 class="dt-product-name">Sour Diesel</h3>
  <span class="dt-price">$50</span>
  <div class="dt-thc">THC: 24%</div>
</div>
```

**Extraction**:
```javascript
$('.dt-product, .product').each((i, elem) => {
  const name = $(elem).find('.product-name, h3').text();
  const price = $(elem).find('.price, .dt-price').text();
  // ...
});
```

### Strategy C: WooCommerce (WordPress)

Standard WooCommerce markup:

```html
<article class="product type-product">
  <h2 class="woocommerce-loop-product__title">Product Name</h2>
  <span class="price">
    <span class="amount">$45.00</span>
  </span>
</article>
```

**Extraction**:
```javascript
$('.product, .woocommerce-product').each((i, elem) => {
  // Extract using standard WooCommerce selectors
});
```

---

## Docker Setup

### Build and Run

```bash
# Build image
docker build -t gotham-scraper .

# Or use docker-compose
docker-compose up --build

# Run curl scraper (primary)
docker-compose run gotham-scraper node scraper-curl.js

# Run API scraper (alternative)
docker-compose run gotham-scraper node scraper-wordpress-api.js
```

### Lightweight Container

Since no browser is needed, the container is very small:

```
Image size: ~150 MB (vs 2+ GB for Playwright containers)
Memory usage: ~50 MB (vs 500+ MB for browser automation)
Startup time: <1 second
```

---

## Data Schema

### Product Object

```javascript
{
  "id": "123",
  "name": "Blue Dream 1/8oz",
  "brand": "Good Chemistry",
  "category": "Flower",
  
  "price": 45.00,
  "priceFormatted": "$45.00",
  
  "thc": {
    "formatted": "THC: 24.5%",
    "value": 24.5
  },
  "cbd": {
    "formatted": "CBD: 0.1%",
    "value": 0.1
  },
  
  "image": "https://gotham.nyc/photos/blue-dream.jpg",
  "images": ["url1", "url2"],
  
  "description": "Uplifting sativa-dominant hybrid...",
  "url": "https://gotham.nyc/product/blue-dream",
  
  "inStock": true,
  
  "scrapedAt": "2026-03-05T12:00:00Z",
  "source": "gotham-nyc",
  "sourceUrl": "https://gotham.nyc/menu"
}
```

### Expected Fields

| Field | Availability | Method | Notes |
|-------|--------------|--------|-------|
| `name` | ✅ Always | All | Product name |
| `price` | ✅ Always | All | Always displayed |
| `category` | ⚠️  Usually | HTML | From category page or name |
| `brand` | ⚠️  Sometimes | JSON-LD/HTML | May be in name |
| `thc` | ⚠️  Usually | HTML text | Regex extraction |
| `cbd` | ⚠️  Sometimes | HTML text | Often missing |
| `image` | ✅ Usually | JSON-LD/HTML | Product photo |
| `url` | ✅ Usually | JSON-LD/HTML | Product detail page |
| `inStock` | ✅ Always | HTML | Via "out of stock" detection |
| `id` | ⚠️  Sometimes | API | Only if API available |

---

## Age Gate Handling

### Detection

```javascript
checkAgeGate(html) {
  const indicators = [
    'age verification',
    'confirm you are',
    'are you 21',
    'must be 21'
  ];
  
  return indicators.some(text => 
    html.toLowerCase().includes(text)
  );
}
```

### Bypass Methods

**Method 1: Cookie** (Recommended)
```javascript
headers: {
  'Cookie': 'age_verified=1; age_gate_passed=true'
}
```

**Method 2: Session Storage** (Browser only)
```javascript
await page.evaluate(() => {
  localStorage.setItem('age_verified', 'true');
  sessionStorage.setItem('age_gate_passed', 'true');
});
```

**Method 3: Direct URL** (Skip gate page)
```javascript
// Instead of /menu, try:
// /menu?age_verified=1
// /shop
// /products
```

---

## Testing & Validation

### Test Checklist

- [ ] Page fetches successfully (200 status)
- [ ] No age gate blocking access
- [ ] JSON-LD data is extracted (if present)
- [ ] HTML products are extracted (fallback)
- [ ] Required fields present (name, price)
- [ ] Potency data extracted (THC/CBD)
- [ ] Images are valid URLs
- [ ] No duplicate products
- [ ] Data is saved to JSON

### Validation Commands

```bash
# Check scraper output
cat gotham-products-*.json | jq '. | length'

# Verify required fields
cat gotham-products-*.json | jq '.[] | {name, price}'

# Find products missing data
cat gotham-products-*.json | jq '.[] | select(.price == null or .name == null)'

# Check potency data
cat gotham-products-*.json | jq '.[] | {name, thc: .thc.value, cbd: .cbd.value}'

# Verify images
cat gotham-products-*.json | jq '.[] | select(.image == null) | .name'
```

### Quick Test

```bash
# Test if menu page is accessible
curl -L https://gotham.nyc/menu | head -100

# Test with age verification cookie
curl -L -b "age_verified=1" https://gotham.nyc/menu | grep -i "product"

# Check if WordPress API is available
curl https://gotham.nyc/wp-json/
curl https://gotham.nyc/wp-json/wc/v3/products
```

---

## Troubleshooting

### Issue: Age gate blocking scraper

**Error**: HTML contains "Verify your age" text

**Solution 1**: Set age verification cookie
```javascript
headers: {
  'Cookie': 'age_verified=1'
}
```

**Solution 2**: Find direct menu URL
```bash
# Try these URLs:
https://gotham.nyc/shop
https://gotham.nyc/products
https://gotham.nyc/menu?age_verified=1
```

### Issue: No products found

**Debug steps**:

1. Check raw HTML:
```javascript
const html = await scraper.fetchPage(url);
fs.writeFileSync('gotham-page.html', html);
// Review HTML structure
```

2. Check for JavaScript rendering:
```bash
curl https://gotham.nyc/menu | grep -i "product"
# If no products in HTML, site might use JavaScript
```

3. Update selectors:
```javascript
// Inspect HTML and update selectors
const selectors = [
  '.your-actual-product-class',
  'article.product'
];
```

### Issue: WordPress API returns 404

**Cause**: API might not be enabled or requires different endpoint

**Solution**: Use curl scraper instead
```bash
node scraper-curl.js  # Works without API
```

---

## Performance Metrics

### Expected Performance

| Metric | curl Method | WordPress API | Browser (fallback) |
|--------|-------------|---------------|-------------------|
| **Products** | 150-300 | 150-300 | 150-300 |
| **Duration** | 1-5 seconds | 2-5 seconds | 15-30 seconds |
| **Memory** | 50-100 MB | 50-100 MB | 500+ MB |
| **Reliability** | 98%+ | 95%+ (if enabled) | 98%+ |
| **Data Quality** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

### Gotham is the Fastest!

- **Simplest implementation** of all three dispensaries
- **No browser needed** (unlike Conbud and Housing Works)
- **Server-rendered HTML** (all data in source)
- **Perfect for production** (low resources, high speed)

---

## Comparison with Other Dispensaries

| Feature | Gotham (WordPress) | Housing Works (Blaze) | Conbud (Dutchie) |
|---------|-------------------|---------------------|------------------|
| **Browser Required** | ❌ No | ✅ Yes | ✅ Yes |
| **API Available** | ⚠️  Maybe | ⚠️  Discover | ✅ GraphQL |
| **Speed** | ⭐⭐⭐⭐⭐ Fastest | ⭐⭐⭐ Medium | ⭐⭐⭐ Medium |
| **Complexity** | ⭐⭐ Easy | ⭐⭐⭐ Medium | ⭐⭐⭐⭐⭐ Hard |
| **Resource Usage** | ⭐⭐⭐⭐⭐ Lowest | ⭐⭐⭐ Medium | ⭐⭐⭐ Medium |
| **Reliability** | ⭐⭐⭐⭐⭐ Best | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐ Good |
| **Deployment** | Anywhere | Needs Playwright | Needs Playwright |

---

## Production Recommendations

### For Production Use:

1. **Primary method**: curl scraper (Method #1)
2. **Fallback**: WordPress API (Method #2) if available
3. **Last resort**: Browser automation (only if needed)

### Deployment Options:

- ✅ **AWS Lambda** (perfect fit, no custom runtime needed)
- ✅ **Vercel/Netlify** (serverless functions)
- ✅ **GitHub Actions** (scheduled cron)
- ✅ **Docker** (minimal container size)
- ✅ **Local cron** (simplest option)
- ✅ **Raspberry Pi** (low resource requirements)

### Configuration:

```javascript
// Production config
const config = {
  timeout: 30000,
  retries: 3,
  headers: {
    'Cookie': process.env.AGE_VERIFICATION_COOKIE || 'age_verified=1'
  },
  rateLimit: {
    requests: 1,
    per: 1000 // 1 request per second (be nice!)
  }
};
```

---

## Next Steps

1. ✅ Documentation complete
2. ⏳ Test scrapers in Node.js environment
3. ⏳ Verify age gate handling
4. ⏳ Check if WordPress API is available
5. ⏳ Validate data completeness
6. ⏳ Choose best method for production
7. ⏳ Deploy with monitoring

---

**Phase 5 Status**: ✅ Complete (Documentation)

Ready to proceed to **Phase 6: Final Scorecard & Environment Guide**
