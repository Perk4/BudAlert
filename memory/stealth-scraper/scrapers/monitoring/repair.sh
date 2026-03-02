#!/bin/bash
"""
repair.sh - Re-run failed stores and attempt repairs

Identifies failed stores and attempts to repair them by:
1. Re-running failed scrapers
2. Clearing potential cache/state issues
3. Updating scraper dependencies
4. Reporting on repair attempts
"""

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRAPERS_DIR="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$SCRIPT_DIR"
LOG_DIR="$MONITORING_DIR/logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Log file for this repair run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPAIR_LOG="$LOG_DIR/repair_$TIMESTAMP.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$REPAIR_LOG"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$REPAIR_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$REPAIR_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$REPAIR_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$REPAIR_LOG"
}

log_repair() {
    echo -e "${PURPLE}[REPAIR]${NC} $*" | tee -a "$REPAIR_LOG"
}

# Function to identify failed stores
identify_failed_stores() {
    log_info "Identifying failed stores..."
    
    python3 -c "
import sys
sys.path.append('$MONITORING_DIR')
from dashboard import DashboardAggregator
from metrics import MetricsCalculator

dashboard = DashboardAggregator()
metrics = MetricsCalculator()

failed_stores = []
warning_stores = []

# Get all active stores
active_stores = [name for name, config in dashboard.stores_config.items() if config.get('active', True)]

for store_name in active_stores:
    status = dashboard.get_store_status(store_name)
    store_metrics = metrics.calculate_store_metrics(store_name)
    
    # Criteria for failed stores
    is_failed = (
        status.consecutive_failures >= 3 or
        store_metrics.success_rate_24h < 50 or
        (store_metrics.time_since_last_success_hours and store_metrics.time_since_last_success_hours > 6)
    )
    
    # Criteria for warning stores
    is_warning = (
        not is_failed and (
            status.consecutive_failures >= 1 or
            store_metrics.success_rate_24h < 80 or
            (store_metrics.time_since_last_success_hours and store_metrics.time_since_last_success_hours > 2)
        )
    )
    
    if is_failed:
        failed_stores.append({
            'name': store_name,
            'platform': status.platform,
            'consecutive_failures': status.consecutive_failures,
            'success_rate': store_metrics.success_rate_24h,
            'hours_since_success': store_metrics.time_since_last_success_hours,
            'last_error': status.last_error
        })
    elif is_warning:
        warning_stores.append({
            'name': store_name,
            'platform': status.platform,
            'consecutive_failures': status.consecutive_failures,
            'success_rate': store_metrics.success_rate_24h,
            'hours_since_success': store_metrics.time_since_last_success_hours,
            'last_error': status.last_error
        })

# Output results in a format the shell can parse
if failed_stores:
    print('FAILED_STORES=' + ','.join([store['name'] for store in failed_stores]))
    print()
    print('Failed stores requiring repair:')
    for store in failed_stores:
        print(f'  {store[\"name\"]} ({store[\"platform\"]}): {store[\"consecutive_failures\"]} failures, {store[\"success_rate\"]:.1f}% success')
        if store['last_error']:
            print(f'    Last error: {store[\"last_error\"]}')
else:
    print('FAILED_STORES=')
    print('No failed stores found.')

if warning_stores:
    print('WARNING_STORES=' + ','.join([store['name'] for store in warning_stores]))
    print()
    print('Warning stores (degraded performance):')
    for store in warning_stores:
        print(f'  {store[\"name\"]} ({store[\"platform\"]}): {store[\"consecutive_failures\"]} failures, {store[\"success_rate\"]:.1f}% success')
else:
    print('WARNING_STORES=')
"
}

# Function to find scraper script for a store
find_scraper_script() {
    local store_name="$1"
    local possible_paths=(
        "$SCRAPERS_DIR/$store_name/${store_name}_scraper.py"
        "$SCRAPERS_DIR/${store_name//-/_}/${store_name//-/_}_scraper.py"
        "$SCRAPERS_DIR/${store_name}_scraper.py"
        "$SCRAPERS_DIR/blaze/blaze_scraper.py"
        "$SCRAPERS_DIR/joint/joint_scraper.py"
        "$SCRAPERS_DIR/dutchie/dutchie_scraper.py"
    )
    
    for path in "${possible_paths[@]}"; do
        if [[ -f "$path" ]]; then
            echo "$path"
            return 0
        fi
    done
    
    return 1
}

