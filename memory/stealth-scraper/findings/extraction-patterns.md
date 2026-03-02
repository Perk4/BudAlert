# Extraction Patterns - Medium Custom Sites

## Successful Patterns

### Server-Side Rendering Extraction (Travel Agency)
**Pattern**: React/Remix SSR with embedded JSON data
```javascript
// Look for embedded context data
window.__remixContext = {
  "state": {
    "loaderData": {
      "routes/menu": {
        "products": [
          {
            "_17": "product_id",
            "_33": "product_name", 
            "_95": "brand",
            "_102": price,
            "_109": "thc_percentage",
            "_111": "cbd_percentage"
          }
        ]
      }
    }
  }
}
```

**Extraction Method**:
1. Parse HTML for `window.__remixContext` JavaScript assignment
2. Extract JSON data using regex: `window\.__remixContext\s*=\s*({.+?});`
3. Navigate object structure to find product arrays
4. Map obfuscated keys to product attributes

**Success Rate**: 90%+
**Data Quality**: Excellent - complete product information
**Challenges**: Obfuscated property names require reverse engineering

## Failed Patterns (Require Browser Automation)

### WordPress AJAX Loading
**Pattern**: WordPress with JavaScript product loading
```javascript
// Common WordPress AJAX patterns
wp.ajax.post('load_products', {
  action: 'get_dispensary_products',
  nonce: wpAjax.nonce
});

// WooCommerce REST API
/wp-json/wc/v3/products
```

**Why Failed**: Products loaded after initial page render
**Solution Required**: Playwright with wait conditions
**Retry Strategy**: 
1. Wait for AJAX completion: `page.waitForSelector('.product-grid')`
2. Monitor network requests for API endpoints
3. Extract data from rendered DOM

### Age Verification Gates
**Pattern**: JavaScript modal blocking content access
```javascript
// Age verification popup patterns
if (!getCookie('age_verified')) {
  showAgeGate();
  blockContent();
}

// DOM manipulation
document.getElementById('main-content').style.display = 'none';
```

**Why Failed**: Content hidden until age verification
**Solution Required**: Browser automation with form interaction
**Bypass Strategy**:
1. Detect age gate: `page.locator('[class*="age"]')`
2. Fill form: `page.fill('#birth-year', '1990')`
3. Submit: `page.click('button[type="submit"]')`
4. Wait for content: `page.waitForSelector('.products')`

### CSRF Protection (Rails)
**Pattern**: Rails CSRF token requirement
```html
<meta name="csrf-token" content="abc123..." />
<form action="/products">
  <input type="hidden" name="authenticity_token" value="abc123..." />
</form>
```

**Why Failed**: Requests rejected without valid session
**Solution Required**: Session management with token extraction
**Implementation**:
1. Extract CSRF token from meta tag
2. Include in all subsequent requests
3. Maintain session cookies

### Magento Enterprise Protection
**Pattern**: Enterprise e-commerce platform security
```javascript
// Customer session validation
if (!customer.isLoggedIn()) {
  require(['customerData'], function(customerData) {
    // Complex session handling
  });
}
```

**Why Failed**: Enterprise-grade bot detection and session requirements
**Solution Required**: Full browser simulation with customer session
**Approach**:
1. Create customer account or guest session
2. Navigate as real browser user
3. Extract data from rendered product pages

## Framework-Specific Approaches

### WordPress Sites (Gotham, Dazed, Green Apple)
**Common Structure**:
```html
<div class="products-container">
  <div class="product-item" data-product-id="123">
    <h3 class="product-name">Product Name</h3>
    <span class="price">$50.00</span>
    <span class="thc">THC: 25%</span>
  </div>
</div>
```

**Extraction Strategy**:
1. Browser automation required for all
2. Age gate handling for Dazed/Green Apple
3. Wait for JavaScript product loading
4. Extract from final rendered DOM

