#!/usr/bin/env python3
"""
Change Detection Validation Script
Tests the change detection system with simulated data before running live test.
"""

import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from change_detector import InventoryChangeDetector


def test_change_detection():
    """Test change detection with known changes."""
    print("🧪 Testing Change Detection System")
    print("=" * 50)
    
    # Create test detector
    detector = InventoryChangeDetector(data_dir="test_run/change_test")
    
    # Test data - baseline
    baseline_products = [
        {
            'id': 'test_001',
            'name': 'Blue Dream 3.5g',
            'price': 50.0,
            'category': 'flower',
            'in_stock': True,
            'store': 'test_store'
        },
        {
            'id': 'test_002', 
            'name': 'OG Kush 1g',
            'price': 20.0,
            'category': 'flower',
            'in_stock': True,
            'store': 'test_store'
        },
        {
            'id': 'test_003',
            'name': 'Gummy Bears 10mg',
            'price': 15.0,
            'category': 'edibles',
            'in_stock': False,
            'store': 'test_store'
        }
    ]
    
    print(f"📦 Baseline: {len(baseline_products)} products")
    
    # Save baseline snapshot
    detector.save_snapshot('test_store', baseline_products)
    
    # Modified data with various changes
    modified_products = [
        {
            'id': 'test_001',
            'name': 'Blue Dream 3.5g',
            'price': 45.0,  # Price decrease
            'category': 'flower',
            'in_stock': True,
            'store': 'test_store'
        },
        {
            'id': 'test_002',
            'name': 'OG Kush 1g', 
            'price': 20.0,
            'category': 'flower',
            'in_stock': False,  # Stock out
            'store': 'test_store'
        },
        {
            'id': 'test_003',
            'name': 'Gummy Bears 10mg',
            'price': 15.0,
            'category': 'edibles',
            'in_stock': True,  # Back in stock
            'store': 'test_store'
        },
        {
            'id': 'test_004',  # New product
            'name': 'White Widow 7g',
            'price': 80.0,
            'category': 'flower',
            'in_stock': True,
            'store': 'test_store'
        }
        # Note: test_005 removed (simulated discontinuation)
    ]
    
    print(f"🔄 Modified: {len(modified_products)} products")
    
    # Detect changes
    print("\n🔍 Detecting changes...")
    changes = detector.detect_changes('test_store', modified_products)
    
    print(f"Found {len(changes)} changes:")
    
    expected_changes = {
        'price_change': 1,  # Blue Dream price drop
        'stock_out': 1,     # OG Kush out of stock  
        'stock_in': 1,      # Gummy Bears back in stock
        'new_product': 1    # White Widow added
        # No removed products in this test
    }
    
    change_summary = detector.get_change_summary(changes)
    
    print("\nDetected changes:")
    for change_type, count in change_summary.items():
        if count > 0:
            expected = expected_changes.get(change_type, 0)
            status = "✅" if count == expected else "❌"
            print(f"  {status} {change_type}: {count} (expected: {expected})")
    
    print("\nChange details:")
    for change in changes:
        if change.type == 'price_change':
            print(f"  💰 Price change: {change.product_name} ${change.old_price} → ${change.new_price}")
        elif change.type == 'stock_out':
            print(f"  📉 Stock out: {change.product_name}")
        elif change.type == 'stock_in':
            print(f"  📈 Stock in: {change.product_name}")
        elif change.type == 'new_product':
            print(f"  🆕 New product: {change.product_name}")
        elif change.type == 'removed_product':
            print(f"  🗑️  Removed product: {change.product_name}")
    
    # Validate results
    all_correct = all(
        change_summary.get(change_type, 0) == expected_count
        for change_type, expected_count in expected_changes.items()
    )
    
    if all_correct:
        print("\n✅ Change detection test PASSED")
        return True
    else:
        print("\n❌ Change detection test FAILED")
        return False


def test_real_store_data():
    """Test change detection with real store data."""
    print("\n🏪 Testing with Real Store Data") 
    print("=" * 50)
    
    detector = InventoryChangeDetector(data_dir="test_run/real_data_test")
    
    # Test with Smacked Village data
    smacked_village_file = Path("test_run/smacked_village_baseline.json")
    if not smacked_village_file.exists():
        print("❌ Baseline file not found")
        return False
    
    with open(smacked_village_file, 'r') as f:
        products = json.load(f)
    
    print(f"📦 Loaded {len(products)} products from Smacked Village")
    
    # Save as baseline
    detector.save_snapshot('smacked_village', products)
    
    # Create modified version
    modified_products = []
    for i, product in enumerate(products):
        modified = product.copy()
        
        # Add some random changes
        if i == 0:
            # Price change on first product
            if 'price' in modified:
                modified['price'] = float(modified['price']) + 3.0
        elif i == 1:
            # Stock change on second product
            modified['stock_status'] = 'out_of_stock'
            modified['in_stock'] = False
        elif i < len(products) - 1:  # Skip last product (removal)
            modified_products.append(modified)
            continue
            
        modified_products.append(modified)
    
    # Add a new product
    new_product = products[0].copy()
    new_product['name'] = f"TEST New Product {datetime.now().strftime('%H%M%S')}"
    if 'id' in new_product:
        new_product['id'] = "test_new_001"
    new_product['price'] = 99.99
    modified_products.append(new_product)
    
    print(f"🔄 Modified to {len(modified_products)} products")
    
    # Detect changes
    changes = detector.detect_changes('smacked_village', modified_products)
    print(f"🔍 Detected {len(changes)} changes")
    
    if changes:
        change_summary = detector.get_change_summary(changes)
        for change_type, count in change_summary.items():
            if count > 0:
                print(f"  - {change_type}: {count}")
        
        print("\nFirst few changes:")
        for change in changes[:5]:
            print(f"  {change.type}: {change.product_name}")
    
    return len(changes) > 0


if __name__ == "__main__":
    try:
        print("Starting change detection validation...\n")
        
        # Test 1: Controlled test with known changes
        test1_passed = test_change_detection()
        
        # Test 2: Real data test
        test2_passed = test_real_store_data()
        
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"✅ Controlled test: {'PASSED' if test1_passed else 'FAILED'}")
        print(f"✅ Real data test: {'PASSED' if test2_passed else 'FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n🎉 Change detection system is working correctly!")
            print("Ready to proceed with live polling test.")
        else:
            print("\n❌ Change detection system needs fixes before live test.")
            
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        traceback.print_exc()