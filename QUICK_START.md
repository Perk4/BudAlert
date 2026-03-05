# BudAlert Quick Start Guide

**Goal**: Run your first scraper in 5 minutes ⏱️

---

## Prerequisites

Pick **one** of these setups:

### Option 1: Docker (Recommended - Easiest)
```bash
# Install Docker Desktop
# macOS: https://docs.docker.com/desktop/mac/install/
# Windows: https://docs.docker.com/desktop/windows/install/
# Linux: sudo apt-get install docker.io docker-compose

# Verify installation
docker --version  # Should be 20.10+
```

### Option 2: Local Node.js
```bash
# Install Node.js 20+
# macOS: brew install node
# Windows: Download from nodejs.org
# Linux: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

# Verify installation
node --version  # Should be v20+
```

---

## 5-Minute Setup

### Step 1: Get the Code (30 seconds)

```bash
cd ~/clawd/budalert/research/phase5-gotham
ls -la  # Verify you see: scraper-curl.js, package.json, Dockerfile
```

---

### Step 2: Run Your First Scraper (2 minutes)

**Using Docker** (recommended):
```bash
# Build image
docker-compose build

# Run scraper
docker-compose up

# Expected output:
# 🌐 Fetching https://gotham.nyc/menu...
# ✅ Page fetched (XXX bytes)
# ✨ Found XX products via JSON-LD
# ✅ Total products extracted: XX
# ✅ Saved XX products to output/gotham-products-TIMESTAMP.json
```

**Using Node.js directly**:
```bash
# Install dependencies
npm install

# Run scraper
node scraper-curl.js

# Same expected output as above
```

---

### Step 3: Check Your Results (1 minute)

```bash
# View output
ls -lh output/*.json

# Count products
cat output/gotham-products-*.json | jq '. | length'
# Expected: 150-300

# View first product
cat output/gotham-products-*.json | jq '.[0]'
# Expected:
# {
#   "name": "Product Name",
#   "price": 45.00,
#   "category": "Flower",
#   "thc": { "value": 25.5 },
#   "image": "https://...",
#   "inStock": true
# }
```

---

### Step 4: Try Other Scrapers (Optional - 5 minutes each)

**Housing Works** (requires browser):
```bash
cd ../phase4-housing-works

# Docker method (includes browser)
docker-compose build  # Takes 5-10 min first time
docker-compose up

# OR Local Python method
pip3 install playwright
playwright install chromium
cd ../../memory/stealth-scraper
python3 -m scrapers.blaze.housing_works
```

**Conbud LES** (most complex):
```bash
cd ~/clawd/budalert/research/phase3-conbud

# Docker method
docker-compose build  # Takes 5-10 min first time
docker-compose up

# Note: May need to solve CAPTCHA manually if it appears
```

---

## Test Commands Reference

### Gotham NYC (WordPress - Fastest)

```bash
cd ~/clawd/budalert/research/phase5-gotham

# Method 1: curl + HTML parsing (2-5 seconds)
node scraper-curl.js

# Method 2: WordPress API (2-5 seconds)
node scraper-wordpress-api.js

# Docker
docker-compose up
```

**Expected Results**:
- ✅ 150-300 products
- ✅ Speed: 2-5 seconds
- ✅ Data: name, price, category, THC
- ✅ No browser needed

---

### Housing Works (Blaze - Medium)

```bash
cd ~/clawd/budalert/research/phase4-housing-works

# Method 1: Playwright browser automation (30-60 seconds)
node scraper-playwright.js

# Method 2: Python (existing scraper)
cd ../../memory/stealth-scraper
python3 -m scrapers.blaze.housing_works

# Docker
cd ~/clawd/budalert/research/phase4-housing-works
docker-compose up
```

**Expected Results**:
- ✅ 200-400 products
- ✅ Speed: 30-60 seconds (browser), 5-10s (API after discovery)
- ✅ Data: name, price, quantity, category
- ✅ Best inventory data

---

### Conbud LES (Dutchie - Complex)

