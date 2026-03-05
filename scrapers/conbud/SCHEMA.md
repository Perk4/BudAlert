# Dutchie GraphQL Schema Documentation

This document describes the Dutchie GraphQL API schema based on research and network traffic analysis.

**API Endpoint:** `https://api.dutchie.com/graphql`  
**Authentication:** None required for public product queries  
**Rate Limiting:** Unknown (implement conservative 1-2 req/sec)

---

## Core Types

### Product

The main product type returned by menu queries.

```graphql
type Product {
  # Identification
  id: ID!
  name: String!
  
  # Brand
  brand: Brand
  brandName: String  # Alternative field
  
  # Classification
  category: String!
  subcategory: String
  productType: String
  cannabinoidType: String
  menuType: String
  
  # Pricing
  price: Float!
  Price: Float  # Alternative capitalization
  priceMin: Float
  priceMax: Float
  
  # Potency
  potencyThc: Potency
  potencyCbd: Potency
  THCContent: PotencyContent  # Alternative structure
  CBDContent: PotencyContent
  
  # Inventory
  inStock: Boolean!
  quantity: Int
  POSMetaData: POSMetadata
  
  # Media
  image: String
  imageUrl: String
  images: [String!]
  
  # Details
  description: String
  strainType: String  # "indica", "sativa", "hybrid"
  strain: String      # Alternative field
  effects: [String!]
  
  # Variants
  variants: [ProductVariant!]
  
  # Weight
  weight: String
  manualWeight: String
  
  # Flags
  staffPick: Boolean
  featured: Boolean
  special: Boolean
  specialData: SpecialData
  
  # Reviews
  reviewCount: Int
  reviewRating: Float
  
  # Lab Results
  labResults: LabResults
  
  # Timestamps
  createdAt: String
  updatedAt: String
}
```

### Brand

```graphql
type Brand {
  id: ID!
  name: String!
  description: String
  imageUrl: String
}
```

### Potency

```graphql
type Potency {
  formatted: String   # e.g., "22.5%"
  range: [Float!]     # e.g., [22.5, 25.0]
  unit: String        # e.g., "PERCENTAGE"
}
```

### PotencyContent

Alternative potency structure.

```graphql
type PotencyContent {
  unit: String
  range: [Float!]
  formatted: String
}
```

### ProductVariant

Different sizes/weights of the same product.

```graphql
type ProductVariant {
  id: ID!
  option: String!     # e.g., "1g", "3.5g", "7g"
  price: Float!
  inStock: Boolean!
  quantity: Int
}
```

### POSMetadata

Point-of-sale system metadata.

```graphql
type POSMetadata {
  id: ID
  quantity: Int
  canonicalID: String
  canonicalEffectivePotency: Potency
}
```

### SpecialData

Information about product specials/promotions.

```graphql
type SpecialData {
  name: String
  description: String
  type: String
}
```

### LabResults

Laboratory testing results.

```graphql
type LabResults {
  thcPercent: Float
  cbdPercent: Float
  terpenes: [Terpene!]
}

type Terpene {
  name: String!
  percentage: Float!
}
```

---

## Queries

### filteredProducts

**Primary query for fetching products with filters.**

```graphql
query FilteredProducts(
  $dispensaryId: ID!
  $filters: FilterInput
  $offset: Int
  $limit: Int
) {
  filteredProducts(
    dispensaryId: $dispensaryId
    filters: $filters
    offset: $offset
    limit: $limit
  ) {
    products: [Product!]!
    totalCount: Int!
    pageInfo: PageInfo
  }
}
```

**Variables:**

```json
{
  "dispensaryId": "6430f42042cf3c004e37f0f8",
  "filters": {
    "category": ["Flower", "Vapes"],
    "subcategory": ["Indica"],
    "strainType": ["indica"],
    "brand": ["Brand Name"],
    "price": {
      "min": 10,
      "max": 50
    },
    "inStock": true
  },
  "offset": 0,
  "limit": 100
}
```

### menu

**Alternative query structure.**

```graphql
query GetMenu($dispensaryId: ID!) {
  menu(dispensaryId: $dispensaryId) {
    id: ID!
    name: String
    products: [Product!]!
    categories: [Category!]
  }
}
```

### product

**Get single product details.**

```graphql
query GetProduct($productId: ID!, $dispensaryId: ID!) {
  product(id: $productId, dispensaryId: $dispensaryId) {
    # ... all Product fields
  }
}
```

---

## Input Types

### FilterInput

```graphql
input FilterInput {
  category: [String!]
  subcategory: [String!]
  strainType: [String!]
  brand: [String!]
  price: PriceRangeInput
  inStock: Boolean
}
```

### PriceRangeInput

