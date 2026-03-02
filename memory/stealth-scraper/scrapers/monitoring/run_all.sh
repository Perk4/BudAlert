#!/bin/bash
"""
run_all.sh - Execute all scrapers in sequence

Runs all active store scrapers with proper error handling,
logging, and coordination with the monitoring system.
"""

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRAPERS_DIR="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$SCRIPT_DIR"
LOG_DIR="$MONITORING_DIR/logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Log file for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RUN_LOG="$LOG_DIR/run_all_$TIMESTAMP.log"

# Store configuration (matches dashboard.py)
declare -A STORE_CONFIGS
STORE_CONFIGS[housing-works]="Blaze:true"
STORE_CONFIGS[conbud]="Dutchie Embed:true"
STORE_CONFIGS[torches]="Joint Ecommerce:true"
STORE_CONFIGS[stoops]="Joint Ecommerce:true"
STORE_CONFIGS[alta]="Joint Ecommerce:false"
STORE_CONFIGS[smacked-village]="Custom Easy:false"
STORE_CONFIGS[yerba-buena]="Custom Easy:false"
STORE_CONFIGS[terp-bros]="Custom Easy:false"
STORE_CONFIGS[flynnstoned]="Custom Easy:false"
STORE_CONFIGS[happy-munkey]="Custom Easy:false"
STORE_CONFIGS[travel-agency]="Custom Medium:false"
STORE_CONFIGS[gotham]="Custom Medium:false"
STORE_CONFIGS[dazed]="Custom Medium:false"
STORE_CONFIGS[green-apple]="Custom Medium:false"
STORE_CONFIGS[chelsea-cannabis]="Custom Medium:false"
STORE_CONFIGS[verilife]="Custom Medium:false"
STORE_CONFIGS[qube]="LeafBridge:false"
STORE_CONFIGS[rise]="Jane + CF:false"
STORE_CONFIGS[curaleaf]="MSO + CF:false"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$RUN_LOG"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$RUN_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$RUN_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$RUN_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$RUN_LOG"
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

# Function to run a single store scraper
run_store_scraper() {
    local store_name="$1"
    local platform="$2"
    
    log_info "Running scraper for $store_name ($platform)"
    
    # Find the scraper script
    local scraper_script
    if ! scraper_script=$(find_scraper_script "$store_name"); then
        log_error "No scraper script found for $store_name"
        return 1
    fi
    
    # Create store-specific log
    local store_log="$LOG_DIR/${store_name}_$TIMESTAMP.log"
    
    # Run the scraper with timeout
    local start_time=$(date +%s)
    local timeout=300  # 5 minutes
    
    if timeout "$timeout" python3 "$scraper_script" > "$store_log" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        # Try to extract product count from output
        local products=0
        if [[ -f "$store_log" ]]; then
            # Look for common patterns in scraper output
            if grep -q "products extracted" "$store_log"; then
                products=$(grep -oE "([0-9]+) products extracted" "$store_log" | tail -1 | cut -d' ' -f1)
            elif grep -q "Found [0-9]+ products" "$store_log"; then
                products=$(grep -oE "Found ([0-9]+) products" "$store_log" | tail -1 | cut -d' ' -f2)
            fi
        fi
        
        log_success "$store_name completed in ${duration}s - $products products extracted"
        
        # Record success in monitoring system
        python3 -c "
import sys
sys.path.append('$MONITORING_DIR')
from dashboard import DashboardAggregator
dashboard = DashboardAggregator()
dashboard.record_scrape_result(
    store_name='$store_name',
    success=True,
    products=$products,
    latency_ms=$((duration * 1000))
)
"
        return 0
    else
        local exit_code=$?
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        if [[ $exit_code -eq 124 ]]; then
            log_error "$store_name timed out after ${timeout}s"
            error_msg="Timeout after ${timeout}s"
        else
            log_error "$store_name failed with exit code $exit_code"
            error_msg="Exit code $exit_code"
        fi
        
        # Record failure in monitoring system
        python3 -c "
import sys
sys.path.append('$MONITORING_DIR')
from dashboard import DashboardAggregator
dashboard = DashboardAggregator()
dashboard.record_scrape_result(
    store_name='$store_name',
    success=False,
    latency_ms=$((duration * 1000)),
    error='$error_msg'
)
"
        return 1
    fi
}

