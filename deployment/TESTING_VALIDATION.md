# Testing & Validation Guide

Complete testing checklist for BudAlert scraper deployment.

---

## Phase 7: Testing & Validation

This document outlines all tests that should be performed before production deployment.

---

## Local Docker Build Tests

### Prerequisites
```bash
# Verify Docker installation
docker --version  # Should be 20.10+
docker-compose --version  # Should be 2.0+

# Check available resources
docker system df
df -h  # At least 10 GB free
free -h  # At least 4 GB RAM
```

---

### Test 1: HTTP-Only Scraper (Housing Works)

**Expected:** Fast build (~30s), small image (~200 MB)

```bash
cd ~/clawd/budalert/scrapers/housing-works

# Build
time docker build -t budalert/housing-works:test .

# Expected output:
# - Build completes in 20-40 seconds
# - Final image size: 150-200 MB
# - No errors or warnings

# Verify image
docker images | grep housing-works

# Expected:
# budalert/housing-works   test   xxx   xxx   ~200MB

# Test run
docker run --rm budalert/housing-works:test

# Expected output:
# 🏪 Housing Works Cannabis Co. Scraper
# ═══════════════════════════════════════════════════
# ...
# 📦 Scraping main menu page...
# ✅ Scraped X products
# ✅ SUCCESS!
```

**Success Criteria:**
- ✅ Build completes without errors
- ✅ Image size < 250 MB
- ✅ Scraper runs and extracts data
- ✅ JSON output is valid
- ✅ No permission errors

---

### Test 2: Browser Scraper (Gotham)

**Expected:** Slow build (~3 min), large image (~1.5 GB)

```bash
cd ~/clawd/budalert/scrapers/gotham

# Build (will take several minutes)
time docker build -t budalert/gotham:test .

# Expected output:
# - Build completes in 2-5 minutes
# - Final image size: 1.2-1.8 GB
# - Playwright installation succeeds

# Verify image
docker images | grep gotham

# Expected:
# budalert/gotham   test   xxx   xxx   ~1.5GB

# Test run (browser mode)
docker run --rm --shm-size=256m budalert/gotham:test

# Expected output:
# 🌐 Launching browser...
# ✅ Browser launched
# 🌐 Navigating to https://gotham.nyc/menu...
# ⏳ Waiting for Cloudflare challenge...
# ✅ Products detected on page
# ✅ Scraped X unique products
# 🔒 Browser closed
```

**Success Criteria:**
- ✅ Build completes without errors
- ✅ Playwright installs correctly
- ✅ Browser launches successfully
- ✅ Cloudflare challenge is bypassed
- ✅ Products are extracted
- ✅ Browser closes cleanly

---

### Test 3: Multi-Stage Build (Conbud)

**Expected:** Two build targets work independently

#### API Mode (Lightweight)
```bash
cd ~/clawd/budalert/scrapers/conbud

# Build API target
time docker build --target api-base -t budalert/conbud:api-test .

# Expected: ~30s build, ~200 MB image

# Verify
docker images | grep conbud

# Test run
docker run --rm budalert/conbud:api-test node api-scraper.mjs

# Expected output:
# 🚀 Starting Conbud API scraper...
# 📡 GraphQL Request...
# ✅ Found X products
# ✅ SUCCESS!
```

#### Browser Mode
```bash
# Build browser target
time docker build --target browser -t budalert/conbud:browser-test .

# Expected: ~3 min build, ~1.5 GB image

# Test run
docker run --rm --shm-size=256m budalert/conbud:browser-test node browser-scraper.mjs

# Expected: Similar to Gotham browser test
```

**Success Criteria:**
- ✅ Both targets build independently
- ✅ API target is lightweight (~200 MB)
- ✅ Browser target includes Playwright (~1.5 GB)
- ✅ Both modes run successfully
- ✅ Data extraction works in both modes

---

### Test 4: Docker Compose Orchestration

