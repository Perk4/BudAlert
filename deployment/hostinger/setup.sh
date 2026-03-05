#!/bin/bash
# Hostinger VPS Setup Script
# Installs Docker, configures environment, deploys BudAlert scrapers

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 BudAlert Scrapers - Hostinger VPS Setup"
echo "==========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root (or use sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Running as root${NC}"

# 1. Update system
echo ""
echo -e "${YELLOW}📦 Updating system packages...${NC}"
apt-get update -y
apt-get upgrade -y
apt-get install -y curl git ca-certificates gnupg lsb-release

# 2. Install Docker
if ! command -v docker &> /dev/null; then
    echo ""
    echo -e "${YELLOW}🐳 Installing Docker...${NC}"
    
    # Add Docker's official GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Start Docker
    systemctl start docker
    systemctl enable docker
    
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

# 3. Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo ""
    echo -e "${YELLOW}📦 Installing Docker Compose...${NC}"
    
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

# 4. Create deployment user
if ! id -u budalert &>/dev/null; then
    echo ""
    echo -e "${YELLOW}👤 Creating deployment user 'budalert'...${NC}"
    
    useradd -m -s /bin/bash budalert
    usermod -aG docker budalert
    
    echo -e "${GREEN}✅ User created and added to docker group${NC}"
else
    echo -e "${GREEN}✅ User 'budalert' already exists${NC}"
fi

# 5. Create app directory
echo ""
echo -e "${YELLOW}📁 Creating app directory...${NC}"
mkdir -p /opt/budalert
mkdir -p /opt/budalert/output
mkdir -p /opt/budalert/logs
chown -R budalert:budalert /opt/budalert
echo -e "${GREEN}✅ Directory created: /opt/budalert${NC}"

# 6. Clone repository
echo ""
echo -e "${YELLOW}📥 Cloning BudAlert repository...${NC}"
cd /opt/budalert

if [ -d "budalert/.git" ]; then
    echo "Repository already exists, pulling latest..."
    cd budalert
    sudo -u budalert git pull
else
    sudo -u budalert git clone https://github.com/Perk4/BudAlert.git budalert
    cd budalert
    sudo -u budalert git checkout scraping-research-exercise
fi

echo -e "${GREEN}✅ Repository cloned${NC}"

# 7. Create environment file
echo ""
echo -e "${YELLOW}📝 Creating environment configuration...${NC}"
cat > /opt/budalert/.env << EOF
# BudAlert Environment Configuration
NODE_ENV=production
SCRAPER_TIMEOUT=30000
HEADLESS=true
TZ=America/New_York

# Output paths
OUTPUT_DIR=/app/output
LOG_DIR=/app/logs
EOF

chown budalert:budalert /opt/budalert/.env
echo -e "${GREEN}✅ Environment file created${NC}"

# 8. Build Docker images
echo ""
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
cd /opt/budalert/budalert/scrapers

sudo -u budalert docker-compose build --parallel

echo -e "${GREEN}✅ Images built${NC}"

# 9. Set up systemd services
echo ""
echo -e "${YELLOW}⚙️  Creating systemd services...${NC}"

# Service for docker-compose
cat > /etc/systemd/system/budalert-scrapers.service << EOF
[Unit]
Description=BudAlert Scrapers
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/budalert/budalert/scrapers
User=budalert
Group=budalert
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable budalert-scrapers.service

echo -e "${GREEN}✅ Systemd service created${NC}"

# 10. Set up cron jobs for scheduled scraping
echo ""
echo -e "${YELLOW}⏰ Setting up cron jobs...${NC}"

# Add cron jobs for user budalert
sudo -u budalert crontab - << EOF
# BudAlert Scraper Cron Jobs
# Run scrapers every 6 hours

# Housing Works - Every 6 hours
0 */6 * * * cd /opt/budalert/budalert/scrapers && docker-compose run --rm housing-works >> /opt/budalert/logs/housing-works.log 2>&1

# Gotham NYC - Every 6 hours (offset by 2 hours)
0 2,8,14,20 * * * cd /opt/budalert/budalert/scrapers && docker-compose run --rm gotham >> /opt/budalert/logs/gotham.log 2>&1

# Conbud API - Every 6 hours (offset by 4 hours)
0 4,10,16,22 * * * cd /opt/budalert/budalert/scrapers && docker-compose run --rm conbud-api >> /opt/budalert/logs/conbud-api.log 2>&1

# Log cleanup - Daily at 3 AM
0 3 * * * find /opt/budalert/logs -name "*.log" -mtime +7 -delete
0 3 * * * find /opt/budalert/output -name "*.json" -mtime +30 -delete
EOF

echo -e "${GREEN}✅ Cron jobs configured${NC}"

# 11. Configure firewall (if ufw is available)
if command -v ufw &> /dev/null; then
    echo ""
    echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
    
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    
    echo -e "${GREEN}✅ Firewall configured${NC}"
fi

# 12. Configure log rotation
echo ""
echo -e "${YELLOW}📋 Setting up log rotation...${NC}"

cat > /etc/logrotate.d/budalert << EOF
/opt/budalert/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 budalert budalert
    sharedscripts
}
EOF

echo -e "${GREEN}✅ Log rotation configured${NC}"

# 13. Start services
echo ""
echo -e "${YELLOW}🚀 Starting services...${NC}"
systemctl start budalert-scrapers.service

echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Check service status: systemctl status budalert-scrapers"
echo "  2. View logs: docker-compose -f /opt/budalert/budalert/scrapers/docker-compose.yml logs"
echo "  3. Test scraper: docker-compose -f /opt/budalert/budalert/scrapers/docker-compose.yml run housing-works"
echo "  4. Monitor cron: tail -f /opt/budalert/logs/*.log"
echo ""
echo "Service management:"
echo "  Start:   systemctl start budalert-scrapers"
echo "  Stop:    systemctl stop budalert-scrapers"
echo "  Restart: systemctl restart budalert-scrapers"
echo "  Status:  systemctl status budalert-scrapers"
echo ""
echo "Data locations:"
echo "  App:     /opt/budalert/budalert"
echo "  Output:  /opt/budalert/output"
echo "  Logs:    /opt/budalert/logs"
