# Test Fixtures Documentation

## Overview

Test fixtures are sample data files used to simulate real-world scraping scenarios without hitting live websites. This ensures fast, reliable, deterministic tests.

---

## Table of Contents

1. [Fixture Files](#fixture-files)
2. [Creating Fixtures](#creating-fixtures)
3. [Using Fixtures](#using-fixtures)
4. [Maintenance](#maintenance)
5. [Best Practices](#best-practices)

---

## Fixture Files

### Current Fixtures

#### `gotham-sample.html`

**Source:** Gotham NYC (https://gotham.nyc/menu)  
**Captured:** 2026-03-05  
**Purpose:** Test Gotham scraper extraction strategies  
**Size:** ~1.5 KB

**Contents:**
- 1 product with JSON-LD structured data (Purple Haze)
- 1 product with HTML-only data (Sour Diesel Vape)
- 1 out-of-stock product (OG Kush Pre-Roll)

**Test Coverage:**
- JSON-LD extraction
- HTML parsing (multiple selector strategies)
- Stock status detection
- Potency (THC/CBD) extraction
- Price parsing
- Category classification

**Example Structure:**
```html
<script type="application/ld+json">
{
  "@type": "Product",
  "name": "Purple Haze Premium Flower",
  "sku": "GTH-001",
  "brand": { "name": "Gotham Growers" },
  "offers": {
    "price": "45.00",
    "availability": "InStock"
  }
}
</script>

<div class="dt-product">
  <h2>Purple Haze Premium Flower</h2>
  <div class="dt-price">$45.00</div>
  <div>THC: 24.5% CBD: 0.3%</div>
</div>
```

---

#### `housing-works-sample.html`

**Source:** Housing Works Cannabis Co. (https://hwcannabis.co/menu/broadway/)  
**Captured:** 2026-03-05  
**Purpose:** Test Housing Works scraper (Blaze platform)  
**Size:** ~1 KB

**Contents:**
- 1 complete product (Lemon Haze)
- 1 minimal product (Blue Dream Vape)
- 1 out-of-stock product (Strawberry Gummies)
- 1 disabled add-to-cart product (Gelato Pre-Roll)

**Test Coverage:**
- Multi-selector strategy (`.product`, `.product-item`, `.menu-item`)
- Stock detection (multiple patterns)
- Price parsing
- Potency extraction
- Category extraction
- Weight/size parsing

**Example Structure:**
```html
<div class="product">
  <h3 class="product-name">Lemon Haze Flower</h3>
  <div class="brand">Green Thumb Industries</div>
  <span class="price">$50.00</span>
  <div class="thc">THC: 22.5%</div>
  <div class="cbd">CBD: 0.5%</div>
</div>
```

---

#### `conbud-api-response.json`

**Source:** Conbud LES / Dutchie API (https://api.dutchie.com/graphql)  
**Captured:** 2026-03-05  
**Purpose:** Test Conbud API scraper  
**Size:** ~2.6 KB

**Contents:**
- 3 products (Gorilla Glue #4, Sour Diesel Cart, Blue Dream Pre-Roll)
- Multiple variants (different sizes/prices)
- Complete potency data
- Effects and terpenes
- In-stock and out-of-stock examples

**Test Coverage:**
- GraphQL response parsing
- Product normalization
- Variant handling
- Brand extraction
- Potency structure conversion

**Example Structure:**
```json
{
  "data": {
    "filteredProducts": {
      "products": [
        {
          "id": "prod_123",
          "name": "Gorilla Glue #4",
          "brand": {
            "id": "brand_1",
            "name": "Premium Cannabis Co."
          },
          "category": "FLOWER",
          "potencyThc": {
            "formatted": "25.5%",
            "range": [25.5, 26.0]
          },
          "price": 55.00,
          "variants": [
            {
              "id": "var_1",
              "option": "3.5g",
              "price": 55.00
            }
          ],
          "inStock": true,
          "quantity": 25
        }
      ]
    }
  }
}
```

---

## Creating Fixtures

### Step 1: Capture Real Data

#### For HTML Fixtures

```bash
# Capture full page
curl 'https://example.com/menu' > tests/fixtures/example-sample.html

# With headers (for age gates)
curl -H 'Cookie: age_verified=1' \
     -H 'User-Agent: Mozilla/5.0...' \
     'https://example.com/menu' > tests/fixtures/example-sample.html

# Using browser DevTools
# 1. Open page in browser
# 2. Open DevTools > Network tab
# 3. Refresh page
# 4. Find HTML request
# 5. Right-click > Copy > Copy response
# 6. Paste into fixture file
```

#### For JSON/API Fixtures

```bash
# Capture GraphQL response
curl -X POST 'https://api.example.com/graphql' \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ products { id name } }"}' > tests/fixtures/example-api-response.json

# Using browser DevTools
# 1. Open Network tab
# 2. Filter: XHR/Fetch
# 3. Find API call
# 4. Right-click > Copy > Copy response
# 5. Paste into fixture file
```

### Step 2: Sanitize Data

**Remove:**
- Personal information (emails, phone numbers)
- API keys, tokens, secrets
- Real addresses (if not public dispensaries)
- Payment information
- Session IDs

**Preserve:**
- HTML structure (classes, IDs)
- Product names (public data)
- Prices (public data)
- THC/CBD percentages (public data)

### Step 3: Minimize Size

**Keep:**
- Representative examples of each product type
- Edge cases (out of stock, missing data)
- Different HTML structures

**Remove:**
- Duplicate products
- Unnecessary page elements (headers, footers)
- External scripts
- Large images (keep URLs, remove base64)

### Step 4: Document

Add comment at top of fixture:

```html
<!--
  Fixture: gotham-sample.html
  Source: https://gotham.nyc/menu
  Captured: 2026-03-05
  Purpose: Test multi-strategy extraction
  Contains: 3 products (1 JSON-LD, 2 HTML)
-->
```

---

## Using Fixtures

### In Tests

```javascript
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fixturesDir = join(__dirname, '../../fixtures');

// Load fixture
const html = readFileSync(
  join(fixturesDir, 'gotham-sample.html'),
  'utf-8'
);

// Use in test
it('should parse fixture', () => {
  const products = scraper.parseProducts(html);
  expect(products.length).toBeGreaterThan(0);
});
```

### Mocking HTTP Requests

```javascript
import { vi } from 'vitest';

// Mock axios
vi.spyOn(scraper, 'fetchPage').mockResolvedValue(fixtureHTML);

// Mock with multiple fixtures
const fixtures = {
  'https://example.com/menu': fixtureHTML1,
  'https://example.com/category/flower': fixtureHTML2,
};

vi.spyOn(scraper, 'fetchPage').mockImplementation((url) => {
  return Promise.resolve(fixtures[url] || '<html></html>');
});
```

### Fixture Helpers

```javascript
// tests/helpers/fixtures.mjs
export function loadFixture(name) {
  return readFileSync(
    join(fixturesDir, `${name}.html`),
    'utf-8'
  );
}

// In tests
import { loadFixture } from '../helpers/fixtures.mjs';

const html = loadFixture('gotham-sample');
```

---

## Maintenance

### When to Update Fixtures

1. **Website structure changes**
   - HTML class names change
   - New product fields added
   - Different layout

2. **New edge cases discovered**
   - Unusual price formats
   - Missing data scenarios
   - Error pages

3. **New features added**
   - Testing new extraction logic
   - New data fields

### Update Process

1. **Capture new data:**
   ```bash
   curl 'https://example.com/menu' > tests/fixtures/example-sample-new.html
   ```

2. **Compare with old fixture:**
   ```bash
   diff tests/fixtures/example-sample.html tests/fixtures/example-sample-new.html
   ```

3. **Update fixture:**
   - Replace old file, or
   - Create dated version: `example-sample-2026-03-05.html`

4. **Update tests:**
   - Fix any broken assertions
   - Add tests for new fields

5. **Commit changes:**
   ```bash
   git add tests/fixtures/
   git commit -m "Update fixtures: website structure changed"
   ```

### Fixture Versioning

For historical tracking:

```
tests/fixtures/
├── gotham-sample.html           # Current version
├── gotham-sample-2026-03-05.html  # Dated snapshot
└── gotham-sample-2026-02-01.html  # Previous version
```

---

## Best Practices

### 1. Representative Data

Include examples of:
- In-stock products
- Out-of-stock products
- Products with full data
- Products with missing data
- Different categories
- Different price ranges

### 2. Realistic but Minimal

- Use real HTML structure
- Keep only necessary elements
- Remove duplicates
- Aim for <5 KB per fixture

### 3. Privacy First

**Never include:**
- User emails
- Phone numbers (unless public)
- Credit card info
- Session tokens
- Private API keys

### 4. Self-Documenting

Add comments:
```html
<!-- Product 1: Complete data -->
<div class="product">...</div>

<!-- Product 2: Missing optional fields -->
<div class="product">...</div>

<!-- Product 3: Out of stock -->
<div class="product out-of-stock">...</div>
```

### 5. Test Edge Cases

Include fixtures for:
- Empty pages
- Malformed HTML
- Missing fields
- Unusual formatting
- Error responses

**Example: `gotham-empty.html`**
```html
<html>
<body>
  <div class="menu-container">
    <!-- No products -->
  </div>
</body>
</html>
```

**Example: `conbud-error.json`**
```json
{
  "errors": [
    {
      "message": "Dispensary not found",
      "code": "NOT_FOUND"
    }
  ]
}
```

### 6. Keep in Sync

When scraper changes:
1. Update fixtures
2. Update tests
3. Document changes

---

## Fixture Checklist

Before committing a fixture:

- [ ] Real data from target site
- [ ] Sanitized (no sensitive info)
- [ ] Minimized (only necessary data)
- [ ] Documented (header comment)
- [ ] Tested (all tests pass)
- [ ] Representative (covers edge cases)
- [ ] Privacy-safe (no PII)
- [ ] Self-documenting (inline comments)

---

## Example: Adding New Fixture

### Scenario: Add support for new dispensary "GreenLeaf"

1. **Capture data:**
   ```bash
   curl 'https://greenleaf.com/menu' > tests/fixtures/greenleaf-sample.html
   ```

2. **Sanitize:**
   - Remove `<script>` for analytics
   - Remove large inline images
   - Keep product structure

3. **Add header comment:**
   ```html
   <!--
     Fixture: greenleaf-sample.html
     Source: https://greenleaf.com/menu
     Captured: 2026-03-05
     Purpose: Test GreenLeaf scraper (WooCommerce platform)
     Contains: 5 products (3 in-stock, 2 out-of-stock)
   -->
   ```

4. **Create test file:**
   ```javascript
   // tests/unit/scrapers/greenleaf.test.mjs
   import { loadFixture } from '../helpers/fixtures.mjs';
   import GreenLeafScraper from '../../../scrapers/greenleaf/scraper.mjs';

   describe('GreenLeafScraper', () => {
     it('should parse products', () => {
       const html = loadFixture('greenleaf-sample');
       const products = scraper.parseProducts(html);
       expect(products).toHaveLength(5);
     });
   });
   ```

5. **Commit:**
   ```bash
   git add tests/fixtures/greenleaf-sample.html tests/unit/scrapers/greenleaf.test.mjs
   git commit -m "Add GreenLeaf scraper fixtures and tests"
   ```

---

## Troubleshooting

### Fixture Not Loading

**Error:** `ENOENT: no such file or directory`

**Fix:**
```javascript
// Check path resolution
console.log(__dirname);
console.log(join(__dirname, '../../fixtures/gotham-sample.html'));

// Use absolute path
const fixturePath = join(__dirname, '../../fixtures/gotham-sample.html');
```

### Fixture Too Large

**Error:** Tests slow or OOM

**Fix:**
- Remove duplicate products
- Keep only 3-5 representative examples
- Remove base64 images
- Minify HTML (remove whitespace)

### Fixture Out of Date

**Error:** Tests fail after website changes

**Fix:**
1. Re-capture fixture
2. Update expected outputs
3. Add test for new structure

---

## Resources

- **Fixtures Location:** `tests/fixtures/`
- **Test Helpers:** `tests/helpers/fixtures.mjs`
- **Testing Guide:** `TESTING.md`

---

**Last Updated:** 2026-03-05  
**Questions?** See TESTING.md or open an issue.