```graphql
input PriceRangeInput {
  min: Float
  max: Float
}
```

---

## Response Types

### PageInfo

Pagination information (cursor-based).

```graphql
type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

### Category

```graphql
type Category {
  id: ID!
  name: String!
  type: String
  subcategories: [String!]
}
```

---

## Known Dispensary IDs

| Dispensary | ID |
|------------|-----|
| Conbud LES | `6430f42042cf3c004e37f0f8` |
| Conbud (Chain) | `conbud` |

**Retailer ID:** `7d9a369e-6b29-4ccb-84c8-e802e28ae23e`

---

## Common Categories

Based on typical Dutchie implementations:

- `Flower` - Whole flower cannabis
- `Pre-Rolls` - Pre-rolled joints
- `Vapes` - Vape cartridges and pens
- `Edibles` - Infused food products
- `Concentrates` - Extracts, wax, shatter
- `Topicals` - Creams, lotions, balms
- `Tinctures` - Liquid extracts
- `Accessories` - Pipes, papers, etc.

## Common Subcategories

### Flower
- `Indica`
- `Sativa`
- `Hybrid`

### Strain Types
- `indica` (lowercase)
- `sativa`
- `hybrid`

---

## Example Responses

### filteredProducts Response

```json
{
  "data": {
    "filteredProducts": {
      "products": [
        {
          "id": "64a1b2c3d4e5f6a7b8c9d0e1",
          "name": "Blue Dream",
          "brand": {
            "name": "House Brand",
            "id": "brand123"
          },
          "category": "Flower",
          "subcategory": "Sativa",
          "price": 45.00,
          "potencyThc": {
            "formatted": "22.5%",
            "range": [22.5, 24.0],
            "unit": "PERCENTAGE"
          },
          "potencyCbd": {
            "formatted": "0.1%",
            "range": [0.1],
            "unit": "PERCENTAGE"
          },
          "image": "https://images.dutchie.com/...",
          "images": ["https://images.dutchie.com/1.jpg"],
          "strainType": "sativa",
          "effects": ["creative", "energetic", "uplifted"],
          "description": "A sativa-dominant hybrid...",
          "inStock": true,
          "quantity": 47,
          "variants": [
            {
              "id": "v1",
              "option": "3.5g",
              "price": 45.00,
              "inStock": true
            },
            {
              "id": "v2",
              "option": "7g",
              "price": 85.00,
              "inStock": true
            }
          ]
        }
      ],
      "totalCount": 127,
      "pageInfo": {
        "hasNextPage": false,
        "hasPreviousPage": false
      }
    }
  }
}
```

### menu Response

```json
{
  "data": {
    "menu": {
      "id": "menu123",
      "name": "Conbud LES Menu",
      "products": [
        {
          "id": "prod123",
          "name": "Blue Dream",
          "brandName": "House Brand",
          "category": "Flower",
          "Price": 45.00,
          "THCContent": {
            "formatted": "22.5%",
            "range": [22.5]
          },
          "image": "https://images.dutchie.com/...",
          "POSMetaData": {
            "quantity": 47
          }
        }
      ],
      "categories": [
        {
          "id": "cat1",
          "name": "Flower",
          "type": "FLOWER",
          "subcategories": ["Indica", "Sativa", "Hybrid"]
        }
      ]
    }
  }
}
```

---

## Field Mapping

Different query types may return products with different field names:

| Normalized Field | filteredProducts | menu |
|------------------|------------------|------|
| `brand` | `brand.name` | `brandName` |
| `price` | `price` | `Price` |
| `thc` | `potencyThc.formatted` | `THCContent.formatted` |
| `cbd` | `potencyCbd.formatted` | `CBDContent.formatted` |
| `quantity` | `quantity` | `POSMetaData.quantity` |

The `normalizeProduct()` function in `queries.mjs` handles these variations.

---

## Notes

### Undocumented Fields

These fields appear in responses but may not be consistently available:

- `weight` - Product weight as string
- `manualWeight` - Manually entered weight
- `staffPick` - Staff recommendation flag
- `featured` - Featured product flag
- `reviewCount` - Number of reviews
- `reviewRating` - Average rating

### Pagination

Dutchie supports two pagination styles:

1. **Offset-based:** Use `offset` and `limit` variables
2. **Cursor-based:** Use `startCursor`/`endCursor` from `pageInfo`

For scraping all products, offset-based with high limit (1000) is simplest.

### API Changes

The Dutchie API may change without notice. If queries start failing:

1. Run `browser-scraper.mjs` to capture current queries
2. Compare with templates in `queries.mjs`
3. Update query structures as needed
4. Document changes in this file

---

**Last Updated:** 2026-03-05  
**Schema Version:** Inferred from research  
**Status:** Partially documented (needs live validation)
