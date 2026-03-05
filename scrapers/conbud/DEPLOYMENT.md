# Deployment Guide: Sandbox vs Production

This document explains what's achievable in different environments and provides deployment strategies.

---

## Environment Constraints

### Sandbox Environment (OpenClaw/Restricted)

**Limitations:**
- ❌ No Chromium/Playwright (browser automation blocked)
- ❌ No GUI/display server (DISPLAY not available)
- ✅ Node.js and npm available
- ✅ Network access (HTTP/HTTPS)
- ✅ File system access

**What Works:**
- ✅ **API Scraper** (`api-scraper.mjs`) - Direct GraphQL calls
- ✅ Query definitions (`queries.mjs`)
- ✅ Data processing and normalization
- ❌ **Browser Scraper** (`browser-scraper.mjs`) - Requires Chromium

**Recommended Approach:**
1. Run browser scraper locally or in a proper environment
2. Extract GraphQL queries
3. Deploy API scraper to sandbox
4. Use extracted queries for production scraping

---

### Local Development Environment

**Capabilities:**
- ✅ Full Playwright/Chromium support
- ✅ GUI for debugging (headless=false)
- ✅ Manual CAPTCHA solving
- ✅ Network inspection tools

**What Works:**
- ✅ **Browser Scraper** - Full functionality
- ✅ **API Scraper** - Full functionality
- ✅ Query extraction and validation
- ✅ Real-time debugging

**Recommended Workflow:**
```bash
# 1. Extract queries using browser scraper
HEADLESS=false node browser-scraper.mjs

# 2. Validate extracted queries
cat conbud-extracted-queries-*.mjs

# 3. Test API scraper
node api-scraper.mjs

# 4. Deploy to production
```

---

### Production Environment (Server/Cloud)

**Requirements:**
- ✅ Node.js 18+
- ✅ Network access to api.dutchie.com
- ⚠️  Chromium (optional, for browser scraper)

**Deployment Options:**

| Platform | Browser Scraper | API Scraper | Notes |
|----------|-----------------|-------------|-------|
| **VPS (Ubuntu)** | ✅ Full support | ✅ Full support | Best for both |
| **AWS Lambda** | ⚠️  Complex | ✅ Ideal | Use Playwright Layer |
| **Docker** | ✅ Full support | ✅ Full support | Recommended |
| **GitHub Actions** | ✅ Works | ✅ Works | Free tier limits |
| **Heroku** | ⚠️  Limited | ✅ Works | Dyno size matters |
| **Vercel/Netlify** | ❌ No browser | ✅ Works | Serverless only |

---

## Deployment Strategies

### Strategy 1: Hybrid (Recommended)

**Best for:** Production use with reliability

**Setup:**
1. **Local/development:** Run browser scraper periodically
2. **Extract queries:** Save to version control
3. **Production:** Deploy API scraper with extracted queries
4. **Fallback:** Browser scraper on VPS for emergencies

**Pros:**
- ✅ Fast production scraping
- ✅ Low resource usage
- ✅ Easy to deploy
- ✅ Fallback option available

**Cons:**
- ⚠️  Requires manual query updates when API changes

---

### Strategy 2: Browser-Only

**Best for:** Development, testing, query discovery

**Setup:**
1. Deploy browser scraper to VPS with Chromium
2. Run on schedule or on-demand
3. Extract both products and queries

**Pros:**
- ✅ Always captures latest query structure
- ✅ No need to manually update queries
- ✅ Visual debugging possible

**Cons:**
- ❌ Slower execution
- ❌ Higher resource usage
- ❌ CAPTCHA may require intervention

---

### Strategy 3: API-Only

**Best for:** Sandbox environments, lightweight deployments

**Setup:**
1. Use pre-extracted queries (from research or dev environment)
2. Deploy API scraper only
3. Monitor for API changes

**Pros:**
- ✅ Minimal resource requirements
- ✅ Fast execution
- ✅ Works in restricted environments

**Cons:**
- ❌ Breaks if API changes
- ❌ Requires external query extraction

