# Stealth Scraper Monitoring & Alerting Infrastructure

Unified monitoring, alerting, and operational visibility system for the stealth scraper infrastructure covering 15+ cannabis dispensary stores across multiple platforms.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Individual    │    │    Monitoring    │    │    Alerting     │
│    Scrapers     │───▶│    Dashboard     │───▶│     System      │
│                 │    │                  │    │                 │
│ • Housing Works │    │ • Metrics Calc   │    │ • Webhook       │
│ • CONBUD        │    │ • Health Checks  │    │ • Email         │
│ • Torches       │    │ • Status Agg     │    │ • Console       │
│ • + 12 more     │    │ • SQLite DB      │    │ • Slack/Discord │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Unified       │    │   Operational    │    │    Logging      │
│   Logs          │    │     Scripts      │    │ Infrastructure  │
│                 │    │                  │    │                 │
│ • JSON Format   │    │ • run_all.sh     │    │ • Rotation      │
│ • Daily Files   │    │ • status.sh      │    │ • Aggregation   │
│ • Error Logs    │    │ • repair.sh      │    │ • Structured    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Components

### 1. Dashboard System (`dashboard.py`)
Central aggregation point for all store status and metrics.

**Features:**
- Real-time status for all 15+ stores
- Success rate tracking (1h, 24h, 7d)
- Product extraction counts
- Platform-based grouping
- SQLite database for metrics storage

**Usage:**
```bash
# Quick overview
python3 dashboard.py

# JSON output
python3 dashboard.py --json

# Specific store
python3 dashboard.py --store housing-works

# Save snapshot
python3 dashboard.py --save
```

### 2. Metrics Calculator (`metrics.py`)
Advanced analytics and trend analysis.

**Key Metrics:**
- Success rate trends
- Latency analysis (avg, p95)
- Cost per product calculations
- Platform performance comparison
- Uptime percentages

**Usage:**
```bash
# Infrastructure-wide metrics
python3 metrics.py --infrastructure

# Store-specific metrics
python3 metrics.py --store conbud

# JSON output for integration
python3 metrics.py --infrastructure --json
```

### 3. Health Checker (`health_checker.py`)
Proactive health monitoring with async checks.

**Checks Performed:**
- Site reachability (response time < 5s)
- Product extraction capability (min 1 product)
- End-to-end latency (< 60s threshold)
- Error detection and categorization

**Usage:**
```bash
# Check active stores
python3 health_checker.py

# Check specific stores
python3 health_checker.py --stores housing-works conbud

# Check all configured stores
python3 health_checker.py --all

# Save results to health_status.json
python3 health_checker.py --save
```

### 4. Alerting System (`alerter.py`)
Intelligent alerting with multiple channels and cooldown periods.

**Alert Triggers:**
- 3+ consecutive failures
- Success rate < 80% (warning) / < 50% (critical)
- No successful extraction in 6+ hours
- Product count drop > 50%

**Alert Channels:**
- Console/log output
- Webhook (Slack/Discord)
- Email (SMTP)

**Usage:**
```bash
# Run alert check cycle
python3 alerter.py --check

# Send test alert
python3 alerter.py --test housing-works

# Show configuration
python3 alerter.py --config
```

### 5. Operational Scripts

#### `run_all.sh` - Execute All Scrapers
```bash
# Run active stores only
./run_all.sh

# Run all configured stores
./run_all.sh all

# Run specific store
./run_all.sh housing-works
```

#### `status.sh` - Quick Status Overview
```bash
# Summary view
./status.sh

# Complete status report
./status.sh all

# Specific components
./status.sh health
./status.sh alerts
./status.sh activity
```

#### `repair.sh` - Automated Repair System
```bash
# Auto-repair failed stores
./repair.sh

# Identify problems only
./repair.sh identify

# Get repair recommendations
./repair.sh recommendations housing-works

# Force repair specific store
./repair.sh force housing-works
```

### 6. Logging Infrastructure (`logging_config.py`)
Unified logging with structured output and automatic rotation.

**Log Files:**
- `stealth_scraper_unified.log` - JSON structured logs
- `stealth_scraper_errors.log` - Human-readable errors
- `daily/scraper_activity_YYYY-MM-DD.log` - Daily activity

