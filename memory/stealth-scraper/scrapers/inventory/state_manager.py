"""
State management for inventory polling system.
Handles persistent state, failure tracking, retry logic, and graceful recovery.
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiofiles
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StoreStatus(Enum):
    """Store operational status."""
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR_BACKOFF = "error_backoff"
    MAINTENANCE = "maintenance"


@dataclass
class StoreState:
    """State information for a single store."""
    name: str
    status: StoreStatus
    last_successful_poll: Optional[str] = None
    last_attempt: Optional[str] = None
    consecutive_failures: int = 0
    total_polls: int = 0
    successful_polls: int = 0
    failed_polls: int = 0
    last_error: Optional[str] = None
    next_poll_time: Optional[str] = None
    backoff_until: Optional[str] = None
    last_product_count: int = 0
    last_changes_count: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class GlobalState:
    """Global polling system state."""
    started_at: str
    last_cycle: Optional[str] = None
    total_cycles: int = 0
    stores_processed: int = 0
    total_errors: int = 0
    is_running: bool = False
    last_cleanup: Optional[str] = None
    version: str = "1.0"


class StateManager:
    """Manages persistent state for the inventory polling system."""
    
    def __init__(self, state_dir: str = "state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        
        self.state_file = self.state_dir / "global_state.json"
        self.stores_file = self.state_dir / "stores_state.json"
        
        # Configuration
        self.max_consecutive_failures = 5
        self.base_backoff_minutes = 5
        self.max_backoff_minutes = 1440  # 24 hours
        self.backoff_multiplier = 2
        
        # In-memory state
        self.global_state: Optional[GlobalState] = None
        self.store_states: Dict[str, StoreState] = {}
        
        # Load state on initialization
        asyncio.create_task(self.load_state())
    
    async def load_state(self):
        """Load state from disk."""
        try:
            # Load global state
            if self.state_file.exists():
                async with aiofiles.open(self.state_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    self.global_state = GlobalState(**data)
            else:
                self.global_state = GlobalState(
                    started_at=datetime.utcnow().isoformat(),
                    is_running=True
                )
            
            # Load store states
            if self.stores_file.exists():
                async with aiofiles.open(self.stores_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    
                    for store_name, store_data in data.items():
                        # Convert status string back to enum
                        if 'status' in store_data:
                            store_data['status'] = StoreStatus(store_data['status'])
                        
                        self.store_states[store_name] = StoreState(**store_data)
            
            logger.info(f"Loaded state for {len(self.store_states)} stores")
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            self.global_state = GlobalState(
                started_at=datetime.utcnow().isoformat(),
                is_running=True
            )
    
    async def save_state(self):
        """Save state to disk."""
        try:
            # Save global state
            global_data = asdict(self.global_state)
            async with aiofiles.open(self.state_file, 'w') as f:
                await f.write(json.dumps(global_data, indent=2))
            
            # Save store states
            stores_data = {}
            for store_name, store_state in self.store_states.items():
                store_data = asdict(store_state)
                # Convert enum to string for JSON serialization
                store_data['status'] = store_state.status.value
                stores_data[store_name] = store_data
            
            async with aiofiles.open(self.stores_file, 'w') as f:
                await f.write(json.dumps(stores_data, indent=2))
            
            logger.debug("State saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get_store_state(self, store_name: str) -> StoreState:
        """Get state for a store, creating if it doesn't exist."""
        if store_name not in self.store_states:
            self.store_states[store_name] = StoreState(
                name=store_name,
                status=StoreStatus.ACTIVE
            )
        return self.store_states[store_name]
    
    def is_store_ready_for_poll(self, store_name: str, interval_minutes: int) -> bool:
        """Check if a store is ready to be polled."""
        store_state = self.get_store_state(store_name)
        
        # Check if store is active
        if store_state.status == StoreStatus.DISABLED:
            return False
        
        # Check if store is in backoff period
        if store_state.status == StoreStatus.ERROR_BACKOFF:
            if store_state.backoff_until:
                backoff_time = datetime.fromisoformat(store_state.backoff_until)
                if datetime.utcnow() < backoff_time:
                    return False
                else:
                    # Backoff period expired, reset to active
                    store_state.status = StoreStatus.ACTIVE
                    store_state.backoff_until = None
        
        # Check if enough time has passed since last poll
        if store_state.last_attempt:
            last_attempt = datetime.fromisoformat(store_state.last_attempt)
            next_poll = last_attempt + timedelta(minutes=interval_minutes)
            if datetime.utcnow() < next_poll:
                return False
        
        return True
    
    def record_poll_attempt(self, store_name: str):
        """Record that a poll attempt is starting."""
        store_state = self.get_store_state(store_name)
        store_state.last_attempt = datetime.utcnow().isoformat()
        store_state.total_polls += 1
    
    def record_poll_success(self, store_name: str, product_count: int, changes_count: int):
        """Record a successful poll."""
        store_state = self.get_store_state(store_name)
        
        now = datetime.utcnow().isoformat()
        store_state.last_successful_poll = now
        store_state.successful_polls += 1
        store_state.last_product_count = product_count
        store_state.last_changes_count = changes_count
        
        # Reset failure tracking on success
        store_state.consecutive_failures = 0
        store_state.last_error = None
        
        # Reset to active status if it was in error state
        if store_state.status == StoreStatus.ERROR_BACKOFF:
            store_state.status = StoreStatus.ACTIVE
            store_state.backoff_until = None
        
        logger.info(f"✅ {store_name} poll successful: {product_count} products, {changes_count} changes")
    
    def record_poll_failure(self, store_name: str, error_message: str):
        """Record a failed poll and apply backoff logic."""
        store_state = self.get_store_state(store_name)
        
        store_state.failed_polls += 1
        store_state.consecutive_failures += 1
        store_state.last_error = error_message
        
        # Apply backoff logic
        if store_state.consecutive_failures >= self.max_consecutive_failures:
            # Disable store after too many failures
            store_state.status = StoreStatus.DISABLED
            logger.warning(f"🚫 {store_name} disabled after {self.max_consecutive_failures} consecutive failures")
        else:
            # Apply exponential backoff
            backoff_minutes = min(
                self.base_backoff_minutes * (self.backoff_multiplier ** (store_state.consecutive_failures - 1)),
                self.max_backoff_minutes
            )
            
            backoff_until = datetime.utcnow() + timedelta(minutes=backoff_minutes)
            store_state.status = StoreStatus.ERROR_BACKOFF
            store_state.backoff_until = backoff_until.isoformat()
            
            logger.warning(f"⏰ {store_name} in backoff for {backoff_minutes} min after {store_state.consecutive_failures} failures")
    
    def get_next_poll_time(self, store_name: str, interval_minutes: int) -> Optional[datetime]:
        """Get the next scheduled poll time for a store."""
        store_state = self.get_store_state(store_name)
        
        if store_state.status == StoreStatus.DISABLED:
            return None
        
        # If in backoff, use backoff time
        if store_state.status == StoreStatus.ERROR_BACKOFF and store_state.backoff_until:
            return datetime.fromisoformat(store_state.backoff_until)
        
        # Otherwise, use normal interval
        if store_state.last_attempt:
            last_attempt = datetime.fromisoformat(store_state.last_attempt)
            return last_attempt + timedelta(minutes=interval_minutes)
        
        # Never polled before, ready now
        return datetime.utcnow()
    
    def reset_store_state(self, store_name: str):
        """Reset a store to active state (useful for manual recovery)."""
        store_state = self.get_store_state(store_name)
        store_state.status = StoreStatus.ACTIVE
        store_state.consecutive_failures = 0
        store_state.backoff_until = None
        store_state.last_error = None
        
        logger.info(f"🔄 {store_name} state reset to active")
    
    def disable_store(self, store_name: str, reason: str = "Manual disable"):
        """Manually disable a store."""
        store_state = self.get_store_state(store_name)
        store_state.status = StoreStatus.DISABLED
        store_state.last_error = reason
        
        logger.info(f"🚫 {store_name} manually disabled: {reason}")
    
    def enable_store(self, store_name: str):
        """Enable a disabled store."""
        store_state = self.get_store_state(store_name)
        store_state.status = StoreStatus.ACTIVE
        store_state.last_error = None
        store_state.consecutive_failures = 0
        store_state.backoff_until = None
        
        logger.info(f"✅ {store_name} enabled")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health statistics."""
        total_stores = len(self.store_states)
        active_stores = sum(1 for s in self.store_states.values() if s.status == StoreStatus.ACTIVE)
        disabled_stores = sum(1 for s in self.store_states.values() if s.status == StoreStatus.DISABLED)
        backoff_stores = sum(1 for s in self.store_states.values() if s.status == StoreStatus.ERROR_BACKOFF)
        
        total_polls = sum(s.total_polls for s in self.store_states.values())
        successful_polls = sum(s.successful_polls for s in self.store_states.values())
        failed_polls = sum(s.failed_polls for s in self.store_states.values())
        
        success_rate = (successful_polls / total_polls * 100) if total_polls > 0 else 0
        
        # Get stores with recent errors
        recent_errors = []
        for store_name, state in self.store_states.items():
            if state.consecutive_failures > 0:
                recent_errors.append({
                    'store': store_name,
                    'failures': state.consecutive_failures,
                    'last_error': state.last_error,
                    'status': state.status.value
                })
        
        return {
            'system_status': 'running' if self.global_state.is_running else 'stopped',
            'total_stores': total_stores,
            'active_stores': active_stores,
            'disabled_stores': disabled_stores,
            'backoff_stores': backoff_stores,
            'total_polls': total_polls,
            'successful_polls': successful_polls,
            'failed_polls': failed_polls,
            'success_rate': round(success_rate, 2),
            'uptime': self._calculate_uptime(),
            'recent_errors': recent_errors
        }
    
    def _calculate_uptime(self) -> str:
        """Calculate system uptime."""
        if not self.global_state.started_at:
            return "unknown"
        
        started = datetime.fromisoformat(self.global_state.started_at)
        uptime = datetime.utcnow() - started
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        return f"{days}d {hours}h {minutes}m"
    
    def get_store_status_report(self) -> List[Dict[str, Any]]:
        """Get detailed status report for all stores."""
        stores = []
        
        for store_name, state in self.store_states.items():
            next_poll = None
            if state.last_attempt:
                # This would need interval from config
                next_poll = "calculated based on interval"
            
            stores.append({
                'name': store_name,
                'status': state.status.value,
                'last_successful_poll': state.last_successful_poll,
                'last_attempt': state.last_attempt,
                'consecutive_failures': state.consecutive_failures,
                'success_rate': round((state.successful_polls / state.total_polls * 100) if state.total_polls > 0 else 0, 2),
                'last_product_count': state.last_product_count,
                'last_changes_count': state.last_changes_count,
                'last_error': state.last_error,
                'backoff_until': state.backoff_until
            })
        
        return sorted(stores, key=lambda x: x['name'])
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old state files and data."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # This would clean up old snapshots, logs, etc.
        # Implementation depends on file structure
        
        self.global_state.last_cleanup = datetime.utcnow().isoformat()
        logger.info(f"Cleaned up data older than {days_to_keep} days")
    
    async def periodic_save(self, interval_seconds: int = 300):
        """Periodically save state to disk."""
        while self.global_state.is_running:
            await asyncio.sleep(interval_seconds)
            await self.save_state()
    
    def start(self):
        """Mark system as started."""
        self.global_state.is_running = True
        if not self.global_state.started_at:
            self.global_state.started_at = datetime.utcnow().isoformat()
    
    def stop(self):
        """Mark system as stopped."""
        self.global_state.is_running = False


# Example usage and testing
async def test_state_manager():
    """Test the state management system."""
    manager = StateManager(state_dir="test_state")
    
    manager.start()
    
    # Simulate some poll attempts
    stores = ['housing_works', 'conbud', 'alta']
    
    for store in stores:
        print(f"\nTesting {store}:")
        
        # First poll - success
        manager.record_poll_attempt(store)
        manager.record_poll_success(store, product_count=25, changes_count=3)
        
        # Second poll - failure
        manager.record_poll_attempt(store)
        manager.record_poll_failure(store, "Network timeout")
        
        # Check if ready for next poll
        ready = manager.is_store_ready_for_poll(store, interval_minutes=60)
        print(f"  Ready for next poll: {ready}")
        
        state = manager.get_store_state(store)
        print(f"  Status: {state.status.value}")
        print(f"  Consecutive failures: {state.consecutive_failures}")
    
    # Print system health
    health = manager.get_system_health()
    print(f"\nSystem Health:")
    for key, value in health.items():
        print(f"  {key}: {value}")
    
    # Save state
    await manager.save_state()
    
    manager.stop()


if __name__ == "__main__":
    asyncio.run(test_state_manager())