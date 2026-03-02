#!/bin/bash
"""
status.sh - Quick status overview

Provides a quick overview of scraper infrastructure health,
recent runs, and current metrics.
"""

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emojis for status
HEALTHY_EMOJI="✅"
WARNING_EMOJI="⚠️"
CRITICAL_EMOJI="❌"
UNKNOWN_EMOJI="❓"
INFO_EMOJI="ℹ️"

# Function to get status emoji
get_status_emoji() {
    local status="$1"
    case "$status" in
        "healthy") echo "$HEALTHY_EMOJI" ;;
        "warning") echo "$WARNING_EMOJI" ;;
        "critical") echo "$CRITICAL_EMOJI" ;;
        "unknown") echo "$UNKNOWN_EMOJI" ;;
        *) echo "$INFO_EMOJI" ;;
    esac
}

# Function to format duration
format_duration() {
    local seconds="$1"
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    
    if [[ $hours -gt 0 ]]; then
        echo "${hours}h ${minutes}m"
    elif [[ $minutes -gt 0 ]]; then
        echo "${minutes}m"
    else
        echo "${seconds}s"
    fi
}

# Function to show dashboard overview
show_dashboard() {
    echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        STEALTH SCRAPER DASHBOARD        ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
    echo ""
    
    # Get dashboard data
    local dashboard_output
    if ! dashboard_output=$(python3 "$MONITORING_DIR/dashboard.py" --json 2>/dev/null); then
        echo -e "${RED}Error: Could not get dashboard data${NC}"
        return 1
    fi
    
    # Parse key metrics using python
    python3 -c "
import json
import sys
data = json.loads('$dashboard_output')
summary = data['summary']

print(f'📊 Overview:')
print(f'   Total Stores: {summary[\"total_stores\"]}')
print(f'   Active Stores: {summary[\"active_stores\"]}')
print(f'   Products Extracted (Total): {summary[\"total_products_extracted\"]}')
print(f'   Overall Success Rate: {summary[\"overall_success_rate\"]}%')
print()

print(f'🏥 Health Status:')
print(f'   Healthy: {summary[\"healthy_stores\"]} ✅')
print(f'   Warning: {summary[\"warning_stores\"]} ⚠️')  
print(f'   Critical: {summary[\"critical_stores\"]} ❌')
print()
"
}

# Function to show store details
show_store_details() {
    local show_all="${1:-false}"
    
    echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║            STORE STATUS              ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
    echo ""
    
    # Get detailed store information
    python3 -c "
import json
import sys
import datetime
sys.path.append('$MONITORING_DIR')
from dashboard import DashboardAggregator

dashboard = DashboardAggregator()
stores_data = dashboard.get_all_stores_status()

# Filter to active stores unless show_all is true
if '$show_all' != 'true':
    stores_data = [s for s in stores_data if s.is_active]

if not stores_data:
    print('No stores to display')
    sys.exit(0)

# Sort by success rate (descending)
stores_data.sort(key=lambda x: x.success_rate_24h, reverse=True)

print(f'{'Store':<20} {'Platform':<15} {'Status':<8} {'Success':<8} {'Products':<8} {'Last Success':<12}')
print('─' * 85)

for store in stores_data:
    # Determine status
    if store.success_rate_24h >= 80:
        status = '✅ Good'
    elif store.success_rate_24h >= 50:
        status = '⚠️  Warn'
    else:
        status = '❌ Crit'
    
    # Format last success time
    if store.last_successful_run:
        now = datetime.datetime.now()
        delta = now - store.last_successful_run
        if delta.days > 0:
            last_success = f'{delta.days}d ago'
        elif delta.seconds > 3600:
            last_success = f'{delta.seconds // 3600}h ago'
        else:
            last_success = f'{delta.seconds // 60}m ago'
    else:
        last_success = 'Never'
    
    print(f'{store.store_name:<20} {store.platform:<15} {status:<8} {store.success_rate_24h:>6.1f}% {store.products_extracted:>8} {last_success:<12}')
"
}

# Function to show health check results
show_health_status() {
    echo -e "${PURPLE}╔══════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║          HEALTH CHECK STATUS         ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════╝${NC}"
    echo ""
    
    local health_file="$MONITORING_DIR/health_status.json"
    
    if [[ ! -f "$health_file" ]]; then
        echo -e "${YELLOW}No health check data available. Run health checker first:${NC}"
        echo "  python3 $MONITORING_DIR/health_checker.py"
        return 0
    fi
    
    # Parse and display health check results
    python3 -c "
import json
import datetime

with open('$health_file', 'r') as f:
    data = json.load(f)

summary = data['summary']
timestamp = datetime.datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
age = datetime.datetime.now(timestamp.tzinfo) - timestamp

print(f'Last health check: {age.total_seconds() / 60:.1f} minutes ago')
print()

print(f'Summary:')
print(f'  Total checked: {summary[\"total_stores_checked\"]}')
print(f'  Healthy: {summary[\"healthy_count\"]} ✅')
print(f'  Warning: {summary[\"warning_count\"]} ⚠️')
print(f'  Critical: {summary[\"critical_count\"]} ❌')
print()

# Show individual store results
stores = data['stores']
if stores:
    print(f'{'Store':<20} {'Overall':<8} {'Site':<6} {'Extract':<8} {'Latency':<8} {'Error':<30}')
    print('─' * 85)
    
    for store in stores:
        status_map = {'healthy': '✅', 'warning': '⚠️', 'critical': '❌', 'unknown': '❓'}
        status_emoji = status_map.get(store['overall_status'], '❓')
        
        site_status = '✅' if store['site_reachable'] else '❌'
        extract_status = '✅' if store['extraction_successful'] else '❌'
        
        total_latency = store['site_response_time_ms'] + store['extraction_time_ms']
        latency_str = f'{total_latency}ms'
        
        error_msg = store.get('error_message', '')[:30] if store.get('error_message') else ''
        
        print(f'{store[\"store_name\"]:<20} {status_emoji:<8} {site_status:<6} {extract_status:<8} {latency_str:<8} {error_msg:<30}')
"
}