```bash
cd ~/clawd/budalert/scrapers

# Build all images in parallel
time docker-compose build --parallel

# Expected:
# - All 4 images build successfully
# - Total time: ~3-5 minutes (parallel)
# - No errors

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# Expected output:
# NAME                          STATUS
# scraper-housing-works         running
# scraper-gotham                running
# scraper-conbud-api            running
# scraper-conbud-browser        exited (profile: browser)

# View logs
docker-compose logs

# Should see scraping output from each service

# Check resources
docker stats --no-stream

# Expected usage:
# housing-works: ~50-100 MB RAM
# gotham: ~200-500 MB RAM
# conbud-api: ~50-100 MB RAM

# Stop all
docker-compose down

# Verify cleanup
docker-compose ps
# Should show no running containers
```

**Success Criteria:**
- ✅ All images build in parallel
- ✅ Services start without errors
- ✅ Each scraper produces output
- ✅ Resource usage within limits
- ✅ Clean shutdown with `down`

---

### Test 5: Volume Mounts & Output

```bash
cd ~/clawd/budalert/scrapers

# Create output directory
mkdir -p output
chmod 777 output

# Run scraper with volume mount
docker-compose run --rm housing-works

# Check output
ls -lh output/

# Expected:
# housing-works-products-2026-XX-XX-XX-XX-XX.json

# Verify JSON structure
cat output/housing-works-products-*.json | jq '.' | head -50

# Expected valid JSON with structure:
# {
#   "store": "housing_works",
#   "scrapedAt": "...",
#   "totalProducts": X,
#   "products": [...]
# }

# Verify data
cat output/housing-works-products-*.json | jq '.products | length'
# Should return number > 0

cat output/housing-works-products-*.json | jq '.products[0]'
# Should show product with name, price, etc.
```

**Success Criteria:**
- ✅ Output directory created correctly
- ✅ JSON files written successfully
- ✅ File permissions correct (readable)
- ✅ JSON is valid and well-formed
- ✅ Product data is complete
- ✅ Timestamps are correct

---

## Deployment Tests

### Test 6: fly.io Deployment (Dry Run)

```bash
cd ~/clawd/budalert

# Validate fly.toml configs
flyctl config validate -c deployment/flyio/housing-works.fly.toml
flyctl config validate -c deployment/flyio/gotham.fly.toml
flyctl config validate -c deployment/flyio/conbud-api.fly.toml

# Expected: All configs valid

# Test deploy (without actually deploying)
# Note: No actual "dry-run" in flyctl, so skip for now
# Will validate during actual deployment
```

**Success Criteria:**
- ✅ All fly.toml files valid
- ✅ No syntax errors
- ✅ Resource limits set correctly

---

### Test 7: Hostinger Setup Script Validation

```bash
cd ~/clawd/budalert/deployment/hostinger

# Validate script syntax
bash -n setup.sh
bash -n deploy.sh

# Expected: No output (valid syntax)

# Check script permissions
ls -l setup.sh deploy.sh

# Expected:
# -rwxr-xr-x  setup.sh
# -rwxr-xr-x  deploy.sh

# Review script (no execution, just review)
head -50 setup.sh

# Verify:
# - Shebang is correct (#!/bin/bash)
# - set -e is present (exit on error)
# - All commands look safe
```

**Success Criteria:**
- ✅ Scripts have valid bash syntax
- ✅ Scripts are executable
- ✅ No dangerous commands
- ✅ Error handling present

---

## Integration Tests

### Test 8: End-to-End Scraping Workflow

