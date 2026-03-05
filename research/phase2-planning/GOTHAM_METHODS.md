# Gotham NYC - Scraping Method Analysis

**Platform**: WordPress + Dovetail ecommerce plugin
**Complexity**: ⭐⭐ (Low-Medium)
**URL**: https://gotham.nyc/menu
**Existing Scraper**: ✅ `memory/stealth-scraper/scrapers/custom-medium/gotham.py`

---

## Method 1: Use/Improve Existing curl-based Scraper ⭐ RECOMMENDED

### Description
The existing Python scraper uses simple curl requests with HTML parsing and JSON-LD extraction. Server-rendered WordPress should work well with this approach.

### Current Implementation Features
```python
class GothamScraper:
    - curl-based HTTP requests (subprocess)
    - HTML regex parsing for products
    - JSON-LD structured data extraction
    - Multiple product element patterns
    - Age gate detection/bypass attempts
    - Dovetail-specific selectors (dt-*)
```

### Approach Options

#### Option A: Use Python Scraper As-Is
- Simple HTTP requests
- No browser required
- Fast and lightweight

#### Option B: Port to Node.js with Cheerio
```javascript
const axios = require('axios');
const cheerio = require('cheerio');

async function scrapeGotham() {
  const { data } = await axios.get('https://gotham.nyc/menu');
  const $ = cheerio.load(data);
  
  // Parse products
  const products = $('.dt-product, .product').map((i, el) => {
    return {
      name: $(el).find('.product-title').text(),
      price: $(el).find('.price').text(),
      // ... more fields
    };
  }).get();
  
  // Also extract JSON-LD
  const jsonLd = $('script[type="application/ld+json"]')
    .map((i, el) => JSON.parse($(el).html()))
    .get()
    .filter(obj => obj['@type'] === 'Product');
  
  return products;
}
```

### Pros
- ✅ Simple and fast
- ✅ No browser required
- ✅ Server-side rendering (content in HTML)
- ✅ JSON-LD provides structured data
- ✅ Lightweight resource usage

### Cons
- ⚠️ May hit age gate
- ⚠️ Limited to HTML content
- ⚠️ May miss JS-loaded products

### Data Fields Extractable
- ✅ Product name, Price
- ✅ Category, Brand (from JSON-LD)
- ✅ THC %, CBD % (if in HTML)
- ✅ Image URL
- ✅ Stock status (from JSON-LD availability)
- ⚠️ Product URL (if present)

### Improvements to Consider
1. **Better age gate handling** - Check if needed, bypass properly
2. **Enhanced JSON-LD parsing** - Extract all structured data
3. **Add retry logic** - Handle temporary failures
4. **Rate limiting** - Add delays to avoid blocks
5. **Session management** - Persist cookies if age gate exists

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 4/5 | WordPress is stable |
| **Speed** | 5/5 | Very fast (no browser) |
| **Maintainability** | 4/5 | HTML changes are moderate |
| **Hackiness** | 1/5 | Standard web scraping |
| **Data Completeness** | 4/5 | JSON-LD helps |

**Total Score**: 18/25

---

## Method 2: WordPress REST API (If Available)

### Description
WordPress has a built-in REST API. Check if Gotham exposes product data via the WP API.

### Investigation Steps
1. Test endpoint: `https://gotham.nyc/wp-json/wp/v2/posts`
2. Check for custom post types: `/wp-json/wp/v2/products`
3. Test WooCommerce API if present: `/wp-json/wc/v3/products`
4. Check Dovetail plugin API endpoints

### Common WordPress API Endpoints
```javascript
// Standard WordPress
GET /wp-json/wp/v2/products

// WooCommerce (if used)
GET /wp-json/wc/v3/products
GET /wp-json/wc/v3/products/categories

// Dovetail-specific (hypothetical)
GET /wp-json/dovetail/v1/menu
GET /wp-json/dovetail/v1/products
```

### Implementation (if API exists)
```javascript
const response = await axios.get('https://gotham.nyc/wp-json/wc/v3/products', {
  params: {
    per_page: 100,
    category: 'flower'
  },
  auth: {
    username: 'consumer_key', // If required
    password: 'consumer_secret'
  }
});

const products = response.data;
```

### Pros
- ✅ Official API (if available)
- ✅ Structured JSON data
- ✅ Fast and reliable
- ✅ Pagination support
- ✅ Filtering options

### Cons
- ⚠️ May not exist
- ⚠️ May require authentication
- ⚠️ May not include all data
- ⚠️ Might be disabled

### Feasibility Check
- 🔍 **REQUIRES INVESTIGATION**
- Test API endpoints
- If exists, **this becomes primary method**

### Scoring (if API exists)
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 5/5 | Official API |
| **Speed** | 5/5 | Direct JSON |
| **Maintainability** | 5/5 | API versioning |
| **Hackiness** | 1/5 | Not hacky at all |
| **Data Completeness** | 5/5 | Full product data |

**Total Score**: 21/25 (Best if available)

---

## Method 3: Enhanced JSON-LD Extraction