# Function to show recent activity
show_recent_activity() {
    echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          RECENT ACTIVITY             ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
    echo ""
    
    # Show recent log files
    local log_dir="$MONITORING_DIR/logs"
    if [[ -d "$log_dir" ]]; then
        echo "Recent run logs:"
        find "$log_dir" -name "run_all_*.log" -type f -printf '%T@ %p\n' | sort -nr | head -3 | while read -r timestamp filepath; do
            local filename=$(basename "$filepath")
            local date_str=$(date -d "@${timestamp%.*}" '+%Y-%m-%d %H:%M')
            local size=$(stat --format=%s "$filepath")
            echo "  📄 $filename ($date_str, ${size} bytes)"
        done
        echo ""
    fi
    
    # Show current infrastructure metrics
    python3 -c "
import sys
sys.path.append('$MONITORING_DIR')
from metrics import MetricsCalculator
import json

try:
    calculator = MetricsCalculator()
    metrics = calculator.get_infrastructure_metrics()
    
    print('Infrastructure Metrics (24h):')
    print(f'  Products extracted: {metrics[\"volume_metrics\"][\"products_extracted_24h\"]}')
    print(f'  Extraction rate: {metrics[\"volume_metrics\"][\"extraction_rate_per_hour\"]:.1f}/hour')
    print(f'  Average latency: {metrics[\"performance_metrics\"][\"avg_latency_ms\"]}ms')
    print(f'  Estimated cost: ${metrics[\"cost_metrics\"][\"total_daily_cost_usd\"]:.2f}/day')
    print()
    
    # Platform breakdown
    platforms = metrics['platform_breakdown']
    if platforms:
        print('By Platform:')
        for platform, data in platforms.items():
            print(f'  {platform}: {data[\"store_count\"]} stores, {data[\"products\"]} products, {data[\"avg_success_rate\"]:.1f}% success')
        
except Exception as e:
    print(f'Could not load metrics: {e}')
"
}

# Function to show alerts
show_alerts() {
    echo -e "${RED}╔══════════════════════════════════════╗${NC}"
    echo -e "${RED}║               ALERTS                 ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════╝${NC}"
    echo ""
    
    # Get recent alerts from database
    python3 -c "
import sys
import sqlite3
import datetime
import os
sys.path.append('$MONITORING_DIR')

alerts_db = os.path.join('$MONITORING_DIR', 'alerts.db')
if not os.path.exists(alerts_db):
    print('No alerts database found. No alerts to show.')
    exit(0)

# Get alerts from last 24 hours
cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)

with sqlite3.connect(alerts_db) as conn:
    cursor = conn.execute('''
        SELECT alert_id, timestamp, severity, store_name, alert_type, message, resolved
        FROM alerts 
        WHERE timestamp > ? 
        ORDER BY timestamp DESC 
        LIMIT 10
    ''', (cutoff.isoformat(),))
    
    alerts = cursor.fetchall()
    
    if not alerts:
        print('✅ No recent alerts (last 24h)')
        exit(0)
    
    print(f'Recent alerts (last 24h): {len(alerts)}')
    print()
    
    for alert in alerts:
        alert_id, timestamp, severity, store_name, alert_type, message, resolved = alert
        
        # Format timestamp
        dt = datetime.datetime.fromisoformat(timestamp)
        time_str = dt.strftime('%H:%M')
        
        # Severity emoji
        emoji = {'info': 'ℹ️', 'warning': '⚠️', 'critical': '🚨'}.get(severity, '❗')
        
        # Resolution status
        status_str = '✅ Resolved' if resolved else '🔴 Active'
        
        print(f'{emoji} {time_str} [{severity.upper()}] {store_name}: {message}')
        print(f'    Type: {alert_type} | Status: {status_str}')
        print()
"
}

# Function to run quick health check
run_quick_health_check() {
    echo -e "${CYAN}Running quick health check...${NC}"
    
    if python3 "$MONITORING_DIR/health_checker.py" --save >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check completed${NC}"
    else
        echo -e "${RED}❌ Health check failed${NC}"
    fi
    echo ""
}

# Main function
main() {
    local mode="${1:-summary}"
    
    case "$mode" in
        "summary"|"")
            show_dashboard
            show_store_details false
            ;;
        "all")
            show_dashboard
            show_store_details true
            show_health_status
            show_recent_activity
            show_alerts
            ;;
        "stores")
            show_store_details true
            ;;
        "health")
            show_health_status
            ;;
        "activity")
            show_recent_activity
            ;;
        "alerts")
            show_alerts
            ;;
        "quick-check")
            run_quick_health_check
            show_dashboard
            ;;
        "help"|"--help"|"-h")
            echo "Usage: $0 [mode]"
            echo ""
            echo "Modes:"
            echo "  summary     - Quick overview (default)"
            echo "  all         - Complete status report"
            echo "  stores      - Detailed store status"
            echo "  health      - Health check results"
            echo "  activity    - Recent activity and metrics"
            echo "  alerts      - Recent alerts"
            echo "  quick-check - Run health check then show summary"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown mode: $mode${NC}"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"