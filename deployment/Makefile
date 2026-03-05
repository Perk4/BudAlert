# BudAlert Scrapers - Deployment Makefile
# Quick commands for building, deploying, and managing scrapers

.PHONY: help build test clean deploy-fly deploy-hostinger local status logs

# Colors
CYAN := \033[0;36m
GREEN := \033[0;32m
NC := \033[0m

help: ## Show this help message
	@echo "$(CYAN)BudAlert Scrapers - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================
# Local Development
# ============================================

build: ## Build all Docker images locally
	@echo "$(CYAN)Building all Docker images...$(NC)"
	cd ../scrapers && docker-compose build --parallel

build-http: ## Build HTTP-only scrapers (lightweight)
	@echo "$(CYAN)Building HTTP scrapers...$(NC)"
	cd ../scrapers && docker-compose build housing-works conbud-api

build-browser: ## Build browser scrapers (large)
	@echo "$(CYAN)Building browser scrapers...$(NC)"
	cd ../scrapers && docker-compose build gotham conbud-browser

test: ## Run all scrapers once (test mode)
	@echo "$(CYAN)Running test scrapes...$(NC)"
	cd ../scrapers && docker-compose run --rm housing-works
	cd ../scrapers && docker-compose run --rm gotham
	cd ../scrapers && docker-compose run --rm conbud-api

test-housing: ## Test Housing Works scraper
	cd ../scrapers && docker-compose run --rm housing-works

test-gotham: ## Test Gotham scraper
	cd ../scrapers && docker-compose run --rm gotham

test-conbud: ## Test Conbud API scraper
	cd ../scrapers && docker-compose run --rm conbud-api

local: ## Start all scrapers locally
	@echo "$(CYAN)Starting all scrapers...$(NC)"
	cd ../scrapers && docker-compose up -d

local-logs: ## View local Docker logs
	cd ../scrapers && docker-compose logs -f

local-stop: ## Stop all local scrapers
	@echo "$(CYAN)Stopping scrapers...$(NC)"
	cd ../scrapers && docker-compose down

status: ## Show status of all scrapers
	@echo "$(CYAN)Local Docker Status:$(NC)"
	cd ../scrapers && docker-compose ps
	@echo ""
	@echo "$(CYAN)System Resources:$(NC)"
	docker stats --no-stream

# ============================================
# fly.io Deployment
# ============================================

deploy-fly: ## Deploy all scrapers to fly.io
	@echo "$(CYAN)Deploying to fly.io...$(NC)"
	./flyio/deploy.sh all

deploy-fly-housing: ## Deploy Housing Works to fly.io
	./flyio/deploy.sh housing-works

deploy-fly-gotham: ## Deploy Gotham to fly.io
	./flyio/deploy.sh gotham

deploy-fly-conbud: ## Deploy Conbud API to fly.io
	./flyio/deploy.sh conbud-api

fly-status: ## Check fly.io deployment status
	@echo "$(CYAN)fly.io Status:$(NC)"
	flyctl status --app budalert-housing-works || true
	flyctl status --app budalert-gotham || true
	flyctl status --app budalert-conbud-api || true

fly-logs: ## View fly.io logs (Housing Works)
	flyctl logs --app budalert-housing-works

fly-scale-up: ## Scale up fly.io machines
	flyctl scale count 1 --app budalert-housing-works
	flyctl scale count 1 --app budalert-gotham
	flyctl scale count 1 --app budalert-conbud-api

fly-scale-down: ## Scale down fly.io machines (save costs)
	flyctl scale count 0 --app budalert-housing-works
	flyctl scale count 0 --app budalert-gotham
	flyctl scale count 0 --app budalert-conbud-api

# ============================================
# Hostinger VPS Deployment
# ============================================

deploy-hostinger: ## Deploy updates to Hostinger VPS
	@echo "$(CYAN)Deploying to Hostinger...$(NC)"
	ssh root@$${HOSTINGER_IP} "cd /opt/budalert/budalert/deployment/hostinger && ./deploy.sh"

hostinger-setup: ## Initial Hostinger VPS setup
	@echo "$(CYAN)Setting up Hostinger VPS...$(NC)"
	@echo "IP: $${HOSTINGER_IP}"
	scp hostinger/setup.sh root@$${HOSTINGER_IP}:/root/
	ssh root@$${HOSTINGER_IP} "chmod +x /root/setup.sh && /root/setup.sh"

hostinger-status: ## Check Hostinger VPS status
	@echo "$(CYAN)Hostinger Status:$(NC)"
	ssh root@$${HOSTINGER_IP} "systemctl status budalert-scrapers"

hostinger-logs: ## View Hostinger logs
	ssh root@$${HOSTINGER_IP} "tail -f /opt/budalert/logs/*.log"

# ============================================
# Maintenance
# ============================================

clean: ## Clean up Docker resources
	@echo "$(CYAN)Cleaning Docker resources...$(NC)"
	docker system prune -f
	cd ../scrapers && docker-compose down -v

clean-all: ## Clean everything including images
	@echo "$(CYAN)Cleaning all Docker resources...$(NC)"
	cd ../scrapers && docker-compose down -v --rmi all
	docker system prune -a -f --volumes

update: ## Pull latest code and rebuild
	@echo "$(CYAN)Updating repository...$(NC)"
	cd .. && git pull origin scraping-research-exercise
	$(MAKE) build

logs: ## View all logs (local + remote)
	@echo "$(CYAN)Local logs:$(NC)"
	cd ../scrapers && docker-compose logs --tail=50
	@echo ""
	@echo "For fly.io logs: make fly-logs"
	@echo "For Hostinger logs: make hostinger-logs"

# ============================================
# Documentation
# ============================================

docs: ## Open deployment documentation
	@echo "$(CYAN)Deployment Documentation:$(NC)"
	@echo "  Local:     ../scrapers/README.md"
	@echo "  fly.io:    ./flyio/README.md"
	@echo "  Hostinger: ./hostinger/README.md"
	@echo "  Inventory: ./docs/SCRAPER_INVENTORY.md"

# ============================================
# Environment Setup
# ============================================

env-example: ## Create example .env file
	@echo "# BudAlert Environment Variables" > .env.example
	@echo "HOSTINGER_IP=your.vps.ip.address" >> .env.example
	@echo "FLY_API_TOKEN=your-fly-token" >> .env.example
	@echo "" >> .env.example
	@echo "$(GREEN).env.example created$(NC)"

# ============================================
# Version Info
# ============================================

version: ## Show version and build info
	@echo "$(CYAN)BudAlert Scrapers$(NC)"
	@echo "Version: 1.0.0"
	@echo "Branch: scraping-research-exercise"
	@echo ""
	@echo "Images:"
	@docker images | grep -E "budalert|REPOSITORY"
