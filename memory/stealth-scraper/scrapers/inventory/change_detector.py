"""
Inventory change detection system.
Compares current vs previous extractions to detect changes in products,
prices, stock status, and availability.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, asdict
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InventoryChange:
    """Represents a single inventory change event."""
    type: str  # price_change, stock_out, stock_in, new_product, removed_product
    product_id: str
    product_name: str
    store: str
    timestamp: str
    category: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    old_price: Optional[float] = None
    new_price: Optional[float] = None
    price_change: Optional[float] = None
    metadata: Optional[Dict] = None


class InventoryChangeDetector:
    """Detects and analyzes changes between inventory snapshots."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Thresholds for change detection
        self.price_change_threshold = 0.01  # Minimum price change to report
        self.similarity_threshold = 0.9  # For product name matching
        
    def get_store_data_path(self, store: str) -> Path:
        """Get the data directory path for a store."""
        store_dir = self.data_dir / store
        store_dir.mkdir(exist_ok=True)
        return store_dir
    
    def get_latest_snapshot_path(self, store: str) -> Optional[Path]:
        """Get the path to the most recent snapshot for a store."""
        store_dir = self.get_store_data_path(store)
        
        # Look for JSON files with timestamp pattern
        json_files = list(store_dir.glob("*.json"))
        if not json_files:
            return None
        
        # Sort by modification time and return the latest
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        return latest_file
    
    def save_snapshot(self, store: str, products: List[Dict]) -> str:
        """Save a new inventory snapshot."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{timestamp}.json"
        filepath = self.get_store_data_path(store) / filename
        
        # Add metadata
        snapshot_data = {
            'store': store,
            'timestamp': datetime.utcnow().isoformat(),
            'product_count': len(products),
            'products': products
        }
        
        with open(filepath, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
        
        logger.info(f"Saved snapshot for {store}: {len(products)} products to {filename}")
        return str(filepath)
    
    def load_snapshot(self, filepath: Path) -> Optional[Dict]:
        """Load a snapshot from file."""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load snapshot {filepath}: {e}")
            return None
    
    def normalize_product(self, product: Dict) -> Dict:
        """Normalize product data for comparison."""
        normalized = {
            'id': str(product.get('id', '')),
            'name': product.get('name', '').strip().lower(),
            'price': float(product.get('price', 0)),
            'category': product.get('category', 'unknown').lower(),
            'in_stock': bool(product.get('in_stock', True)),
            'url': product.get('url', ''),
        }
        
        # Add optional fields if present
        for field in ['thc_content', 'cbd_content', 'strain_type', 'description']:
            if field in product:
                normalized[field] = product[field]
        
        return normalized
    
    def calculate_product_similarity(self, prod1: Dict, prod2: Dict) -> float:
        """Calculate similarity between two products based on name and other attributes."""
        # Name similarity (primary factor)
        name1 = prod1.get('name', '').lower().strip()
        name2 = prod2.get('name', '').lower().strip()
        
        if name1 == name2:
            name_sim = 1.0
        else:
            # Simple character-based similarity
            common_chars = set(name1) & set(name2)
            total_chars = set(name1) | set(name2)
            name_sim = len(common_chars) / len(total_chars) if total_chars else 0
        
        # Category similarity
        cat1 = prod1.get('category', '').lower()
        cat2 = prod2.get('category', '').lower()
        cat_sim = 1.0 if cat1 == cat2 else 0.5
        
        # URL similarity
        url1 = prod1.get('url', '')
        url2 = prod2.get('url', '')
        url_sim = 1.0 if url1 and url2 and url1 == url2 else 0.3
        
        # Weighted combination
        similarity = (name_sim * 0.7) + (cat_sim * 0.2) + (url_sim * 0.1)
        return similarity
    
    def find_matching_product(self, target_product: Dict, product_list: List[Dict]) -> Optional[Tuple[Dict, float]]:
        """Find the best matching product in a list."""
        best_match = None
        best_score = 0
        
        for product in product_list:
            # Check exact ID match first
            if target_product.get('id') and product.get('id') == target_product.get('id'):
                return product, 1.0
            
            # Calculate similarity
            similarity = self.calculate_product_similarity(target_product, product)
            if similarity > best_score and similarity >= self.similarity_threshold:
                best_score = similarity
                best_match = product
        
        return (best_match, best_score) if best_match else (None, 0)
    
    def detect_price_changes(self, old_product: Dict, new_product: Dict) -> Optional[InventoryChange]:
        """Detect price changes between two product versions."""
        old_price = float(old_product.get('price', 0))
        new_price = float(new_product.get('price', 0))
        
        price_diff = new_price - old_price
        
        if abs(price_diff) >= self.price_change_threshold:
            return InventoryChange(
                type='price_change',
                product_id=new_product.get('id', ''),
                product_name=new_product.get('name', ''),
                store=new_product.get('store', ''),
                timestamp=datetime.utcnow().isoformat(),
                category=new_product.get('category'),
                old_price=old_price,
                new_price=new_price,
                price_change=price_diff,
                old_value=old_price,
                new_value=new_price
            )
        
        return None
    
    def detect_stock_changes(self, old_product: Dict, new_product: Dict) -> Optional[InventoryChange]:
        """Detect stock status changes between two product versions."""
        old_stock = bool(old_product.get('in_stock', True))
        new_stock = bool(new_product.get('in_stock', True))
        
        if old_stock != new_stock:
            change_type = 'stock_in' if new_stock else 'stock_out'
            
            return InventoryChange(
                type=change_type,
                product_id=new_product.get('id', ''),
                product_name=new_product.get('name', ''),
                store=new_product.get('store', ''),
                timestamp=datetime.utcnow().isoformat(),
                category=new_product.get('category'),
                old_value=old_stock,
                new_value=new_stock
            )
        
        return None
    
    def detect_changes(self, store: str, current_products: List[Dict]) -> List[InventoryChange]:
        """Detect all changes between current products and the last snapshot."""
        changes = []
        
        # Get the latest snapshot
        latest_snapshot_path = self.get_latest_snapshot_path(store)
        if not latest_snapshot_path:
            logger.info(f"No previous snapshot found for {store}, treating all products as new")
            # All products are new
            for product in current_products:
                changes.append(InventoryChange(
                    type='new_product',
                    product_id=product.get('id', ''),
                    product_name=product.get('name', ''),
                    store=store,
                    timestamp=datetime.utcnow().isoformat(),
                    category=product.get('category'),
                    new_value=product.get('price'),
                    metadata=product
                ))
            return changes
        
        # Load previous snapshot
        previous_snapshot = self.load_snapshot(latest_snapshot_path)
        if not previous_snapshot:
            logger.error(f"Failed to load snapshot for {store}")
            return changes
        
        previous_products = [self.normalize_product(p) for p in previous_snapshot.get('products', [])]
        current_products_norm = [self.normalize_product(p) for p in current_products]
        
        # Track which products we've seen
        matched_previous = set()
        matched_current = set()
        
        # 1. Check for changes in existing products
        for i, current_product in enumerate(current_products_norm):
            match_result = self.find_matching_product(current_product, previous_products)
            
            if match_result[0]:  # Found a match
                old_product = match_result[0]
                old_idx = previous_products.index(old_product)
                
                matched_previous.add(old_idx)
                matched_current.add(i)
                
                # Check for price changes
                price_change = self.detect_price_changes(old_product, current_product)
                if price_change:
                    changes.append(price_change)
                
                # Check for stock changes
                stock_change = self.detect_stock_changes(old_product, current_product)
                if stock_change:
                    changes.append(stock_change)
        
        # 2. Check for new products
        for i, current_product in enumerate(current_products_norm):
            if i not in matched_current:
                changes.append(InventoryChange(
                    type='new_product',
                    product_id=current_product.get('id', ''),
                    product_name=current_product.get('name', ''),
                    store=store,
                    timestamp=datetime.utcnow().isoformat(),
                    category=current_product.get('category'),
                    new_value=current_product.get('price'),
                    metadata=current_product
                ))
        
        # 3. Check for removed products
        for i, previous_product in enumerate(previous_products):
            if i not in matched_previous:
                changes.append(InventoryChange(
                    type='removed_product',
                    product_id=previous_product.get('id', ''),
                    product_name=previous_product.get('name', ''),
                    store=store,
                    timestamp=datetime.utcnow().isoformat(),
                    category=previous_product.get('category'),
                    old_value=previous_product.get('price'),
                    metadata=previous_product
                ))
        
        logger.info(f"Detected {len(changes)} changes for {store}")
        return changes
    
    def save_changes(self, store: str, changes: List[InventoryChange]) -> str:
        """Save changes to a JSON file."""
        if not changes:
            return ""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"changes_{timestamp}.json"
        filepath = self.get_store_data_path(store) / filename
        
        # Convert changes to dict format
        changes_data = {
            'store': store,
            'timestamp': datetime.utcnow().isoformat(),
            'change_count': len(changes),
            'changes': [asdict(change) for change in changes]
        }
        
        with open(filepath, 'w') as f:
            json.dump(changes_data, f, indent=2)
        
        logger.info(f"Saved {len(changes)} changes for {store} to {filename}")
        return str(filepath)
    
    def process_inventory_update(self, store: str, products: List[Dict]) -> Tuple[List[InventoryChange], str]:
        """Complete process: detect changes and save new snapshot."""
        # Detect changes first (before saving new snapshot)
        changes = self.detect_changes(store, products)
        
        # Save new snapshot
        snapshot_path = self.save_snapshot(store, products)
        
        # Save changes if any
        changes_path = ""
        if changes:
            changes_path = self.save_changes(store, changes)
        
        return changes, snapshot_path
    
    def get_change_summary(self, changes: List[InventoryChange]) -> Dict[str, int]:
        """Get a summary of change types."""
        summary = {
            'price_change': 0,
            'stock_out': 0,
            'stock_in': 0,
            'new_product': 0,
            'removed_product': 0
        }
        
        for change in changes:
            summary[change.type] = summary.get(change.type, 0) + 1
        
        return summary


# Example usage and testing
def main():
    """Test the change detection system."""
    detector = InventoryChangeDetector(data_dir="test_data")
    
    # Simulate first snapshot (no changes expected)
    initial_products = [
        {'id': '1', 'name': 'Blue Dream 3.5g', 'price': 50.0, 'category': 'flower', 'in_stock': True, 'store': 'test'},
        {'id': '2', 'name': 'OG Kush 1g', 'price': 20.0, 'category': 'flower', 'in_stock': True, 'store': 'test'},
        {'id': '3', 'name': 'Gummy Bears 10mg', 'price': 15.0, 'category': 'edibles', 'in_stock': False, 'store': 'test'}
    ]
    
    changes1, snapshot1 = detector.process_inventory_update('test_store', initial_products)
    print(f"First snapshot: {len(changes1)} changes")
    print(f"Summary: {detector.get_change_summary(changes1)}")
    
    # Simulate second snapshot with changes
    updated_products = [
        {'id': '1', 'name': 'Blue Dream 3.5g', 'price': 45.0, 'category': 'flower', 'in_stock': True, 'store': 'test'},  # Price drop
        {'id': '2', 'name': 'OG Kush 1g', 'price': 20.0, 'category': 'flower', 'in_stock': False, 'store': 'test'},  # Stock out
        {'id': '3', 'name': 'Gummy Bears 10mg', 'price': 15.0, 'category': 'edibles', 'in_stock': True, 'store': 'test'},  # Back in stock
        {'id': '4', 'name': 'White Widow 7g', 'price': 80.0, 'category': 'flower', 'in_stock': True, 'store': 'test'}  # New product
        # Product #5 removed
    ]
    
    changes2, snapshot2 = detector.process_inventory_update('test_store', updated_products)
    print(f"\nSecond snapshot: {len(changes2)} changes")
    print(f"Summary: {detector.get_change_summary(changes2)}")
    
    # Print individual changes
    for change in changes2:
        print(f"  {change.type}: {change.product_name}")
        if change.type == 'price_change':
            print(f"    Price: ${change.old_price} → ${change.new_price} (${change.price_change:+.2f})")


if __name__ == "__main__":
    main()