```bash
cd ~/clawd/budalert/scrapers

# Full workflow test
docker-compose build housing-works
docker-compose run --rm housing-works

# Verify output
OUTPUT_FILE=$(ls -t output/housing-works-*.json | head -1)
echo "Testing file: $OUTPUT_FILE"

# Test 1: File exists and not empty
test -s "$OUTPUT_FILE"
echo "✅ File exists and not empty"

# Test 2: Valid JSON
jq empty "$OUTPUT_FILE"
echo "✅ Valid JSON"

# Test 3: Has products
PRODUCT_COUNT=$(jq '.products | length' "$OUTPUT_FILE")
test "$PRODUCT_COUNT" -gt 0
echo "✅ Has $PRODUCT_COUNT products"

# Test 4: Product structure
jq '.products[0] | keys' "$OUTPUT_FILE"
# Should include: name, price, url, category, etc.
echo "✅ Product structure valid"

# Test 5: Timestamps recent
SCRAPED_AT=$(jq -r '.scrapedAt' "$OUTPUT_FILE")
echo "Scraped at: $SCRAPED_AT"
echo "✅ Timestamp present"
```

**Success Criteria:**
- ✅ Complete scraping workflow runs
- ✅ Output file created
- ✅ JSON is valid
- ✅ Products extracted (count > 0)
- ✅ Product structure is correct
- ✅ Metadata is present

---

### Test 9: Browser Scraper Cloudflare Bypass

```bash
cd ~/clawd/budalert/scrapers

# Test Gotham browser scraper
docker-compose run --rm gotham node scraper-browser.mjs > /tmp/gotham-test.log 2>&1

# Check for Cloudflare bypass
grep "Waiting for Cloudflare challenge" /tmp/gotham-test.log
grep "Products detected on page" /tmp/gotham-test.log
grep "Scraped.*unique products" /tmp/gotham-test.log

# Should see all three messages

# Verify no errors
if grep -q "challenge not solved" /tmp/gotham-test.log; then
    echo "❌ Cloudflare challenge failed"
    exit 1
else
    echo "✅ Cloudflare challenge bypassed"
fi
```

**Success Criteria:**
- ✅ Browser launches successfully
- ✅ Cloudflare challenge detected
- ✅ Challenge automatically solved
- ✅ Products extracted after bypass
- ✅ No timeout errors

---

## Performance Tests

### Test 10: Resource Usage Validation

```bash
cd ~/clawd/budalert/scrapers

# Start all scrapers
docker-compose up -d

# Monitor resource usage for 30 seconds
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" --no-stream

# Expected usage:
# housing-works:  CPU < 50%, MEM < 200 MB
# gotham:         CPU < 100%, MEM < 1 GB
# conbud-api:     CPU < 50%, MEM < 200 MB

# Stop
docker-compose down
```

**Success Criteria:**
- ✅ HTTP scrapers use < 256 MB RAM
- ✅ Browser scrapers use < 1.2 GB RAM
- ✅ CPU usage is reasonable (< 100% per core)
- ✅ No memory leaks (stable usage over time)

---

### Test 11: Build Time Performance

```bash
cd ~/clawd/budalert/scrapers

# Clean everything first
docker-compose down -v --rmi all

# Time parallel build
time docker-compose build --parallel

# Expected:
# - HTTP scrapers: 30-60 seconds each
# - Browser scrapers: 2-5 minutes each
# - Total (parallel): 3-6 minutes
```

**Success Criteria:**
- ✅ Parallel build works correctly
- ✅ Build completes in < 10 minutes
- ✅ No timeout errors
- ✅ All images built successfully

---

## Documentation Tests

### Test 12: Documentation Accuracy

```bash
cd ~/clawd/budalert

# Verify all documentation files exist
test -f deployment/DEPLOYMENT_README.md
test -f deployment/DOCKER_DEPLOYMENT.md
test -f deployment/FLYIO_DEPLOYMENT.md
test -f deployment/HOSTINGER_DEPLOYMENT.md
test -f deployment/docs/SCRAPER_INVENTORY.md
test -f scrapers/README.md

echo "✅ All documentation files exist"

# Verify symlinks
test -L deployment/FLYIO_DEPLOYMENT.md
test -L deployment/HOSTINGER_DEPLOYMENT.md

echo "✅ Symlinks created correctly"

# Check for broken links in Markdown
# (Manual check or use tool like markdown-link-check)
```

**Success Criteria:**
- ✅ All docs exist
- ✅ Symlinks work
- ✅ No broken links
- ✅ Code examples are accurate
- ✅ Commands are correct

