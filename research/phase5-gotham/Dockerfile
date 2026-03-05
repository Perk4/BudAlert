# Dockerfile for Gotham (WordPress) Scraper
# Simple Node.js setup (no browser needed)

FROM node:20-alpine

# Install curl for testing
RUN apk add --no-cache curl

# Create app directory
WORKDIR /app

# Install Node dependencies
COPY package*.json ./
RUN npm install

# Copy scraper code
COPY . .

# Run scraper
CMD ["node", "scraper-curl.js"]
