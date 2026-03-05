# Hostinger VPS Deployment Guide

Deploy BudAlert scrapers to Hostinger VPS using Docker and systemd.

## Prerequisites

### 1. Hostinger VPS Requirements
- **VPS Plan:** Minimum KVM 1 or Cloud Startup
- **OS:** Ubuntu 20.04 or 22.04 LTS
- **RAM:** 2 GB minimum (4 GB recommended for browser scrapers)
- **Storage:** 20 GB minimum (40 GB recommended)
- **vCPU:** 1 core minimum (2 cores recommended)

### 2. Access
- SSH access to your Hostinger VPS
- Root or sudo privileges
- Public IP address

### 3. Domain (Optional)
- Point domain to VPS IP for API endpoints
- Set up SSL with Let's Encrypt (optional)

## Quick Setup (Automated)

### 1. SSH into VPS
```bash
ssh root@your-vps-ip
```

### 2. Download and Run Setup Script
```bash
curl -fsSL https://raw.githubusercontent.com/Perk4/BudAlert/scraping-research-exercise/deployment/hostinger/setup.sh -o setup.sh
chmod +x setup.sh
sudo ./setup.sh
```

The script will:
- ✅ Install Docker and Docker Compose
- ✅ Create deployment user (`budalert`)
- ✅ Clone BudAlert repository
- ✅ Build Docker images
- ✅ Set up systemd services
- ✅ Configure cron jobs for scheduled scraping
- ✅ Set up log rotation
- ✅ Configure firewall

**Setup time:** ~10-15 minutes

## Manual Setup

### 1. Install Docker
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. Create Deployment User
```bash
sudo useradd -m -s /bin/bash budalert
sudo usermod -aG docker budalert
```

### 3. Clone Repository
```bash
sudo mkdir -p /opt/budalert
sudo chown budalert:budalert /opt/budalert

# Switch to budalert user
sudo su - budalert

# Clone repo
cd /opt/budalert
git clone https://github.com/Perk4/BudAlert.git budalert
cd budalert
git checkout scraping-research-exercise
```

### 4. Build Images
```bash
cd /opt/budalert/budalert/scrapers
docker-compose build
```

### 5. Create Systemd Service
```bash
# Exit budalert user back to root
exit

# Create service file
sudo nano /etc/systemd/system/budalert-scrapers.service
```

Paste:
```ini
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
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable budalert-scrapers.service
sudo systemctl start budalert-scrapers.service
```

### 6. Set Up Cron Jobs
```bash
# Switch to budalert user
sudo su - budalert

# Edit crontab
crontab -e
```

Add:
```cron
# Housing Works - Every 6 hours
0 */6 * * * cd /opt/budalert/budalert/scrapers && docker-compose run --rm housing-works >> /opt/budalert/logs/housing-works.log 2>&1

# Gotham NYC - Every 6 hours (offset)
0 2,8,14,20 * * * cd /opt/budalert/budalert/scrapers && docker-compose run --rm gotham >> /opt/budalert/logs/gotham.log 2>&1

# Conbud API - Every 6 hours (offset)
0 4,10,16,22 * * * cd /opt/budalert/budalert/scrapers && docker-compose run --rm conbud-api >> /opt/budalert/logs/conbud-api.log 2>&1

# Cleanup old files
0 3 * * * find /opt/budalert/logs -name "*.log" -mtime +7 -delete
0 3 * * * find /opt/budalert/output -name "*.json" -mtime +30 -delete
```

## Deployment

### Initial Deployment
```bash
# Already done by setup.sh
systemctl status budalert-scrapers
```

### Update Deployment
```bash
# SSH into VPS
ssh root@your-vps-ip

# Run deployment script
cd /opt/budalert/budalert/deployment/hostinger
./deploy.sh
```

Or manually:
```bash
cd /opt/budalert/budalert
sudo -u budalert git pull origin scraping-research-exercise
cd scrapers
sudo -u budalert docker-compose build
sudo -u budalert docker-compose down
sudo -u budalert docker-compose up -d
```

## Monitoring

### Service Status
```bash
# Check systemd service
sudo systemctl status budalert-scrapers

# Check Docker containers
sudo docker ps

# Check with docker-compose
cd /opt/budalert/budalert/scrapers
sudo -u budalert docker-compose ps
```

### View Logs
```bash
# Real-time Docker logs
cd /opt/budalert/budalert/scrapers
sudo -u budalert docker-compose logs -f

# Specific scraper
sudo -u budalert docker-compose logs -f housing-works

# Cron job logs
tail -f /opt/budalert/logs/*.log

# System logs
sudo journalctl -u budalert-scrapers -f
```