```bash
cd ~/clawd/budalert/research/phase3-conbud

# Method 1: Network intercept (capture GraphQL)
node scraper-network-intercept.js

# Method 2: Direct GraphQL (after query extraction)
node scraper-graphql-direct.js

# Docker
docker-compose up
```

**Expected Results**:
- ✅ 100-300 products
- ✅ Speed: 30-60 seconds (browser), 2-5s (GraphQL direct)
- ✅ Data: name, price, brand, variants, potency
- ⚠️ May require CAPTCHA solving on first run

---

## Common Issues & Solutions

### Issue: `MODULE_NOT_FOUND`
```bash
# Solution: Install dependencies
npm install
# or for Python:
pip3 install playwright
```

### Issue: Browser won't launch
```bash
# Solution: Install Playwright browsers
npx playwright install chromium
# or for Python:
playwright install chromium
```

### Issue: Docker build fails
```bash
# Solution: Check if Dockerfile exists
ls -la Dockerfile

# Rebuild without cache
docker-compose build --no-cache
```

### Issue: No products extracted
```bash
# Solution 1: Check internet connection
curl -I https://gotham.nyc/menu

# Solution 2: Dump page HTML to debug
# Add to scraper: fs.writeFileSync('debug.html', html);

# Solution 3: Check if age gate is blocking
# Update scraper headers with: 'Cookie': 'age_verified=1'
```

### Issue: CAPTCHA appears (Conbud)
```bash
# Solution: Run with visible browser
# Edit scraper-network-intercept.js:
# headless: false  # Change from true

# Wait for CAPTCHA to appear, solve manually
# Script will wait 30 seconds for you
```

---

## Environment Requirements

### Gotham (Minimal)
- ✅ Node.js 18+ or Docker
- ✅ 256 MB RAM
- ✅ No browser needed
- ✅ Works on: Pi, VPS, Lambda, anywhere

### Housing Works (Medium)
- ✅ Node.js 20+ or Python 3.9+ with Docker
- ✅ 1-2 GB RAM
- ✅ Chromium browser required
- ✅ Works on: Desktop, VPS, EC2

### Conbud (Complex)
- ✅ Node.js 20+ with Docker
- ✅ 1-2 GB RAM
- ✅ Chromium browser required
- ⚠️ CAPTCHA may require manual intervention
- ✅ Works on: Desktop, VPS, EC2

---

## Next Steps After Quick Start

### ✅ Successful First Run? Do This Next:

1. **Schedule automatic runs**:
   ```bash
   # Add to crontab for every 6 hours
   crontab -e
   # Add line: 0 */6 * * * cd ~/clawd/budalert/research/phase5-gotham && docker-compose up
   ```

2. **Set up database**:
   ```bash
   # See PRODUCTION_ROADMAP.md Week 1, Day 3-4
   # PostgreSQL or Convex recommended
   ```

3. **Deploy other scrapers**:
   ```bash
   # Housing Works next (existing code works)
   # Then Conbud (most complex)
   ```

4. **Review the roadmap**:
   ```bash
   # Read full production plan
   cat ~/clawd/budalert/PRODUCTION_ROADMAP.md
   ```

---

## Quick Reference

### File Locations

```
~/clawd/budalert/
├── research/
│   ├── phase3-conbud/          # Conbud scraper (Dutchie)
│   ├── phase4-housing-works/   # Housing Works (Blaze)
│   ├── phase5-gotham/          # Gotham scraper (WordPress) ⭐ START HERE
│   └── phase6-scorecard/       # Research docs
│       ├── SCORECARD.md        # Method comparison
│       ├── NEXT_STEPS.md       # Production recommendations
│       ├── IMPLEMENTATION_GUIDE.md  # Detailed steps
│       └── DOCKER_SETUP.md     # Docker guide
├── PRODUCTION_ROADMAP.md       # Week-by-week plan (this doc's companion)
└── QUICK_START.md              # This guide
```

### Command Cheat Sheet

