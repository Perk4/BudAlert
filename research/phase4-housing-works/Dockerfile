# Dockerfile for Housing Works (Blaze) Scraper
# Includes Node.js + Playwright + Chromium

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

# Create app directory
WORKDIR /app

# Install Node dependencies
COPY package*.json ./
RUN npm install
RUN npx playwright install chromium

# Copy scraper code
COPY . .

# Run scraper
CMD ["node", "scraper-playwright.js"]
