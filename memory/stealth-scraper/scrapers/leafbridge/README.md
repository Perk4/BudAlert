# LeafBridge Platform Analysis & Extraction Guide

## Platform Overview

LeafBridge is a WordPress plugin that provides a complete e-commerce solution for cannabis dispensaries. It integrates with Dutchie Plus and Dutchie E-Commerce Pro to deliver a standardized menu management system.

**Key Characteristics:**
- WordPress plugin architecture
- Dutchie E-Commerce backend integration
- AJAX-based product loading
- Age verification gates
- Standardized retailer identification system
- Multi-state compatibility

## Architecture Analysis

### Core Components

1. **WordPress Plugin**: `leafbridge/` plugin directory
2. **Dutchie Integration**: Backend API connection to Dutchie E-Commerce Pro
3. **AJAX Endpoints**: Custom WordPress AJAX handlers for product data
4. **Session Management**: WordPress sessions + optional age verification

### URL Structure

```
https://example.com/
├── ?dtche[path]=products          # Dutchie E-Commerce product path
├── /categories/flower/            # Category-specific pages  
├── /shop                          # Main shop page
├── /wp-admin/admin-ajax.php       # AJAX endpoint for all API calls
└── /wp-json/                      # WordPress REST API (limited LeafBridge endpoints)
```

### API Endpoints

#### WordPress AJAX Actions
All API calls go through `wp-admin/admin-ajax.php` with these actions:

| Action | Purpose | Key Parameters |
|--------|---------|----------------|
| `get_default_retailer` | Get store configuration | none |
| `wizard_show_products` | Get product listings | `retailer_id`, `menu_type`, `category`, `prods_per_page` |
| `show_featured_products_func` | Get featured products | `retailer_id` |
| `leafbridge_single_product` | Get single product details | `product_id`, `retailer_id` |
| `leafbridge_nearby_retailers` | Find nearby stores | `latitude`, `longitude` |
| `show_delivery_pickup_ajax` | Get fulfillment options | `retailer_id` |
| `leafbridge_shop_add_products_to_cart` | Add to cart | `product_id`, `quantity` |
| `leafbridge_get_cart_items` | Get cart contents | `retailer_id` |

#### Custom REST API Namespaces
- `lbcustom/v1/` - Basic LeafBridge endpoints
- `leafbridge-cron-ping/v1/` - Cron/health check endpoints

## Retailer Identification System

Each LeafBridge store has a unique Dutchie retailer ID (UUID format):

```
Example: 5fb99a40-9e34-4b1e-88be-b37b754a33d8 (QUBE NYC)
```

This ID is used in all API calls to identify which store's data to retrieve.

## Product Data Structure

### Standard LeafBridge Product Schema

```javascript
{
  "id": "product_uuid",
  "name": "Product Name", 
  "brand": "Brand Name",
  "category": "FLOWER|PRE_ROLLS|EDIBLES|CONCENTRATES|VAPORIZERS|TOPICALS|TINCTURES|ACCESSORIES",
  "subcategory": "Specific subcategory",
  "price": 29.99,
  "displayPrice": "$29.99",
  "thcPercent": 24.5,
  "cbdPercent": 0.2,
  "strainType": "hybrid|indica|sativa",
  "effects": ["relaxed", "happy", "euphoric"],
  "inStock": true,
  "weight": "3.5g",
  "description": "Product description text",
  "image": "https://example.com/image.jpg"
}
```

## Extraction Strategy

### 1. Session Initialization
```python
# Visit main page to establish session
response = session.get(base_url)

# Handle age verification if required
# (Usually handled client-side via localStorage/cookies)
```

### 2. Retailer Detection
```python
# Auto-detect retailer ID
response = session.post(f"{base_url}/wp-admin/admin-ajax.php", data={
    'action': 'get_default_retailer'
})
retailer_id = response.json()['data']['leafbridge_default_settings']['default_store']
```

### 3. Product Extraction
```python
# Get products via AJAX
response = session.post(f"{base_url}/wp-admin/admin-ajax.php", data={
    'action': 'wizard_show_products',
    'retailer_id': retailer_id,
    'menu_type': 'RECREATIONAL',
    'prods_per_page': 100
})
```

## Platform Quirks & Gotchas

### 1. Age Verification
- Often handled entirely client-side via JavaScript
- May require localStorage/sessionStorage manipulation
- Some sites have server-side age gates via AJAX