### Description
WordPress sites often have extensive JSON-LD structured data. Extract and prioritize this over HTML parsing.

### JSON-LD Schema Types
```javascript
// Look for these schema types
@type: "Product"
@type: "ItemList" 
@type: "Offer"
```

### Implementation
```javascript
const $ = cheerio.load(html);

// Extract all JSON-LD blocks
const jsonLdBlocks = $('script[type="application/ld+json"]')
  .map((i, el) => {
    try {
      return JSON.parse($(el).html());
    } catch (e) {
      return null;
    }
  })
  .get()
  .filter(obj => obj !== null);

// Filter for products
const products = jsonLdBlocks
  .filter(obj => obj['@type'] === 'Product')
  .map(product => ({
    name: product.name,
    price: product.offers?.price,
    brand: product.brand?.name,
    image: product.image,
    description: product.description,
    sku: product.sku,
    availability: product.offers?.availability,
    category: product.category
  }));

// Also check for ItemList
const itemLists = jsonLdBlocks
  .filter(obj => obj['@type'] === 'ItemList')
  .flatMap(list => list.itemListElement || []);
```

### Pros
- ✅ Structured, clean data
- ✅ SEO-optimized (less likely to change)
- ✅ Standard format
- ✅ Often more complete than HTML

### Cons
- ⚠️ May not include all products
- ⚠️ May be outdated/cached
- ⚠️ Might not have inventory data

### Data Fields Available
- ✅ Product name, price, brand
- ✅ Image URL, description
- ✅ SKU, category
- ✅ Availability status
- ⚠️ THC/CBD % (may not be in schema)

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 5/5 | Schema is stable |
| **Speed** | 5/5 | Same as HTML parsing |
| **Maintainability** | 5/5 | Standard format |
| **Hackiness** | 1/5 | Using intended data |
| **Data Completeness** | 4/5 | Most fields present |

**Total Score**: 20/25 (Excellent approach)

---

## Method 4: Age Gate Bypass Strategies

### Description
If Gotham has age verification, implement proper bypass methods.

### Strategy Options

#### A. Cookie-Based Bypass
```javascript
// Set age verification cookie
const cookies = [
  { name: 'age_verified', value: 'true', domain: 'gotham.nyc' },
  { name: 'age_gate_passed', value: '1', domain: 'gotham.nyc' }
];

const response = await axios.get('https://gotham.nyc/menu', {
  headers: { Cookie: cookies.map(c => `${c.name}=${c.value}`).join('; ') }
});
```

#### B. Session-Based Bypass
```javascript
// First visit: Accept age gate
const session = axios.create();
await session.post('https://gotham.nyc/age-verify', {
  age_confirmed: true,
  birthdate: '1990-01-01'
});

// Subsequent requests use session cookies
const products = await session.get('https://gotham.nyc/menu');
```

#### C. Direct URL Access
```javascript
// Some age gates only protect homepage
// Direct menu access might bypass
await axios.get('https://gotham.nyc/menu'); // No age gate?
await axios.get('https://gotham.nyc/products'); // Different path?
```

### Investigation Steps
1. Visit site and check if age gate exists
2. Inspect what happens after verification
3. Check cookies/localStorage after accepting
4. Test direct URL access
5. Look for age verification endpoint

### Pros
- ✅ Allows access to full content
- ✅ Can be automated
- ✅ Usually simple implementation

### Cons
- ⚠️ May need periodic re-verification
- ⚠️ Cookie might expire
- ⚠️ Site may change verification method

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 4/5 | Usually stable |
| **Speed** | 5/5 | One-time setup |
| **Maintainability** | 3/5 | May change |
| **Hackiness** | 2/5 | Minor workaround |
| **Data Completeness** | 5/5 | Full access |

**Total Score**: 19/25 (Necessary if age gate exists)

---

## Method 5: RSS Feed Scraping (If Available)

### Description
WordPress sites often have RSS feeds for posts/products. Check if Gotham publishes product feed.

### Common WordPress Feed URLs
```
https://gotham.nyc/feed/
https://gotham.nyc/products/feed/
https://gotham.nyc/menu/feed/
https://gotham.nyc/?feed=rss2
https://gotham.nyc/?post_type=product&feed=rss2
```

### Implementation
```javascript
const Parser = require('rss-parser');
const parser = new Parser();

const feed = await parser.parseURL('https://gotham.nyc/products/feed/');

const products = feed.items.map(item => ({
  name: item.title,
  description: item.content,
  url: item.link,
  pubDate: item.pubDate,
  // Extract additional data from content/description
}));
```

### Pros
- ✅ Official feed format
- ✅ Updated automatically
- ✅ Simple parsing
- ✅ No age gate issues

### Cons
- ⚠️ May not exist for products
- ⚠️ Limited data fields
- ⚠️ May only show recent items
- ❌ Likely no inventory data

### Feasibility
- 🔍 **REQUIRES INVESTIGATION**
- Check if product feed exists
- Unlikely for ecommerce, but worth checking

