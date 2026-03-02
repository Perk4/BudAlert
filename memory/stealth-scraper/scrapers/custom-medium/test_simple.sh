#!/bin/bash

echo "Testing medium custom sites..."
echo ""

# Test Gotham for product data
echo "Gotham test:"
curl -L -s -A "Mozilla/5.0" "https://gotham.nyc/menu" | grep -i "product\|cannabis\|thc" | head -3

echo ""
echo "Green Apple test:"
curl -L -s -A "Mozilla/5.0" "https://greenapple.nyc" | grep -i "menu\|dispensary" | head -2

echo ""
echo "Chelsea Cannabis test:"  
curl -L -s -A "Mozilla/5.0" "https://chelseacannabis.co" | grep -i "dispensary\|cannabis" | head -2

echo ""
echo "Verilife test:"
curl -L -s -A "Mozilla/5.0" "https://www.verilife.com/ny" | grep -i "product\|dispensary" | head -2

echo ""
echo "Done."