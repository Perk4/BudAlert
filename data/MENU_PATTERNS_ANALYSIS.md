# Menu URL Discovery - Pattern Analysis

## Phase 1 Findings (Sample of 10 Stores)

### Success Rate
- **Total Processed:** 10
- **Menu URLs Found:** 10 (100%)
- **Validated:** 10 (100%)

### Common URL Patterns Found

All stores in the sample used standard path-based menu URLs:

1. `/menu` - 40% (4/10)
   - The Flowery Staten Island
   - Curaleaf Plattsburgh
   - Leaf & Fog Dispensary
   - Stonedhouse Dispensary

2. `/shop` - 30% (3/10)
   - Gotham Buds (Dutchie provider)
   - Alta Dispensary
   - Devil's Lettuce

3. `/cannabis` - 20% (2/10)
   - Gotham CAURD LLC
   - Cotton Mouth Dispensary

4. `/store` - 10% (1/10)
   - Dansville Dispensary

### Providers Detected

- **Dutchie:** 1 confirmed (Gotham Buds)
- **Unknown/Custom:** 9 stores

### Discovery Methods

- **common_path:** 100% (all found via standard path checking)
- **link_scan:** 0% (not needed - all found via common paths)

### Next Steps

The high success rate with common path checking suggests that most NYS dispensaries follow standard URL patterns. The full batch processing should:

1. Continue prioritizing common path checks
2. Fall back to link scanning only when common paths fail
3. Track provider distribution for categorization

### Rate Limiting

- Current: 1 request per second per store
- Plus 500ms between path checks
- Estimated time for 599 stores: ~15-20 minutes total