### Scoring (if exists)
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 5/5 | Standard WordPress |
| **Speed** | 5/5 | XML parsing is fast |
| **Maintainability** | 5/5 | Feed format stable |
| **Hackiness** | 1/5 | Official feature |
| **Data Completeness** | 2/5 | Limited fields |

**Total Score**: 18/25 (Supplementary if exists)

---

## Method 6: Sitemap XML Scraping

### Description
Use WordPress sitemap.xml to discover all product URLs, then scrape individual pages.

### Process
1. Fetch `https://gotham.nyc/sitemap.xml`
2. Extract product URLs
3. Scrape each product page
4. Aggregate data

### Implementation
```javascript
// Get sitemap
const sitemapResponse = await axios.get('https://gotham.nyc/sitemap.xml');
const $ = cheerio.load(sitemapResponse.data, { xmlMode: true });

// Extract product URLs
const productUrls = $('url > loc')
  .map((i, el) => $(el).text())
  .get()
  .filter(url => url.includes('/product/') || url.includes('/menu/'));

// Scrape each product
const products = await Promise.all(
  productUrls.map(url => scrapeProductPage(url))
);
```

### Pros
- ✅ Comprehensive product discovery
- ✅ Official WordPress feature
- ✅ Can get detailed individual pages

### Cons
- ❌ Slow (one request per product)
- ⚠️ May not include all products
- ⚠️ Sitemap might be cached/outdated
- ❌ Many requests = higher detection risk

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 4/5 | Sitemap usually exists |
| **Speed** | 1/5 | Very slow |
| **Maintainability** | 4/5 | Sitemap is standard |
| **Hackiness** | 1/5 | Using official data |
| **Data Completeness** | 5/5 | Full product pages |

**Total Score**: 15/25 (Fallback only)

---

## Method 7: Browser Automation (Fallback)

### Description
If HTML scraping fails (age gate, JS requirements), use Playwright as fallback.

### When to Use
- Age gate cannot be bypassed with cookies
- Products are dynamically loaded via JavaScript
- Pagination requires browser interaction
- Other methods fail

### Implementation
```javascript
const { chromium } = require('playwright');

const browser = await chromium.launch();
const page = await browser.newPage();

// Handle age gate if present
page.on('dialog', dialog => dialog.accept());

await page.goto('https://gotham.nyc/menu');

// Wait for products
await page.waitForSelector('.product, .dt-product');

// Extract data
const products = await page.$$eval('.product', elements => {
  return elements.map(el => ({
    name: el.querySelector('.product-title')?.textContent,
    price: el.querySelector('.price')?.textContent,
    // ... more fields
  }));
});
```

### Pros
- ✅ Handles any age gate
- ✅ Executes JavaScript
- ✅ Can interact with page elements

### Cons
- ❌ Slower than curl
- ❌ More resource-intensive
- ❌ Overkill for server-rendered site

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 5/5 | Will always work |
| **Speed** | 2/5 | Slow browser overhead |
| **Maintainability** | 4/5 | Resilient to changes |
| **Hackiness** | 2/5 | Standard automation |
| **Data Completeness** | 5/5 | Full page access |

**Total Score**: 18/25 (Use only if needed)

---

## Recommended Implementation Strategy

### Phase 1: Investigation (Day 1)
1. ✅ Test for age gate
2. ✅ Check WordPress REST API endpoints
3. ✅ Inspect JSON-LD availability
4. ✅ Test RSS feeds
5. ✅ Check sitemap

### Phase 2: Implementation (Day 2)
**Primary**: Method 3 (Enhanced JSON-LD) + Method 1 (HTML fallback)
```javascript
async function scrapeGotham() {
  const { data: html } = await axios.get('https://gotham.nyc/menu', {
    headers: {
      Cookie: 'age_verified=true' // If needed
    }
  });
  
  // Try JSON-LD first
  const jsonLdProducts = extractJsonLD(html);
  
  if (jsonLdProducts.length > 0) {
    return jsonLdProducts;
  }
  
  // Fallback to HTML parsing
  return parseHTML(html);
}
```

### Phase 3: Optimization (Week 1)
- If WP REST API exists, switch to Method 2
- Add caching for age verification
- Implement retry logic
- Add error handling

---

## Summary Comparison

| Method | Score | Use Case |
|--------|-------|----------|
| **#1: curl + HTML** | 18/25 | **Baseline** - Works |
| **#2: WordPress API** | 21/25 | **Best** - If exists |
| **#3: JSON-LD** | 20/25 | **Primary** - Recommended |
| #4: Age Gate Bypass | 19/25 | Necessary if gate exists |
| #5: RSS Feed | 18/25 | Supplementary |
| #6: Sitemap | 15/25 | Avoid - Too slow |
| #7: Browser | 18/25 | Fallback only |

**Recommendation**:
1. Investigate WordPress API (Method #2)
2. Use JSON-LD extraction (Method #3) as primary
3. Keep HTML parsing (Method #1) as fallback
4. Use browser (Method #7) only if absolutely needed

---

