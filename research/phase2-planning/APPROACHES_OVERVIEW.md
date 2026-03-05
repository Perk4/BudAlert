# Phase 2: Scraping Method Planning

**Date**: 2026-03-05
**Status**: 🔄 IN PROGRESS

---

## Objective

Design and evaluate multiple scraping approaches for each dispensary, ranging from clean/reliable to hacky/experimental. Each approach will be ranked on:
- **Reliability**: How consistently it works
- **Speed**: Performance and resource usage
- **Maintainability**: Ease of updates when sites change
- **Hackiness**: How "clever" vs straightforward
- **Data Completeness**: What fields can be extracted

---

## Approach Categories

### 1. Clean & Reliable
- Official APIs or documented endpoints
- Standard HTML parsing
- Well-supported tools (Playwright, Cheerio)
- Minimal risk of breaking

### 2. Network Interception
- Browser automation with request/response capture
- GraphQL query extraction
- API endpoint discovery
- Moderate complexity

### 3. Hacky & Experimental
- LocalStorage inspection
- Service Worker interception
- Cookie/token extraction
- DOM manipulation tricks
- High risk of breaking

### 4. Fallback Methods
- Screenshot + OCR
- Cached data sources
- Third-party aggregators
- Manual extraction tools

---

## Evaluation Matrix (1-5 scale)

| Approach | Reliability | Speed | Maintainability | Hackiness | Data Completeness |
|----------|------------|-------|----------------|-----------|-------------------|
| *To be filled per dispensary* | | | | | |

**Scoring Guide**:
- **Reliability**: 5 = Always works, 1 = Frequently fails
- **Speed**: 5 = Very fast, 1 = Very slow
- **Maintainability**: 5 = Easy to update, 1 = Breaks often
- **Hackiness**: 5 = Very hacky, 1 = Standard approach
- **Data Completeness**: 5 = All fields, 1 = Minimal data

---

