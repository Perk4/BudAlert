# BudAlert Scrapers - Docker Deployment

Dockerized web scrapers for NYC cannabis dispensaries.

## Quick Start

### 1. Local Docker (Development)

```bash
# Build all scrapers
docker-compose build

# Run all scrapers
docker-compose up

# Run specific scraper
docker-compose up housing-works

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f housing-works

# Stop all
docker-compose down
```

### 2. Build Individual Scrapers

```bash
# Housing Works (HTTP-only, ~200 MB)
cd housing-works
docker build -t budalert/housing-works:latest .
docker run -v $(pwd)/output:/app/output budalert/housing-works

# Gotham NYC (Browser, ~1.5 GB)
cd gotham
docker build -t budalert/gotham:latest .
docker run -v $(pwd)/output:/app/output budalert/gotham

# Conbud API (HTTP-only, ~200 MB)
cd conbud
docker build --target api-base -t budalert/conbud:api .
docker run -v $(pwd)/output:/app/output budalert/conbud:api

# Conbud Browser (~1.5 GB)
cd conbud
docker build --target browser -t budalert/conbud:browser .
docker run -v $(pwd)/output:/app/output budalert/conbud:browser
```

## Scraper Details

| Scraper | Size | RAM | Type | Build Time |
|---------|------|-----|------|------------|
| **Housing Works** | ~200 MB | 256 MB | HTTP | ~30s |
| **Gotham** | ~1.5 GB | 1 GB | Browser | ~3min |
| **Conbud (API)** | ~200 MB | 256 MB | HTTP | ~30s |
| **Conbud (Browser)** | ~1.5 GB | 1 GB | Browser | ~3min |

## Output

All scrapers save results to `./output/` directory:

```
output/
├── housing-works-products-{timestamp}.json
├── gotham-products-{timestamp}.json
└── conbud-products-api-{timestamp}.json
```

## Environment Variables

### Housing Works
```bash
SCRAPER_TIMEOUT=30000  # Request timeout (ms)
NODE_ENV=production    # Environment
```

### Gotham
```bash
HEADLESS=true          # Run browser headless
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
```

### Conbud
```bash
SCRAPER_TIMEOUT=30000  # For API mode
HEADLESS=true          # For browser mode
```

## Deployment Platforms

### Local Docker
See above quick start.

### fly.io
See [`../deployment/flyio/`](../deployment/flyio/README.md)

### Hostinger VPS
See [`../deployment/hostinger/`](../deployment/hostinger/README.md)

## Development

### Run Tests
```bash
# Housing Works
docker-compose run housing-works node test.mjs

# Gotham
docker-compose run gotham node test.mjs

# Conbud
docker-compose run conbud-api node example.mjs
```

### Debug Browser Scrapers
```bash
# Run with visible browser (for debugging)
docker-compose run -e HEADLESS=false gotham node scraper-browser.mjs

# Access container shell
docker-compose run gotham sh
```

### Rebuild After Code Changes
```bash
docker-compose build housing-works
docker-compose up housing-works
```

## Troubleshooting

### "Permission denied" errors
```bash
# Fix output directory permissions
mkdir -p output
chmod 777 output
```

### "Browser launch failed"
```bash
# Increase shared memory
docker-compose up gotham  # Already configured with shm_size: 256m

# Or run with --shm-size flag
docker run --shm-size=256m budalert/gotham
```

### "Module not found"
```bash
# Rebuild with no cache
docker-compose build --no-cache housing-works
```

## Image Optimization

### Current Sizes
- HTTP images: ~150-200 MB (Alpine-based)
- Browser images: ~1.2-1.5 GB (Playwright requirement)

### Size Reduction Tips
- ✅ Using Alpine for HTTP scrapers
- ✅ Multi-stage builds for Conbud
- ✅ Only installing Chromium (not Firefox/WebKit)
- ✅ Production dependencies only
- ❌ Can't reduce browser images further (Playwright needs Debian + Chrome)

## Architecture

```
scrapers/
├── housing-works/
│   ├── Dockerfile           # Alpine-based HTTP scraper
│   ├── package.json
│   └── scraper.mjs
├── gotham/
│   ├── Dockerfile           # Playwright browser scraper
│   ├── package.json
│   ├── scraper.mjs          # HTTP fallback
│   └── scraper-browser.mjs  # Cloudflare bypass
├── conbud/
│   ├── Dockerfile           # Multi-stage (API + Browser)
│   ├── package.json
│   ├── api-scraper.mjs      # Lightweight API
│   └── browser-scraper.mjs  # Query extraction
├── docker-compose.yml       # Local orchestration
└── output/                  # Scraped data (mounted volume)
```

## Next Steps

1. Test all scrapers locally
2. Deploy to fly.io (see Phase 4)
3. Deploy to Hostinger (see Phase 5)
4. Set up cron jobs for scheduled scraping
5. Add monitoring and alerts

---

**Last Updated:** 2026-03-05 (Phase 3)  
**Status:** ✅ Ready for local testing