# Function to perform basic repair actions
perform_basic_repairs() {
    local store_name="$1"
    local repair_actions=0
    
    log_repair "Performing basic repairs for $store_name"
    
    # 1. Clear browser cache/data if it exists
    local cache_dirs=(
        "/tmp/playwright_cache"
        "/tmp/selenium_cache"  
        "$HOME/.cache/ms-playwright"
        "$SCRAPERS_DIR/$store_name/cache"
        "$SCRAPERS_DIR/${store_name//-/_}/cache"
    )
    
    for cache_dir in "${cache_dirs[@]}"; do
        if [[ -d "$cache_dir" ]]; then
            log_repair "Clearing cache directory: $cache_dir"
            rm -rf "$cache_dir" 2>/dev/null || true
            repair_actions=$((repair_actions + 1))
        fi
    done
    
    # 2. Clear any lock files
    local lock_files=(
        "/tmp/${store_name}.lock"
        "$SCRAPERS_DIR/$store_name/${store_name}.lock"
        "$SCRAPERS_DIR/${store_name//-/_}/${store_name//-/_}.lock"
    )
    
    for lock_file in "${lock_files[@]}"; do
        if [[ -f "$lock_file" ]]; then
            log_repair "Removing lock file: $lock_file"
            rm -f "$lock_file" 2>/dev/null || true
            repair_actions=$((repair_actions + 1))
        fi
    done
    
    # 3. Check and kill any hung processes
    local process_count
    process_count=$(pgrep -fc "${store_name}_scraper" || echo "0")
    if [[ $process_count -gt 0 ]]; then
        log_repair "Killing $process_count hung processes for $store_name"
        pkill -f "${store_name}_scraper" 2>/dev/null || true
        sleep 2
        repair_actions=$((repair_actions + 1))
    fi
    
    # 4. Update Python dependencies if requirements.txt exists
    local scraper_dir
    for possible_dir in "$SCRAPERS_DIR/$store_name" "$SCRAPERS_DIR/${store_name//-/_}"; do
        if [[ -d "$possible_dir" ]] && [[ -f "$possible_dir/requirements.txt" ]]; then
            scraper_dir="$possible_dir"
            break
        fi
    done
    
    if [[ -n "${scraper_dir:-}" ]]; then
        log_repair "Updating dependencies from $scraper_dir/requirements.txt"
        if pip3 install -r "$scraper_dir/requirements.txt" --upgrade --quiet 2>/dev/null; then
            repair_actions=$((repair_actions + 1))
        else
            log_warning "Failed to update dependencies for $store_name"
        fi
    fi
    
    if [[ $repair_actions -gt 0 ]]; then
        log_repair "Performed $repair_actions repair actions for $store_name"
    else
        log_info "No basic repairs needed for $store_name"
    fi
    
    return $repair_actions
}

# Function to test a store after repair
test_store() {
    local store_name="$1"
    
    log_info "Testing $store_name after repair"
    
    # Find the scraper script
    local scraper_script
    if ! scraper_script=$(find_scraper_script "$store_name"); then
        log_error "No scraper script found for $store_name"
        return 1
    fi
    
    # Run a quick test
    local test_log="$LOG_DIR/${store_name}_test_$TIMESTAMP.log"
    local start_time=$(date +%s)
    
    if timeout 60 python3 "$scraper_script" --test > "$test_log" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_success "$store_name test passed in ${duration}s"
        return 0
    else
        local exit_code=$?
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        if [[ $exit_code -eq 124 ]]; then
            log_error "$store_name test timed out after 60s"
        else
            log_error "$store_name test failed with exit code $exit_code"
        fi
        
        # Show last few lines of error log
        if [[ -f "$test_log" ]] && [[ -s "$test_log" ]]; then
            log_error "Last few lines of test output:"
            tail -5 "$test_log" | sed 's/^/    /' | tee -a "$REPAIR_LOG"
        fi
        
        return 1
    fi
}

# Function to attempt full repair of a store
repair_store() {
    local store_name="$1"
    local repair_successful=false
    
    log_info "Starting repair process for $store_name"
    
    # Step 1: Basic repairs
    if perform_basic_repairs "$store_name"; then
        log_repair "Basic repairs completed for $store_name"
    else
        log_warning "No basic repairs performed for $store_name"
    fi
    
    # Step 2: Test the store
    if test_store "$store_name"; then
        log_success "Repair successful for $store_name"
        repair_successful=true
    else
        log_error "Repair failed for $store_name - store still not working"
    fi
    
    # Step 3: Record repair attempt in dashboard
    python3 -c "
import sys
sys.path.append('$MONITORING_DIR')
from dashboard import DashboardAggregator

dashboard = DashboardAggregator()
dashboard.record_scrape_result(
    store_name='$store_name',
    success=$([[ $repair_successful == true ]] && echo True || echo False),
    products=0,
    latency_ms=0,
    error='Repair attempt' if not $([[ $repair_successful == true ]] && echo True || echo False) else None,
    metadata={'repair_attempt': True, 'timestamp': '$(date --iso-8601=seconds)'}
)
"
    
    return $([[ $repair_successful == true ]] && echo 0 || echo 1)
}

