#!/bin/bash
"""
Test script for medium custom site scrapers
Tests each scraper's ability to fetch data using curl
"""

echo "=== Testing Medium Custom Sites Scrapers ==="
echo ""

# Test Travel Agency
echo "1. Testing Travel Agency (thetravelagency.co)..."
travel_agency_data=$(curl -L -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "https://thetravelagency.co/menu" | grep -o '"product.*"' | head -5)
if [ ! -z "$travel_agency_data" ]; then
    echo "✓ Travel Agency: Found product data"
    echo "Sample: $(echo "$travel_agency_data" | head -1)"
else
    echo "✗ Travel Agency: No product data found"
fi
echo ""

# Test Gotham
echo "2. Testing Gotham (gotham.nyc)..."
gotham_data=$(curl -L -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "https://gotham.nyc/menu" | grep -i "product\|cannabis\|flower" | head -3)
if [ ! -z "$gotham_data" ]; then
    echo "✓ Gotham: Found cannabis/product references"
else
    echo "✗ Gotham: No product references found"
fi
echo ""

# Test Dazed
echo "3. Testing Dazed (dazed.fun)..."
dazed_data=$(curl -L -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "https://dazed.fun" | grep -i "age\|menu\|product" | head -3)
if [ ! -z "$dazed_data" ]; then
    echo "✓ Dazed: Found age gate or menu references"
else
    echo "✗ Dazed: No menu/age gate found"
fi
echo ""

# Test Green Apple
echo "4. Testing Green Apple (greenapple.nyc)..."
green_apple_data=$(curl -L -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "https://greenapple.nyc" | grep -i "dispensary\|menu\|product" | head -3)
if [ ! -z "$green_apple_data" ]; then
    echo "✓ Green Apple: Found dispensary/menu references"
else
    echo "✗ Green Apple: No dispensary content found"
fi
echo ""

# Test Chelsea Cannabis
echo "5. Testing Chelsea Cannabis (chelseacannabis.co)..."
chelsea_data=$(curl -L -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "https://chelseacannabis.co" | grep -i "dispensary\|cannabis\|menu" | head -3)
if [ ! -z "$chelsea_data" ]; then
    echo "✓ Chelsea Cannabis: Found cannabis references"
else
    echo "✗ Chelsea Cannabis: No cannabis content found"
fi
echo ""

# Test Verilife
echo "6. Testing Verilife (verilife.com/ny)..."
verilife_data=$(curl -L -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "https://www.verilife.com/ny" | grep -i "dispensary\|menu\|product" | head -3)
if [ ! -z "$verilife_data" ]; then
    echo "✓ Verilife: Found dispensary/menu references"
else
    echo "✗ Verilife: No dispensary content found"
fi
echo ""

echo "=== Framework Analysis ==="
echo ""

echo "Travel Agency framework check..."
travel_framework=$(curl -L -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "https://thetravelagency.co" | grep -E "(react|remix|next)" -i | head -1)
echo "Framework: $travel_framework"

echo ""
echo "Gotham framework check..."
gotham_framework=$(curl -L -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "https://gotham.nyc" | grep -E "(wordpress|wp-|dovetail)" -i | head -1)
echo "Framework: $gotham_framework"

echo ""
echo "Dazed framework check..."
dazed_framework=$(curl -L -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "https://dazed.fun" | grep -E "(wordpress|wp-)" -i | head -1)
echo "Framework: $dazed_framework"

echo ""
echo "Green Apple framework check..."
green_apple_framework=$(curl -L -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "https://greenapple.nyc" | grep -E "(wordpress|wp-|custom)" -i | head -1)
echo "Framework: $green_apple_framework"

echo ""
echo "Chelsea Cannabis framework check..."
chelsea_framework=$(curl -L -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "https://chelseacannabis.co" | grep -E "(rails|ruby|csrf)" -i | head -1)
echo "Framework: $chelsea_framework"

echo ""
echo "Verilife framework check..."
verilife_framework=$(curl -L -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "https://www.verilife.com/ny" | grep -E "(magento|mage)" -i | head -1)
echo "Framework: $verilife_framework"

echo ""
echo "=== Test Complete ==="