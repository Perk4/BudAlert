# Implementation Guide - Step-by-Step Execution

**Project**: BudAlert Dispensary Scrapers  
**Audience**: Developers implementing the research findings  
**Updated**: 2026-03-05

---

## Overview

This guide provides step-by-step instructions for implementing all three dispensary scrapers, from environment setup through production deployment.

### Prerequisites

Before starting, ensure you have:

- ✅ Node.js 18+ installed (or Python 3.9+ for Housing Works)
- ✅ Docker Desktop installed (recommended)
- ✅ Git access to repository
- ✅ 4+ GB RAM available
- ✅ Stable internet connection

---

## Implementation Roadmap

### Week 1: Setup & Testing

**Day 1-2**: Environment setup and Gotham (easiest)  
**Day 3-4**: Housing Works (existing scraper)  
**Day 5**: Conbud initial setup

### Week 2: Optimization

**Day 1-2**: API discovery for all platforms  
**Day 3-4**: Direct API implementations  
**Day 5**: Testing and validation

### Week 3: Production

**Day 1-2**: Docker deployment  
**Day 3-4**: Monitoring and error handling  
**Day 5**: Launch and documentation

---

## Step 1: Environment Setup

### Option A: Docker (Recommended)

```bash
# Install Docker Desktop
# macOS: https://docs.docker.com/desktop/mac/install/
# Windows: https://docs.docker.com/desktop/windows/install/
# Linux: sudo apt-get install docker.io docker-compose

# Verify installation
docker --version  # Should be 20.10+
docker-compose --version  # Should be 1.29+

# Clone repository
cd ~/clawd/budalert/research

# Test setup
docker run hello-world
```

### Option B: Local Node.js

```bash
# Install Node.js 20+
# macOS: brew install node
# Windows: Download from nodejs.org
# Linux: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
#        sudo apt-get install -y nodejs

# Verify installation
node --version  # Should be v20+
npm --version   # Should be 10+

# Install Playwright globally
npm install -g playwright
playwright install chromium
```

### Option C: Python (For Housing Works)

```bash
# Install Python 3.11+
# macOS: brew install python@3.11
# Windows: Download from python.org
# Linux: sudo apt-get install python3.11 python3-pip

# Verify installation
python3 --version  # Should be 3.11+
pip3 --version

# Install Playwright
pip3 install playwright asyncio
playwright install chromium
```

---

## Step 2: Gotham NYC (Start Here - Easiest)

### 2.1 Setup

```bash
cd ~/clawd/budalert/research/phase5-gotham

# Install dependencies
npm install

# Verify package.json exists
cat package.json
```

### 2.2 Test curl Method (Primary)

```bash
# Run scraper
node scraper-curl.js

# Expected output:
# 🌐 Fetching https://gotham.nyc/menu...
# ✅ Page fetched (XXX bytes)
# 📦 Parsing HTML for products...
#   ✨ Found XX products via JSON-LD
# ✅ Total products extracted: XX
# 💾 Saving XX unique products...
# ✅ Saved XX products to gotham-products-TIMESTAMP.json
```

### 2.3 Verify Output

```bash
# Check output file
ls -lh gotham-products-*.json

# Validate JSON
cat gotham-products-*.json | jq '. | length'

# Check product structure
cat gotham-products-*.json | jq '.[0]'

# Expected fields:
# {
#   "name": "Product Name",
#   "price": 45.00,
#   "thc": {...},
#   "image": "...",
#   "inStock": true
# }
```

### 2.4 Test WordPress API Method (Alternative)

```bash
# Run API scraper
node scraper-wordpress-api.js

# Expected output:
# 🔍 Discovering WordPress API endpoints...
#   ✅ Found working endpoint: /wp-json/wc/v3/products
# 📡 Fetching from WooCommerce API...
#   → Fetched page 1: XX products
# ✅ Found XX products via WooCommerce
# ✅ Saved XX products to gotham-products-api-TIMESTAMP.json
```

### 2.5 Handle Age Gate (If Needed)

