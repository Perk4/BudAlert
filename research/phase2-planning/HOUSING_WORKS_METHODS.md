# Housing Works SoHo - Scraping Method Analysis

**Platform**: Blaze
**Complexity**: ⭐⭐⭐ (Medium)
**URL**: https://hwcannabis.co/menu/broadway/
**Existing Scraper**: ✅ `memory/stealth-scraper/scrapers/blaze/housing_works.py`

---

## Method 1: Use/Improve Existing Playwright Scraper ⭐ RECOMMENDED

### Description
The existing Python scraper uses Playwright with comprehensive product extraction, quantity parsing, and cart probing. Either use as-is or port to Node.js.

### Current Implementation Features
```python
class HousingWorksScraper:
    - Playwright browser automation
    - Stealth mode (UA rotation, resource blocking)
    - Network request tracking
    - Product extraction from page
    - Quantity parser (multiple detection methods)
    - Cart prober for inventory
    - Category navigation
    - Pagination/infinite scroll
```

### Approach Options

#### Option A: Use Python Scraper As-Is
- Set up Python environment
- Test existing implementation
- Fix any bugs
- Validate data output

#### Option B: Port to Node.js
- Rewrite in JavaScript with Playwright
- Maintain same logic and features
- Test equivalence
- Easier to run in current environment

### Pros
- ✅ Already implemented and tested
- ✅ Comprehensive feature set
- ✅ Includes quantity detection
- ✅ Handles pagination
- ✅ Well-documented code

### Cons
- ⚠️ Requires Python (if using as-is)
- ⚠️ Porting takes time
- ⚠️ May have undiscovered bugs

### Data Fields Extractable
- ✅ Product ID, Name, Price
- ✅ Product URL, Category
- ✅ Store name, timestamp
- ✅ Quantity info (via quantity_parser)
- ✅ In-stock status
- ✅ Max quantity (if available)

### Improvements to Consider
1. Add brand extraction if missing
2. Enhance THC/CBD % parsing
3. Add image URL extraction
4. Implement better error handling
5. Add retry logic for failures

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 4/5 | Proven to work |
| **Speed** | 3/5 | Browser automation (moderate) |
| **Maintainability** | 4/5 | Well-structured code |
| **Hackiness** | 2/5 | Standard approach |
| **Data Completeness** | 5/5 | Includes quantity |

**Total Score**: 18/25

---

## Method 2: Direct HTML Scraping (Simplified)

### Description
If Blaze renders some product data server-side, attempt simpler curl-based approach without browser.

### Investigation Steps
1. Fetch page HTML with curl
2. Check if products are in initial HTML
3. Parse with Cheerio/regex if available

### Implementation
```javascript
const axios = require('axios');
const cheerio = require('cheerio');

const response = await axios.get('https://hwcannabis.co/menu/broadway/');
const $ = cheerio.load(response.data);

// Look for product elements
const products = $('.product').map((i, el) => {
  return {
    name: $(el).find('.product-name').text(),
    price: $(el).find('.price').text(),
    // ... more fields
  };
}).get();
```

### Pros
- ✅ Fast (no browser)
- ✅ Lightweight
- ✅ Simple implementation

### Cons
- ⚠️ Likely won't work (Blaze is SPA)
- ❌ No quantity information
- ❌ May miss dynamically loaded products

### Feasibility Check Required
- Test if products are in initial HTML
- Likely: **LOW** (Blaze platforms are usually client-rendered)

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 2/5 | Probably won't work fully |
| **Speed** | 5/5 | Very fast |
| **Maintainability** | 3/5 | Simple if it works |
| **Hackiness** | 1/5 | Standard HTML parsing |
| **Data Completeness** | 2/5 | Likely incomplete |

**Total Score**: 13/25 (Investigate, but likely insufficient)

---

## Method 3: API Endpoint Discovery & Replication

### Description
Use network inspection from existing scraper to identify Blaze API endpoints, then make direct API calls.

### Process
1. Run existing scraper with network logging
2. Identify API endpoints called by Blaze platform
3. Extract request format and headers
4. Replicate requests directly

### Expected API Structure
```javascript
// Example Blaze API call (hypothetical)
const response = await axios.get(
  'https://hwcannabis.co/api/menu/products',
  {
    params: {
      location: 'broadway',
      category: 'flower'
    },
    headers: {
      'User-Agent': '...',
      'X-Blaze-Token': '...' // If needed
    }
  }
);
```

### Pros
- ✅ Fast (direct API)
- ✅ Structured data
- ✅ No browser needed (once discovered)
- ✅ Can get inventory data if API provides

### Cons
- ⚠️ Requires initial discovery phase
- ⚠️ May need authentication
- ⚠️ API could change
- ⚠️ May have rate limiting

### Discovery Required
- ✅ Can use existing scraper's network tracking
- Already logs API requests in Python code

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 4/5 | If API is stable |
| **Speed** | 5/5 | Very fast |
| **Maintainability** | 3/5 | Depends on API stability |
| **Hackiness** | 3/5 | Moderate - API replication |
| **Data Completeness** | 4/5 | Should match scraper |

**Total Score**: 19/25 (Good optimization path)

---

## Method 4: Enhanced Quantity Detection

### Description
Improve the existing quantity detection beyond what the current scraper offers.

