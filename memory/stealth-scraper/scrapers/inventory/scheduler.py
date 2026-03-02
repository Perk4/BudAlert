"""
Unified inventory polling scheduler for all dispensary stores.
Manages tiered polling schedules and coordinates scraping operations.
"""

import asyncio
import json
import logging
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiofiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InventoryScheduler:
    """Manages polling schedules for all stores."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = {}
        self.state_file = Path("scheduler_state.json")
        self.running = False
        self.tasks = {}
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load polling configuration for all stores."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            else:
                # Create default configuration
                self.create_default_config()
                
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create default polling configuration."""
        self.config = {
            'stores': {
                # High-value stores (every 15 minutes)
                'housing_works': {
                    'platform': 'blaze',
                    'priority': 'high',
                    'interval_minutes': 15,
                    'enabled': True,
                    'max_retries': 3,
                    'timeout': 60
                },
                'stoops': {
                    'platform': 'joint_ecommerce',
                    'priority': 'high',
                    'interval_minutes': 15,
                    'enabled': True,
                    'max_retries': 3,
                    'timeout': 60
                },
                
                # Medium priority stores (every hour)
                'conbud': {
                    'platform': 'dutchie_embed',
                    'priority': 'medium',
                    'interval_minutes': 60,
                    'enabled': True,
                    'max_retries': 2,
                    'timeout': 45
                },
                'torches': {
                    'platform': 'joint_ecommerce',
                    'priority': 'medium',
                    'interval_minutes': 60,
                    'enabled': True,
                    'max_retries': 2,
                    'timeout': 45
                },
                'alta': {
                    'platform': 'joint_ecommerce',
                    'priority': 'medium',
                    'interval_minutes': 60,
                    'enabled': True,
                    'max_retries': 2,
                    'timeout': 45
                },
                
                # Low priority stores (every 4 hours)
                'smacked_village': {
                    'platform': 'custom',
                    'priority': 'low',
                    'interval_minutes': 240,
                    'enabled': True,
                    'max_retries': 1,
                    'timeout': 30
                },
                'yerba_buena': {
                    'platform': 'custom',
                    'priority': 'low',
                    'interval_minutes': 240,
                    'enabled': True,
                    'max_retries': 1,
                    'timeout': 30
                }
            },
            
            'global_settings': {
                'max_concurrent_scrapers': 3,
                'default_delay_between_stores': 5,
                'state_save_interval': 300,  # 5 minutes
                'cleanup_old_data_days': 30
            }
        }
        
        # Save default config
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        
        logger.info(f"Created default config at {self.config_path}")
    
    async def load_state(self) -> Dict:
        """Load scheduler state from disk."""
        try:
            if self.state_file.exists():
                async with aiofiles.open(self.state_file, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
        except Exception as e:
            logger.warning(f"Could not load state: {e}")
        
        return {
            'last_polls': {},
            'errors': {},
            'stats': {
                'total_polls': 0,
                'successful_polls': 0,
                'failed_polls': 0
            }
        }
    
    async def save_state(self, state: Dict):
        """Save scheduler state to disk."""
        try:
            async with aiofiles.open(self.state_file, 'w') as f:
                await f.write(json.dumps(state, indent=2))
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def is_poll_due(self, store_name: str, state: Dict) -> bool:
        """Check if a store is due for polling."""
        store_config = self.config['stores'].get(store_name, {})
        if not store_config.get('enabled', True):
            return False
        
        interval_minutes = store_config.get('interval_minutes', 60)
        last_poll = state['last_polls'].get(store_name)
        
        if not last_poll:
            return True
        
        last_poll_time = datetime.fromisoformat(last_poll)
        next_poll_time = last_poll_time + timedelta(minutes=interval_minutes)
        
        return datetime.utcnow() >= next_poll_time
    
    async def poll_store(self, store_name: str, state: Dict) -> bool:
        """Poll a single store for inventory updates."""
        try:
            logger.info(f"Starting poll for {store_name}")
            
            store_config = self.config['stores'][store_name]
            platform = store_config.get('platform', 'unknown')
            
            # Import and run the appropriate scraper
            success = await self.run_scraper(store_name, platform, store_config)
            
            # Update state
            state['last_polls'][store_name] = datetime.utcnow().isoformat()
            state['stats']['total_polls'] += 1
            
            if success:
                state['stats']['successful_polls'] += 1
                # Clear error count on success
                state['errors'].pop(store_name, None)
                logger.info(f"✅ {store_name} poll successful")
            else:
                state['stats']['failed_polls'] += 1
                # Increment error count
                state['errors'][store_name] = state['errors'].get(store_name, 0) + 1
                logger.warning(f"❌ {store_name} poll failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Poll failed for {store_name}: {e}")
            state['stats']['failed_polls'] += 1
            state['errors'][store_name] = state['errors'].get(store_name, 0) + 1
            return False
    
    async def run_scraper(self, store_name: str, platform: str, config: Dict) -> bool:
        """Run the appropriate scraper for the store."""
        try:
            timeout = config.get('timeout', 60)
            
            if platform == 'blaze':
                # Import and run Blaze scraper (Housing Works)
                return await self.run_blaze_scraper(store_name, timeout)
            
            elif platform == 'dutchie_embed':
                # Import and run Dutchie embed scraper (CONBUD)
                return await self.run_dutchie_scraper(store_name, timeout)
            
            elif platform == 'joint_ecommerce':
                # Import and run Joint Ecommerce scraper (Torches, Stoops, Alta)
                return await self.run_joint_ecommerce_scraper(store_name, timeout)
            
            elif platform == 'custom':
                # Import and run custom scraper
                return await self.run_custom_scraper(store_name, timeout)
            
            else:
                logger.error(f"Unknown platform: {platform}")
                return False
                
        except asyncio.TimeoutError:
            logger.error(f"Scraper timeout for {store_name}")
            return False
        except Exception as e:
            logger.error(f"Scraper error for {store_name}: {e}")
            return False
    
    async def run_blaze_scraper(self, store_name: str, timeout: int) -> bool:
        """Run Blaze platform scraper."""
        # This would import and run the actual Blaze scraper
        logger.info(f"Running Blaze scraper for {store_name} (timeout: {timeout}s)")
        await asyncio.sleep(2)  # Simulate scraping
        return True
    
    async def run_dutchie_scraper(self, store_name: str, timeout: int) -> bool:
        """Run Dutchie embed scraper."""
        logger.info(f"Running Dutchie scraper for {store_name} (timeout: {timeout}s)")
        await asyncio.sleep(2)  # Simulate scraping
        return True
    
    async def run_joint_ecommerce_scraper(self, store_name: str, timeout: int) -> bool:
        """Run Joint Ecommerce platform scraper."""
        logger.info(f"Running Joint Ecommerce scraper for {store_name} (timeout: {timeout}s)")
        
        if store_name == 'alta':
            # Use the Alta scraper we just created
            try:
                # This would import and run the Alta scraper
                # from joint_ecommerce.alta import scrape_alta
                # products = await asyncio.wait_for(scrape_alta(), timeout=timeout)
                # return len(products) > 0
                
                # For now, simulate
                await asyncio.sleep(3)
                return True
            except Exception as e:
                logger.error(f"Alta scraper failed: {e}")
                return False
        
        # Other Joint Ecommerce stores (Torches, Stoops)
        await asyncio.sleep(2)  # Simulate scraping
        return True
    
    async def run_custom_scraper(self, store_name: str, timeout: int) -> bool:
        """Run custom store scraper."""
        logger.info(f"Running custom scraper for {store_name} (timeout: {timeout}s)")
        await asyncio.sleep(2)  # Simulate scraping
        return True
    
    async def poll_cycle(self):
        """Run one polling cycle for all due stores."""
        state = await self.load_state()
        
        # Get stores that need polling
        due_stores = []
        for store_name in self.config['stores']:
            if self.is_poll_due(store_name, state):
                due_stores.append(store_name)
        
        if not due_stores:
            logger.debug("No stores due for polling")
            return
        
        logger.info(f"Polling {len(due_stores)} stores: {due_stores}")
        
        # Limit concurrent scrapers
        max_concurrent = self.config['global_settings'].get('max_concurrent_scrapers', 3)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def poll_with_limit(store_name):
            async with semaphore:
                return await self.poll_store(store_name, state)
        
        # Run polls concurrently
        tasks = [poll_with_limit(store) for store in due_stores]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        
        logger.info(f"Polling cycle complete: {successful} successful, {failed} failed")
        
        # Save updated state
        await self.save_state(state)
    
    async def start(self):
        """Start the scheduler."""
        self.running = True
        logger.info("Inventory scheduler started")
        
        # Main polling loop
        while self.running:
            try:
                await self.poll_cycle()
                
                # Wait before next cycle (check every 5 minutes)
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        logger.info("Inventory scheduler stopped")
    
    async def get_status(self) -> Dict:
        """Get current scheduler status."""
        state = await self.load_state()
        
        # Calculate next poll times
        next_polls = {}
        for store_name, store_config in self.config['stores'].items():
            if not store_config.get('enabled', True):
                next_polls[store_name] = "disabled"
                continue
                
            last_poll = state['last_polls'].get(store_name)
            if not last_poll:
                next_polls[store_name] = "due now"
            else:
                interval = store_config.get('interval_minutes', 60)
                last_time = datetime.fromisoformat(last_poll)
                next_time = last_time + timedelta(minutes=interval)
                
                if next_time <= datetime.utcnow():
                    next_polls[store_name] = "due now"
                else:
                    next_polls[store_name] = next_time.isoformat()
        
        return {
            'running': self.running,
            'total_stores': len(self.config['stores']),
            'enabled_stores': sum(1 for s in self.config['stores'].values() if s.get('enabled', True)),
            'stats': state.get('stats', {}),
            'errors': state.get('errors', {}),
            'next_polls': next_polls
        }


async def main():
    """Main entry point for running the scheduler."""
    scheduler = InventoryScheduler()
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())