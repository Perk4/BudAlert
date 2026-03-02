# Inventory Detection Approaches

**Document:** Detection methods and strategies for inventory monitoring across different platforms.

## Detection Methods

### 1. Price Change Detection
- **Method:** Compare current price vs previous extraction
- **Threshold:** Any price difference (even $0.01)
- **Priority:** High (affects purchasing decisions)

### 2. Stock Status Monitoring
- **In Stock → Out of Stock:** High priority alert
- **Out of Stock → In Stock:** Medium priority alert
- **Quantity changes:** Track if quantity numbers are available

### 3. New Product Detection
- **Method:** Compare current product IDs vs previous extraction
- **Criteria:** New product appears in listings
- **Priority:** Medium

### 4. Product Removal Detection
- **Method:** Previous product no longer in current extraction
- **Criteria:** Product disappeared from listings
- **Priority:** Low (might be temporary)

### 5. Category/Menu Changes
- **Method:** Compare available categories/strains
- **Criteria:** New categories appear or disappear
- **Priority:** Low

## Platform-Specific Considerations

### Blaze Platform (Housing Works)
- **Product IDs:** Stable across extractions
- **Price format:** $XX.XX format
- **Stock status:** "In Stock" / "Out of Stock" text

### Dutchie Embed (CONBUD)
- **Product IDs:** JSON-based, stable
- **Price format:** Numerical values
- **Stock status:** Boolean availability flags

### Joint Ecommerce (Torches, Stoops, Alta)
- **Product IDs:** URL-based or SKU-based
- **Price format:** Various formats
- **Stock status:** Availability text or flags
- **Navigation:** Category-based browsing

## Change Event Format

```json
{
  "store": "housing_works",
  "timestamp": "2026-03-02T01:30:00Z",
  "changes": [
    {
      "type": "price_change",
      "product_id": "product_123",
      "product_name": "Blue Dream 3.5g",
      "old_price": 50.00,
      "new_price": 45.00,
      "category": "flower"
    },
    {
      "type": "stock_out",
      "product_id": "product_124",
      "product_name": "OG Kush 1g",
      "category": "flower"
    },
    {
      "type": "new_product",
      "product_id": "product_125",
      "product_name": "White Widow 7g",
      "price": 80.00,
      "category": "flower"
    }
  ]
}
```

## Polling Strategy

### Tiered Approach
- **High-value stores** (Housing Works, Stoops): Every 15 minutes
- **Medium stores** (Most others): Every 1 hour
- **Low-priority stores**: Every 4 hours

### Error Handling
- **Network failures:** Retry 3x with exponential backoff
- **Parsing failures:** Log error, continue with other stores
- **Rate limiting:** Respect store-specific delays