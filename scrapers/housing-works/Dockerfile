# Housing Works Scraper - Docker Image
# Lightweight HTTP-only scraper
# Extends: Dockerfile.http (Alpine-based)

FROM node:20-alpine

# Install security updates
RUN apk upgrade --no-cache

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production --ignore-scripts && \
    npm cache clean --force

# Copy scraper code
COPY scraper.mjs ./

# Create non-root user
RUN addgroup -g 1001 -S scraper && \
    adduser -S -D -H -u 1001 -h /app -s /sbin/nologin -G scraper -g scraper scraper && \
    chown -R scraper:scraper /app

USER scraper

# Environment variables
ENV NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "console.log('healthy')" || exit 1

# Run scraper
CMD ["node", "scraper.mjs"]
