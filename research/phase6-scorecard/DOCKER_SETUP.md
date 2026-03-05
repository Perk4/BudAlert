# Docker Environment Setup Guide

**Project**: BudAlert Dispensary Scrapers  
**Platforms**: Dutchie (Conbud), Blaze (Housing Works), WordPress (Gotham)  
**Updated**: 2026-03-05

---

## Overview

This guide provides complete Docker setup instructions for running all three dispensary scrapers in isolated, reproducible environments.

### Why Docker?

- ✅ **Consistent environment** across development and production
- ✅ **Isolated dependencies** (Node.js, Python, Playwright, Chromium)
- ✅ **Easy deployment** to any Docker-compatible platform
- ✅ **No local setup required** (browsers, dependencies auto-installed)
- ✅ **Reproducible builds** (same results everywhere)

---

## Quick Start

### Prerequisites

```bash
# Install Docker
# macOS/Windows: Download Docker Desktop
# Linux: sudo apt-get install docker.io docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Run All Scrapers

```bash
# Clone/navigate to repository
cd ~/clawd/budalert/research

# Build all containers
docker-compose -f docker-compose-all.yml build

# Run Gotham (fastest, no browser)
docker-compose -f docker-compose-all.yml run gotham

# Run Housing Works (Python)
docker-compose -f docker-compose-all.yml run housing-works

# Run Conbud (complex, GraphQL)
docker-compose -f docker-compose-all.yml run conbud
```

---

## Individual Setup Instructions

### 1. Gotham NYC (WordPress)

**Requirements**: Node.js + axios + cheerio (no browser)  
**Image Size**: ~150 MB  
**Memory**: 256 MB recommended  
**Startup Time**: <1 second

#### Dockerfile

```dockerfile
# phase5-gotham/Dockerfile
FROM node:20-alpine

RUN apk add --no-cache curl

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

CMD ["node", "scraper-curl.js"]
```

#### docker-compose.yml

```yaml
# phase5-gotham/docker-compose.yml
version: '3.8'

services:
  gotham-scraper:
    build: .
    container_name: gotham-scraper
    volumes:
      - ./output:/app/output
    environment:
      - NODE_ENV=production
    mem_limit: 512m
    cpus: 1.0
```

#### Build & Run

```bash
cd phase5-gotham

# Build image
docker build -t gotham-scraper .

# Run scraper (curl method)
docker run --rm \
  -v $(pwd)/output:/app/output \
  gotham-scraper \
  node scraper-curl.js

# Run scraper (WordPress API method)
docker run --rm \
  -v $(pwd)/output:/app/output \
  gotham-scraper \
  node scraper-wordpress-api.js

# Using docker-compose
docker-compose up
```

#### Output

```bash
# Check output
ls -lh output/
cat output/gotham-products-*.json | jq '. | length'
```

---

### 2. Housing Works (Blaze)

**Requirements**: Node.js + Playwright + Chromium  
**Image Size**: ~1.5 GB  
**Memory**: 1-2 GB recommended  
**Startup Time**: 5-10 seconds

#### Dockerfile

```dockerfile
# phase4-housing-works/Dockerfile
FROM node:20-bullseye

# Install Playwright system dependencies
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libatspi2.0-0 libwayland-client0 \
    ca-certificates fonts-liberation libappindicator3-1 \
    libu2f-udev xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package*.json ./
RUN npm install
RUN npx playwright install chromium

COPY . .

CMD ["node", "scraper-playwright.js"]
```

#### docker-compose.yml

```yaml
# phase4-housing-works/docker-compose.yml
version: '3.8'

services:
  housing-works-scraper:
    build: .
    container_name: housing-works-scraper
    volumes:
      - ./output:/app/output
      - ./scraper-playwright.js:/app/scraper-playwright.js
      - ./scraper-api-direct.js:/app/scraper-api-direct.js
    environment:
      - PLAYWRIGHT_BROWSERS_PATH=/app/.cache
      - NODE_ENV=production
    stdin_open: true
    tty: true
    mem_limit: 2g
    cpus: 2.0
```

#### Build & Run

```bash
cd phase4-housing-works

# Build image (takes 5-10 minutes first time)
docker build -t housing-works-scraper .

# Run browser scraper
docker run --rm \
  -v $(pwd)/output:/app/output \
  housing-works-scraper \
  node scraper-playwright.js

# Run API discovery
docker run --rm \
  -v $(pwd)/output:/app/output \
  housing-works-scraper \
  node scraper-api-direct.js discover output/housing-works-api-requests-*.json