### Resource Usage
```bash
# Docker stats
sudo docker stats

# System resources
htop  # Install: sudo apt-get install htop

# Disk usage
df -h
du -sh /opt/budalert/*
```

## Management

### Start/Stop Services
```bash
# Start all
sudo systemctl start budalert-scrapers

# Stop all
sudo systemctl stop budalert-scrapers

# Restart
sudo systemctl restart budalert-scrapers

# Individual scraper
cd /opt/budalert/budalert/scrapers
sudo -u budalert docker-compose up -d housing-works
sudo -u budalert docker-compose stop gotham
```

### Manual Scrape
```bash
cd /opt/budalert/budalert/scrapers

# Run once
sudo -u budalert docker-compose run --rm housing-works

# Run with output saved
sudo -u budalert docker-compose run --rm housing-works > /opt/budalert/output/manual-$(date +%Y%m%d-%H%M%S).json
```

### Update Scrapers
```bash
# Pull latest code
cd /opt/budalert/budalert
sudo -u budalert git pull

# Rebuild and restart
cd scrapers
sudo -u budalert docker-compose build
sudo systemctl restart budalert-scrapers
```

## Data Management

### Output Files
```bash
# View scraped data
ls -lh /opt/budalert/output/

# Latest file
ls -t /opt/budalert/output/*.json | head -1 | xargs cat | jq .

# Count products in latest file
cat $(ls -t /opt/budalert/output/*.json | head -1) | jq '.products | length'
```

### Backup
```bash
# Backup output data
sudo tar -czf budalert-backup-$(date +%Y%m%d).tar.gz /opt/budalert/output/

# Download to local machine
scp root@your-vps-ip:/root/budalert-backup-*.tar.gz ./

# Automated backup to external storage (optional)
# Set up rclone to S3, Dropbox, etc.
```

### Cleanup
```bash
# Remove old JSON files (>30 days)
find /opt/budalert/output -name "*.json" -mtime +30 -delete

# Remove old logs (>7 days)
find /opt/budalert/logs -name "*.log" -mtime +7 -delete

# Clean Docker images
sudo docker system prune -a
```

## Security

### Firewall
```bash
# Enable UFW
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Check status
sudo ufw status
```

### SSH Hardening
```bash
# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no

# Use key-based auth only
# Set: PasswordAuthentication no

# Restart SSH
sudo systemctl restart sshd
```

### Updates
```bash
# Auto-updates
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades

# Manual updates
sudo apt-get update
sudo apt-get upgrade -y
```

## Costs

### Hostinger VPS Pricing (2026)
- **KVM 1:** $4.99/mo - 1 vCPU, 4 GB RAM, 50 GB SSD
- **KVM 2:** $6.99/mo - 2 vCPU, 8 GB RAM, 100 GB SSD
- **Cloud Startup:** $8.99/mo - 2 vCPU, 8 GB RAM, 200 GB NVMe

**Recommended:** KVM 1 ($4.99/mo) is sufficient for all scrapers

### Resource Requirements
- HTTP scrapers: ~256 MB RAM each
- Browser scrapers: ~1 GB RAM each
- **Total:** ~2.5 GB RAM for all scrapers running simultaneously

## Troubleshooting

### Docker daemon not running
```bash
sudo systemctl start docker
sudo systemctl status docker
```

### Permission denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Out of disk space
```bash
# Check usage
df -h

# Clean Docker
sudo docker system prune -a --volumes

# Clean old data
find /opt/budalert/output -mtime +30 -delete
```

### Scraper failing
```bash
# Check logs
sudo -u budalert docker-compose logs housing-works

# Run manually to debug
sudo -u budalert docker-compose run --rm housing-works

# Rebuild image
sudo -u budalert docker-compose build --no-cache housing-works
```

### Cron jobs not running
```bash
# Check cron service
sudo systemctl status cron

# View cron logs
grep CRON /var/log/syslog

# Test cron command manually
cd /opt/budalert/budalert/scrapers && docker-compose run --rm housing-works
```

## Advanced

### Add SSL Certificate (Optional)
```bash
# Install Certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Configure nginx (if serving API)
# ...
```

### Set Up Monitoring (Optional)
```bash
# Install Netdata for system monitoring
bash <(curl -Ss https://my-netdata.io/kickstart.sh)

# Access at: http://your-vps-ip:19999
```

### Remote Logging (Optional)
```bash
# Forward logs to external service
# Configure syslog, Papertrail, Loggly, etc.
```

## Next Steps

- [ ] Complete VPS setup
- [ ] Test all scrapers
- [ ] Verify cron jobs
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Harden security
- [ ] Document access credentials

---

**Created:** 2026-03-05 (Phase 5)  
**Status:** ✅ Ready for Hostinger deployment
