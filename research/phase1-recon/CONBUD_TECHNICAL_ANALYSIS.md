# Conbud LES Technical Analysis

## Platform: Dutchie Embedded (React SPA)

### Discovery
- **URL**: https://conbud.com/stores/conbud-les
- **Base API**: https://api.dutchie.com
- **Personalization API**: https://api.dutchie.com/personalize
- **Assets**: https://assets2.dutchie.com

### Configuration (from window.reactEnv)
```javascript
{
  "dispensaryId": "6430f42042cf3c004e37f0f8",
  "chainId": "conbud",
  "retailerId": "7d9a369e-6b29-4ccb-84c8-e802e28ae23e",
  "enterpriseId": "66033851-a3df-4ef5-b6d9-7ebe3770b7f0",
  "apiUrl": "https://api.dutchie.com",
  "adminUrl": "https://admin.dutchie.com",
  "consumerUrl": "https://dutchie.com"
}
```

### Technical Stack
- **Framework**: Next.js (SSG/SSR)
- **Build ID**: mc4_xNwY3nQhPLIGTo5Yq
- **Rendering**: Client-side React (`<div id="__next"></div>`)
- **Data Loading**: GraphQL via api.dutchie.com
- **Protection**: Turnstile CAPTCHA (siteKey: 0x4AAAAAAA1_LIO4cx5r-Yf4)

### HTML Structure
```html
<body>
  <div id="__next"></div>
  <script id="__NEXT_DATA__" type="application/json">
    {"props":{"pageProps":{}},"page":"/stores/[cName]","query":{},"buildId":"mc4_xNwY3nQhPLIGTo5Yq"}
  </script>
</body>
```

### Challenges Identified

#### 1. Client-Side Rendering
- **Problem**: All product data loaded via JavaScript
- **Impact**: Simple curl/HTML parsing won't work
- **Solution**: Requires browser automation or API interception

#### 2. GraphQL API
- **Problem**: Need to reverse-engineer query structure
- **Impact**: Direct API access requires proper query format
- **Solution**: Monitor network requests or use browser automation

#### 3. Authentication/Headers
- **Problem**: API likely requires specific headers/tokens
- **Impact**: Simple curl requests may be blocked
- **Solution**: Extract headers from browser session

#### 4. CAPTCHA Protection
- **Problem**: Turnstile may trigger on automation
- **Impact**: Could block headless browser access
- **Solution**: Use stealth mode, rotate IPs, or human-like behavior

## Scraping Approaches (Ranked by Feasibility)

### 1. ✅ Browser Automation with Network Interception (RECOMMENDED)
**Method**: Use Playwright/Puppeteer to load page and intercept GraphQL responses
- **Pros**: 
  - Guaranteed to work (executes real JavaScript)
  - Can extract full data structure from API responses
  - Can handle dynamic content
  - Bypasses most anti-bot measures
- **Cons**: 
  - Slower than direct API calls
  - Requires browser environment
  - More resource-intensive
- **Implementation Complexity**: Medium
- **Reliability**: Very High

### 2. ✅ GraphQL API Replication
**Method**: Reverse-engineer GraphQL queries and replicate them
- **Pros**:
  - Fast (direct API calls)
  - Lightweight
  - Structured data format
- **Cons**:
  - Requires reverse engineering
  - May need authentication tokens
  - Queries could change
- **Implementation Complexity**: High (initial setup), Low (maintenance)
- **Reliability**: High (if we get the queries right)

### 3. ⚠️  Server-Side Rendering Extraction
**Method**: Check if Dutchie provides any SSR/SSG content
- **Pros**:
  - Would be fast if available
  - Simple parsing
- **Cons**:
  - Unlikely to exist (Next.js exports seem static)
  - Current page shows empty `__next` div
- **Implementation Complexity**: N/A
- **Reliability**: Low (probably not available)

### 4. ❌ Direct HTML Parsing
**Method**: Parse static HTML
- **Pros**: Simple, fast
- **Cons**: **WILL NOT WORK** - no product data in static HTML
- **Implementation Complexity**: Easy
- **Reliability**: None

## Recommended Implementation Strategy

### Phase 1: Browser-Based Network Interception
1. Use Playwright to load the Conbud store page
2. Intercept all GraphQL requests/responses to api.dutchie.com
3. Extract product data from intercepted JSON responses
4. Save GraphQL query structure for Phase 2

### Phase 2: Direct GraphQL API (if possible)
1. Use captured GraphQL queries from Phase 1
2. Test direct API calls with proper headers
3. If successful, switch to direct API for speed
4. Fall back to browser automation if blocked

## Required Data Extraction

### Product Fields (Target)
- ✅ Product ID
- ✅ Name
- ✅ Brand
- ✅ Category
- ✅ Price
- ✅ THC %
- ✅ CBD %
- ✅ Image URL
- ⚠️  Inventory/Stock (may require cart probing)
- ⚠️  Quantity available (may not be in product listings)

### Sample GraphQL Query Structure (Estimated)
```graphql
query GetDispensaryMenu($dispensaryId: ID!, $category: String) {
  dispensary(id: $dispensaryId) {
    id
    name
    products(category: $category) {
      id
      name
      brand {
        id
        name
      }
      category
      subcategory
      strainType
      price
      variants {
        id
        option
        price
        thcPercent
        cbdPercent
      }
      image
      potencyCbd {
        formatted
        unit
      }
      potencyThc {
        formatted
        unit
      }
      inventory {
        available
        quantity
      }
    }
  }
}
```

## Next Steps
1. Set up proper browser automation environment (install dependencies)
2. Create network interception scraper
3. Extract and document actual GraphQL schema
4. Test reliability and data completeness
