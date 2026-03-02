# Inventory Polling Infrastructure

A unified inventory monitoring system for all dispensary stores with tiered polling schedules, change detection, and robust error handling.

## Architecture Overview

```
┌─────────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Scheduler         │    │  Change          │    │  State          │
│   - Tiered polling  │    │  Detector        │    │  Manager        │
│   - Store management│    │  - Compare       │    │  - Persistence  │
│   - Concurrency     │    │  - Events        │    │  - Error track  │
└─────────────────────┘    └──────────────────┘    └─────────────────┘
           │                          │                        │
           ▼                          ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Platform Scrapers                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │    Blaze     │  │ Joint Ecom   │  │   Custom     │              │
│  │ Housing Works│  │Alta,Torches, │  │  Individual  │              │
│  │              │  │    Stoops    │  │   Stores     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Scheduler (`scheduler.py`)
- **Purpose**: Manages polling schedules for all stores
- **Features**: 
  - Tiered polling (15 min / 1 hour / 4 hours)
  - Concurrent execution with limits
  - Automatic retry with backoff
  - Store-specific configurations

### 2. Change Detector (`change_detector.py`)
- **Purpose**: Compares inventory snapshots to detect changes
- **Detects**:
  - Price changes
  - Stock status (in/out)
  - New products
  - Removed products
  - Category changes

### 3. State Manager (`state_manager.py`)
- **Purpose**: Persistent state and error handling
- **Features**:
  - Tracks last successful polls
  - Failure counting and backoff
  - Health monitoring
  - Graceful recovery

### 4. Configuration (`config.yaml`)
- **Purpose**: Central configuration for all stores
- **Contains**: Polling intervals, platform types, URLs, timeouts

## Polling Tiers

### High-Value Stores (15 minutes)
- **Housing Works** - Popular Blaze platform store
- **Stoops** - High-traffic Brooklyn location

### Medium Priority (1 hour)
- **CONBUD** - Dutchie embed platform
- **Torches** - Joint Ecommerce platform
- **Alta** - Joint Ecommerce platform

### Low Priority (4 hours)
- **Custom stores** - Individual implementations
- **New platforms** - Testing/validation phase

## Change Event Types

### Price Changes
```json
{
  "type": "price_change",
  "product_id": "product_123",
  "product_name": "Blue Dream 3.5g",
  "old_price": 50.00,
  "new_price": 45.00,
  "price_change": -5.00,
  "category": "flower"
}
```

### Stock Changes
```json
{
  "type": "stock_out",
  "product_id": "product_124",
  "product_name": "OG Kush 1g",
  "category": "flower"
}
```

### New Products
```json
{
  "type": "new_product",
  "product_id": "product_125",
  "product_name": "White Widow 7g",
  "price": 80.00,
  "category": "flower"
}
```

## Installation & Setup

### Prerequisites
```bash
# Python dependencies
pip install asyncio aiofiles pyyaml playwright

# Install Playwright browsers
playwright install chromium
```

### Directory Structure
```
scrapers/inventory/
├── scheduler.py           # Main polling scheduler
├── change_detector.py     # Change detection logic
├── state_manager.py       # State persistence
├── config.yaml           # Store configurations
├── README.md             # This documentation
├── data/                 # Inventory snapshots
│   ├── housing_works/
│   ├── conbud/
│   └── alta/
└── state/               # System state files
    ├── global_state.json
    └── stores_state.json
```

### Quick Start

1. **Configure stores** (optional - defaults provided):
```bash
cp config.yaml.example config.yaml
# Edit store URLs, intervals, etc.
```

2. **Start the scheduler**:
```python
from scheduler import InventoryScheduler

scheduler = InventoryScheduler()
await scheduler.start()  # Runs indefinitely
```

3. **Check system health**:
```python
status = await scheduler.get_status()
print(f"Active stores: {status['enabled_stores']}")
print(f"Success rate: {status['stats']['success_rate']}%")
```

## Adding New Stores

### 1. Update Configuration
Add store to `config.yaml`:
```yaml
stores:
  new_store_name:
    platform: custom|blaze|dutchie_embed|joint_ecommerce
    priority: high|medium|low
    interval_minutes: 60
    enabled: true
    max_retries: 2
    timeout: 45
    url: https://newstore.com
    description: "New Store Description"
```

### 2. Implement Scraper
Create scraper following platform pattern:
```python
# For custom stores
async def scrape_new_store() -> List[Dict]:
    # Implementation here
    return products

# Register in scheduler.py
async def run_custom_scraper(self, store_name: str, timeout: int):
    if store_name == 'new_store_name':
        return await scrape_new_store()