```bash
# If age gate blocks access, update headers:
# Edit scraper-curl.js:

# headers: {
#   'Cookie': 'age_verified=1; age_gate_passed=true'
# }

# Or test with curl:
curl -L -b "age_verified=1" https://gotham.nyc/menu | grep -i "product"
```

### 2.6 Docker Deployment

```bash
# Build image
docker build -t gotham-scraper .

# Run scraper
docker run --rm \
  -v $(pwd)/output:/app/output \
  gotham-scraper

# Or use docker-compose
docker-compose up

# Check output
ls -lh output/gotham-products-*.json
```

### ✅ Gotham Complete Checklist

- [ ] Dependencies installed
- [ ] Scraper runs successfully
- [ ] Products extracted (name, price)
- [ ] JSON output valid
- [ ] Age gate handled (if present)
- [ ] Docker build successful

---

## Step 3: Housing Works (Existing Scraper)

### 3.1 Option A: Use Existing Python Scraper

```bash
cd ~/clawd/budalert/memory/stealth-scraper

# Install dependencies
pip3 install playwright asyncio

# Install browser
playwright install chromium

# Run scraper
python3 -m scrapers.blaze.housing_works

# Expected output:
# Housing Works browser session started
# Navigating to https://hwcannabis.co/menu/broadway/
# Products loaded successfully
# Found categories: ['Flower', 'Edibles', 'Vapes', ...]
# Scraping category: Flower
#   → Found XX products
# ...
# ✅ Saved XX products
```

### 3.2 Option B: Node.js Port

```bash
cd ~/clawd/budalert/research/phase4-housing-works

# Install dependencies
npm install

# Run Playwright scraper
node scraper-playwright.js

# Expected output:
# 🚀 Launching browser for Housing Works...
# ✅ Browser initialized
# 📡 Setting up network tracking...
# 🌐 Navigating to https://hwcannabis.co/menu/broadway/...
# ✅ Menu page loaded
# 📂 Extracting categories...
# ✅ Found X categories: [...]
# 📂 Scraping category: Flower
# 📦 Extracting products from page...
# ✅ Extracted XX products from page
# ...
# 💾 Saving XX unique products...
# ✅ Data saved successfully
```

### 3.3 API Discovery

```bash
# Run scraper to capture API requests
node scraper-playwright.js

# Analyze captured API requests
cat housing-works-api-requests-*.json | jq '.[] | .url' | sort | uniq

# Example output:
# "https://api.blaze.me/stores/housing-works/products"
# "https://api.blaze.me/menu/items"

# Extract endpoints
node scraper-api-direct.js discover housing-works-api-requests-*.json

# Review discovered endpoints
cat housing-works-api-endpoints-*.json | jq '.'
```

### 3.4 Implement Direct API Scraper

```bash
# Update scraper-api-direct.js with discovered endpoints

# Example:
# const HOUSING_WORKS_CONFIG = {
#   apiBaseUrl: 'https://api.blaze.me',  # From discovery
#   storeId: 'housing-works-broadway',   # From discovery
#   ...
# };

# Test direct API scraper
node scraper-api-direct.js

# Expected output:
# 📡 Fetching products from Blaze API...
# ✅ Fetched XX products from API
# ✅ Saved XX products to housing-works-products-api-TIMESTAMP.json
```

### 3.5 Docker Deployment

```bash
# Build Node.js image
docker build -t housing-works-scraper .

# Run Playwright scraper
docker run --rm \
  -v $(pwd)/output:/app/output \
  housing-works-scraper \
  node scraper-playwright.js

# Run API scraper (after discovery)
docker run --rm \
  -v $(pwd)/output:/app/output \
  housing-works-scraper \
  node scraper-api-direct.js

# Or use docker-compose
docker-compose up
```

### ✅ Housing Works Complete Checklist

- [ ] Python scraper tested (or Node.js port)
- [ ] Products extracted with quantity data
- [ ] API endpoints discovered
- [ ] Direct API scraper implemented
- [ ] Network logs saved for analysis
- [ ] Docker build successful

---

## Step 4: Conbud LES (Most Complex)

### 4.1 Setup

