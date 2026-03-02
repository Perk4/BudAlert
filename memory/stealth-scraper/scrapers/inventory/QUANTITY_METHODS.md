# Quantity Extraction Methods Documentation

## Overview

This document describes the various methods implemented to extract actual inventory quantities from dispensary websites, moving beyond simple boolean "in stock" indicators to provide real quantity numbers.

## Problem Statement

**Current State:** Scrapers only detect "in stock" vs "out of stock" boolean status.  
**Goal:** Extract actual inventory quantities (e.g., "12 available", "Only 3 left").  
**Challenge:** Different dispensary platforms use varying methods to display/limit quantities.

## Extraction Methods

### 1. Quantity Dropdown Analysis

**How it works:** Many dispensary sites have quantity dropdowns that reveal maximum available stock.

```html
<select name="quantity">
  <option value="1">1</option>
  <option value="2">2</option>
  <option value="3">3</option>
  <!-- Max value indicates available stock -->
</select>
```

**Implementation:**
- Find quantity dropdowns using selectors
- Extract all option values and text
- Determine maximum selectable quantity
- Treat max value as available stock

**Reliability:** HIGH - Direct indication of available quantities
**Coverage:** Medium - Not all sites use dropdowns

**Selectors used:**
- `select[name*="quantity"]`
- `select[name*="qty"]`
- `select.quantity`
- `.quantity-select select`

### 2. Quantity Input Max Attribute

**How it works:** Quantity input fields often have `max` attributes indicating stock limits.

```html
<input type="number" name="quantity" min="1" max="8" />
```

**Implementation:**
- Find quantity input fields
- Read the `max` attribute value
- Use as available quantity

**Reliability:** HIGH - Explicit quantity limit
**Coverage:** Medium - Only when inputs have max attributes

### 3. Stock Status Text Parsing

**How it works:** Parse text content for quantity indicators.

**Common patterns:**
- "Only 5 left"
- "12 in stock"
- "8 available"
- "Stock: 15"
- "Qty: 7"

**Implementation:**
- Scan page text for quantity patterns using regex
- Extract numeric values from matching text
- Handle variations in formatting and language

**Regex patterns used:**
```python
patterns = [
    r'only\s*(\d+)\s*left',     # "Only 5 left"
    r'(\d+)\s*in\s*stock',      # "12 in stock"  
    r'(\d+)\s*available',       # "8 available"
    r'stock:\s*(\d+)',          # "Stock: 15"
    r'qty:\s*(\d+)',            # "Qty: 7"
    r'quantity:\s*(\d+)',       # "Quantity: 9"
]
```

**Reliability:** MEDIUM - Depends on consistent text formatting
**Coverage:** HIGH - Many sites display stock text

### 4. Cart Probing Method

**How it works:** Attempt to add high quantities to cart and parse error messages for actual limits.

**Process:**
1. Set quantity input to high number (e.g., 99)
2. Click "Add to Cart" button
3. Parse error message for actual quantity limit
4. Extract real stock number from error text

**Example error messages:**
- "Maximum of 5 items allowed"
- "Only 3 available in stock"
- "Cannot add more than 7 items"

**Implementation:**
```python
# Try high quantity
await set_quantity_input(page, 99)
result = await attempt_add_to_cart(page)
if result['error_message']:
    actual_qty = extract_quantity_from_error(result['error_message'])
```

**Reliability:** HIGH - Direct server-side validation
**Coverage:** HIGH - Works on most e-commerce sites
**Cost:** HIGH - Resource intensive, potential rate limiting

### 5. Binary Search Cart Probing

**How it works:** Use binary search to efficiently find maximum addable quantity.

**Process:**
1. Set initial range (e.g., 1-50)
2. Try midpoint quantity
3. If successful, try higher; if failed, try lower
4. Converge on maximum quantity

**Benefits:**
- More efficient than linear testing
- Reduces number of cart operations
- Less likely to trigger rate limiting

