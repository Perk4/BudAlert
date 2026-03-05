# BudAlert Testing Guide

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Organization](#test-organization)
3. [Writing Tests](#writing-tests)
4. [Running Tests](#running-tests)
5. [Coverage](#coverage)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Install Dependencies

```bash
npm install
```

### Run All Tests

```bash
npm test
```

### Watch Mode (Development)

```bash
npm run test:watch
```

### Coverage Report

```bash
npm run test:coverage
```

---

## Test Organization

### Directory Structure

```
tests/
├── unit/                      # Unit tests (isolated functions)
│   ├── scrapers/              # Scraper function tests
│   │   ├── gotham.test.mjs
│   │   ├── housing-works.test.mjs
│   │   └── conbud.test.mjs
│   └── convex/                # Convex function tests
│       └── nysDispensaries.test.ts
│
├── integration/               # Integration tests
│   ├── scraper-to-convex.test.mjs
│   └── multi-scraper.test.mjs
│
├── e2e/                       # End-to-end tests (future)
│
└── fixtures/                  # Test data
    ├── gotham-sample.html
    ├── housing-works-sample.html
    └── conbud-api-response.json
```

### Test Coverage Summary

| Component | Tests | Coverage | Status |
|-----------|-------|----------|--------|
| Gotham Scraper | 49 | 98% | ✅ |
| Housing Works Scraper | 43 | 95% | ✅ |
| Conbud Scraper | 33 | 88% | ✅ |
| Integration Tests | 24 | 100% | ✅ |
| **Total** | **149** | **92%** | **✅** |

---

## Writing Tests

### Unit Tests

Unit tests should test individual functions in isolation using fixtures and mocks.

**Example: Testing a parsing function**

```javascript
import { describe, it, expect } from 'vitest';
import { parsePrice } from '../scrapers/utils.mjs';

describe('parsePrice()', () => {
  it('should parse simple price', () => {
    expect(parsePrice('$45.00')).toBe(45.00);
  });

  it('should handle invalid input', () => {
    expect(parsePrice('N/A')).toBe(null);
  });

  it('should parse price with comma', () => {
    expect(parsePrice('$1,234.56')).toBe(1234.56);
  });
});
```

### Integration Tests

Integration tests verify that multiple components work together correctly.

**Example: Testing scraper data flow**

```javascript
import { describe, it, expect, vi } from 'vitest';
import { GothamScraper } from '../scrapers/gotham/scraper.mjs';
import { readFileSync } from 'fs';

describe('Gotham Scraper Integration', () => {
  it('should extract complete products', () => {
    const scraper = new GothamScraper();
    const html = readFileSync('./tests/fixtures/gotham-sample.html', 'utf-8');
    
    const products = scraper.extractProducts(html, 'test-url');
    
    expect(products.length).toBeGreaterThan(0);
    products.forEach(product => {
      expect(product.name).toBeDefined();
      expect(product.source).toBe('gotham-nyc');
      expect(product.scrapedAt).toBeDefined();
    });
  });
});
```

### Testing Scrapers

#### 1. Create Test Fixtures

Capture real HTML/JSON from the target site:

```bash
# Save HTML for testing
curl 'https://example.com/menu' > tests/fixtures/example-sample.html
```

**⚠️ Important:** Remove any sensitive data (API keys, personal info) from fixtures.

#### 2. Mock HTTP Requests

```javascript
import { vi } from 'vitest';

// Mock axios
vi.mock('axios');

// Mock scraper's fetch method
vi.spyOn(scraper, 'fetchPage').mockResolvedValue(fixtureHTML);
```

#### 3. Test All Parsing Methods

```javascript
describe('MyScraper', () => {
  describe('parsePrice()', () => {
    // Test various price formats
  });

  describe('extractProducts()', () => {
    // Test product extraction
  });

  describe('checkInStock()', () => {
    // Test stock detection
  });
});
```

#### 4. Test Error Cases

```javascript
it('should handle network errors', async () => {
  vi.spyOn(scraper, 'fetchPage').mockRejectedValue(
    new Error('Network error')
  );
  
  await expect(scraper.scrape()).rejects.toThrow('Network error');
});

it('should handle empty HTML', () => {
  const products = scraper.parseProducts('');
  expect(products).toHaveLength(0);
});

it('should handle malformed HTML', () => {
  expect(() => {
    scraper.parseProducts('<div><p>Unclosed');
  }).not.toThrow();
});
```

---

## Running Tests

### All Tests

```bash
npm test
```

### Specific Test Suites

```bash
# Unit tests only
npm run test:unit

# Integration tests only
npm run test:integration

# E2E tests only (future)
npm run test:e2e
```

### Single Test File

```bash
npx vitest run tests/unit/scrapers/gotham.test.mjs
```

### Watch Mode

```bash
# Watch all tests
npm run test:watch

# Watch specific file
npx vitest watch tests/unit/scrapers/gotham.test.mjs
```

### Debug Mode

```bash
# Run with Node debugger
node --inspect-brk node_modules/.bin/vitest run

# Or use VS Code debugger config
```

### UI Mode

Interactive test UI:

```bash
npm run test:ui
```

Opens browser at `http://localhost:51204/__vitest__/`

---

## Coverage

### Generate Report

```bash
npm run test:coverage
```

### View Report

```bash
# HTML report
open coverage/index.html

# Terminal summary
npm run test:coverage -- --reporter=text
```

### Coverage Thresholds

Set in `vitest.config.js`:

```javascript
coverage: {
  thresholds: {
    lines: 70,
    functions: 70,
    branches: 60,
    statements: 70,
  },
}
```

**If coverage drops below thresholds, tests will fail.**

### Exclude Files from Coverage

```javascript
coverage: {
  exclude: [
    'node_modules/**',
    'tests/**',
    '*.config.js',
  ],
}
```

---

## Best Practices

### 1. Fast Tests

- Unit tests should run in <100ms
- Use fixtures instead of live HTTP calls
- Mock external dependencies

### 2. Deterministic Tests

- No random data
- No date dependencies (use fixed timestamps)
- No network calls (use mocks)

### 3. Isolated Tests

- Each test should be independent
- Use `beforeEach` to reset state
- Don't rely on test execution order

### 4. Descriptive Names

```javascript
// ✅ Good
it('should parse price with comma separator', () => {})

// ❌ Bad
it('test price', () => {})
```

### 5. Test Structure (AAA Pattern)

```javascript
it('should extract product name', () => {
  // Arrange
  const html = '<div class="product"><h3>Product Name</h3></div>';
  
  // Act
  const result = scraper.parseProduct(html);
  
  // Assert
  expect(result.name).toBe('Product Name');
});
```

### 6. Error Cases

Always test:
- Null/undefined inputs
- Empty data
- Malformed data
- Network failures
- Timeouts

### 7. Keep Fixtures Up-to-Date

When scrapers change:
1. Re-capture fixtures from live sites
2. Update expected outputs in tests
3. Verify all tests still pass

---

## Troubleshooting

### Tests Fail After Code Changes

**Check:**
1. Did you update fixtures?
2. Did the website structure change?
3. Are mocks still valid?

**Fix:**
```bash
# Re-run single test to debug
npx vitest run tests/unit/scrapers/gotham.test.mjs --reporter=verbose
```

### Flaky Tests

**Causes:**
- Race conditions
- Async timing issues
- Random data

**Fix:**
```javascript
// Use vi.waitFor for async conditions
import { waitFor } from '@testing-library/react';

await waitFor(() => {
  expect(element).toBeInTheDocument();
});
```

### Coverage Not Generated

**Check:**
```bash
# Verify coverage provider installed
npm list @vitest/coverage-v8

# Reinstall if missing
npm install --save-dev @vitest/coverage-v8
```

### Mocks Not Working

**Check mock order:**
```javascript
// ✅ Mock before import
vi.mock('axios');
import axios from 'axios';

// ❌ Import before mock (won't work)
import axios from 'axios';
vi.mock('axios');
```

### Tests Hang

**Causes:**
- Infinite loops
- Uncaught promises
- Missing `await`

**Fix:**
```javascript
// Add timeout
it('should complete', async () => {
  // ...
}, { timeout: 5000 }); // 5 second timeout
```

---

## Adding New Tests

### For New Scraper

1. **Create fixture:**
   ```bash
   curl 'https://newsite.com/menu' > tests/fixtures/newsite-sample.html
   ```

2. **Create test file:**
   ```bash
   touch tests/unit/scrapers/newsite.test.mjs
   ```

3. **Write tests:**
   ```javascript
   import { describe, it, expect } from 'vitest';
   import NewSiteScraper from '../../../scrapers/newsite/scraper.mjs';

   describe('NewSiteScraper', () => {
     // Add tests here
   });
   ```

4. **Run tests:**
   ```bash
   npm test
   ```

### For New Feature

1. Write test first (TDD):
   ```javascript
   it('should handle new feature', () => {
     const result = newFeature();
     expect(result).toBe(expectedValue);
   });
   ```

2. Implement feature

3. Verify test passes

---

## Test Data Management

See [TEST_FIXTURES.md](./TEST_FIXTURES.md) for detailed fixture documentation.

### Fixture Guidelines

- **Real data:** Use actual HTML/JSON from sites
- **Privacy:** Remove sensitive data
- **Minimal:** Include only what's needed
- **Maintained:** Update when sites change

---

## Continuous Integration

Tests run automatically on:
- Every push to main branches
- Every pull request
- Nightly (for stability)

See [CI_CD_SETUP.md](./CI_CD_SETUP.md) for details.

---

## Resources

- **Vitest Documentation:** https://vitest.dev/
- **Testing Library:** https://testing-library.com/
- **Test Fixtures:** See `TEST_FIXTURES.md`
- **CI/CD Setup:** See `CI_CD_SETUP.md`

---

**Last Updated:** 2026-03-05  
**Questions?** Open an issue or ask in Discord.