```bash
cd ~/clawd/budalert/research/phase3-conbud

# Install dependencies
npm install
```

### 4.2 Run Network Intercept Scraper

```bash
# Run browser scraper to capture GraphQL
node scraper-network-intercept.js

# Expected output:
# 🚀 Launching browser...
# ✅ Browser initialized
# 📡 Setting up network interception...
# 🌐 Navigating to https://conbud.com/stores/conbud-les...
# ✅ Page loaded
# ⏳ Waiting for GraphQL requests...
# 📤 GraphQL Request: FilteredProducts
# 📥 GraphQL Response received
# ✨ Found XX products in response
# ...
# 💾 Saving XX unique products...
# ✅ Data saved successfully
```

### 4.3 Handle CAPTCHA (If Present)

```bash
# If Turnstile CAPTCHA appears:

# Option 1: Manual solving
# Run with headless=false:
# Edit scraper-network-intercept.js:
# headless: false  # Can see browser and solve CAPTCHA

# Option 2: Wait for manual intervention
# Script includes 30-second wait for manual CAPTCHA solving

# Option 3: Use CAPTCHA solving service (production)
# Integrate 2captcha.com or similar
```

### 4.4 Extract GraphQL Queries

```bash
# Check captured queries
cat conbud-graphql-requests-*.json | jq '.[0]'

# Example output:
# {
#   "url": "https://api.dutchie.com/graphql",
#   "query": "query FilteredProducts($dispensaryId: ID!) { ... }",
#   "variables": {
#     "dispensaryId": "6430f42042cf3c004e37f0f8"
#   },
#   "operationName": "FilteredProducts"
# }

# Extract queries programmatically
node -e "
  const { extractQueriesFromLog } = require('./scraper-graphql-direct.js');
  extractQueriesFromLog('conbud-graphql-requests-*.json');
"

# Output: conbud-extracted-queries.js
```

### 4.5 Implement Direct GraphQL Scraper

```bash
# Update scraper-graphql-direct.js with extracted queries

# Copy query from conbud-extracted-queries.js
# Paste into QUERIES object in scraper-graphql-direct.js

# Test direct API scraper
node scraper-graphql-direct.js

# Expected output:
# 📡 Fetching products from Dutchie API...
# ✅ Found XX products (query 1)
# ✅ Saved XX products to conbud-products-direct-TIMESTAMP.json
```

### 4.6 Docker Deployment

```bash
# Build image
docker build -t conbud-scraper .

# Run network intercept scraper
docker run --rm \
  -v $(pwd)/output:/app/output \
  conbud-scraper \
  node scraper-network-intercept.js

# Run direct API scraper (after query extraction)
docker run --rm \
  -v $(pwd)/output:/app/output \
  conbud-scraper \
  node scraper-graphql-direct.js

# Or use docker-compose
docker-compose up
```

### ✅ Conbud Complete Checklist

- [ ] Browser scraper runs successfully
- [ ] GraphQL requests captured
- [ ] Queries extracted and documented
- [ ] Direct API scraper implemented
- [ ] CAPTCHA handling tested
- [ ] Products extracted with variants
- [ ] Docker build successful

---

## Step 5: Unified Deployment

### 5.1 All-in-One docker-compose

```bash
cd ~/clawd/budalert/research

# Create unified docker-compose.yml (see DOCKER_SETUP.md)

# Build all images
docker-compose -f docker-compose-all.yml build

# Run all scrapers
docker-compose -f docker-compose-all.yml up

# Run individually
docker-compose -f docker-compose-all.yml run gotham
docker-compose -f docker-compose-all.yml run housing-works
docker-compose -f docker-compose-all.yml run conbud
```

### 5.2 Verify All Outputs

```bash
# Check all output directories
ls -lh output/gotham/*.json
ls -lh output/housing-works/*.json
ls -lh output/conbud/*.json

# Count total products
echo "Gotham: $(cat output/gotham/*.json | jq '. | length')"
echo "Housing Works: $(cat output/housing-works/*.json | jq '. | length')"
echo "Conbud: $(cat output/conbud/*.json | jq '. | length')"

# Validate data quality
cat output/gotham/*.json | jq '.[] | {name, price, thc: .thc.value}'
cat output/housing-works/*.json | jq '.[] | {name, price, quantity}'
cat output/conbud/*.json | jq '.[] | {name, brand, price, thc: .thc.value}'
```

