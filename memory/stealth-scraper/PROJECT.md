# Stealth Scraper Bake-off Project

**Started:** 2026-03-01
**Goal:** Build reliable scraping infrastructure for NYS cannabis dispensary product/inventory data

---

## Current Phase: Phase 6 — Scale-Up & Monitoring

### Completed Phases

**Phase 1: Store Recon** ✅
- 20 NYC dispensaries profiled

**Phase 2: Proxy Research** ✅
- Oxylabs abandoned, tiered approach adopted

**Phase 3: Stagehand + Pattern Analysis** ✅
- Extraction patterns documented per platform

**Phase 4: Validation Testing** ✅
- Blaze, Dutchie embed, Joint Ecommerce validated

**Phase 5: Production Deployment** ✅
- **Housing Works (Blaze):** 26 products, production-ready
- **CONBUD (Dutchie Embed):** 26 products, CF bypass working
- **Torches (Joint Ecommerce):** 6 products extracted
- **Stoops (Joint Ecommerce):** 4 products extracted
- **Alta:** Framework ready, needs completion
- **Store reclassification:** All 20 stores audited

### Phase 6: Scale-Up & Monitoring 🔄 (In Progress)

**Objective:** Expand to all 20 stores, implement monitoring, optimize operations.

**Workstreams:**

| Stream | Task | Stores | Status |
|--------|------|--------|--------|
| 6A | Easy custom sites | Smacked Village, Yerba Buena, Terp Bros, FlynnStoned, Happy Munkey | 🔄 |
| 6B | Medium custom sites | Travel Agency, Gotham, Dazed, Green Apple, Chelsea Cannabis, Verilife | 🔄 |
| 6C | LeafBridge platform | QUBE NYC | 🔄 |
| 6D | Alta completion + inventory polling | Alta + polling infra | 🔄 |
| 6E | Monitoring & alerting | All stores | 🔄 |
| 6F | Hard targets | RISE (Jane), Curaleaf (MSO) | 🔄 |

**Expected Outputs:**
- Working scrapers for all 20 stores
- Unified monitoring dashboard
- Inventory change detection
- Alerting infrastructure
- Cost/performance optimization

---

## Production Coverage (Phase 5 Complete)

| Store | Platform | Products | Status |
|-------|----------|----------|--------|
| Housing Works | Blaze | 26 | ✅ Production |
| CONBUD | Dutchie Embed | 26 | ✅ Working |
| Torches | Joint Ecommerce | 6 | ✅ Working |
| Stoops | Joint Ecommerce | 4 | ✅ Working |
| Alta | Joint Ecommerce | 0 | 🟡 Framework ready |
| **Subtotal** | | **62** | **4/20 stores** |

---

## Remaining Stores (Phase 6 Target)

### Easy Custom (5 stores)
- Smacked Village (getsmacked.online)
- Yerba Buena (yerbabuena.nyc)
- Terp Bros (terpbrosnyc.com)
- FlynnStoned (flynnstoned.com)
- Happy Munkey (happymunkey.com)

### Medium Custom (6 stores)
- The Travel Agency (thetravelagency.co) - Remix/React
- Gotham (gotham.nyc)
- Dazed Cannabis (dazed.fun)
- Green Apple (greenapple.nyc)
- Chelsea Cannabis Co. (chelseacannabis.co)
- Verilife (verilife.com/ny)

### New Platforms (1 store)
- QUBE NYC (qubenyc.com) - LeafBridge

### Hard Targets (2 stores)
- RISE Manhattan (risecannabis.com) - Jane + Cloudflare
- Curaleaf NYC (curaleaf.com) - MSO + Cloudflare

---

## Tech Stack (Validated)

| Tier | Use Case | Solution | Cost |
|------|----------|----------|------|
| Tier 1 | Hard targets | Stagehand + Browserbase | ~$50/mo |
| Tier 2 | Medium/Easy | Playwright + Decodo | ~$50/mo |
| **Total** | 20 stores | Hybrid | **~$100/mo** |

---

## Files

- `PROJECT.md` — This file
- `findings/` — Research documents
- `scrapers/` — Working extraction code
- `stores/` — Store database and classification