**Features:**
- Automatic log rotation (50MB unified, 10MB errors)
- 30-day retention policy
- Structured JSON format for parsing
- Store-specific context injection

## Store Configuration

The monitoring system tracks 15+ stores across multiple platforms:

### Production Stores (Phase 5 - Active)
- **Housing Works** (Blaze) - 26 products
- **CONBUD** (Dutchie Embed) - 26 products  
- **Torches** (Joint Ecommerce) - 6 products
- **Stoops** (Joint Ecommerce) - 4 products

### Development Pipeline (Phase 6 - Inactive)
- **Alta** (Joint Ecommerce) - Framework ready
- **Easy Custom Sites** (5 stores): Smacked Village, Yerba Buena, Terp Bros, FlynnStoned, Happy Munkey
- **Medium Custom Sites** (6 stores): Travel Agency, Gotham, Dazed, Green Apple, Chelsea Cannabis, Verilife
- **LeafBridge Platform** (1 store): QUBE NYC
- **Hard Targets** (2 stores): RISE (Jane + CF), Curaleaf (MSO + CF)

## Alert Configuration

### Configure Webhooks

Edit `monitoring/alert_config.json`:

```json
{
  "channels": {
    "webhook": {
      "enabled": true,
      "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
      "format": "slack"
    }
  },
  "thresholds": {
    "consecutive_failure_limit": 3,
    "success_rate_warning": 80,
    "success_rate_critical": 50,
    "max_hours_without_success": 6,
    "product_count_drop_percentage": 50
  }
}
```

### Configure Email Alerts

```json
{
  "channels": {
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "your-email@gmail.com",
      "password": "your-app-password",
      "from_email": "scraper-alerts@yourdomain.com",
      "to_emails": ["admin@yourdomain.com", "ops@yourdomain.com"]
    }
  }
}
```

## Dashboard Viewing

### Quick Status Check
```bash
./status.sh
```

Output:
```
╔══════════════════════════════════════╗
║        STEALTH SCRAPER DASHBOARD        ║
╚══════════════════════════════════════╝

📊 Overview:
   Total Stores: 15
   Active Stores: 4
   Products Extracted (Total): 62
   Overall Success Rate: 85.2%

🏥 Health Status:
   Healthy: 3 ✅
   Warning: 1 ⚠️
   Critical: 0 ❌
```

### Detailed Store Status
```bash
./status.sh stores
```

Output:
```
Store                Platform        Status   Success  Products Last Success
─────────────────────────────────────────────────────────────────────────────
housing-works        Blaze           ✅ Good    95.5%       26  12m ago
conbud               Dutchie Embed   ✅ Good    92.1%       26  8m ago  
torches              Joint Ecommerce ⚠️  Warn   78.3%        6  45m ago
stoops               Joint Ecommerce ✅ Good    88.9%        4  15m ago
```

### Health Check Results
```bash
./status.sh health
```

Output:
```
Store                Overall  Site  Extract  Latency  Error
─────────────────────────────────────────────────────────────────────
housing-works        ✅       ✅    ✅       2450ms   
conbud               ✅       ✅    ✅       1890ms   
torches              ⚠️       ✅    ❌       8500ms   Timeout after 120s
stoops               ✅       ✅    ✅       3200ms   
```

## Runbook for Common Issues

### Store Showing as Critical

**Symptoms:** Red status, consecutive failures > 3, success rate < 50%

**Diagnosis Steps:**
1. Check recent logs: `./status.sh activity`
2. Run health check: `python3 health_checker.py --stores <store-name>`
3. Get repair recommendations: `./repair.sh recommendations <store-name>`

**Common Fixes:**
```bash
# Auto-repair (clears cache, kills hung processes, updates deps)
./repair.sh force <store-name>

# Manual investigation
tail -50 logs/stealth_scraper_errors.log
```

### High Latency Issues

**Symptoms:** Warning status, extraction time > 30s, timeouts

**Diagnosis:**
```bash
# Check latency trends
python3 metrics.py --store <store-name>
```

**Fixes:**
- Check if target site is responding slowly
- Increase timeout values in scraper config
- Consider adding delays between requests

### Cloudflare Detection

**Symptoms:** "Cloudflare" in error messages, blocked requests

