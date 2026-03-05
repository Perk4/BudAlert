# BudAlert Scrapers - Deployment Guide

Complete deployment documentation for all platforms.

## 📚 Documentation Index

### Quick Links
- **[Docker Deployment](DOCKER_DEPLOYMENT.md)** - Local & containerization guide
- **[fly.io Deployment](FLYIO_DEPLOYMENT.md)** - Cloud platform (auto-scaling)
- **[Hostinger Deployment](HOSTINGER_DEPLOYMENT.md)** - VPS deployment (cost-effective)
- **[Scraper Inventory](docs/SCRAPER_INVENTORY.md)** - Technical specs & requirements

---

## 🚀 Quick Start

### Local Development (Docker)

```bash
cd ~/clawd/budalert/deployment

# Build all images
make build

# Test all scrapers
make test

# Start locally
make local

# View logs
make local-logs
```

**Time:** 5-10 minutes  
**Requirements:** Docker Desktop, 4 GB RAM

---

### Production: fly.io (Recommended for beginners)

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Deploy
make deploy-fly

# Monitor
make fly-status
make fly-logs
```

**Time:** 15-20 minutes  
**Cost:** ~$12/mo with auto-scaling  
**Best for:** Managed infrastructure, auto-scaling, zero-downtime deploys

---

### Production: Hostinger VPS (Most cost-effective)

```bash
# Set VPS IP
export HOSTINGER_IP=your.vps.ip

# Initial setup (run once)
make hostinger-setup

# Deploy updates
make deploy-hostinger

# Monitor
make hostinger-status
make hostinger-logs
```

**Time:** 15-20 minutes initial setup  
**Cost:** $4.99/mo (fixed)  
**Best for:** Cost savings, full control, predictable pricing

---

## 📊 Platform Comparison

| Platform | Cost/Month | Setup Time | Maintenance | Auto-Scale | Best For |
|----------|------------|------------|-------------|------------|----------|
| **Local Docker** | $0 | 10 min | Manual | No | Development, testing |
| **fly.io** | ~$12 | 20 min | Automatic | Yes | Managed, auto-scaling |
| **Hostinger** | ~$5 | 20 min | Manual | No | Cost-effective, control |
| **Digital Ocean** | ~$6 | 20 min | Manual | No | Similar to Hostinger |
| **AWS** | ~$15+ | 30 min | Manual | Yes | Enterprise, AWS ecosystem |

### Recommendation by Use Case

- **Just learning?** → Local Docker
- **Small budget?** → Hostinger VPS ($5/mo)
- **Want managed?** → fly.io ($12/mo)
- **Need scale?** → AWS or fly.io
- **Already on AWS?** → AWS EC2 + ECS

---

## 📁 Project Structure

```
budalert/
├── scrapers/                    # Scraper source code
│   ├── housing-works/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── scraper.mjs
│   ├── gotham/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── scraper.mjs          # HTTP version
│   │   └── scraper-browser.mjs  # Browser version
│   ├── conbud/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── api-scraper.mjs      # API version
│   │   └── browser-scraper.mjs  # Browser version
│   ├── docker-compose.yml       # Local orchestration
│   └── README.md                # Scraper usage guide
│
└── deployment/                  # Deployment configs
    ├── docker/                  # Base Docker images
    │   ├── Dockerfile.http      # Alpine (200 MB)
    │   ├── Dockerfile.browser   # Playwright (1.5 GB)
    │   └── README.md
    ├── flyio/                   # fly.io configs
    │   ├── *.fly.toml
    │   ├── deploy.sh
    │   └── README.md
    ├── hostinger/               # VPS configs
    │   ├── setup.sh
    │   ├── deploy.sh
    │   └── README.md
    ├── docs/
    │   └── SCRAPER_INVENTORY.md
    ├── Makefile                 # Quick commands
    ├── DOCKER_DEPLOYMENT.md     # This file
    ├── FLYIO_DEPLOYMENT.md      # Symlink to flyio/README.md
    └── HOSTINGER_DEPLOYMENT.md  # Symlink to hostinger/README.md
```

---

## 🎯 Scrapers Overview

### Housing Works Cannabis Co.
- **Platform:** Blaze e-commerce
- **Method:** HTTP-only (axios + cheerio)
- **Image:** ~200 MB (Alpine)
- **RAM:** 256 MB
- **Speed:** Fast (~5-10 seconds)

### Gotham NYC
- **Platform:** WordPress + Dovetail
- **Method:** HTTP + Browser fallback (Cloudflare bypass)
- **Image:** ~1.5 GB (Playwright)
- **RAM:** 1 GB
- **Speed:** Moderate (~15-30 seconds with browser)

### Conbud LES
- **Platform:** Dutchie GraphQL
- **Method:** API (primary) + Browser (query extraction)
- **Image:** ~200 MB (API) or ~1.5 GB (Browser)
- **RAM:** 256 MB (API) or 1 GB (Browser)
- **Speed:** Fast (~5-10 seconds API mode)

---

## ⚙️ Configuration

### Environment Variables

All scrapers support these environment variables:

```bash
# Node environment
NODE_ENV=production

# Scraper timeouts
SCRAPER_TIMEOUT=30000  # 30 seconds