# Main execution function
main() {
    local mode="${1:-all}"  # all, active, or specific store name
    local run_summary=""
    local total_stores=0
    local successful_stores=0
    local failed_stores=0
    
    log "Starting scraper run cycle - Mode: $mode"
    log "Log file: $RUN_LOG"
    
    # Determine which stores to run
    local stores_to_run=()
    
    case "$mode" in
        "all")
            log_info "Running all configured stores"
            for store in "${!STORE_CONFIGS[@]}"; do
                stores_to_run+=("$store")
            done
            ;;
        "active")
            log_info "Running only active stores"
            for store in "${!STORE_CONFIGS[@]}"; do
                local config="${STORE_CONFIGS[$store]}"
                local is_active="${config#*:}"
                if [[ "$is_active" == "true" ]]; then
                    stores_to_run+=("$store")
                fi
            done
            ;;
        *)
            # Specific store
            if [[ -n "${STORE_CONFIGS[$mode]:-}" ]]; then
                log_info "Running specific store: $mode"
                stores_to_run+=("$mode")
            else
                log_error "Unknown store: $mode"
                echo "Usage: $0 [all|active|<store-name>]"
                echo "Available stores: ${!STORE_CONFIGS[*]}"
                exit 1
            fi
            ;;
    esac
    
    if [[ ${#stores_to_run[@]} -eq 0 ]]; then
        log_warning "No stores to run"
        exit 0
    fi
    
    log_info "Running ${#stores_to_run[@]} stores: ${stores_to_run[*]}"
    
    # Run stores sequentially
    for store in "${stores_to_run[@]}"; do
        total_stores=$((total_stores + 1))
        local config="${STORE_CONFIGS[$store]}"
        local platform="${config%:*}"
        
        if run_store_scraper "$store" "$platform"; then
            successful_stores=$((successful_stores + 1))
        else
            failed_stores=$((failed_stores + 1))
        fi
        
        # Small delay between stores to be respectful
        sleep 2
    done
    
    # Generate summary
    local success_rate=0
    if [[ $total_stores -gt 0 ]]; then
        success_rate=$((successful_stores * 100 / total_stores))
    fi
    
    log ""
    log "========== RUN SUMMARY =========="
    log "Total stores: $total_stores"
    log "Successful: $successful_stores"
    log "Failed: $failed_stores"
    log "Success rate: ${success_rate}%"
    log "Log file: $RUN_LOG"
    log "================================="
    
    # Update dashboard with summary
    python3 -c "
import sys
sys.path.append('$MONITORING_DIR')
from dashboard import DashboardAggregator
dashboard = DashboardAggregator()
data = dashboard.get_dashboard_data()
print('Current infrastructure status:')
print(f'Active stores: {data[\"summary\"][\"active_stores\"]}')
print(f'Products extracted: {data[\"summary\"][\"total_products_extracted\"]}')
print(f'Success rate: {data[\"summary\"][\"overall_success_rate\"]}%')
"
    
    # Exit with error if any stores failed
    if [[ $failed_stores -gt 0 ]]; then
        exit 1
    fi
}

# Show usage if requested
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: $0 [all|active|<store-name>]"
    echo ""
    echo "Modes:"
    echo "  all     - Run all configured stores (including inactive)"
    echo "  active  - Run only active stores (default)"
    echo "  <store> - Run specific store"
    echo ""
    echo "Available stores:"
    for store in "${!STORE_CONFIGS[@]}"; do
        local config="${STORE_CONFIGS[$store]}"
        local platform="${config%:*}"
        local is_active="${config#*:}"
        local status="inactive"
        if [[ "$is_active" == "true" ]]; then
            status="active"
        fi
        echo "  $store ($platform) - $status"
    done
    exit 0
fi

# Run main function with arguments
main "${1:-active}"