```bash
# Run Gotham (fastest)
cd ~/clawd/budalert/research/phase5-gotham && docker-compose up

# Run Housing Works
cd ~/clawd/budalert/research/phase4-housing-works && docker-compose up

# Run Conbud
cd ~/clawd/budalert/research/phase3-conbud && docker-compose up

# Run all scrapers
cd ~/clawd/budalert/research && docker-compose -f docker-compose-all.yml up

# Check output
ls -lh ~/clawd/budalert/research/output/*/*.json

# Count products
cat ~/clawd/budalert/research/output/*/*.json | jq '. | length'

# View latest Gotham data
cat ~/clawd/budalert/research/phase5-gotham/output/gotham-products-*.json | jq '.[0:3]'
```

---

## Validation Checklist

After running each scraper, verify:

- [ ] ✅ Command completed without errors
- [ ] ✅ JSON file created in output/ directory
- [ ] ✅ Product count matches expected range
- [ ] ✅ Products have required fields (name, price)
- [ ] ✅ JSON is valid (use `jq` to parse)
- [ ] ✅ Images have URLs (if applicable)
- [ ] ✅ Data looks accurate (manual spot check)

---

## Getting Help

**Something not working?**

1. **Check the logs**: Look for error messages in terminal output
2. **Verify prerequisites**: Make sure Docker/Node is installed correctly
3. **Read the docs**: See IMPLEMENTATION_GUIDE.md for detailed troubleshooting
4. **Review the code**: Scrapers have inline comments explaining each step

**Common Questions**:

**Q: Which scraper should I start with?**  
A: Gotham (phase5-gotham) - it's the easiest and fastest.

**Q: How long does the first run take?**  
A: Gotham: 2-5 seconds. Housing Works: 30-60s. Conbud: 30-60s.

**Q: Do I need to install browsers?**  
A: Not for Gotham. Yes for Housing Works and Conbud (Playwright handles it).

**Q: Can I run this on a Raspberry Pi?**  
A: Yes for Gotham. Housing Works/Conbud need more RAM (2GB+).

**Q: What if CAPTCHA blocks me?**  
A: Run with `headless: false` to solve manually, or use a CAPTCHA service for automation.

**Q: How often should I run scrapers?**  
A: Every 6 hours is good. Gotham can run more frequently (no browser overhead).

---

## Success Indicators

**You're ready to move to production when you see:**

✅ Gotham: 150-300 products extracted consistently  
✅ Housing Works: 200-400 products with quantity data  
✅ Conbud: 100-300 products with variants and potency  
✅ No errors in last 3 runs  
✅ Data validates (all products have name + price)  
✅ JSON files are properly formatted

**Next**: Read PRODUCTION_ROADMAP.md for the full deployment plan!

---

## Time Estimates

| Task | Time |
|------|------|
| **Install Docker** | 5-10 min |
| **First Gotham run** | 2 min |
| **Verify output** | 1 min |
| **Run Housing Works** | 10 min (including Docker build) |
| **Run Conbud** | 10 min (including Docker build) |
| **All 3 scrapers running** | 30 min |
| **Add to cron for automation** | 5 min |
| **Total to automated system** | ~1 hour |

---

## What You Get

After completing this quick start:

📊 **Data**:
- 500-1000 cannabis products
- Prices, THC/CBD content, categories
- Images and product details
- Structured JSON format

🤖 **Automation**:
- 3 working scrapers
- Docker containers ready
- Cron job examples
- Error handling built-in

📚 **Knowledge**:
- How each platform works
- Scraping methods (browser vs API)
- Docker deployment basics
- Data validation techniques

🚀 **Next Steps**:
- Production roadmap (4-week plan)
- Database integration
- Monitoring setup
- Scaling to 10+ dispensaries

---

**Ready? Let's go! Start with Gotham.** 🎯

```bash
cd ~/clawd/budalert/research/phase5-gotham
docker-compose up
```

See you in 2 minutes with your first 200 products! ✨