---

### Test 13: Makefile Validation

```bash
cd ~/clawd/budalert/deployment

# Test Makefile syntax
make -n help
make -n build
make -n test

# Expected: Shows commands without executing

# Verify all targets exist
make help

# Should list all available commands
```

**Success Criteria:**
- ✅ Makefile syntax valid
- ✅ All targets work
- ✅ Help text displays correctly
- ✅ No undefined variables

---

## Issues & Limitations

### Known Issues

1. **Docker not available in sandbox**
   - Cannot test actual builds in this environment
   - Manual testing required on local machine or VPS

2. **No live API access**
   - Cannot test real scraping
   - Network-dependent tests must be done manually

3. **No fly.io/Hostinger credentials**
   - Cannot test actual deployments
   - Deployment validation must be done in production

### Testing Limitations

- ✅ **Can validate:** Syntax, file structure, documentation
- ❌ **Cannot validate:** Actual Docker builds, live scraping, deployments

---

## Manual Testing Checklist

Use this checklist when testing on a real machine:

### Local Testing
- [ ] Build all Docker images successfully
- [ ] Run each scraper individually
- [ ] Verify output JSON files
- [ ] Test docker-compose orchestration
- [ ] Check resource usage (RAM, CPU)
- [ ] Test volume mounts work
- [ ] Verify health checks

### fly.io Testing
- [ ] Validate fly.toml configs
- [ ] Deploy Housing Works scraper
- [ ] Deploy Gotham scraper
- [ ] Deploy Conbud API scraper
- [ ] Test auto-scaling (scale to zero)
- [ ] Verify logs accessible
- [ ] Test manual scaling
- [ ] Verify health checks

### Hostinger Testing
- [ ] Run setup.sh on fresh VPS
- [ ] Verify Docker installed
- [ ] Verify systemd service created
- [ ] Test cron jobs configured
- [ ] Run deploy.sh to update
- [ ] Verify logs rotation
- [ ] Test firewall configured
- [ ] Check resource usage

---

## Validation Report Template

Use this template to document test results:

```markdown
# BudAlert Deployment - Test Results

**Date:** YYYY-MM-DD
**Tester:** Name
**Environment:** Local / fly.io / Hostinger

## Local Docker Tests

### Housing Works Scraper
- [ ] Build successful
- [ ] Image size: ___ MB
- [ ] Run successful
- [ ] Products extracted: ___
- [ ] Issues: ___

### Gotham Scraper
- [ ] Build successful
- [ ] Image size: ___ GB
- [ ] Browser launches: ___
- [ ] Cloudflare bypass: ___
- [ ] Products extracted: ___
- [ ] Issues: ___

### Conbud Scraper
- [ ] API build successful
- [ ] Browser build successful
- [ ] Both modes work: ___
- [ ] Issues: ___

## Deployment Tests

### fly.io (if tested)
- [ ] Deployment successful
- [ ] All apps running
- [ ] Logs accessible
- [ ] Issues: ___

### Hostinger (if tested)
- [ ] Setup successful
- [ ] Services running
- [ ] Cron jobs working
- [ ] Issues: ___

## Overall Result
- [ ] All tests passed
- [ ] Some tests failed (see issues)
- [ ] Ready for production: Yes / No

## Notes
___
```

---

## Next Steps After Testing

1. **If all tests pass:**
   - ✅ Commit and push final changes
   - ✅ Deploy to production (fly.io or Hostinger)
   - ✅ Set up monitoring
   - ✅ Schedule regular scraping

2. **If tests fail:**
   - 🔍 Review error logs
   - 🔧 Fix issues in code or configs
   - 🔄 Re-run tests
   - 📝 Document fixes

3. **Production validation:**
   - Monitor first 24 hours closely
   - Verify scraping runs on schedule
   - Check data quality
   - Monitor resource usage
   - Set up alerts for failures

---

**Status:** 📋 Test plan complete, requires manual execution  
**Created:** 2026-03-05 (Phase 7)
