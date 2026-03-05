# BudAlert Test Gap Analysis

**Generated:** 2026-03-05  
**Purpose:** Identify testing gaps, prioritize by risk/impact, and plan comprehensive test coverage

---

## Table of Contents

1. [Current Test Coverage](#current-test-coverage)
2. [Testing Gaps by Component](#testing-gaps-by-component)
3. [Risk Assessment](#risk-assessment)
4. [Prioritized Test Plan](#prioritized-test-plan)
5. [Test Strategy](#test-strategy)

---

## Current Test Coverage

### Existing Tests

#### 1. `scrapers/gotham/test.mjs` ✅
**Type:** Integration test  
**Coverage:**
- End-to-end scraper execution
- Data validation checks (name, price, category presence)
- Category breakdown analysis
- Data quality scoring
- Sample output inspection

**Strengths:**
- Comprehensive validation logic
- Good metrics (% fields populated)
- Sample data inspection
- JSON output for review

**Weaknesses:**
- No mocking (hits live site every time)
- No assertion framework (manual review)
- Single happy path test
- No error scenario testing

---

#### 2. `research/phase4-housing-works/test-quick.js` ⚠️
**Type:** Research prototype  
**Status:** Abandoned in favor of production scraper

---

#### 3. `memory/stealth-scraper/scrapers/monitoring/test_runner.js` ⚠️
**Type:** Monitoring test for legacy system  
**Status:** Not applicable to current codebase

---

### Coverage Summary

| Component | Unit Tests | Integration Tests | E2E Tests | Total Coverage |
|-----------|-----------|-------------------|-----------|----------------|
| **Scrapers** | 0% | ~10% | 0% | **~3%** |
| Gotham | 0% | 1 test | 0 | ~10% |
| Housing Works | 0% | 0 | 0 | 0% |
| Conbud | 0% | 0 | 0 | 0% |
| **Convex** | 0% | 0% | 0% | **0%** |
| Schema | 0% | 0 | 0 | 0% |
| Mutations | 0% | 0 | 0 | 0% |
| Queries | 0% | 0 | 0 | 0% |
| **Scripts** | 0% | 0% | 0% | **0%** |
| **Overall** | 0% | ~1% | 0% | **~1%** |

---

## Testing Gaps by Component

### 1. Scrapers (High Priority)

#### Gotham Scraper (`scrapers/gotham/scraper.mjs`)

**Missing Unit Tests:**
- [ ] `fetchPage()` - HTTP error handling, timeout, redirects
- [ ] `extractJsonLd()` - JSON parsing, schema validation, array handling
- [ ] `normalizeJsonLdProduct()` - Data transformation, null handling
- [ ] `extractHtmlProducts()` - Selector strategies, empty results
- [ ] `parseProductElement()` - Field extraction, missing data
- [ ] `extractWooCommerceProducts()` - WooCommerce patterns
- [ ] `parsePrice()` - Currency parsing, edge cases ($1,234.56, $5, N/A)
- [ ] `extractPotencyFromText()` - THC/CBD regex, multiple matches
- [ ] `extractCategory()` - Category classification logic
- [ ] `checkAgeGate()` - Age gate detection accuracy

**Missing Integration Tests:**
- [ ] Full scrape with mocked HTTP responses
- [ ] Multi-strategy extraction (JSON-LD + HTML fallback)
- [ ] Deduplication logic
- [ ] Error recovery (partial failures)
- [ ] Age gate cookie handling

**Missing E2E Tests:**
- [ ] Live site scraping (smoke test)
- [ ] Data quality validation
- [ ] Performance benchmarks (< 30s target)

**Risk Level:** 🔴 **HIGH**  
**Reason:** Main production scraper, complex multi-strategy extraction, no error handling tests

---

#### Housing Works Scraper (`scrapers/housing-works/scraper.mjs`)

**Missing Unit Tests:**
- [ ] `fetchPage()` - HTTP errors, timeouts
- [ ] `parseProducts()` - Selector fallback logic, empty pages
- [ ] `extractProductData()` - Field extraction, missing elements
- [ ] `trySelectors()` - Selector matching, fallback behavior
- [ ] `tryAttribute()` - Attribute extraction
- [ ] `checkInStock()` - Stock status detection (various formats)
- [ ] `parsePrice()` - Price parsing edge cases
- [ ] `parsePotency()` - THC/CBD parsing
- [ ] `extractCategories()` - Category discovery, defaults

**Missing Integration Tests:**
- [ ] Full scrape with mocked responses
- [ ] Category crawling logic
- [ ] Rate limiting (2s delay)
- [ ] Debug mode (HTML save on failure)
- [ ] Deduplication by name+price

**Missing E2E Tests:**
- [ ] Live site scraping
- [ ] Multi-category scraping
- [ ] Data quality metrics

**Risk Level:** 🔴 **HIGH**  
**Reason:** Zero test coverage, adaptive selector logic untested, rate limiting unverified

---

#### Conbud Scraper (`scrapers/conbud/api-scraper.mjs`)

**Missing Unit Tests:**
- [ ] `query()` - GraphQL execution, error parsing
- [ ] `extractOperationName()` - Query name extraction
- [ ] `fetchAllProducts()` - Pagination, limits
- [ ] `fetchAllProductsAlternative()` - Fallback query logic
- [ ] `fetchByCategory()` - Category filtering
- [ ] `processProducts()` - Normalization, deduplication
- [ ] `saveData()` - File I/O

**Missing Tests for `queries.mjs`:**
- [ ] `buildFilters()` - Filter construction logic
- [ ] `normalizeProduct()` - API → standard format
- [ ] `getFilteredProductsVariables()` - Variable construction
- [ ] GraphQL query syntax validation

**Missing Integration Tests:**
- [ ] Full API scrape with mocked responses
- [ ] Retry logic (3 attempts, exponential backoff)
- [ ] Multi-category scraping
- [ ] Error handling (GraphQL errors, network failures)

**Missing E2E Tests:**
- [ ] Live API scraping
- [ ] Dutchie API compatibility

**Risk Level:** 🟡 **MEDIUM-HIGH**  
**Reason:** API-based (less fragile than HTML), but zero test coverage, retry logic unverified

---

### 2. Convex Backend (High Priority)

#### Schema (`convex/schema.ts`)

**Missing Tests:**
- [ ] Schema validation (all 20+ tables)
- [ ] Index definitions (query performance)
- [ ] Data type constraints
- [ ] Required vs optional fields
- [ ] Flexible (`v.any()`) vs strict schemas

**Risk Level:** 🟡 **MEDIUM**  
**Reason:** Schema errors cause runtime failures, but Convex provides built-in validation

---

#### NYS Dispensaries Module (`convex/nysDispensaries.ts`)

**Missing Unit Tests:**
- [ ] `upsert()` - Insert new record
- [ ] `upsert()` - Update existing record (by `entity_name`)
- [ ] `upsert()` - Handle duplicate keys
- [ ] `batchUpsert()` - Bulk insert logic
- [ ] `batchUpsert()` - Partial failure handling
- [ ] `batchUpsert()` - Error collection
- [ ] `list()` - Return all dispensaries
- [ ] `getByCity()` - City filter accuracy
- [ ] `getByZip()` - ZIP filter accuracy
- [ ] `count()` - Accurate counting
- [ ] `getStats()` - Statistics calculation

**Missing Integration Tests:**
- [ ] Full upsert workflow (insert → update → verify)
- [ ] Batch operations with large datasets (100+ records)
- [ ] Concurrent upserts (race conditions)
- [ ] Query performance with indexes

**Risk Level:** 🔴 **HIGH**  
**Reason:** Data integrity critical, batch operations prone to errors, no error handling tests

---

#### Load Dispensaries (`convex/loadDispensaries.ts`)

**Missing Tests:**
- [ ] CSV parsing logic
- [ ] Data transformation
- [ ] Error handling (malformed CSV)
- [ ] Batch size optimization

**Risk Level:** 🟢 **LOW**  
**Reason:** One-time import script, manual verification possible

---

### 3. Scripts (Low Priority)

#### `scripts/import-nys-dispensaries.js`

**Missing Tests:**
- [ ] CSV reading
- [ ] Convex API calls
- [ ] Error handling

**Risk Level:** 🟢 **LOW**  
**Reason:** Utility script, infrequent use

---

### 4. Data Transformation (Not Yet Implemented)

**Missing Components:**
- [ ] Entity resolution (match products across stores)
- [ ] Brand extraction/normalization
- [ ] Category classification
- [ ] Data validation pipelines

**Risk Level:** ⚪ **N/A**  
**Reason:** Not implemented yet, but critical for Phase 2

---

### 5. Integration Flows (High Priority)

**Missing Tests:**
- [ ] Scraper → Convex data flow
- [ ] Multi-scraper orchestration
- [ ] Error recovery (scraper fails, data persists)
- [ ] Duplicate product detection across scrapers
- [ ] Inventory change detection (snapshot → delta → event)

**Risk Level:** 🔴 **HIGH**  
**Reason:** End-to-end reliability depends on integration testing

---

## Risk Assessment

### Critical Risks (🔴 High Priority)

| Risk | Impact | Likelihood | Priority | Mitigation |
|------|--------|-----------|----------|------------|
| **Scraper fails silently** | HIGH | MEDIUM | P0 | Unit tests for error handling + alerting |
| **Data extraction errors** | HIGH | HIGH | P0 | Unit tests for all extraction methods |
| **Convex mutations fail** | HIGH | MEDIUM | P0 | Integration tests with rollback |
| **No duplicate detection** | HIGH | MEDIUM | P1 | Integration tests for deduplication |
| **Price parsing errors** | MEDIUM | HIGH | P1 | Unit tests with edge cases |
| **Stock status misdetection** | MEDIUM | MEDIUM | P2 | Unit tests for `checkInStock()` |

### Medium Risks (🟡 Medium Priority)

| Risk | Impact | Likelihood | Priority | Mitigation |
|------|--------|-----------|----------|------------|
| **GraphQL schema changes** | MEDIUM | LOW | P2 | Integration tests + schema validation |
| **HTML structure changes** | MEDIUM | MEDIUM | P2 | Monitoring + selector fallbacks |
| **Rate limiting / IP bans** | MEDIUM | LOW | P3 | Rate limit tests + monitoring |
| **Age gate blocks** | LOW | MEDIUM | P3 | Cookie handling tests |

### Low Risks (🟢 Low Priority)

| Risk | Impact | Likelihood | Priority | Mitigation |
|------|--------|-----------|----------|------------|
| **CSV import errors** | LOW | LOW | P4 | Manual verification |
| **Analytics calculation bugs** | LOW | LOW | P4 | Unit tests (future) |

---

## Prioritized Test Plan

### Phase 1: Critical Path Testing (P0)

**Goal:** Prevent production failures in core scraping + storage

**Tests to Implement:**

1. **Scraper Error Handling**
   - Network timeouts
   - HTTP errors (404, 500, 403)
   - Empty responses
   - Malformed HTML/JSON

2. **Data Extraction Accuracy**
   - Price parsing (all formats)
   - Stock status detection
   - THC/CBD extraction
   - Required field validation

3. **Convex CRUD Operations**
   - Insert mutations
   - Update mutations
   - Query accuracy
   - Error handling

4. **Integration: Scraper → Convex**
   - Full data flow
   - Error recovery
   - Rollback on failure

**Estimated Effort:** 3-4 days  
**Impact:** Blocks production deployment

---

### Phase 2: Reliability Testing (P1)

**Goal:** Ensure data quality and consistency

**Tests to Implement:**

1. **Deduplication Logic**
   - Cross-scraper duplicate detection
   - Same product, multiple formats

2. **Multi-Scraper Orchestration**
   - Parallel scraping
   - Error isolation (one fails, others continue)
   - Batch completion tracking

3. **Data Validation Pipelines**
   - Required fields enforcement
   - Data type validation
   - Business logic rules

4. **Retry & Recovery**
   - Exponential backoff
   - Dead letter queue
   - Manual retry triggers

**Estimated Effort:** 2-3 days  
**Impact:** Improves reliability, reduces manual intervention

---

### Phase 3: Edge Cases & Monitoring (P2)

**Goal:** Handle edge cases gracefully

**Tests to Implement:**

1. **Selector Fallbacks**
   - Multiple HTML structure changes
   - Adaptive selector validation

2. **API Schema Evolution**
   - GraphQL schema changes
   - Backward compatibility

3. **Rate Limiting**
   - Request throttling
   - IP rotation (future)

4. **Monitoring & Alerts**
   - Scraper health checks
   - Data quality metrics
   - Alert generation

**Estimated Effort:** 1-2 days  
**Impact:** Proactive issue detection

---

### Phase 4: Future Features (P3-P4)

**Goal:** Test upcoming features

**Tests to Implement:**

1. **Entity Resolution**
2. **Velocity Calculation**
3. **Notification Delivery**
4. **B2B Analytics**

**Estimated Effort:** TBD  
**Impact:** Feature-dependent

---

## Test Strategy

### Testing Approach

**Framework:** Vitest (recommended) or Jest  
**Why Vitest?**
- Native ESM support (`.mjs` files)
- Fast execution
- Built-in mocking
- TypeScript support

**Alternative:** Node's built-in `node:test` runner (v20+)

---

### Test Organization

```
tests/
├── unit/                      # Unit tests (isolated functions)
│   ├── scrapers/
│   │   ├── gotham.test.mjs
│   │   ├── housing-works.test.mjs
│   │   └── conbud.test.mjs
│   └── convex/
│       └── nysDispensaries.test.ts
│
├── integration/               # Integration tests (component interactions)
│   ├── scraper-to-convex.test.mjs
│   ├── multi-scraper.test.mjs
│   └── data-validation.test.mjs
│
├── e2e/                       # End-to-end tests (full workflows)
│   ├── full-scrape.test.mjs
│   └── smoke.test.mjs
│
└── fixtures/                  # Test data
    ├── gotham-sample.html
    ├── housing-works-sample.html
    ├── conbud-api-response.json
    └── expected-output.json
```

---

### Mocking Strategy

**HTTP Requests:**
- Use `nock` or Vitest's `vi.mock()` to intercept `axios` calls
- Store real HTML/JSON responses as fixtures
- Test both success and error scenarios

**Convex Backend:**
- Mock Convex client for unit tests
- Use Convex test environment for integration tests
- Seed test data for queries

**File I/O:**
- Mock `fs` operations
- Use in-memory file system for tests

---

### Test Data Management

**Fixtures:**
1. **Real scraped data** (capture from live sites, sanitize if needed)
2. **Edge cases** (empty pages, malformed HTML, API errors)
3. **Expected outputs** (normalized product format)

**Fixture Creation:**
```bash
# Capture live data for testing
node scrapers/gotham/scraper.mjs > tests/fixtures/gotham-live.json
```

---

### Coverage Goals

| Metric | Current | Phase 1 | Phase 2 | Phase 3 | Target |
|--------|---------|---------|---------|---------|--------|
| **Overall** | ~1% | 40% | 60% | 75% | 80%+ |
| **Scrapers** | ~3% | 50% | 70% | 80% | 85%+ |
| **Convex** | 0% | 60% | 80% | 90% | 90%+ |
| **Scripts** | 0% | 20% | 40% | 60% | 60%+ |

**Focus:** Prioritize critical paths over 100% coverage

---

### CI/CD Integration

**GitHub Actions Workflow:**
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '22'
      - run: npm install
      - run: npm test
      - run: npm run test:coverage
      - uses: codecov/codecov-action@v3  # Coverage reports
```

**Test Commands:**
- `npm test` - Run all tests
- `npm run test:unit` - Unit tests only
- `npm run test:integration` - Integration tests
- `npm run test:e2e` - E2E tests
- `npm run test:coverage` - Generate coverage report

---

## Success Metrics

**Definition of "Comprehensive Test Coverage":**

1. ✅ **All critical paths tested** (scrape → store → validate)
2. ✅ **>80% code coverage** on scrapers and Convex functions
3. ✅ **Error scenarios covered** (network, parsing, validation)
4. ✅ **CI/CD pipeline** with automated test runs
5. ✅ **Regression prevention** (tests fail before bugs ship)

**Acceptance Criteria:**
- No production deploy without passing tests
- Test runtime < 2 minutes
- Flaky tests < 5%

---

## Next Steps

1. ✅ Review and approve this analysis
2. ⏭️ **Phase 3:** Implement unit tests (scrapers + Convex)
3. ⏭️ **Phase 4:** Implement integration tests
4. ⏭️ **Phase 5:** Set up CI/CD pipeline
5. ⏭️ **Phase 6:** Write testing documentation

---

**Document Version:** 1.0  
**Last Updated:** 2026-03-05  
**Next Review:** After Phase 3 completion