---

## Sandbox Deployment (Current Environment)

### What You Can Do Now

```bash
cd ~/clawd/budalert/scrapers/conbud

# Install dependencies (axios only, skip playwright)
npm install axios --save

# Test API scraper (will use template queries)
node api-scraper.mjs
```

**Expected Result:**
- ⚠️  May fail with "GraphQL queries need to be updated" error
- This is expected - template queries may not match current API

### Making It Work in Sandbox

**Option 1: Use Pre-Extracted Queries**

If you have access to a machine with browser capabilities:

```bash
# On local machine:
cd ~/clawd/budalert/scrapers/conbud
npm install
node browser-scraper.mjs

# Copy extracted queries to sandbox
scp conbud-extracted-queries-*.mjs user@sandbox:/path/to/conbud/

# In sandbox:
# Update queries.mjs with extracted queries
# Run API scraper
node api-scraper.mjs
```

**Option 2: Manual Query Extraction**

1. Visit https://conbud.com/stores/conbud-les in browser
2. Open DevTools → Network tab
3. Filter by "graphql"
4. Find POST request to `api.dutchie.com`
5. Copy query from request payload
6. Update `queries.mjs` with actual query
7. Test API scraper

**Option 3: Use Research Data**

The research phase already has working scrapers:

```bash
# Check if research scrapers have extracted queries
cat ~/clawd/budalert/research/phase3-conbud/scraper-*.js

# If they work, extract queries from there
# Port to queries.mjs
```

---

## Docker Deployment

### Dockerfile (Full Support)

```dockerfile
FROM mcr.microsoft.com/playwright:v1.40.0-jammy

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy scraper files
COPY *.mjs ./

# Default to browser scraper (can override)
CMD ["node", "browser-scraper.mjs"]
```

### Dockerfile (API-Only)

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json ./
RUN npm install axios

# Copy scraper files
COPY *.mjs ./