**Selectors**:
- Product containers: `.product-item`, `[class*="product"]`
- Names: `.product-name`, `.product-title`, `h3`
- Prices: `.price`, `[class*="price"]`, `.woocommerce-Price-amount`
- THC/CBD: Text patterns `THC\s*:?\s*([0-9.]+%?)`

### Rails Applications (Chelsea Cannabis)
**REST API Patterns**:
```
GET /api/products.json
GET /products.json
POST /search/products
```

**Headers Required**:
```
X-CSRF-Token: <token>
X-Requested-With: XMLHttpRequest
Cookie: _session_id=<session>
```

**Extraction Strategy**:
1. Load main page to get CSRF token
2. Attempt direct API access with token
3. Fall back to browser automation if API blocked
4. Parse JSON responses or rendered HTML

### Magento Sites (Verilife)
**GraphQL Endpoint**:
```graphql
query getProducts($filter: ProductAttributeFilterInput!) {
  products(filter: $filter) {
    items {
      name
      price_range {
        minimum_price {
          final_price {
            value
            currency
          }
        }
      }
      image {
        url
      }
    }
  }
}
```

**REST API Patterns**:
```
GET /rest/V1/products
GET /rest/V1/categories
```

**Extraction Strategy**:
1. Attempt GraphQL query (most efficient)
2. Try REST API endpoints
3. Browser automation as fallback
4. Handle store-specific routing (/ny/)

## Data Normalization Patterns

### Price Extraction
```regex
# Common price patterns
\$\s*[\d,]+\.?\d*           # $50.00, $1,200
[\d,]+\.?\d*\s*dollars?     # 50 dollars
price[\":\s]*([0-9.]+)      # JSON: "price": 50.00
```

### THC/CBD Content
```regex
# Cannabinoid patterns  
THC[:\s]*([0-9.]+%?)        # THC: 25.5%
CBD[:\s]*([0-9.]+%?)        # CBD: 0.5%
(\d+\.?\d*)%?\s*THC         # 25% THC
```

### Product Categories
```javascript
// Category normalization
const categoryMap = {
  'flower': 'FLOWER',
  'bud': 'FLOWER', 
  'edibles': 'EDIBLES',
  'gummies': 'EDIBLES',
  'vape': 'VAPORIZERS',
  'cart': 'VAPORIZERS',
  'concentrate': 'CONCENTRATES',
  'wax': 'CONCENTRATES'
};
```

## Recommended Tool Stack

### Browser Automation
```javascript
// Playwright configuration
const browser = await playwright.chromium.launch({
  headless: true,
  args: ['--disable-blink-features=AutomationControlled']
});

const context = await browser.newContext({
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  viewport: { width: 1366, height: 768 }
});
```

### Age Gate Handling
```javascript
// Generic age verification
async function handleAgeGate(page) {
  const ageGate = await page.locator('[class*="age"], [id*="age"]');
  if (await ageGate.isVisible()) {
    await page.selectOption('select[name*="year"]', '1990');
    await page.selectOption('select[name*="month"]', '01'); 
    await page.selectOption('select[name*="day"]', '01');
    await page.click('button[type="submit"], .age-submit');
    await page.waitForSelector('.products, .menu');
  }
}
```

### Product Data Extraction
```javascript
// Universal product extractor
async function extractProducts(page) {
  return await page.evaluate(() => {
    const products = [];
    const productElements = document.querySelectorAll(
      '.product-item, [class*="product"], .woocommerce-LoopProduct-link'
    );
    
    productElements.forEach(el => {
      const name = el.querySelector('h1, h2, h3, .product-name, .product-title')?.textContent?.trim();
      const price = el.querySelector('.price, [class*="price"]')?.textContent?.match(/\$[\d,]+\.?\d*/)?.[0];
      const thc = el.textContent.match(/THC[:\s]*([0-9.]+%?)/i)?.[1];
      const cbd = el.textContent.match(/CBD[:\s]*([0-9.]+%?)/i)?.[1];
      
      if (name) {
        products.push({ name, price, thc, cbd });
      }
    });
    
    return products;
  });
}
```