---

## Step 6: Production Deployment

### 6.1 AWS Lambda

```bash
# Package for Lambda
cd phase5-gotham
zip -r gotham-lambda.zip . -x "node_modules/*" -x "output/*"

# Upload to Lambda
aws lambda create-function \
  --function-name gotham-scraper \
  --runtime nodejs20.x \
  --handler scraper-curl.handler \
  --zip-file fileb://gotham-lambda.zip \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --timeout 30 \
  --memory-size 512

# Test
aws lambda invoke \
  --function-name gotham-scraper \
  output.json
```

### 6.2 GitHub Actions Scheduled

```bash
# Create .github/workflows/scrape.yml (see DOCKER_SETUP.md)

# Commit and push
git add .github/workflows/scrape.yml
git commit -m "Add scheduled scraping workflow"
git push

# Verify in GitHub Actions tab
# Should run every 6 hours (or your chosen schedule)
```

### 6.3 Cron Job (Local)

```bash
# Add to crontab
crontab -e

# Run Gotham every 6 hours
0 */6 * * * cd ~/clawd/budalert/research/phase5-gotham && docker-compose up

# Run all scrapers daily at 6 AM
0 6 * * * cd ~/clawd/budalert/research && docker-compose -f docker-compose-all.yml up
```

---

## Step 7: Monitoring & Validation

### 7.1 Health Checks

```bash
# Create health check script
cat > health-check.sh << 'EOF'
#!/bin/bash

# Check if scrapers ran successfully
for dir in output/*/; do
  latest=$(ls -t ${dir}*.json 2>/dev/null | head -1)
  
  if [ -f "$latest" ]; then
    count=$(cat "$latest" | jq '. | length')
    echo "$(basename $dir): $count products"
  else
    echo "$(basename $dir): NO DATA"
  fi
done
EOF

chmod +x health-check.sh
./health-check.sh
```

### 7.2 Data Validation

```bash
# Validate required fields
cat output/gotham/*.json | jq '.[] | select(.name == null or .price == null) | {name, price}'

# Check for recent data
find output/ -name "*.json" -mtime -1  # Modified in last 24 hours

# Alert if product count drops >20%
# (Implement in monitoring script)
```

### 7.3 Error Logging

```bash
# Capture errors
docker-compose -f docker-compose-all.yml up > logs/scraper.log 2>&1

# Review errors
grep -i "error" logs/scraper.log
grep -i "failed" logs/scraper.log

# Set up alerts (example with email)
if grep -q "FAILED" logs/scraper.log; then
  echo "Scraper failed!" | mail -s "Alert: Scraper Failure" admin@example.com
fi
```

---

## Troubleshooting Common Issues

### Issue: `MODULE_NOT_FOUND`

**Solution**: Install dependencies
```bash
npm install  # or pip3 install playwright
```

### Issue: Browser won't launch

**Solution**: Install Playwright browsers
```bash
npx playwright install chromium
# or
playwright install chromium
```

### Issue: Docker build fails

**Solution**: Check Dockerfile and package.json
```bash
ls -la Dockerfile package.json
docker build -t test-build . --no-cache
```

### Issue: No products extracted

**Solution**: Debug with page HTML dump
```javascript
// Add to scraper:
fs.writeFileSync('page-dump.html', html);
// Review HTML structure
```

### Issue: CAPTCHA blocking scraper

**Solution**: Run headless=false and solve manually
```javascript
headless: false  // In browser.launch()
```

---

## Next Steps

After successful implementation:

1. ✅ All three scrapers running
2. ⏳ Set up production deployment
3. ⏳ Implement monitoring
4. ⏳ Configure alerts
5. ⏳ Schedule automated runs
6. ⏳ Document API changes over time

---

**Implementation Complete** ✅  
See NEXT_STEPS.md for production recommendations and optimization strategies.