# Browser settings (for Gotham/Conbud browser)
HEADLESS=true
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Output paths
OUTPUT_DIR=/app/output
LOG_DIR=/app/logs
```

### Secrets Management

#### Local Development
```bash
# Create .env file
cat > scrapers/.env << EOF
SCRAPER_TIMEOUT=30000
NODE_ENV=development
EOF

# Load with docker-compose
docker-compose --env-file .env up
```

#### fly.io
```bash
flyctl secrets set API_KEY=secret --app budalert-housing-works
```

#### Hostinger
```bash
# SSH into VPS
ssh root@your-vps-ip

# Edit environment file
sudo -u budalert nano /opt/budalert/.env
```

---

## 📈 Monitoring

### Local Docker

```bash
# Container status
docker-compose ps

# Resource usage
docker stats

# Logs (all)
docker-compose logs -f

# Logs (specific)
docker-compose logs -f housing-works
```

### fly.io

```bash
# Status
flyctl status --app budalert-housing-works

# Logs
flyctl logs --app budalert-housing-works -f

# Metrics
flyctl metrics --app budalert-housing-works

# Dashboard
flyctl dashboard
```

### Hostinger VPS

```bash
# Service status
ssh root@$HOSTINGER_IP "systemctl status budalert-scrapers"

# Docker status
ssh root@$HOSTINGER_IP "docker ps"

# Logs
ssh root@$HOSTINGER_IP "tail -f /opt/budalert/logs/*.log"

# Resource usage
ssh root@$HOSTINGER_IP "htop"
```

---

## 🔄 Scheduled Scraping

### Cron (Hostinger VPS)

Already configured in `hostinger/setup.sh`:

```cron
# Every 6 hours, staggered
0 */6 * * * housing-works
0 2,8,14,20 * * * gotham
0 4,10,16,22 * * * conbud-api
```

### GitHub Actions (fly.io)

Create `.github/workflows/scrape.yml`:

```yaml
name: Scheduled Scrape
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:  # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger fly.io scraper
        run: |
          curl -X POST https://budalert-housing-works.fly.dev/scrape
```

### External Cron Service

- **cron-job.org** - Free tier available
- **EasyCron** - Paid ($1/mo)
- **AWS EventBridge** - Pay-per-invoke

Configure webhook endpoint: `https://your-app.fly.dev/scrape`

---

## 🛠️ Makefile Commands

```bash
# Build
make build              # All images
make build-http         # HTTP only (lightweight)
make build-browser      # Browser only (large)

# Test
make test               # Run all scrapers once
make test-housing       # Test Housing Works
make test-gotham        # Test Gotham
make test-conbud        # Test Conbud API

# Local
make local              # Start all locally
make local-logs         # View logs
make local-stop         # Stop all

# fly.io
make deploy-fly         # Deploy all to fly.io
make fly-status         # Check status
make fly-logs           # View logs
make fly-scale-up       # Start machines
make fly-scale-down     # Stop machines (save $$$)

# Hostinger
make deploy-hostinger   # Deploy updates
make hostinger-setup    # Initial setup
make hostinger-status   # Check status
make hostinger-logs     # View logs

# Maintenance
make clean              # Clean Docker cache
make update             # Pull + rebuild
make status             # Show all status
make logs               # View all logs

# Help
make help               # Show all commands
make docs               # Show documentation links
```

---

## 🐛 Troubleshooting

### Common Issues

#### "Cannot connect to Docker daemon"
```bash
# Start Docker
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### "Out of disk space"
```bash
# Clean Docker
make clean
docker system prune -a --volumes
```

#### "Browser launch failed"
```bash
# Increase shared memory
docker run --shm-size=256m budalert/gotham

# Or rebuild with no cache
docker-compose build --no-cache gotham
```

#### "Scraper returns no data"
```bash
# Run interactively
docker-compose run --rm housing-works

# Check logs
docker-compose logs housing-works

# Test network
docker-compose run --rm housing-works wget https://hwcannabis.co
```

### Getting Help

1. **Check documentation:**
   - [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
   - [FLYIO_DEPLOYMENT.md](FLYIO_DEPLOYMENT.md)
   - [HOSTINGER_DEPLOYMENT.md](HOSTINGER_DEPLOYMENT.md)

2. **Check logs:**
   ```bash
   make logs
   ```

3. **GitHub Issues:**
   - Create issue with logs and error messages
   - Tag with `deployment` label

---

## ✅ Deployment Checklist

### Initial Setup

- [ ] Choose deployment platform (fly.io or Hostinger)
- [ ] Install required tools (Docker, flyctl, or SSH access)
- [ ] Clone repository
- [ ] Test locally with `make test`
- [ ] Deploy to production
- [ ] Verify scrapers are running
- [ ] Set up scheduled scraping
- [ ] Configure monitoring/alerts

### Regular Maintenance

- [ ] Update code weekly: `make update`
- [ ] Check logs for errors: `make logs`
- [ ] Review resource usage: `make status`
- [ ] Clean old data monthly
- [ ] Update Docker images monthly
- [ ] Backup scraped data (if needed)

---

## 📞 Support

- **Documentation:** See links above
- **Issues:** GitHub Issues
- **Security:** Report privately to maintainers

---

## 📝 License

MIT License - See repository for details

---

**Version:** 1.0.0  
**Last Updated:** 2026-03-05 (Phase 6)  
**Status:** ✅ Production ready
