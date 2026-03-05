# Conbud LES - Scraping Method Analysis

**Platform**: Dutchie (React SPA + GraphQL)
**Complexity**: ⭐⭐⭐⭐⭐ (Very High)
**URL**: https://conbud.com/stores/conbud-les

---

## Method 1: Browser Automation with Network Interception ⭐ RECOMMENDED

### Description
Use Playwright to load the page and intercept GraphQL API requests/responses to extract product data directly from the network traffic.

### Implementation Approach
```javascript
// Playwright with network interception
const page = await browser.newPage();

// Capture API responses
const products = [];
page.on('response', async (response) => {
  if (response.url().includes('api.dutchie.com/graphql')) {
    const data = await response.json();
    if (data.data?.dispensary?.products) {
      products.push(...data.data.dispensary.products);
    }
  }
});

// Navigate and wait for network
await page.goto('https://conbud.com/stores/conbud-les');
await page.waitForLoadState('networkidle');
```

### Pros
- ✅ Guaranteed to work (executes real JavaScript)
- ✅ Captures actual API responses with full data
- ✅ Handles dynamic loading automatically
- ✅ Can extract GraphQL schema for Method 2
- ✅ Bypasses most anti-bot measures (real browser)

### Cons
- ❌ Slower than direct API calls (~10-15s per scrape)
- ❌ Resource-intensive (requires browser)
- ❌ May trigger CAPTCHA if detected as automation
- ❌ Requires proper browser environment

### Data Fields Extractable
- ✅ Product ID, Name, Brand
- ✅ Category, Subcategory
- ✅ Price (with variants)
- ✅ THC %, CBD % (potency objects)
- ✅ Image URL
- ⚠️ Inventory (if in GraphQL response)
- ✅ All GraphQL response fields

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 5/5 | Will always work if page loads |
| **Speed** | 2/5 | Slow due to full browser render |
| **Maintainability** | 4/5 | Resilient to HTML changes |
| **Hackiness** | 2/5 | Standard browser automation |
| **Data Completeness** | 5/5 | Full API data available |

**Total Score**: 18/25

---

## Method 2: Direct GraphQL API Replication

### Description
Reverse-engineer the GraphQL queries from Method 1, then make direct HTTP requests to the Dutchie API with proper headers and query structure.

### Implementation Approach
```javascript
// Direct GraphQL query
const query = `
  query GetProducts($dispensaryId: ID!, $filters: ProductFilters) {
    dispensary(id: $dispensaryId) {
      id
      name
      products(filters: $filters) {
        id
        name
        brand { name }
        category
        price
        variants {
          id
          price
          potencyThc { formatted }
          potencyCbd { formatted }
        }
        image
      }
    }
  }
`;

const response = await axios.post('https://api.dutchie.com/graphql', {
  operationName: 'GetProducts',
  variables: { dispensaryId: '6430f42042cf3c004e37f0f8' },
  query
}, {
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': '...',
    // Other headers from browser inspection
  }
});
```

### Pros
- ✅ Fast (~1-2s per scrape)
- ✅ Lightweight (no browser needed)
- ✅ Structured data format
- ✅ Can paginate/filter easily
- ✅ Low resource usage

### Cons
- ❌ Requires reverse engineering GraphQL schema
- ⚠️ May need authentication headers/tokens
- ⚠️ API might have rate limiting
- ⚠️ Query structure could change
- ⚠️ May detect non-browser requests

### Prerequisites
1. Extract exact GraphQL query from Method 1
2. Identify required headers (auth tokens, cookies, etc.)
3. Test query variations for different categories
4. Implement proper error handling

### Data Fields Extractable
- ✅ Same as Method 1 (if query is correct)
- Depends on GraphQL schema knowledge

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 4/5 | High if queries are correct |
| **Speed** | 5/5 | Very fast direct API |
| **Maintainability** | 3/5 | Breaks if API changes |
| **Hackiness** | 3/5 | Moderate - API replication |
| **Data Completeness** | 5/5 | Full schema access |

**Total Score**: 20/25 (Best if successful)

---

## Method 3: Dutchie Public API (If Exists)

### Description
Check if Dutchie provides a public/documented API for dispensary data that Conbud might be using.

### Investigation Steps
1. Check Dutchie developer docs: https://dutchie.com/developers
2. Look for API documentation or partnerships
3. Test known Dutchie API endpoints
4. Check for API keys in page source

### Pros
- ✅ Official, documented approach
- ✅ Likely stable and supported
- ✅ May have higher rate limits
- ✅ Legal/ethical clarity

### Cons
- ⚠️ May not exist or be public
- ⚠️ Might require API key registration
- ⚠️ Could have usage restrictions
- ⚠️ May not have all data fields

### Status
- 🔍 **REQUIRES INVESTIGATION**
- Check if public API exists
- If yes, this becomes Method 1

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 5/5 | If official API exists |
| **Speed** | 5/5 | Direct API access |
| **Maintainability** | 5/5 | Officially supported |
| **Hackiness** | 1/5 | Not hacky at all |
| **Data Completeness** | ?/5 | Unknown until investigated |

**Total Score**: 16+/25 (Conditional on existence)

---

## Method 4: LocalStorage/SessionStorage Inspection 🔧

### Description
Dutchie might store product data in browser storage for caching. Inspect localStorage/sessionStorage after page load.

### Implementation Approach
```javascript
// After page loads, inspect storage
const storageData = await page.evaluate(() => {
  return {
    localStorage: {...localStorage},
    sessionStorage: {...sessionStorage}
  };
});

// Look for product data in stored objects
const products = extractProductsFromStorage(storageData);
```

