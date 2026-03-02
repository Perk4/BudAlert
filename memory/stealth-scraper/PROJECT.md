# Stealth Scraper Bake-off Project (BudAlert)

**Started:** 2026-03-01
**Repo:** https://github.com/Perk4/BudAlert
**R2 Backup:** budalert-backups/backups/

---

## Current Phase: Phase 7 — Inventory Validation

### Completed Phases

**Phase 1-3:** Research & patterns ✅
**Phase 4:** Validation testing ✅
**Phase 5:** Production deployment ✅
**Phase 6:** Scale-up & monitoring ✅

**Phase 6 Results:**
- 12+ working stores
- 126+ products extracted
- Monitoring infrastructure deployed
- Polling scheduler configured

### Phase 7: Inventory Validation 🔄 (In Progress)

**Problem:** We extract products but don't validate actual inventory quantities or verify change detection works.

**Workstreams:**

| Stream | Task | Goal |
|--------|------|------|
| 7A | Quantity extraction | Implement cart probing / dropdown parsing for real stock numbers |
| 7B | Live polling test | Run 24-hour loop on 3 stores, capture real changes |
| 7C | Ground truth validation | Manually verify scraped data matches reality |
| 7D | Alert verification | Confirm alerts fire correctly on changes |

**Success Criteria:**
- [ ] Actual inventory quantities extracted (not just "in stock" boolean)
- [ ] Change detection verified with real events
- [ ] At least 10 products validated against ground truth
- [ ] Alert system tested end-to-end

---

## Inventory Validation Approach

### Current Gap
Most scrapers return:
```json
{"name": "Product X", "price": 50, "stock_status": "in_stock"}
```

### Target Output
```json
{"name": "Product X", "price": 50, "quantity_available": 23, "last_verified": "2026-03-02T02:00:00Z"}
```

### Methods to Implement
1. **Quantity dropdown parsing** — Many sites show max quantity in dropdown (1-10 means 10+ in stock)
2. **Add-to-cart probing** — Add max qty, check error for actual limit
3. **API response analysis** — Some APIs return inventory counts directly
4. **Cart manipulation** — Add item, check cart for quantity limits

---

## Files

- `PROJECT.md` — This file
- `findings/` — Research documents
- `scrapers/` — Working extraction code
- `scrapers/inventory/` — Polling and change detection
- `scrapers/monitoring/` — Alerting infrastructure
