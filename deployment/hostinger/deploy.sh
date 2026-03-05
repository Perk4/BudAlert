#!/bin/bash
# Hostinger VPS Deployment Script
# Deploys updates to existing Hostinger installation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 BudAlert Scrapers - Hostinger Deployment"
echo "==========================================="
echo ""

# Check if running on Hostinger VPS
if [ ! -d "/opt/budalert" ]; then
    echo -e "${RED}❌ /opt/budalert not found${NC}"
    echo "Run setup.sh first to initialize the VPS"
    exit 1
fi

# Switch to app directory
cd /opt/budalert/budalert

# Pull latest code
echo -e "${YELLOW}📥 Pulling latest code...${NC}"
sudo -u budalert git pull origin scraping-research-exercise

# Rebuild images
echo ""
echo -e "${YELLOW}🔨 Rebuilding Docker images...${NC}"
cd scrapers
sudo -u budalert docker-compose build --parallel

# Restart services
echo ""
echo -e "${YELLOW}♻️  Restarting services...${NC}"
sudo -u budalert docker-compose down
sudo -u budalert docker-compose up -d

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Check status:"
echo "  docker-compose -f /opt/budalert/budalert/scrapers/docker-compose.yml ps"
echo ""
echo "View logs:"
echo "  docker-compose -f /opt/budalert/budalert/scrapers/docker-compose.yml logs -f"