### 2. Empty Product Responses
- API may return empty results if:
  - Store is offline/maintenance mode
  - Age verification not completed
  - Invalid retailer ID
  - Products not synced from Dutchie

### 3. Menu Types
- `RECREATIONAL` - Adult-use menu
- `MEDICAL` - Medical marijuana menu
- Some stores only have one menu type active

### 4. Session Requirements
- WordPress session cookies may be required
- Some stores require referrer headers
- Rate limiting varies by implementation

### 5. JavaScript Dependency
- Heavy reliance on client-side JavaScript
- Product filtering/sorting often client-side
- Some data may only be available after JS execution

## Reusability Assessment

### High Reusability Factors ✅
- **Standardized AJAX actions**: All LeafBridge sites use same action names
- **Consistent retailer ID system**: UUID format across all implementations
- **Common WordPress structure**: Same plugin architecture everywhere
- **Dutchie integration patterns**: Standardized backend API calls

### Variable Implementation Factors ⚠️
- **Age verification**: Different approaches (client/server side)
- **Product data format**: May vary slightly between Dutchie versions
- **Custom styling**: Visual presentation varies significantly
- **Additional features**: Some sites have extra plugins/customizations

### Reusability Score: 85/100

LeafBridge provides excellent reusability potential. The base scraper can be easily adapted to new stores by:

1. Changing the `base_url`
2. Auto-detecting the `retailer_id` 
3. Handling site-specific age verification
4. Adapting to minor data format variations

## Implementation Guide

### For New LeafBridge Stores

1. **Identify LeafBridge**: Look for:
   - Footer text: "Website and Dispensary Menu by LeafBridge"
   - URL patterns with `dtche[path]` parameters
   - WordPress site with LeafBridge plugin assets

2. **Extract Retailer ID**: 
   ```python
   scraper = LeafBridgeBaseScraper("https://newstore.com")
   retailer_id = scraper._detect_retailer_id()
   ```

3. **Create Store-Specific Scraper**:
   ```python
   class NewStoreScraper(LeafBridgeBaseScraper):
       def __init__(self):
           super().__init__(
               base_url="https://newstore.com",
               retailer_id="detected-or-known-retailer-id"
           )
   ```

4. **Handle Store-Specific Quirks**:
   - Custom age verification flows
   - Additional product fields
   - Site-specific rate limiting

## Future Enhancement Opportunities

### 1. JavaScript Rendering
- Use Selenium/Playwright for sites with heavy JS dependency
- Handle client-side age verification automatically
- Access dynamically loaded product data

### 2. Dutchie API Direct Access
- Investigate direct Dutchie API endpoints
- Bypass WordPress layer for faster extraction
- Access real-time inventory data

### 3. Multi-Location Support
- Handle chain stores with multiple locations
- Location-based inventory differences
- Delivery zone detection

### 4. Advanced Filtering
- Category-specific extraction
- Price range filtering
- Strain type targeting

## Known LeafBridge Sites

| Store Name | URL | Location | Retailer ID | Status |
|------------|-----|-----------|------------|---------|
| QUBE NYC | qubenyc.com | Times Square, NY | 5fb99a40-9e34-4b1e-88be-b37b754a33d8 | ✅ Analyzed |

## Troubleshooting

### Common Issues

1. **Empty Product Results**
   - Verify retailer ID is correct
   - Check if age verification is required
   - Confirm store is online and products are synced

2. **AJAX Errors**
   - Ensure proper WordPress session
   - Check for required headers/referrers
   - Verify AJAX action spelling

3. **Rate Limiting**
   - Add delays between requests
   - Respect robots.txt
   - Use appropriate User-Agent headers

### Debug Steps

1. **Manual API Testing**:
   ```bash
   curl -X POST "https://example.com/wp-admin/admin-ajax.php" \
        -d "action=get_default_retailer"
   ```

2. **Network Analysis**:
   - Use browser dev tools to inspect AJAX calls
   - Look for authentication tokens or special headers
   - Monitor session cookie requirements

3. **JavaScript Console**:
   - Check for client-side errors
   - Examine global variables for configuration
   - Test AJAX calls directly in browser console

## Conclusion

LeafBridge provides a highly standardized platform for cannabis e-commerce, making it an excellent target for automated extraction. The consistent API structure and Dutchie integration create reliable patterns that can be exploited across multiple stores with minimal customization.

The platform's WordPress foundation provides familiar development patterns, while the AJAX-based architecture offers clean API endpoints for data extraction. With proper session handling and retailer identification, LeafBridge sites can be efficiently scraped at scale.