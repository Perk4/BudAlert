# Conbud LES Scraper - Docker Image
# Supports both API and browser modes
# Default: API mode (lightweight)
# Browser mode available via CMD override

FROM node:20-alpine AS api-base

# Install security updates
RUN apk upgrade --no-cache

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (without Playwright for API mode)
RUN npm ci --only=production --ignore-scripts && \
    npm cache clean --force

# Copy scraper code
COPY *.mjs ./

# Create non-root user
RUN addgroup -g 1001 -S scraper && \
    adduser -S -D -H -u 1001 -h /app -s /sbin/nologin -G scraper -g scraper scraper && \
    chown -R scraper:scraper /app

USER scraper

ENV NODE_ENV=production

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "console.log('healthy')" || exit 1

# Default to API scraper (fast, lightweight)
CMD ["node", "api-scraper.mjs"]

# ============================================
# Browser variant (for query extraction)
# Build with: docker build --target browser -t conbud-scraper:browser .
# ============================================

FROM mcr.microsoft.com/playwright:v1.40.0-jammy AS browser

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get update && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package*.json ./

RUN npm ci --only=production && \
    npm cache clean --force && \
    npx playwright install chromium && \
    npx playwright install-deps chromium

COPY *.mjs ./

RUN groupadd -g 1001 scraper && \
    useradd -r -u 1001 -g scraper scraper && \
    chown -R scraper:scraper /app

USER scraper

ENV NODE_ENV=production \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    HEADLESS=true

HEALTHCHECK --interval=60s --timeout=30s --start-period=15s --retries=3 \
  CMD node -e "console.log('healthy')" || exit 1

CMD ["node", "browser-scraper.mjs"]
