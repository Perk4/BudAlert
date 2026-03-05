# Docker Base Images

This directory contains optimized base Docker images for BudAlert scrapers.

## Images

### `Dockerfile.http` - Lightweight HTTP Scraper
**For:** HTTP-only scrapers (axios + cheerio)

**Specs:**
- Base: `node:20-alpine`
- Size: ~150-200 MB
- RAM: 128-256 MB
- CPU: 0.1-0.5 cores
- Startup: 1-3 seconds

**Use cases:**
- Housing Works scraper
- Conbud API mode
- Gotham HTTP mode (no Cloudflare)

**Build:**
```bash
docker build -f Dockerfile.http -t budalert/scraper-http:latest .
```

---

### `Dockerfile.browser` - Full Browser Automation
**For:** Browser-based scrapers (Playwright + Chromium)

**Specs:**
- Base: `mcr.microsoft.com/playwright:v1.40.0-jammy`
- Size: ~1.2-1.5 GB
- RAM: 512 MB - 1 GB
- CPU: 0.5-1.0 cores
- Startup: 5-15 seconds

**Use cases:**
- Gotham browser mode (Cloudflare bypass)
- Conbud browser mode (GraphQL query extraction)
- Any scraper requiring JavaScript rendering

**Build:**
```bash
docker build -f Dockerfile.browser -t budalert/scraper-browser:latest .
```

---

## Design Decisions

### Alpine vs Debian
- **HTTP image:** Alpine (minimal, fast, secure)
- **Browser image:** Debian (Playwright requirement, better browser support)

### Security
- ✅ Non-root user (`scraper:1001`)
- ✅ Minimal installed packages
- ✅ Security updates applied
- ✅ No unnecessary capabilities

### Performance
- ✅ Layer caching (dependencies before code)
- ✅ Multi-stage builds ready
- ✅ npm cache cleared
- ✅ Only production dependencies

### Health Checks
- **HTTP:** Simple Node.js liveness check (30s interval)
- **Browser:** Playwright browser launch verification (60s interval)

---

## Usage Examples

### Basic Usage
```bash
# HTTP scraper
docker run -v $(pwd):/app budalert/scraper-http:latest node scraper.mjs

# Browser scraper
docker run -v $(pwd):/app budalert/scraper-browser:latest node scraper-browser.mjs
```

### With docker-compose
See `../docker-compose.yml` for orchestration examples.

### Environment Variables
```bash
docker run -e SCRAPER_TIMEOUT=60000 -e HEADLESS=true budalert/scraper-browser
```

---

## Optimization Tips

### Reduce HTTP Image Size
Already minimal (~150 MB). Possible optimizations:
- Use distroless base (complex)
- Remove npm after install (breaks some packages)
- Use pnpm instead of npm (-10 MB)

### Reduce Browser Image Size
Playwright image is large by necessity. Optimizations:
- ✅ Only install Chromium (not Firefox/WebKit)
- ✅ Use `playwright install-deps chromium` for minimal deps
- ❌ Can't use Alpine (Playwright needs glibc)

### Build Time
Use BuildKit for parallel builds:
```bash
DOCKER_BUILDKIT=1 docker build -f Dockerfile.http .
```

---

## Troubleshooting

### "EACCES: permission denied"
- Check user ownership: `USER scraper` in Dockerfile
- Volume mounts: Ensure host user matches container UID 1001

### "Browser launch failed"
- Browser image: Verify `playwright install chromium` ran
- Check environment: `PLAYWRIGHT_BROWSERS_PATH` set correctly
- Try running as root (for debugging): `docker run --user root ...`

### "Module not found"
- Check `package.json` exists in build context
- Verify `npm ci` completed successfully
- Ensure `.dockerignore` doesn't exclude needed files

---

## Next Steps

1. **Phase 3:** Create per-scraper Dockerfiles extending these bases
2. **Phase 4:** Add fly.io deployment configs
3. **Phase 5:** Add Hostinger deployment configs
4. **Phase 6:** Create unified docker-compose orchestration

---

**Created:** 2026-03-05 (Phase 2)  
**Status:** ✅ Base images ready for testing