**Diagnosis:**
```bash
# Check error details
grep -i cloudflare logs/stealth_scraper_errors.log | tail -10
```

**Fixes:**
- Review proxy configuration
- Update user agents and headers
- Check Browserbase/Stagehand settings for hard targets

### No Recent Extractions

**Symptoms:** Alert for no success in 6+ hours

**Emergency Response:**
```bash
# Immediate check and repair
./repair.sh

# Manual run
./run_all.sh <store-name>

# Check for infrastructure issues
./status.sh all
```

### Sudden Product Count Drop

**Symptoms:** Product count decreased by >50% from previous day

**Investigation:**
1. Check if store website changed structure
2. Verify scraper selectors still work
3. Look for new anti-bot measures

```bash
# Compare today vs yesterday metrics
python3 metrics.py --store <store-name>

# Manual test
python3 <store-scraper-path> --test
```

## Automated Monitoring Setup

### Cron Job Configuration

Add to crontab for automated monitoring:

```cron
# Health checks every 30 minutes
*/30 * * * * cd /path/to/scrapers/monitoring && python3 health_checker.py --save >/dev/null 2>&1

# Alert checks every 15 minutes  
*/15 * * * * cd /path/to/scrapers/monitoring && python3 alerter.py --check >/dev/null 2>&1

# Daily scraper runs at 6 AM
0 6 * * * cd /path/to/scrapers/monitoring && ./run_all.sh active

# Log rotation daily at 2 AM
0 2 * * * cd /path/to/scrapers/monitoring && python3 logging_config.py --rotate

# Weekly repair check on Sundays
0 4 * * 0 cd /path/to/scrapers/monitoring && ./repair.sh
```

### Systemd Service (Alternative)

Create `/etc/systemd/system/stealth-scraper-monitor.service`:

```ini
[Unit]
Description=Stealth Scraper Monitoring Service
After=network.target

[Service]
Type=simple
User=scraper
WorkingDirectory=/path/to/scrapers/monitoring
ExecStart=/bin/bash -c 'while true; do python3 health_checker.py --save && python3 alerter.py --check && sleep 900; done'
Restart=always

[Install]
WantedBy=multi-user.target
```

## Performance Tuning

### Database Optimization
- SQLite database automatically handles concurrent reads
- Consider moving to PostgreSQL for high-volume deployments
- Metrics retention policy: 30 days detailed, 1 year aggregated

### Monitoring Overhead
- Health checks: ~5-10s per store
- Dashboard generation: ~1-2s for all stores
- Log processing: ~100MB/day for active monitoring

### Scaling Considerations
- Async health checks support 5 concurrent store checks
- Add more workers by increasing semaphore limit in `health_checker.py`
- Consider distributed monitoring for 50+ stores

## Troubleshooting

### Dashboard Not Updating
```bash
# Check database permissions
ls -la monitoring/dashboard.db

# Recreate database
rm monitoring/dashboard.db
python3 dashboard.py --json
```

### Alerts Not Sending
```bash
# Test webhook
python3 alerter.py --test test-store

# Check configuration
python3 alerter.py --config

# Verify network connectivity
curl -X POST <webhook-url> -d '{"text":"test"}'
```

### High Memory Usage
```bash
# Check log file sizes
du -sh logs/

# Manual log rotation
python3 logging_config.py --rotate

# Monitor process memory
ps aux | grep python
```

## API Integration

### Dashboard Data
```bash
# Get JSON dashboard data
curl -s http://localhost:8000/api/dashboard | jq .

# Store-specific metrics
curl -s http://localhost:8000/api/stores/housing-works | jq .
```

### Health Status
```bash
# Latest health check results
curl -s http://localhost:8000/api/health | jq .

# Historical health data
curl -s http://localhost:8000/api/health/history?hours=24 | jq .
```

## Contact & Support

For issues with the monitoring infrastructure:

1. Check this runbook first
2. Review recent logs in `logs/`
3. Run diagnostic commands from this guide
4. Check GitHub issues for known problems

**Emergency contacts:**
- Critical infrastructure failures: Use repair.sh auto-repair first
- Dashboard/alerting issues: Check configuration files
- Performance problems: Review scaling considerations

---

**Last Updated:** 2026-03-02  
**Version:** 1.0  
**Coverage:** 15+ stores across 6 platforms