# Function to show repair recommendations
show_repair_recommendations() {
    local store_name="$1"
    
    log_info "Repair recommendations for $store_name:"
    
    # Get store info
    python3 -c "
import sys
sys.path.append('$MONITORING_DIR')
from dashboard import DashboardAggregator
from metrics import MetricsCalculator

dashboard = DashboardAggregator()
metrics = MetricsCalculator()

status = dashboard.get_store_status(store_name='$store_name')
store_metrics = metrics.calculate_store_metrics('$store_name')

print(f'Store: {status.store_name} ({status.platform})')
print(f'Consecutive failures: {status.consecutive_failures}')
print(f'Success rate (24h): {store_metrics.success_rate_24h:.1f}%')
print(f'Last error: {status.last_error or \"None\"}')
print()

# Provide specific recommendations based on platform and errors
recommendations = []

if 'timeout' in (status.last_error or '').lower():
    recommendations.append('- Increase timeout values in scraper configuration')
    recommendations.append('- Check if target site is responding slowly')

if 'cloudflare' in (status.last_error or '').lower():
    recommendations.append('- Review Cloudflare bypass configuration')
    recommendations.append('- Consider updating user agent or headers')

if status.platform in ['Jane + CF', 'MSO + CF']:
    recommendations.append('- Check Browserbase/Stagehand configuration')
    recommendations.append('- Verify proxy settings for Cloudflare bypass')

if 'connection' in (status.last_error or '').lower():
    recommendations.append('- Check network connectivity to target site')
    recommendations.append('- Verify DNS resolution')

if store_metrics.success_rate_24h > 0 but store_metrics.success_rate_24h < 50:
    recommendations.append('- Issue appears intermittent - check for rate limiting')
    recommendations.append('- Consider adding delays between requests')

if not recommendations:
    recommendations.append('- Manual investigation required')
    recommendations.append('- Check scraper logs for specific error details')

print('Recommendations:')
for rec in recommendations:
    print(f'  {rec}')
"
}

# Main repair function
main() {
    local mode="${1:-auto}"
    
    log "Starting repair process - Mode: $mode"
    log "Repair log: $REPAIR_LOG"
    
    case "$mode" in
        "auto"|"")
            # Automatically identify and repair failed stores
            log_info "Auto-repair mode: identifying failed stores"
            
            # Get failed stores
            local identification_output
            identification_output=$(identify_failed_stores)
            echo "$identification_output"
            
            # Parse the failed stores list
            local failed_stores_line
            failed_stores_line=$(echo "$identification_output" | grep "^FAILED_STORES=" || echo "FAILED_STORES=")
            local failed_stores="${failed_stores_line#FAILED_STORES=}"
            
            if [[ -z "$failed_stores" ]]; then
                log_success "No failed stores found - system is healthy!"
                exit 0
            fi
            
            # Split failed stores and repair each
            local repair_count=0
            local success_count=0
            
            IFS=',' read -ra STORE_ARRAY <<< "$failed_stores"
            for store in "${STORE_ARRAY[@]}"; do
                if [[ -n "$store" ]]; then
                    repair_count=$((repair_count + 1))
                    echo ""
                    if repair_store "$store"; then
                        success_count=$((success_count + 1))
                    fi
                fi
            done
            
            echo ""
            log "========== REPAIR SUMMARY =========="
            log "Stores repaired: $repair_count"
            log "Successful repairs: $success_count"
            log "Failed repairs: $((repair_count - success_count))"
            log "Success rate: $(( success_count * 100 / repair_count ))%" 2>/dev/null || log "Success rate: 0%"
            log "===================================="
            ;;
            
        "identify")
            # Just identify failed stores without repairing
            identify_failed_stores
            ;;
            
        "recommendations")
            # Show recommendations for a specific store
            local store_name="${2:-}"
            if [[ -z "$store_name" ]]; then
                echo "Usage: $0 recommendations <store-name>"
                exit 1
            fi
            show_repair_recommendations "$store_name"
            ;;
            
        "test")
            # Test a specific store
            local store_name="${2:-}"
            if [[ -z "$store_name" ]]; then
                echo "Usage: $0 test <store-name>"
                exit 1
            fi
            test_store "$store_name"
            ;;
            
        "force")
            # Force repair a specific store
            local store_name="${2:-}"
            if [[ -z "$store_name" ]]; then
                echo "Usage: $0 force <store-name>"
                exit 1
            fi
            repair_store "$store_name"
            ;;
            
        "help"|"--help"|"-h")
            echo "Usage: $0 [mode] [store-name]"
            echo ""
            echo "Modes:"
            echo "  auto             - Automatically identify and repair failed stores (default)"
            echo "  identify         - Only identify failed stores, don't repair"
            echo "  recommendations  - Show repair recommendations for a specific store"
            echo "  test            - Test a specific store after manual repairs"
            echo "  force           - Force repair a specific store regardless of status"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Auto-repair all failed stores"
            echo "  $0 identify                          # List failed stores"
            echo "  $0 recommendations housing-works     # Get recommendations for specific store"
            echo "  $0 test conbud                      # Test a specific store"
            echo "  $0 force housing-works              # Force repair a specific store"
            exit 0
            ;;
            
        *)
            log_error "Unknown mode: $mode"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with arguments
main "$@"