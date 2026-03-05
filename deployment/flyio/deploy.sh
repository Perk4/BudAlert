#!/bin/bash
# fly.io Deployment Script
# Deploys all BudAlert scrapers to fly.io

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 BudAlert Scrapers - fly.io Deployment"
echo "========================================"
echo ""

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo -e "${RED}❌ flyctl not found${NC}"
    echo "Install: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo -e "${RED}❌ Not logged in to fly.io${NC}"
    echo "Run: flyctl auth login"
    exit 1
fi

echo -e "${GREEN}✅ flyctl found and authenticated${NC}"
echo ""

# Get deployment mode
MODE=${1:-all}

deploy_scraper() {
    local name=$1
    local config=$2
    local target=${3:-""}
    
    echo ""
    echo -e "${YELLOW}📦 Deploying $name...${NC}"
    echo "   Config: $config"
    
    cd ~/clawd/budalert
    
    if [ -n "$target" ]; then
        echo "   Build target: $target"
        flyctl deploy -c "$config" --build-target "$target"
    else
        flyctl deploy -c "$config"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $name deployed successfully${NC}"
    else
        echo -e "${RED}❌ $name deployment failed${NC}"
        exit 1
    fi
}

case $MODE in
    housing-works)
        deploy_scraper "Housing Works" "deployment/flyio/housing-works.fly.toml"
        ;;
    
    gotham)
        deploy_scraper "Gotham NYC" "deployment/flyio/gotham.fly.toml"
        ;;
    
    conbud-api)
        deploy_scraper "Conbud API" "deployment/flyio/conbud-api.fly.toml" "api-base"
        ;;
    
    conbud-browser)
        deploy_scraper "Conbud Browser" "deployment/flyio/conbud-browser.fly.toml" "browser"
        ;;
    
    all)
        echo "Deploying all scrapers..."
        deploy_scraper "Housing Works" "deployment/flyio/housing-works.fly.toml"
        deploy_scraper "Gotham NYC" "deployment/flyio/gotham.fly.toml"
        deploy_scraper "Conbud API" "deployment/flyio/conbud-api.fly.toml" "api-base"
        
        echo ""
        echo -e "${YELLOW}ℹ️  Skipping Conbud Browser (use on-demand only)${NC}"
        echo "   Deploy manually: ./deploy.sh conbud-browser"
        ;;
    
    *)
        echo -e "${RED}❌ Invalid mode: $MODE${NC}"
        echo "Usage: $0 [housing-works|gotham|conbud-api|conbud-browser|all]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Check status: flyctl status --app budalert-housing-works"
echo "  2. View logs: flyctl logs --app budalert-housing-works"
echo "  3. Scale: flyctl scale count 1 --app budalert-housing-works"
echo "  4. Monitor: flyctl dashboard"