### Current Quantity Methods (from code)
1. Quantity dropdown inspection
2. Cart probing (add-to-cart limits)
3. Stock status text parsing
4. Default assumptions

### Additional Methods to Try

#### A. Max Quantity Test via Cart
```javascript
// Try adding large quantity
await page.fill('input[name="quantity"]', '9999');
await page.click('.add-to-cart');

// Check error message
const error = await page.textContent('.error');
// "Only 12 available" -> extract 12
```

#### B. Inspect Network Responses
- Look for inventory data in API responses
- Check for `stock`, `quantity`, `available` fields

#### C. LocalStorage/SessionStorage Check
- Blaze might cache inventory info
- Check browser storage after page load

### Pros
- ✅ Better inventory accuracy
- ✅ Multiple fallback methods
- ✅ Can detect out-of-stock earlier

### Cons
- ⚠️ Cart probing is slow
- ⚠️ May trigger rate limits
- ⚠️ Requires careful implementation

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 4/5 | Multiple methods |
| **Speed** | 2/5 | Cart probing is slow |
| **Maintainability** | 3/5 | Multiple fallbacks |
| **Hackiness** | 4/5 | Cart manipulation |
| **Data Completeness** | 5/5 | Best inventory data |

**Total Score**: 18/25 (Supplement to Method 1)

---

## Method 5: Category-First Scraping Strategy

### Description
Optimize scraping by efficiently navigating categories instead of trying to load all products at once.

### Current Approach (from code)
```python
# Extract categories
categories = await self.extract_categories()

# Scrape each category
for category in categories:
    products = await self.scrape_category(category)
```

### Improvements
1. **Parallel category scraping** - Multiple browser contexts
2. **Smart category filtering** - Skip empty/irrelevant categories
3. **Incremental updates** - Only scrape changed categories
4. **Category caching** - Remember category structure

### Implementation
```javascript
// Parallel category scraping
const categories = await extractCategories(page);

const products = await Promise.all(
  categories.map(async (category) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    return await scrapeCategory(page, category);
  })
);
```

### Pros
- ✅ Faster total scrape time
- ✅ Better organization
- ✅ Can prioritize important categories

### Cons
- ⚠️ More complex orchestration
- ⚠️ Higher resource usage (multiple contexts)
- ⚠️ May trigger rate limiting

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 4/5 | Same as base method |
| **Speed** | 4/5 | Parallel = faster |
| **Maintainability** | 3/5 | More complex |
| **Hackiness** | 2/5 | Standard optimization |
| **Data Completeness** | 5/5 | Same as sequential |

**Total Score**: 18/25 (Good optimization)

---

## Method 6: Hybrid Approach - Browser for Discovery, API for Speed

### Description
Combine methods: Use browser automation occasionally to discover/validate API structure, then use direct API calls for regular scraping.

### Strategy
1. **Weekly/Daily**: Run browser scraper to discover any API changes
2. **Hourly**: Use cached API endpoints for fast scraping
3. **On Failure**: Fall back to browser scraper

### Implementation
```javascript
class HybridScraper {
  async scrape() {
    try {
      // Try fast API method first
      return await this.apiScrape();
    } catch (error) {
      console.log('API failed, falling back to browser');
      return await this.browserScrape();
    }
  }
  
  async discoverAPIs() {
    // Run browser scraper and log all API calls
    const apis = await this.browserScrapeWithLogging();
    this.cacheAPIStructure(apis);
  }
}
```

### Pros
- ✅ Best of both worlds (speed + reliability)
- ✅ Adaptive to changes
- ✅ Reduces browser usage

### Cons
- ⚠️ More complex architecture
- ⚠️ Requires state management
- ⚠️ Two implementations to maintain

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 5/5 | Multiple fallbacks |
| **Speed** | 4/5 | Fast with API, slower fallback |
| **Maintainability** | 3/5 | Two systems to maintain |
| **Hackiness** | 2/5 | Smart but not hacky |
| **Data Completeness** | 5/5 | Full coverage |

**Total Score**: 19/25 (Best long-term approach)

---

## Recommended Implementation Strategy

### Immediate (Week 1)
**Method 1**: Test existing Python scraper
- Set up Python environment
- Run scraper and validate output
- Document any issues or missing data

### Short-term (Week 2-3)
**Method 3**: Discover and document APIs
- Use existing scraper's network logging
- Extract API endpoints and request formats
- Create API replication script

### Medium-term (Month 1)
**Method 6**: Implement hybrid approach
- Keep browser scraper for validation
- Use direct API for regular scrapes
- Add monitoring and fallback logic

### Long-term Maintenance
- Monitor for platform changes
- Update API endpoints as needed
- Maintain both browser and API methods

---

## Summary Comparison

| Method | Score | Use Case |
|--------|-------|----------|
| **#1: Existing Scraper** | 18/25 | **Start here** - Proven |
| #2: HTML Scraping | 13/25 | Skip - Won't work |
| **#3: API Discovery** | 19/25 | **Next step** - Optimization |
| #4: Enhanced Quantity | 18/25 | Supplement |
| #5: Category Parallel | 18/25 | Optimization |
| **#6: Hybrid** | 19/25 | **Best long-term** |

**Recommendation**: 
1. Test Method #1 (existing scraper)
2. Discover APIs (Method #3)
3. Implement hybrid approach (Method #6)

---

