# Phase 2: Method Planning - Complete Report

**Status**: ✅ COMPLETE
**Date**: 2026-03-05
**Branch**: `scraping-research-exercise`

---

## Executive Summary

Comprehensive method planning completed for all three dispensaries. Multiple approaches identified and scored for each platform. Clear implementation roadmap established with recommended primary and fallback methods.

---

## Methods Summary by Dispensary

### Conbud LES (Dutchie Platform)

**Complexity**: ⭐⭐⭐⭐⭐ Very High

| # | Method | Score | Status |
|---|--------|-------|--------|
| 1 | Browser + Network Intercept | 18/25 | ⭐ **Primary** |
| 2 | Direct GraphQL API | 20/25 | ⭐ **Best** (if queries extracted) |
| 3 | Public Dutchie API | 16+/25 | 🔍 Investigate |
| 4 | LocalStorage Inspection | 14/25 | Skip |
| 5 | React State Extraction | 14/25 | Avoid - Too fragile |
| 6 | Service Worker Cache | 15/25 | Investigate only |
| 7 | CDP/Puppeteer | 19/25 | Alternative to #1 |

**Recommended Approach**:
1. Start with **Method #1** (browser automation with network interception)
2. Extract GraphQL queries for **Method #2** (direct API)
3. Investigate **Method #3** (public API) as ideal solution
4. Keep Method #1 as reliable fallback

**Key Challenges**:
- Client-side rendering (no static HTML)
- GraphQL API requires reverse engineering
- Potential CAPTCHA protection
- Browser environment required

---

### Housing Works SoHo (Blaze Platform)

**Complexity**: ⭐⭐⭐ Medium

| # | Method | Score | Status |
|---|--------|-------|--------|
| 1 | Existing Playwright Scraper | 18/25 | ⭐ **Start here** |
| 2 | Direct HTML Scraping | 13/25 | Skip - Won't work |
| 3 | API Discovery & Replication | 19/25 | ⭐ **Next step** |
| 4 | Enhanced Quantity Detection | 18/25 | Supplement to #1 |
| 5 | Category-First Strategy | 18/25 | Optimization |
| 6 | Hybrid (Browser + API) | 19/25 | ⭐ **Best long-term** |