**Implementation:**
```python
low, high = 1, 50
while low <= high:
    mid = (low + high) // 2
    if can_add_quantity(mid):
        found_max = mid
        low = mid + 1
    else:
        high = mid - 1
```

**Reliability:** HIGH - Systematic approach
**Coverage:** HIGH - Works where cart operations are available
**Cost:** MEDIUM - Fewer requests than incremental testing

### 6. API Request Interception

**How it works:** Monitor network requests for inventory/stock API calls.

**Implementation:**
- Intercept XHR/fetch requests
- Look for inventory/stock API endpoints
- Extract quantity data from JSON responses

**Example API patterns:**
```javascript
// Typical inventory API response
{
  "product_id": "123",
  "price": 45.00,
  "inventory": {
    "available": 12,
    "reserved": 2,
    "total": 14
  }
}
```

**Reliability:** HIGHEST - Direct from source data
**Coverage:** LOW - Requires exposed APIs
**Complexity:** HIGH - Platform-specific implementation

## Platform-Specific Implementation

### Blaze Platform (Housing Works)

**Primary methods:**
1. Cart probing with error message parsing
2. Stock status text parsing
3. API request interception

**Characteristics:**
- JavaScript-heavy SPA
- Dynamic content loading
- Standardized cart error messages

**Implementation details:**
```python
# Blaze-specific selectors
selectors = {
    'quantity_input': 'input[name*="quantity"]',
    'add_to_cart': '.add-to-cart button',
    'error_messages': '.error-message'
}
```

### Joint Ecommerce (Stoops, Alta)

**Primary methods:**
1. Quantity dropdown analysis
2. Input max attribute checking
3. Stock text parsing

**Characteristics:**
- More traditional form-based interfaces
- Quantity dropdowns common
- Consistent HTML structure

**Implementation details:**
```python
# Joint Ecommerce selectors
selectors = {
    'quantity_dropdown': 'select[name*="quantity"]',
    'quantity_input': 'input[type="number"]',
    'stock_status': '.stock-status'
}
```

### Dutchie Embed (CONBUD)

**Primary methods:**
1. API request interception
2. JSON data extraction
3. Stock indicator parsing

**Characteristics:**
- Embedded iframe widgets
- GraphQL APIs
- Real-time inventory updates

## Method Selection Strategy

### Priority Order

1. **Quantity dropdown** - Most reliable, direct indication
2. **Input max attribute** - Explicit limit, reliable
3. **API interception** - Highest accuracy when available
4. **Stock text parsing** - Good fallback, widely applicable
5. **Cart probing** - Last resort, resource intensive
6. **Boolean stock status** - Minimum viable information

### Fallback Chain

```python
async def extract_quantity_info(element, product_url):
    # Try dropdown analysis
    dropdown_result = await check_quantity_dropdown(element)
    if dropdown_result['found']:
        return dropdown_result
    
    # Try input max attribute
    input_result = await check_quantity_input(element)
    if input_result['found']:
        return input_result
    
    # Try stock text parsing
    text_result = await check_stock_text(element)
    if text_result['found']:
        return text_result
    
    # Try cart probing (if enabled)
    if enable_cart_probing:
        probe_result = await cart_probe_quantity(product_url)
        if probe_result['success']:
            return probe_result
    
    # Fallback to boolean stock status
    return await check_basic_stock_status(element)
```

## Output Format

### Standard Quantity Information Fields

```python
quantity_info = {
    'quantity_available': 12,           # Number of items available
    'quantity_method': 'dropdown',      # Method used to determine quantity
    'max_quantity': 12,                 # Maximum selectable quantity
    'in_stock': True,                   # Boolean stock status
    'quantity_signals': ['dropdown_max_12'],  # List of signals found
    'confidence': 'high'                # Confidence level in result
}
```

### Method Types