# Using docker-compose
docker-compose up
```

#### Python Alternative

```dockerfile
# Alternative: Python version of Housing Works scraper
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip3 install playwright asyncio
RUN playwright install chromium

COPY memory/stealth-scraper/scrapers/ /app/scrapers/

CMD ["python3", "/app/scrapers/blaze/housing_works.py"]
```

---

### 3. Conbud LES (Dutchie)

**Requirements**: Node.js + Playwright + Chromium  
**Image Size**: ~1.5 GB  
**Memory**: 1-2 GB recommended  
**Startup Time**: 5-10 seconds

#### Dockerfile

```dockerfile
# phase3-conbud/Dockerfile
FROM node:20-bullseye

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libatspi2.0-0 libwayland-client0 \
    ca-certificates fonts-liberation libappindicator3-1 \
    libu2f-udev xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package*.json ./
RUN npm install
RUN npx playwright install chromium

COPY . .

CMD ["node", "scraper-network-intercept.js"]
```

#### docker-compose.yml

```yaml
# phase3-conbud/docker-compose.yml
version: '3.8'

services:
  conbud-scraper:
    build: .
    container_name: conbud-scraper
    volumes:
      - ./output:/app/output
      - ./scraper-network-intercept.js:/app/scraper-network-intercept.js
      - ./scraper-graphql-direct.js:/app/scraper-graphql-direct.js
    environment:
      - PLAYWRIGHT_BROWSERS_PATH=/app/.cache
      - NODE_ENV=production
    stdin_open: true
    tty: true
    mem_limit: 2g
    cpus: 2.0
```

#### Build & Run

```bash
cd phase3-conbud

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

# Using docker-compose
docker-compose up
```

---

## Unified docker-compose

### All Scrapers Together

Create `research/docker-compose-all.yml`:

```yaml
version: '3.8'

services:
  # Gotham NYC (WordPress - Fastest)
  gotham:
    build: ./phase5-gotham
    container_name: gotham-scraper
    volumes:
      - ./output/gotham:/app/output
    environment:
      - NODE_ENV=production
    mem_limit: 512m
    cpus: 1.0

  # Housing Works (Blaze - Medium)
  housing-works:
    build: ./phase4-housing-works
    container_name: housing-works-scraper
    volumes:
      - ./output/housing-works:/app/output
    environment:
      - PLAYWRIGHT_BROWSERS_PATH=/app/.cache
      - NODE_ENV=production
    mem_limit: 2g
    cpus: 2.0

  # Conbud LES (Dutchie - Complex)
  conbud:
    build: ./phase3-conbud
    container_name: conbud-scraper
    volumes:
      - ./output/conbud:/app/output
    environment:
      - PLAYWRIGHT_BROWSERS_PATH=/app/.cache
      - NODE_ENV=production
    mem_limit: 2g
    cpus: 2.0

# Shared network (optional)
networks:
  default:
    name: budalert-scrapers
```

### Usage

```bash
cd ~/clawd/budalert/research

# Build all images
docker-compose -f docker-compose-all.yml build

# Run all scrapers in parallel
docker-compose -f docker-compose-all.yml up

# Run individual scraper
docker-compose -f docker-compose-all.yml run gotham
docker-compose -f docker-compose-all.yml run housing-works
docker-compose -f docker-compose-all.yml run conbud

# Run all in sequence
docker-compose -f docker-compose-all.yml run gotham && \
docker-compose -f docker-compose-all.yml run housing-works && \
docker-compose -f docker-compose-all.yml run conbud

# Clean up
docker-compose -f docker-compose-all.yml down
```

---

## Production Deployment

### AWS ECS/Fargate

```yaml
# task-definition.json
{
  "family": "budalert-scrapers",
  "containerDefinitions": [
    {
      "name": "gotham-scraper",
      "image": "your-registry/gotham-scraper:latest",
      "memory": 512,
      "cpu": 256,
      "essential": false
    },
    {
      "name": "housing-works-scraper",
      "image": "your-registry/housing-works-scraper:latest",
      "memory": 2048,
      "cpu": 1024,
      "essential": false
    },
    {
      "name": "conbud-scraper",
      "image": "your-registry/conbud-scraper:latest",
      "memory": 2048,
      "cpu": 1024,
      "essential": false
    }
  ]
}
```

### Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gotham-scraper
spec:
  replicas: 1
  selector:
    matchLabels:
      app: gotham-scraper
  template:
    metadata:
      labels:
        app: gotham-scraper
    spec:
      containers:
      - name: scraper
        image: gotham-scraper:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### GitHub Actions (Scheduled)

```yaml
# .github/workflows/scrape.yml
name: Run Dispensary Scrapers

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Gotham scraper
        run: |
          cd research/phase5-gotham
          docker-compose up
      
      - name: Run Housing Works scraper
        run: |
          cd research/phase4-housing-works
          docker-compose up
      
      - name: Run Conbud scraper
        run: |
          cd research/phase3-conbud
          docker-compose up
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: scraper-results
          path: research/output/**/*.json