**Recommended Approach**:
1. Test **existing Python scraper** (#1) to validate
2. Discover Blaze API endpoints (#3) using scraper's network logging
3. Implement **hybrid approach** (#6) for production:
   - Use direct API for speed
   - Keep browser automation as fallback
   - Periodic validation

**Key Advantages**:
- Already has working implementation
- Well-documented code with quantity detection
- Optimization path is clear (API discovery)

---

### Gotham NYC (WordPress/Dovetail)

**Complexity**: ⭐⭐ Low-Medium

| # | Method | Score | Status |
|---|--------|-------|--------|
| 1 | curl + HTML Parsing | 18/25 | Baseline |
| 2 | WordPress REST API | 21/25 | ⭐ **Best** (if exists) |
| 3 | Enhanced JSON-LD | 20/25 | ⭐ **Primary** |
| 4 | Age Gate Bypass | 19/25 | Necessary if needed |
| 5 | RSS Feed | 18/25 | Supplementary |
| 6 | Sitemap XML | 15/25 | Avoid - Too slow |
| 7 | Browser Automation | 18/25 | Fallback only |

**Recommended Approach**:
1. **Investigate WordPress REST API** (#2) - Could be easiest
2. Use **JSON-LD extraction** (#3) as primary method
3. Keep **HTML parsing** (#1) as fallback
4. Implement **age gate bypass** (#4) if verification exists
5. Use browser (#7) only if other methods fail

**Key Advantages**:
- Server-side rendering (easiest to scrape)
- JSON-LD structured data likely available
- WordPress API might provide clean data access
- Simple curl-based approach works

---

## Cross-Platform Method Comparison

### By Reliability (5 = most reliable)

| Dispensary | Best Method | Reliability | Notes |
|------------|-------------|-------------|-------|
| Gotham | WordPress API / JSON-LD | 5/5 | Server-rendered, structured |
| Housing Works | Hybrid Browser+API | 5/5 | Multiple fallbacks |
| Conbud | Direct GraphQL | 4/5 | If properly implemented |

### By Speed (5 = fastest)

| Dispensary | Best Method | Speed | Notes |
|------------|-------------|-------|-------|
| Gotham | WordPress API | 5/5 | Direct JSON response |
| Housing Works | API Replication | 5/5 | Once discovered |
| Conbud | Direct GraphQL | 5/5 | Once queries known |

### By Implementation Effort (1 = easiest)

| Dispensary | Best Method | Effort | Notes |
|------------|-------------|--------|-------|
| Gotham | JSON-LD Extraction | ⭐ Low | Standard web scraping |
| Housing Works | Use Existing | ⭐⭐ Medium | Already done, needs testing |
| Conbud | Browser + Network | ⭐⭐⭐⭐ High | New implementation, complex |

### By Maintenance Burden (1 = lowest)

| Dispensary | Best Method | Burden | Notes |
|------------|-------------|--------|-------|
| Gotham | WordPress API | ⭐ Low | Official API stable |
| Conbud | Direct GraphQL | ⭐⭐ Medium | API might change |
| Housing Works | Hybrid | ⭐⭐⭐ Medium-High | Two systems to maintain |

---

## Implementation Roadmap

### Week 1: Testing & Validation

**Gotham** (Easiest - Start here)
- [ ] Day 1-2: Investigate WordPress API
- [ ] Day 2-3: Implement JSON-LD extraction
- [ ] Day 3: Test with Node.js/Python
- [ ] Day 4: Handle age gate if present
- [ ] Day 5: Validate data completeness

**Housing Works** (Medium - Existing scraper)
- [ ] Day 1: Set up Python environment
- [ ] Day 2: Test existing scraper
- [ ] Day 3: Document API endpoints from network log
- [ ] Day 4: Validate quantity detection
- [ ] Day 5: Check data completeness

**Conbud** (Hardest - New implementation)
- [ ] Day 1-2: Set up browser automation environment
- [ ] Day 3-4: Implement network interception
- [ ] Day 5: Extract and document GraphQL queries

### Week 2: Optimization & Implementation

**Gotham**
- [ ] Finalize best method (API vs JSON-LD)
- [ ] Implement with error handling
- [ ] Add retry logic
- [ ] Create automated tests

**Housing Works**
- [ ] Implement direct API calls
- [ ] Create hybrid scraper
- [ ] Add fallback logic
- [ ] Test reliability

**Conbud**
- [ ] Test direct GraphQL queries
- [ ] Implement both browser and API methods
- [ ] Add CAPTCHA detection
- [ ] Create fallback strategy

### Week 3: Production Readiness

**All Dispensaries**
- [ ] Standardize output format
- [ ] Implement logging and monitoring
- [ ] Add rate limiting
- [ ] Create health checks
- [ ] Document deployment process

---

## "Hacky" Approaches Summary

### Clever But Risky (Not Recommended for Production)

1. **React State Extraction** (Conbud)
   - Score: 14/25
   - Risk: Very High - Will break with React updates
   - Use: Never (unless desperate)

2. **LocalStorage Inspection** (All)
   - Score: 14/25
   - Risk: High - Data may be incomplete
   - Use: Supplementary only

3. **Service Worker Cache** (Conbud)
   - Score: 15/25
   - Risk: High - Cache strategy may change
   - Use: Investigation only

4. **Cart Quantity Probing** (Housing Works)
   - Score: 18/25 (already in scraper)
   - Risk: Medium - Slow and detectable
   - Use: Supplement for inventory data

### Acceptable Workarounds

1. **Age Gate Cookie Bypass** (Gotham)
   - Score: 19/25
   - Risk: Low - Standard practice
   - Use: ✅ Recommended if age gate exists

2. **Network Interception** (Conbud, Housing Works)
   - Score: 18-19/25
   - Risk: Low - Standard automation
   - Use: ✅ Recommended

3. **API Replication** (All)
   - Score: 19-20/25
   - Risk: Medium - APIs may change
   - Use: ✅ Recommended with monitoring

---

## Data Extraction Comparison

### Product Fields Availability

| Field | Conbud | Housing Works | Gotham | Notes |
|-------|--------|---------------|--------|-------|
| **Product ID** | ✅ | ✅ | ✅ | All platforms |
| **Name** | ✅ | ✅ | ✅ | All platforms |
| **Brand** | ✅ | ⚠️ | ✅ | HW needs enhancement |
| **Category** | ✅ | ✅ | ✅ | All platforms |
| **Price** | ✅ | ✅ | ✅ | All platforms |
| **THC %** | ✅ | ⚠️ | ⚠️ | Varies by platform |
| **CBD %** | ✅ | ⚠️ | ⚠️ | Varies by platform |
| **Image URL** | ✅ | ⚠️ | ✅ | HW needs enhancement |
| **Inventory/Stock** | ⚠️ | ✅ | ⚠️ | Best on HW |
| **Quantity Available** | ⚠️ | ✅ | ❌ | HW has quantity parser |

### Data Completeness Scoring

| Dispensary | Completeness | Missing Fields | Priority Fixes |
|------------|--------------|----------------|----------------|
| **Conbud** | 90% | Inventory (maybe) | Investigate inventory in GraphQL |
| **Housing Works** | 95% | Brand, Images | Add brand/image extraction |
| **Gotham** | 75% | Inventory, Potency | Enhance THC/CBD parsing |

---

## Risk Assessment

### High Risk Approaches (Avoid)

1. **React State Extraction** - Extremely fragile, breaks with any update
2. **Sitemap Individual Page Scraping** - Too slow, high detection risk
3. **No Fallback Strategy** - Any single method can fail

### Medium Risk (Monitor Closely)

1. **Direct API Calls without Browser Validation** - May break silently
2. **Aggressive Cart Probing** - Could trigger rate limits
3. **Cached Data Reliance** - May be stale

### Low Risk (Recommended)

1. **Browser Automation with Network Capture** - Proven reliable
2. **JSON-LD Structured Data** - SEO-friendly, stable
3. **Hybrid Approaches** - Multiple fallbacks
4. **Official APIs** - Supported and documented

---

## Technology Stack Recommendations

### For Conbud (Dutchie)
```json
{
  "primary": "Playwright (Node.js)",
  "libraries": ["axios", "graphql-request"],
  "fallback": "Puppeteer with CDP",
  "monitoring": "Network request logging"
}
```

### For Housing Works (Blaze)
```json
{
  "primary": "Playwright (Python or Node.js)",
  "libraries": ["requests/axios", "beautifulsoup4/cheerio"],
  "optimization": "Direct API calls",
  "monitoring": "Hybrid health checks"
}
```

### For Gotham (WordPress)
```json
{
  "primary": "Axios + Cheerio (Node.js)",
  "libraries": ["cheerio", "xml2js (for RSS/Sitemap)"],
  "fallback": "Playwright if JS required",
  "monitoring": "Age gate detection"
}
```

---

## Success Metrics & KPIs

### Per-Scraper Metrics
- **Success Rate**: % of successful scrapes
- **Data Completeness**: % of fields extracted
- **Scrape Duration**: Time per full scrape
- **Error Rate**: % of failed requests
- **Product Count**: Total products found

### Target Benchmarks (Week 4)

| Dispensary | Success Rate | Completeness | Duration | Products |
|------------|--------------|--------------|----------|----------|
| Conbud | >95% | >90% | <30s | ~100-300 |
| Housing Works | >98% | >95% | <45s | ~200-400 |
| Gotham | >98% | >75% | <10s | ~150-300 |

---

## Next Phase: Implementation

### Phase 3: Conbud LES Implementation
1. Set up browser automation
2. Implement network interception
3. Extract GraphQL queries
4. Test reliability
5. Document findings
6. Commit code

### Phase 4: Housing Works SoHo Implementation
1. Test existing Python scraper
2. Port to Node.js (if needed)
3. Discover and document APIs
4. Enhance data extraction
5. Test reliability
6. Commit code

### Phase 5: Gotham Implementation
1. Test WordPress API
2. Implement JSON-LD extraction
3. Handle age gate
4. Test reliability
5. Validate data completeness
6. Commit code

---

## Phase 2 Deliverables ✅

1. ✅ **APPROACHES_OVERVIEW.md** - Evaluation framework
2. ✅ **CONBUD_METHODS.md** - 7 methods analyzed and scored
3. ✅ **HOUSING_WORKS_METHODS.md** - 6 methods analyzed and scored
4. ✅ **GOTHAM_METHODS.md** - 7 methods analyzed and scored
5. ✅ **PHASE2_COMPLETE_REPORT.md** - This comprehensive summary

**Total Methods Analyzed**: 20 approaches across 3 dispensaries
**Documentation**: ~40KB of detailed planning
**Recommendations**: Clear primary and fallback methods for each

---

**Ready to proceed to Phase 3: Implementation - Conbud LES** ✅

