# Docker Deployment Guide

Complete guide for deploying BudAlert scrapers using Docker.

## Table of Contents

1. [Local Development](#local-development)
2. [Production Deployment](#production-deployment)
3. [Architecture](#architecture)
4. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites

- Docker Desktop or Docker Engine (20.10+)
- Docker Compose (2.0+)
- 4 GB RAM minimum
- 10 GB free disk space

### Quick Start

```bash
cd ~/clawd/budalert/scrapers

# Build all images
docker-compose build

# Start all scrapers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all
docker-compose down
```

### Individual Scrapers

```bash
# Build specific scraper
docker-compose build housing-works

# Run once and exit
docker-compose run --rm housing-works

# Start in background
docker-compose up -d housing-works

# Stop specific scraper
docker-compose stop housing-works
```

### Development Workflow

1. **Make code changes** in `scrapers/*/`
2. **Rebuild image:**
   ```bash
   docker-compose build housing-works
   ```
3. **Test:**
   ```bash
   docker-compose run --rm housing-works
   ```
4. **Deploy** when ready

---

## Production Deployment

### Option 1: fly.io (Recommended)

**Best for:** Auto-scaling, zero-downtime deploys, managed infrastructure

See [FLYIO_DEPLOYMENT.md](FLYIO_DEPLOYMENT.md)

**Pros:**
- ✅ Auto-scaling (scale to zero when idle)
- ✅ Free tier available
- ✅ Global CDN
- ✅ Zero-downtime deploys
- ✅ Built-in health checks

**Cons:**
- ❌ More expensive than VPS at scale
- ❌ Vendor lock-in

**Cost:** ~$12/mo for all scrapers with auto-scaling

---

### Option 2: Hostinger VPS

**Best for:** Cost-effective, full control, predictable pricing

See [HOSTINGER_DEPLOYMENT.md](HOSTINGER_DEPLOYMENT.md)

**Pros:**
- ✅ Low cost ($4.99/mo)
- ✅ Full root access
- ✅ Predictable pricing
- ✅ Can run other services

**Cons:**
- ❌ Manual setup required
- ❌ You manage updates/security
- ❌ No auto-scaling

**Cost:** $4.99-6.99/mo (fixed)

---

### Option 3: Other Platforms

#### Digital Ocean
Similar to Hostinger, slightly more expensive ($6/mo minimum)

```bash
# Use Hostinger deployment scripts
# Just replace SSH target
```

#### AWS EC2
More expensive, but integrates well with AWS ecosystem

```bash
# Use Hostinger setup script on Ubuntu 22.04 EC2 instance
# Configure security groups for ports 80, 443, 22
```

#### Google Cloud Run
Serverless container platform (good for HTTP scrapers)

```bash
# Deploy HTTP scrapers
gcloud run deploy housing-works \
  --image gcr.io/project/housing-works \
  --platform managed \
  --region us-east1
```

---

## Architecture

### Image Hierarchy

```
Base Images:
├── Dockerfile.http (Alpine, ~200 MB)
│   ├── housing-works/Dockerfile
│   └── conbud/Dockerfile (API target)
│
└── Dockerfile.browser (Playwright, ~1.5 GB)
    ├── gotham/Dockerfile
    └── conbud/Dockerfile (Browser target)
```

### Resource Requirements

| Scraper | Type | RAM | CPU | Storage | Build Time |
|---------|------|-----|-----|---------|------------|
| Housing Works | HTTP | 256 MB | 0.5 | ~200 MB | ~30s |
| Gotham | Browser | 1 GB | 1.0 | ~1.5 GB | ~3min |
| Conbud API | HTTP | 256 MB | 0.5 | ~200 MB | ~30s |
| Conbud Browser | Browser | 1 GB | 1.0 | ~1.5 GB | ~3min |

**Total for all scrapers:** 2.5 GB RAM, 4 GB storage

### Network Flow

```
Scraper Container
    ↓ HTTP/HTTPS
Target Website
    ↓ Response
Scraper Process
    ↓ JSON
Volume Mount (/app/output)
    ↓
Host Filesystem
```

### Data Persistence

**Volumes:**
- `./output:/app/output` - Scraped JSON files
- `./logs:/app/logs` - Application logs (Hostinger)

**File naming:**
- `housing-works-products-{timestamp}.json`
- `gotham-products-{timestamp}.json`
- `conbud-products-api-{timestamp}.json`

---

## Troubleshooting

### Build Issues

#### "Cannot find module"
```bash
# Clear cache and rebuild
docker-compose build --no-cache housing-works
```

#### "No space left on device"
```bash
# Clean up Docker
docker system prune -a --volumes

# Remove old images
docker images | grep "none" | awk '{print $3}' | xargs docker rmi
```

#### "Playwright installation failed"
```bash
# Verify base image
docker pull mcr.microsoft.com/playwright:v1.40.0-jammy

# Build with verbose output
docker-compose build --progress=plain gotham
```

---

### Runtime Issues

#### "Permission denied: /app/output"
```bash
# Fix permissions on host
mkdir -p ./output
chmod 777 ./output
```

#### "Browser launch failed"
```bash
# Increase shared memory
docker run --shm-size=256m budalert/gotham

# Or in docker-compose.yml (already configured):
shm_size: 256m
```

#### "Container exits immediately"
```bash
# Check logs
docker-compose logs housing-works

# Run interactively
docker-compose run --rm housing-works sh

# Test scraper manually
docker-compose run --rm housing-works node scraper.mjs
```

#### "Out of memory"
```bash
# Check container memory
docker stats

# Increase limit in docker-compose.yml
mem_limit: 512m  # Increase this
```

---

### Network Issues

#### "Connection timeout"
```bash
# Test from within container
docker-compose run --rm housing-works sh
wget https://hwcannabis.co

# Check DNS
docker-compose run --rm housing-works nslookup hwcannabis.co
```

#### "SSL certificate error"
```bash
# Update CA certificates
docker-compose build --no-cache housing-works
```

---

## Best Practices

### Development

1. **Use volume mounts** for hot reloading:
   ```yaml
   volumes:
     - ./housing-works:/app
   ```

2. **Tag images** for versions:
   ```bash
   docker build -t budalert/housing-works:v1.0.0 .
   ```

3. **Multi-stage builds** for size optimization (already implemented)

### Production

1. **Always use specific versions:**
   ```dockerfile
   FROM node:20-alpine  # Good
   FROM node:alpine     # Bad (unpredictable)
   ```

2. **Health checks** (already configured)

3. **Resource limits:**
   ```yaml
   mem_limit: 256m
   cpus: 0.5
   ```

4. **Restart policies:**
   ```yaml
   restart: unless-stopped
   ```

5. **Log rotation** (configured for Hostinger)

### Security

1. ✅ **Non-root user** (UID 1001)
2. ✅ **Minimal base images** (Alpine)
3. ✅ **No secrets in images** (use environment variables)
4. ✅ **Regular updates** (rebuild images monthly)
5. ✅ **Scan images** for vulnerabilities:
   ```bash
   docker scan budalert/housing-works
   ```

---

## Performance Optimization

### Build Time

```bash
# Parallel builds
docker-compose build --parallel

# Use BuildKit
DOCKER_BUILDKIT=1 docker-compose build

# Layer caching
# Dependencies before code (already optimized)
```

### Image Size

Current sizes:
- HTTP scrapers: ~150-200 MB ✅
- Browser scrapers: ~1.2-1.5 GB (minimum for Playwright)

**Cannot reduce browser images further** (Playwright requires full Debian + Chromium)

### Runtime Performance

```bash
# Use --init for proper signal handling
docker run --init budalert/housing-works

# Limit CPU for stability
docker run --cpus=0.5 budalert/housing-works

# Increase memory for browser
docker run --memory=1g budalert/gotham
```

---

## Maintenance

### Updates

```bash
# Pull latest code
git pull origin scraping-research-exercise

# Rebuild
cd deployment
make build

# Deploy
make deploy-fly  # or deploy-hostinger
```

### Monitoring

```bash
# Resource usage
docker stats

# Logs
docker-compose logs -f --tail=100

# Container health
docker inspect --format='{{.State.Health.Status}}' container_name
```

### Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Clean everything
docker system prune -a --volumes
```

---

## Quick Reference

### Common Commands

```bash
# Build
make build              # All images
make build-http         # HTTP only
make build-browser      # Browser only

# Test
make test               # All scrapers
make test-housing       # Housing Works
make test-gotham        # Gotham

# Deploy
make deploy-fly         # fly.io
make deploy-hostinger   # Hostinger VPS

# Monitor
make status             # Docker status
make logs               # View logs

# Clean
make clean              # Prune Docker
make clean-all          # Remove everything
```

### File Locations

```
deployment/
├── docker/
│   ├── Dockerfile.http        # HTTP base
│   ├── Dockerfile.browser     # Browser base
│   └── .dockerignore          # Build exclusions
├── flyio/
│   ├── *.fly.toml            # fly.io configs
│   └── deploy.sh             # Deployment script
├── hostinger/
│   ├── setup.sh              # Initial setup
│   └── deploy.sh             # Updates
├── Makefile                  # Quick commands
└── docs/
    ├── DOCKER_DEPLOYMENT.md  # This file
    ├── FLYIO_DEPLOYMENT.md   # fly.io guide
    └── HOSTINGER_DEPLOYMENT.md  # Hostinger guide
```

---

**Last Updated:** 2026-03-05 (Phase 6)  
**Version:** 1.0.0