# Run API scraper
CMD ["node", "api-scraper.mjs"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  browser-scraper:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./output:/app/output
    environment:
      - HEADLESS=true
    command: node browser-scraper.mjs

  api-scraper:
    build:
      context: .
      dockerfile: Dockerfile.api
    volumes:
      - ./output:/app/output
    command: node api-scraper.mjs
```

**Usage:**

```bash
# Run browser scraper
docker-compose run browser-scraper

# Run API scraper
docker-compose run api-scraper

# Run both
docker-compose up
```

---

## AWS Lambda Deployment

### API Scraper (Simple)

```javascript
// lambda-handler.mjs
import { ConbudAPIScraper } from './api-scraper.mjs';

export async function handler(event, context) {
  const scraper = new ConbudAPIScraper();
  
  try {
    const result = await scraper.scrape();
    
    // Save to S3, DynamoDB, etc.
    
    return {
      statusCode: 200,
      body: JSON.stringify(result)
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
}
```

### Browser Scraper (Complex)

Requires Playwright Lambda Layer:
- [playwright-aws-lambda](https://github.com/JupiterOne/playwright-aws-lambda)
- Or use [Serverless Playwright](https://github.com/neet/serverless-playwright)

**Not recommended** - use API scraper instead.

---

## GitHub Actions

### Scheduled Scraping

`.github/workflows/scrape-conbud.yml`:

```yaml
name: Scrape Conbud

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:  # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        working-directory: scrapers/conbud
        run: npm install
      
      - name: Install Playwright
        working-directory: scrapers/conbud
        run: npx playwright install chromium --with-deps
      
      - name: Run browser scraper
        working-directory: scrapers/conbud
        run: node browser-scraper.mjs
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: scrape-results
          path: scrapers/conbud/*.json
      
      - name: Commit results (optional)
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          git add scrapers/conbud/*.json
          git commit -m "Update Conbud scrape results" || true
          git push || true
```

### API-Only Version

```yaml
jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install axios
        working-directory: scrapers/conbud
      - run: node api-scraper.mjs
        working-directory: scrapers/conbud
```

---

## VPS Deployment (Ubuntu)

### Initial Setup

```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Clone repository
cd /opt
git clone https://github.com/your/budalert.git
cd budalert/scrapers/conbud

# Install dependencies
npm install

# Install Playwright browsers
npx playwright install chromium --with-deps
```

### Cron Schedule

```bash
# Edit crontab
crontab -e

# Add scheduled scraping (every 6 hours)
0 */6 * * * cd /opt/budalert/scrapers/conbud && node api-scraper.mjs >> /var/log/conbud-scraper.log 2>&1
```

### Systemd Service (Browser Scraper)

`/etc/systemd/system/conbud-scraper.service`:

```ini
[Unit]
Description=Conbud Browser Scraper
After=network.target

[Service]
Type=oneshot
User=scraper
WorkingDirectory=/opt/budalert/scrapers/conbud
ExecStart=/usr/bin/node browser-scraper.mjs
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Timer:**

`/etc/systemd/system/conbud-scraper.timer`:

```ini
[Unit]
Description=Run Conbud Scraper every 6 hours

[Timer]
OnBootSec=5min
OnUnitActiveSec=6h

[Install]
WantedBy=timers.target
```

**Enable:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable conbud-scraper.timer
sudo systemctl start conbud-scraper.timer
```

---

## Monitoring & Alerts

### Health Check

```javascript
// health-check.mjs
import { ConbudAPIScraper } from './api-scraper.mjs';

async function healthCheck() {
  const scraper = new ConbudAPIScraper({ timeout: 10000, retries: 1 });
  
  try {
    const result = await scraper.scrape();
    
    if (result.success && result.productCount > 0) {
      console.log('✅ Healthy:', result.productCount, 'products');
      process.exit(0);
    } else {
      console.error('❌ Unhealthy: No products scraped');
      process.exit(1);
    }
  } catch (error) {
    console.error('❌ Unhealthy:', error.message);
    process.exit(1);
  }
}

healthCheck();
```

### Error Notification

```bash
#!/bin/bash
# notify-on-failure.sh

cd /opt/budalert/scrapers/conbud
node api-scraper.mjs

if [ $? -ne 0 ]; then
  # Send notification (email, Slack, Discord, etc.)
  curl -X POST https://hooks.slack.com/... \
    -d '{"text":"Conbud scraper failed!"}'
fi
```

---

## Troubleshooting by Environment

### Sandbox
- **Issue:** "playwright not found"
  - **Fix:** Use API scraper only
  
- **Issue:** "GraphQL errors"
  - **Fix:** Extract queries from browser scraper elsewhere

### Local
- **Issue:** Browser won't launch
  - **Fix:** `npx playwright install-deps chromium`
  
- **Issue:** CAPTCHA blocks scraper
  - **Fix:** `HEADLESS=false node browser-scraper.mjs`

### Production
- **Issue:** Intermittent failures
  - **Fix:** Increase retries, add error handling
  
- **Issue:** API structure changed
  - **Fix:** Re-run browser scraper, extract new queries

---

## Recommendations

### For Current Sandbox Environment

1. ✅ **Test API scraper** with template queries
2. ⚠️  **Expect it to fail** (queries may be outdated)
3. ✅ **Document the approach** (you're reading this!)
4. ✅ **Plan for external query extraction**

### For Production Deployment

1. ✅ **Use VPS or Docker** for browser scraper initially
2. ✅ **Extract queries** once
3. ✅ **Deploy API scraper** to lightweight environment
4. ✅ **Monitor for failures** and re-extract queries as needed
5. ✅ **Schedule during off-peak hours** (2-6am EST)

### For Long-Term Maintenance

1. ✅ **Version control queries** in Git
2. ✅ **Set up alerts** for scrape failures
3. ✅ **Document API changes** in SCHEMA.md
4. ✅ **Keep browser scraper available** for emergency query extraction

---

**Status:** Ready for deployment  
**Recommended:** Hybrid strategy (browser for extraction, API for production)  
**Sandbox Support:** API scraper only (requires pre-extracted queries)
