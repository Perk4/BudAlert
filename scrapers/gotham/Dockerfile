# Gotham NYC Scraper - Docker Image
# Supports both HTTP and browser modes
# Extends: Dockerfile.browser (handles both scenarios)

FROM mcr.microsoft.com/playwright:v1.40.0-jammy

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get update && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Install Playwright Chromium
RUN npx playwright install chromium && \
    npx playwright install-deps chromium

# Copy scraper code
COPY *.mjs ./

# Create non-root user
RUN groupadd -g 1001 scraper && \
    useradd -r -u 1001 -g scraper scraper && \
    chown -R scraper:scraper /app

USER scraper

# Environment variables
ENV NODE_ENV=production \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    HEADLESS=true

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=15s --retries=3 \
  CMD node -e "console.log('healthy')" || exit 1

# Default to browser scraper (handles Cloudflare)
# Override with: docker run gotham-scraper node scraper.mjs
CMD ["node", "scraper-browser.mjs"]