```

### 3. Test Integration
```python
# Test single store
from scheduler import InventoryScheduler
scheduler = InventoryScheduler()
success = await scheduler.poll_store('new_store_name', {})
```

## Error Handling & Recovery

### Automatic Recovery
- **Network failures**: 3 retries with exponential backoff
- **Parsing errors**: Log and continue with other stores
- **Rate limiting**: Respect store-specific delays

### Backoff Strategy
- **First failure**: 5-minute backoff
- **Subsequent failures**: Exponential (5, 10, 20, 40... minutes)
- **Max backoff**: 24 hours
- **Auto-disable**: After 5 consecutive failures

### Manual Recovery
```python
from state_manager import StateManager
manager = StateManager()

# Reset failed store
manager.reset_store_state('store_name')

# Enable disabled store
manager.enable_store('store_name')

# Check system health
health = manager.get_system_health()
```

## Monitoring & Alerts

### Health Metrics
- **Success rate**: Percentage of successful polls
- **Active stores**: Currently operational stores
- **Error counts**: Per-store failure tracking
- **Uptime**: System operational time

### Status Dashboard
```python
# Get comprehensive status
scheduler = InventoryScheduler()
status = await scheduler.get_status()

print(f"System Status: {status['running']}")
print(f"Success Rate: {status['stats']['success_rate']}%")
print(f"Stores: {status['enabled_stores']}/{status['total_stores']}")

# Store-specific status
for store in status['next_polls']:
    print(f"{store}: {status['next_polls'][store]}")
```

### Change Notifications
Changes are automatically saved to JSON files:
```
data/housing_works/changes_20260302_143000.json
```

## Performance Optimization

### Concurrent Limits
- **Max concurrent scrapers**: 3 (configurable)
- **Store delays**: 5 seconds between store starts
- **Resource monitoring**: Memory and runtime limits

### Data Management
- **Snapshot retention**: 30 days (configurable)
- **State persistence**: Every 5 minutes
- **Cleanup automation**: Remove old data automatically

### Resource Usage
- **Memory**: ~50MB per scraper
- **Network**: ~1-5MB per store poll
- **Disk**: ~10MB per day per store (snapshots + changes)

## Deployment Options

### Local Development
```python
# Single run
from scheduler import InventoryScheduler
scheduler = InventoryScheduler()
await scheduler.poll_cycle()  # One-time poll

# Continuous monitoring
await scheduler.start()  # Runs until stopped
```

### Production Deployment
```bash
# System service
sudo systemctl enable inventory-scheduler
sudo systemctl start inventory-scheduler

# Docker container
docker run -v ./data:/app/data inventory-scheduler

# Cron-based (for low-frequency polling)
*/15 * * * * cd /app && python -c "from scheduler import poll_high_priority; poll_high_priority()"
```

### Cloud Deployment
- **AWS Lambda**: Serverless scheduled functions
- **Google Cloud Functions**: Event-driven execution
- **Kubernetes CronJobs**: Containerized periodic execution

## Troubleshooting

### Common Issues

**Store not polling:**
```python
# Check store state
manager = StateManager()
state = manager.get_store_state('store_name')
print(f"Status: {state.status}")
print(f"Last error: {state.last_error}")
```

**High failure rate:**
- Check network connectivity
- Verify store URLs are still valid
- Review timeout settings
- Check for anti-bot measures

**Memory usage:**
- Reduce concurrent scrapers limit
- Increase cleanup frequency
- Monitor browser instances

### Debug Mode
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Enable detailed logging for specific stores
scheduler = InventoryScheduler()
await scheduler.poll_store('problematic_store', debug=True)
```

### Log Analysis
```bash
# Search for errors
grep "ERROR" logs/inventory.log | tail -20

# Store-specific logs
grep "housing_works" logs/inventory.log

# Success rate analysis
grep "✅\|❌" logs/inventory.log | tail -50
```

## API Reference

### InventoryScheduler
```python
class InventoryScheduler:
    async def start()                    # Start continuous polling
    async def poll_cycle()               # Single polling cycle
    async def poll_store(name, state)    # Poll specific store
    async def get_status()               # System status
    def stop()                          # Stop scheduler
```

### InventoryChangeDetector
```python
class InventoryChangeDetector:
    def detect_changes(store, products)           # Compare with previous
    def save_snapshot(store, products)            # Save new snapshot
    def process_inventory_update(store, products) # Full process
```

### StateManager
```python
class StateManager:
    def get_store_state(store_name)          # Get store state
    def record_poll_success(store, ...)      # Record success
    def record_poll_failure(store, error)    # Record failure
    def reset_store_state(store_name)        # Reset to active
    def get_system_health()                  # Health metrics
```

---

## Next Steps

1. **Alerting Integration**: Add Discord/Slack notifications for significant changes
2. **Web Dashboard**: Build real-time monitoring interface
3. **Analytics**: Historical trend analysis and insights
4. **Machine Learning**: Predict optimal polling intervals based on change patterns
5. **API Endpoints**: REST API for external integrations