```

---

## Troubleshooting

### Issue: Docker build fails

**Error**: `Cannot find module ...`

**Solution**: Ensure package.json is in the directory
```bash
cd phase3-conbud
ls -la package.json  # Verify it exists
docker build -t conbud-scraper .
```

### Issue: Playwright dependencies missing

**Error**: `Host system is missing dependencies`

**Solution**: Use full Debian base (not Alpine)
```dockerfile
FROM node:20-bullseye  # ← Use this, not node:20-alpine
```

### Issue: Container runs out of memory

**Error**: Container killed (exit code 137)

**Solution**: Increase memory limit
```yaml
mem_limit: 4g  # Increase from 2g
```

### Issue: Browser won't launch in Docker

**Error**: `Failed to launch chromium`

**Solution 1**: Add required capabilities
```yaml
cap_add:
  - SYS_ADMIN
```

**Solution 2**: Use --no-sandbox flag (already in code)
```javascript
args: ['--no-sandbox', '--disable-setuid-sandbox']
```

### Issue: Output files not persisting

**Error**: JSON files disappear after container stops

**Solution**: Verify volume mount
```bash
docker run --rm \
  -v $(pwd)/output:/app/output \  # ← Mount output directory
  scraper \
  node scraper.js
```

---

## Performance Optimization

### Multi-Stage Builds

```dockerfile
# Build stage
FROM node:20-bullseye AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
RUN npx playwright install chromium

# Runtime stage
FROM node:20-bullseye-slim
WORKDIR /app

# Copy only necessary files
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /root/.cache/ms-playwright ./ms-playwright
COPY . .

CMD ["node", "scraper.js"]
```

### Layer Caching

```dockerfile
# Copy package files first (cached if unchanged)
COPY package*.json ./
RUN npm install

# Copy code last (changes frequently)
COPY . .
```

### Image Size Reduction

```bash
# Before optimization
gotham-scraper        150 MB
housing-works-scraper 1.5 GB
conbud-scraper        1.5 GB

# After optimization (multi-stage + slim base)
gotham-scraper        80 MB
housing-works-scraper 800 MB
conbud-scraper        800 MB
```

---

## Environment Variables

### Supported Variables

```yaml
environment:
  # Node.js
  - NODE_ENV=production
  - NODE_OPTIONS=--max-old-space-size=2048
  
  # Playwright
  - PLAYWRIGHT_BROWSERS_PATH=/app/.cache
  - PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
  
  # Scraper settings
  - HEADLESS=true
  - TIMEOUT=30000
  - RETRY_COUNT=3
  
  # Proxy (optional)
  - HTTP_PROXY=http://proxy:8080
  - HTTPS_PROXY=http://proxy:8080
  
  # Age verification
  - AGE_VERIFICATION_COOKIE=age_verified=1
```

### Secrets Management

```bash
# Use .env file (NOT committed to git)
echo "AGE_VERIFICATION_COOKIE=age_verified=1" > .env

# Load in docker-compose
env_file:
  - .env
```

---

## Monitoring & Logging

### Container Logs

```bash
# View logs
docker logs gotham-scraper
docker logs -f housing-works-scraper  # Follow mode

# Save logs
docker logs conbud-scraper > logs/conbud.log 2>&1
```

### Health Checks

```dockerfile
# Add to Dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD node -e "console.log('OK')" || exit 1
```

```yaml
# Add to docker-compose.yml
healthcheck:
  test: ["CMD", "node", "-e", "console.log('OK')"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

## Next Steps

1. ✅ Review this guide
2. ⏳ Install Docker Desktop
3. ⏳ Build images for each scraper
4. ⏳ Test locally with `docker-compose up`
5. ⏳ Deploy to production environment
6. ⏳ Set up scheduled runs (cron, GitHub Actions, etc.)

---

**Docker Setup Complete** ✅  
See IMPLEMENTATION_GUIDE.md for step-by-step execution instructions.