- `dropdown` - Extracted from quantity dropdown
- `input_max` - From input field max attribute
- `stock_text` - Parsed from text content
- `cart_probe` - From cart operation testing
- `api_data` - From intercepted API calls
- `stock_indicator` - From stock status elements
- `default_assume_stock` - Fallback assumption
- `unknown` - No reliable method found

### Confidence Levels

- `high` - Direct quantity indication (dropdown, input max, API)
- `medium` - Parsed from text or cart operations
- `low` - Basic stock status or assumptions

## Testing and Validation

### Test Coverage

Each method should be tested on:
- ✅ Housing Works (Blaze platform)
- ✅ Stoops (Joint Ecommerce)
- ✅ Alta (Joint Ecommerce)
- 🔄 CONBUD (Dutchie embed) - Future implementation

### Success Metrics

- **Extraction Rate**: Percentage of products with quantity found
- **Accuracy**: Correctness of extracted quantities (where verifiable)
- **Method Distribution**: Which methods work best per platform
- **Performance**: Speed and resource usage

### Test Results Format

```json
{
  "store": "housing_works",
  "platform": "blaze",
  "total_products": 15,
  "quantities_found": 12,
  "success_rate": 80.0,
  "method_breakdown": {
    "cart_probe": 8,
    "stock_text": 3,
    "dropdown": 1,
    "default_assume_stock": 3
  }
}
```

## Best Practices

### Performance Optimization

1. **Method prioritization** - Try fastest/most reliable methods first
2. **Selective deep analysis** - Only use expensive methods on sample products
3. **Caching** - Store results to avoid repeated analysis
4. **Rate limiting** - Respect site limits, especially for cart probing

### Error Handling

1. **Graceful degradation** - Fall back to simpler methods on failure
2. **Timeout handling** - Prevent hanging on unresponsive operations
3. **Error logging** - Track which methods fail for which sites
4. **Retry logic** - Handle temporary failures

### Stealth Considerations

1. **Human-like behavior** - Add delays between cart operations
2. **Session management** - Handle cart state properly
3. **User agent rotation** - Avoid detection
4. **Request pattern variation** - Don't be too predictable

## Future Improvements

### Enhanced Methods

1. **Machine learning quantity detection** - Train models on quantity patterns
2. **Computer vision** - OCR on quantity images
3. **Real-time inventory tracking** - Monitor quantity changes over time
4. **Cross-validation** - Compare multiple methods for accuracy

### Platform Support

1. **Additional platforms** - Dutchie, Jane, WooCommerce
2. **Mobile-specific handling** - Mobile site quantity patterns
3. **API-first approach** - Direct integration where possible

### Analytics

1. **Quantity trend analysis** - Track inventory changes over time
2. **Restock prediction** - Predict when items come back in stock
3. **Price-quantity correlation** - Analyze pricing vs availability

## Implementation Checklist

### Phase 1: Core Infrastructure ✅
- [x] QuantityParser class
- [x] CartProber class  
- [x] Base selectors and patterns
- [x] Error handling and logging

### Phase 2: Platform Integration ✅
- [x] Housing Works (Blaze) scraper with quantity
- [x] Stoops (Joint Ecommerce) scraper with quantity
- [x] Alta (Joint Ecommerce) scraper with quantity

### Phase 3: Testing and Validation ✅
- [x] Test script for all stores
- [x] Results analysis and reporting
- [x] Method effectiveness comparison

### Phase 4: Production Integration 🔄
- [ ] Update existing scrapers with quantity fields
- [ ] Add quantity change detection to monitoring
- [ ] Implement quantity-based alerting
- [ ] Performance optimization

## Conclusion

The quantity extraction system provides a comprehensive approach to gathering real inventory data from dispensary websites. By implementing multiple detection methods with intelligent fallbacks, we can achieve high coverage while maintaining reliability and performance.

The modular design allows for easy extension to new platforms and methods, while the testing framework ensures consistent quality across implementations.