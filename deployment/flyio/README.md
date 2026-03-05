# fly.io Deployment Guide

Deploy BudAlert scrapers to fly.io with auto-scaling and zero-downtime deploys.

## Prerequisites

1. **Install flyctl:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login to fly.io:**
   ```bash
   flyctl auth login
   ```

3. **Create fly.io account** (if needed):
   - Visit https://fly.io/app/sign-up
   - Free tier: 3 shared-cpu-1x VMs

## Quick Deploy

### Deploy All Scrapers
```bash
cd ~/clawd/budalert
./deployment/flyio/deploy.sh all
```

### Deploy Specific Scraper
```bash
./deployment/flyio/deploy.sh housing-works
./deployment/flyio/deploy.sh gotham
./deployment/flyio/deploy.sh conbud-api
./deployment/flyio/deploy.sh conbud-browser  # On-demand only
```

## Manual Deployment

### 1. Housing Works (HTTP-only)
```bash
cd ~/clawd/budalert

# Create app
flyctl apps create budalert-housing-works

# Deploy
flyctl deploy -c deployment/flyio/housing-works.fly.toml

# Verify
flyctl status --app budalert-housing-works
```

### 2. Gotham NYC (Browser-based)
```bash
# Create app
flyctl apps create budalert-gotham

# Deploy (larger image, takes ~3 min)
flyctl deploy -c deployment/flyio/gotham.fly.toml

# Verify
flyctl status --app budalert-gotham
```

### 3. Conbud API (GraphQL)
```bash
# Create app
flyctl apps create budalert-conbud-api

# Deploy with build target
flyctl deploy -c deployment/flyio/conbud-api.fly.toml --build-target api-base

# Verify
flyctl status --app budalert-conbud-api
```

### 4. Conbud Browser (Optional)
```bash
# Create app
flyctl apps create budalert-conbud-browser

# Deploy (use only when needed for query extraction)
flyctl deploy -c deployment/flyio/conbud-browser.fly.toml --build-target browser

# Scale to zero (save costs)
flyctl scale count 0 --app budalert-conbud-browser
```

## Configuration

Each scraper has a `*.fly.toml` configuration:

| Scraper | App Name | Region | CPUs | RAM | Type |
|---------|----------|--------|------|-----|------|
| Housing Works | budalert-housing-works | ewr | 1 | 256 MB | HTTP |
| Gotham | budalert-gotham | ewr | 2 | 1 GB | Browser |
| Conbud API | budalert-conbud-api | ewr | 1 | 256 MB | HTTP |
| Conbud Browser | budalert-conbud-browser | ewr | 2 | 1 GB | Browser |

**Region:** `ewr` = Newark, NJ (closest to NYC for lowest latency)

## Scaling

### Auto-scaling (Configured)
All scrapers have auto-scaling enabled:
- `min_machines_running = 0` - Scales to zero when idle
- `auto_start_machines = true` - Starts on HTTP request
- `auto_stop_machines = true` - Stops after idle period

### Manual Scaling
```bash
# Scale up
flyctl scale count 1 --app budalert-housing-works

# Scale down (save costs)
flyctl scale count 0 --app budalert-housing-works

# Change VM size
flyctl scale vm shared-cpu-2x --app budalert-gotham  # More power
flyctl scale memory 512 --app budalert-housing-works  # More RAM
```

## Monitoring

### View Status
```bash
flyctl status --app budalert-housing-works
```

### View Logs
```bash
# Real-time logs
flyctl logs --app budalert-housing-works

# Last 100 lines
flyctl logs --app budalert-housing-works -n 100
```

### Dashboard
```bash
flyctl dashboard
# Opens browser to https://fly.io/dashboard
```

### Metrics
```bash
flyctl metrics --app budalert-housing-works
```

## Secrets Management

If scrapers need API keys or secrets:

```bash
# Set secret
flyctl secrets set API_KEY=your-key-here --app budalert-housing-works

# List secrets
flyctl secrets list --app budalert-housing-works

# Remove secret
flyctl secrets unset API_KEY --app budalert-housing-works
```

