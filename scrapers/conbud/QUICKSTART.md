# Conbud Scraper - Quick Start

**5-minute setup guide for different environments.**

---

## For Sandbox (Current Environment)

**❌ Browser scraper won't work here** (no Chromium)  
**⚠️ API scraper needs extracted queries first**

### Option 1: Test with Template Queries

```bash
cd ~/clawd/budalert/scrapers/conbud

# Install dependencies
npm install axios

# Try API scraper (may fail - queries might be outdated)
node api-scraper.mjs
```

**Expected:** Error message about needing to extract queries

### Option 2: Use Pre-Extracted Queries

If you have queries from another machine:

```bash
# 1. Copy extracted queries file to this directory
# 2. Update queries.mjs with actual query structures
# 3. Run API scraper
node api-scraper.mjs
```

---

## For Local Machine (MacOS/Linux/Windows)

**✅ Full functionality available**

### Step 1: Install Dependencies

```bash
cd ~/clawd/budalert/scrapers/conbud

# Install npm packages
npm install

# Install Playwright browsers
npx playwright install chromium
```

### Step 2: Extract Queries (Browser Scraper)

```bash
# Run with visible browser (can solve CAPTCHA manually)
HEADLESS=false node browser-scraper.mjs

# Wait for browser to open and page to load
# If CAPTCHA appears, solve it manually
# Wait for scraping to complete (~60 seconds)
```

**Output files:**
- `conbud-products-browser-*.json` - Products
- `conbud-graphql-requests-*.json` - Captured queries
- `conbud-extracted-queries-*.mjs` - Reusable query file

### Step 3: Test API Scraper

```bash
# Run fast API scraper (uses extracted queries)
node api-scraper.mjs
```

**Output:**
- `conbud-products-api-*.json` - Products from API

---

## For VPS/Server (Ubuntu/Debian)

### Initial Setup

```bash
# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install system dependencies for Playwright
sudo apt-get install -y \
  libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
  libxdamage1 libxfixes3 libxrandr2 libgbm1 \
  libasound2

# Clone/copy project
cd /opt/budalert/scrapers/conbud

# Install packages
npm install
npx playwright install chromium
```

### Run Browser Scraper (Headless)

```bash
# Production mode (no UI)
node browser-scraper.mjs

# Debug mode (shows browser)
HEADLESS=false node browser-scraper.mjs
```

### Schedule with Cron

```bash
crontab -e

# Add: Run every 6 hours
0 */6 * * * cd /opt/budalert/scrapers/conbud && node api-scraper.mjs
```

---

## For Docker

### Method 1: Browser Scraper

```bash
cd ~/clawd/budalert/scrapers/conbud

# Create Dockerfile
cat > Dockerfile <<'EOF'
FROM mcr.microsoft.com/playwright:v1.40.0-jammy
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["node", "browser-scraper.mjs"]
EOF

# Build and run
docker build -t conbud-scraper .
docker run -v $(pwd)/output:/app conbud-scraper
```

### Method 2: API Scraper (Lightweight)

```bash
# Create lightweight Dockerfile
cat > Dockerfile.api <<'EOF'
FROM node:18-alpine
WORKDIR /app
COPY package.json ./
RUN npm install axios
COPY . .
CMD ["node", "api-scraper.mjs"]
EOF

# Build and run
docker build -f Dockerfile.api -t conbud-api .
docker run -v $(pwd)/output:/app conbud-api
```

---

## For AWS Lambda

**Recommended:** Use API scraper only (browser scraper is complex on Lambda)

### Setup

```bash
# 1. Package scraper
cd ~/clawd/budalert/scrapers/conbud
npm install --production
zip -r conbud-lambda.zip *.mjs node_modules package.json

# 2. Create Lambda function
#    - Runtime: Node.js 18.x
#    - Handler: api-scraper.handler (you'll need to add export)
#    - Timeout: 60 seconds
#    - Memory: 512 MB

# 3. Upload conbud-lambda.zip
```

### Lambda Handler

Add to `api-scraper.mjs`:

```javascript
export async function handler(event, context) {
  const scraper = new ConbudAPIScraper();
  const result = await scraper.scrape();
  return { statusCode: 200, body: JSON.stringify(result) };
}
```

---

## Usage Examples

### Run Specific Example

```bash
# See available examples
node example.mjs

# Run example #1 (basic API scrape)
node example.mjs 1

# Run example #3 (fetch specific category)
node example.mjs 3
```

### Programmatic Usage

```javascript
import { ConbudAPIScraper } from './api-scraper.mjs';

const scraper = new ConbudAPIScraper({
  timeout: 30000,
  retries: 3
});

const result = await scraper.scrape();
console.log(`Scraped ${result.productCount} products`);
```

---

## Troubleshooting

### "playwright not found"
→ **Solution:** `npx playwright install chromium --with-deps`

### "GraphQL errors: Query structure invalid"
→ **Solution:** Run browser-scraper first to extract real queries

### "Turnstile CAPTCHA detected"
→ **Solution:** Run with `HEADLESS=false` and solve manually

### "No products in output"
→ **Solution:** Check `*-graphql-responses-*.json` to see API response structure

### "Cannot launch browser in sandbox"
→ **Solution:** Use API scraper only, extract queries elsewhere

---

## Output Files

| File | Content | Use |
|------|---------|-----|
| `conbud-products-*.json` | Scraped products | Import to BudAlert |
| `conbud-graphql-requests-*.json` | Captured queries | Query extraction |
| `conbud-graphql-responses-*.json` | Raw API responses | Debugging |
| `conbud-extracted-queries-*.mjs` | Reusable queries | Update queries.mjs |

---

## Next Steps

1. ✅ **Run browser scraper** to extract queries (if in proper env)
2. ✅ **Validate output** - check product count and structure
3. ✅ **Test API scraper** with extracted queries
4. ✅ **Integrate with BudAlert** - parse JSON and detect changes
5. ✅ **Schedule regular scraping** - every 6 hours recommended
6. ✅ **Set up monitoring** - alert on failures

---

## Quick Commands Reference

```bash
# Install everything
npm install && npx playwright install chromium

# Extract queries (with UI)
HEADLESS=false node browser-scraper.mjs

# Production scrape (headless)
node browser-scraper.mjs

# Fast API scrape
node api-scraper.mjs

# Run usage example
node example.mjs 1

# Check output
cat conbud-products-*.json | jq '.products | length'

# View first product
cat conbud-products-*.json | jq '.products[0]'

# Count by category
cat conbud-products-*.json | jq '.products | group_by(.category) | map({category: .[0].category, count: length})'
```

---

**For detailed docs:** See `README.md`, `SCHEMA.md`, `DEPLOYMENT.md`  
**For integration:** See `example.mjs`  
**For implementation details:** See `IMPLEMENTATION_SUMMARY.md`