### Pros
- ✅ Fast if data is cached
- ✅ Simple extraction
- ✅ No network requests needed

### Cons
- ⚠️ Data may not be complete
- ⚠️ May not include all products
- ⚠️ Format could be complex/encoded
- ❌ Still requires browser automation

### Investigation Needed
- Check if Dutchie caches products locally
- Identify storage keys and format
- Test data completeness

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 2/5 | May not have all data |
| **Speed** | 4/5 | Fast if available |
| **Maintainability** | 2/5 | Storage format may change |
| **Hackiness** | 4/5 | Clever but risky |
| **Data Completeness** | 2/5 | Likely incomplete |

**Total Score**: 14/25

---

## Method 5: React Component State Extraction 🔧🔧

### Description
Extract product data directly from React component state/props in the browser's JavaScript runtime.

### Implementation Approach
```javascript
// Inject script to access React internals
const products = await page.evaluate(() => {
  // Find React root
  const root = document.querySelector('#__next')
    ?._reactRootContainer
    ?._internalRoot
    ?.current;
  
  // Traverse React fiber tree to find product state
  function findProductState(fiber) {
    // ... traverse fiber tree ...
    // Look for component with product data
  }
  
  return findProductState(root);
});
```

### Pros
- ✅ Direct access to app state
- ✅ All rendered data available
- ✅ No network parsing needed

### Cons
- ❌ Very hacky and fragile
- ❌ React internals can change
- ❌ Complex to implement
- ❌ Breaks with React updates
- ❌ Still requires browser

### Risk Assessment
- ⚠️ **HIGH RISK** - Very likely to break
- Only use as last resort

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 1/5 | Extremely fragile |
| **Speed** | 3/5 | Moderate |
| **Maintainability** | 1/5 | Breaks with any update |
| **Hackiness** | 5/5 | Very hacky |
| **Data Completeness** | 4/5 | If successful, complete |

**Total Score**: 14/25 (Not recommended)

---

## Method 6: Service Worker Interception 🔧

### Description
If Dutchie uses a Service Worker for caching, intercept and extract cached product data.

### Investigation Steps
1. Check if Service Worker is registered
2. Inspect SW cache storage
3. Extract product data from cache

### Implementation
```javascript
// Check for service worker
const swData = await page.evaluate(async () => {
  const registration = await navigator.serviceWorker.getRegistration();
  const cache = await caches.open('dutchie-products');
  const keys = await cache.keys();
  // ... extract cached responses
});
```

### Pros
- ✅ May have pre-cached data
- ✅ Fast if available

### Cons
- ⚠️ May not be implemented
- ⚠️ Cache may be incomplete
- ❌ Still requires browser

### Status
- 🔍 **REQUIRES INVESTIGATION**

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 2/5 | If SW exists |
| **Speed** | 4/5 | Fast cache access |
| **Maintainability** | 2/5 | Cache strategy may change |
| **Hackiness** | 4/5 | Clever but risky |
| **Data Completeness** | 3/5 | May be incomplete |

**Total Score**: 15/25

---

## Method 7: Puppeteer with CDP (Chrome DevTools Protocol) 🔧

### Description
Use Puppeteer with CDP to intercept network requests at a lower level than Playwright.

### Advantages over Playwright
- More control over network layer
- Can modify requests/responses
- Access to lower-level browser events

### Implementation
```javascript
const client = await page.target().createCDPSession();
await client.send('Network.enable');

client.on('Network.responseReceived', async (event) => {
  if (event.response.url.includes('dutchie')) {
    const responseBody = await client.send('Network.getResponseBody', {
      requestId: event.requestId
    });
    // Process response
  }
});
```

### Pros
- ✅ More control than Playwright
- ✅ Can intercept at protocol level
- ✅ Access to all network events

### Cons
- ❌ More complex setup
- ❌ Similar speed to Method 1
- ❌ Still requires browser

### Scoring
| Metric | Score | Notes |
|--------|-------|-------|
| **Reliability** | 5/5 | Very reliable |
| **Speed** | 2/5 | Same as browser automation |
| **Maintainability** | 4/5 | Resilient |
| **Hackiness** | 3/5 | More technical |
| **Data Completeness** | 5/5 | Full access |

**Total Score**: 19/25

---

## Recommended Implementation Strategy

### Phase 1: Quick Win (Method 1)
1. **Implement browser automation with network interception**
2. Get working scraper ASAP
3. Extract and document GraphQL queries
4. Validate data completeness

### Phase 2: Optimization (Method 2)
1. Use captured GraphQL queries from Phase 1
2. Implement direct API calls
3. Test reliability and rate limits
4. Optimize for speed

### Phase 3: Fallback (If needed)
1. Keep Method 1 as backup
2. Implement retry logic
3. Add error handling

---

## Summary Comparison

| Method | Score | Recommended Use |
|--------|-------|----------------|
| **#1: Browser + Network Intercept** | 18/25 | **Primary** - Start here |
| **#2: Direct GraphQL API** | 20/25 | **Best** - If queries extracted |
| **#3: Public API** | 16+/25 | **Ideal** - If exists |
| #4: LocalStorage | 14/25 | Skip - Not worth it |
| #5: React State | 14/25 | Avoid - Too fragile |
| #6: Service Worker | 15/25 | Investigate only |
| #7: CDP/Puppeteer | 19/25 | Alternative to #1 |

**Recommendation**: Start with Method #1, extract queries for Method #2, investigate Method #3.

---