Then access in code:
```javascript
const apiKey = process.env.API_KEY;
```

## Scheduled Scraping

### Option 1: fly.io Machines API
Use the Machines API to schedule scrapes:
```bash
# Start scraper on schedule (external cron)
curl -X POST https://api.machines.dev/v1/apps/budalert-housing-works/machines/start
```

### Option 2: GitHub Actions
```yaml
# .github/workflows/scrape.yml
name: Scheduled Scrape
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger fly.io scraper
        run: |
          flyctl machine run budalert-housing-works
```

### Option 3: External Cron Service
- Use cron-job.org, EasyCron, or similar
- HTTP endpoint: `https://budalert-housing-works.fly.dev/scrape`

## Costs

### fly.io Free Tier
- 3 shared-cpu-1x VMs (256 MB RAM)
- 160 GB outbound data transfer

### Estimated Monthly Costs (Hobby Plan)
- **Housing Works:** ~$2/mo (mostly idle)
- **Gotham:** ~$8/mo (larger VM, browser)
- **Conbud API:** ~$2/mo (mostly idle)
- **Conbud Browser:** ~$0/mo (scaled to zero)

**Total:** ~$12/mo for all scrapers with auto-scaling

### Cost Optimization
1. **Scale to zero** when not in use
2. **Use HTTP scrapers** when possible (10x cheaper than browser)
3. **Run on schedule** (not 24/7)
4. **Use smallest VM** that works

## Troubleshooting

### Deployment fails
```bash
# Check build logs
flyctl logs --app budalert-housing-works

# Rebuild with verbose output
flyctl deploy -c deployment/flyio/housing-works.fly.toml --verbose
```

### Out of memory
```bash
# Increase RAM
flyctl scale memory 512 --app budalert-housing-works

# For browser scrapers, also increase shared memory (already configured)
```

### Browser launch fails
```bash
# Verify shm mount (for Gotham/Conbud browser)
flyctl ssh console --app budalert-gotham
df -h /dev/shm  # Should show 1 GB

# Check Playwright installation
flyctl ssh console --app budalert-gotham
npx playwright install --dry-run chromium
```

### Slow cold starts
- Expected for browser images (~10-15 seconds)
- HTTP images start in 1-3 seconds
- Consider keeping 1 machine running during peak hours

## Updates

### Deploy New Version
```bash
# Simply re-run deploy
flyctl deploy -c deployment/flyio/housing-works.fly.toml

# Zero-downtime deployment (automatic)
```

### Rollback
```bash
# List releases
flyctl releases --app budalert-housing-works

# Rollback to previous
flyctl releases rollback --app budalert-housing-works
```

## Health Checks

All scrapers have health checks configured:

- **HTTP scrapers:** 30s interval, 10s timeout
- **Browser scrapers:** 60s interval, 30s timeout

Custom health endpoint (optional):
```javascript
// Add to scraper.mjs
import http from 'http';

http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200);
    res.end('OK');
  }
}).listen(8080);
```

## Best Practices

1. ✅ **Use auto-scaling** - Save costs when idle
2. ✅ **Monitor logs** - Catch errors early
3. ✅ **Set resource limits** - Prevent runaway costs
4. ✅ **Use HTTP when possible** - Browser only when needed
5. ✅ **Scale to zero** - For maintenance/debugging apps
6. ✅ **Use secrets** - Never hardcode credentials
7. ✅ **Version deployments** - Tag releases for rollback

## Next Steps

- [ ] Deploy all scrapers
- [ ] Set up scheduled scraping (GitHub Actions or cron)
- [ ] Configure monitoring/alerts
- [ ] Set up data storage (S3, Cloudflare R2, etc.)
- [ ] Add error notifications (Discord webhook, email, etc.)

---

**Created:** 2026-03-05 (Phase 4)  
**Status:** ✅ Ready for deployment
