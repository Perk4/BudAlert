# Phase 4: Transformation Layer

**Date:** 2026-03-05  
**Focus:** Normalization, entity resolution, aggregation, derived metrics, LLM assistance

---

## Executive Summary

The transformation layer converts **raw, inconsistent data** from hundreds of stores into **clean, unified, enriched data** ready for analysis and delivery. Key challenges:

- **Heterogeneous schemas:** Every platform formats data differently
- **Entity resolution:** Same product at different stores needs to be matched
- **Data quality:** Missing fields, inconsistent formats, typos
- **Enrichment:** Derive insights (velocity scores, trends, comparisons)

**Solution:** Multi-stage transformation pipeline with human-in-the-loop validation for hard cases.

---

## 1. Data Normalization

### Problem: Schema Hell

**Raw data from different platforms:**

```json
// Dutchie (GraphQL)
{
  "Name": "Blue Dream",
  "Brand": { "name": "Alta" },
  "Variants": [{
    "Option": "3.5g",
    "PriceRec": 5500 // cents
  }],
  "Potency": { "THC": [18.5, 19.2] } // range
}

// Jane (REST)
{
  "product_name": "Blue Dream 3.5g",
  "brand_name": "Alta",
  "price": "$55.00",
  "thc_percentage": "18.5-19.2%"
}

// WordPress
{
  "title": { "rendered": "Blue Dream (3.5g) - Alta" },
  "meta_data": [
    { "key": "_price", "value": "55" },
    { "key": "thc", "value": "18.5%" }
  ]
}
```

**Target unified schema:**
```json
{
  "id": "uuid-...",
  "externalId": "dutchie_alta_12345",
  "name": "Blue Dream",
  "variant": "3.5g",
  "brand": "Alta",
  "category": "flower",
  "subcategory": "hybrid",
  "price": 55.00,
  "thc": 18.85, // Average if range
  "thcRange": [18.5, 19.2],
  "cbd": null,
  "quantity": null,
  "inStock": true,
  "imageUrl": "https://...",
  "storeId": "store-123",
  "scrapedAt": 1234567890
}
```

### Normalization Pipeline

```typescript
interface NormalizationRule {
  platform: string;
  extract: (raw: any) => Partial<Product>;
  validate: (product: Product) => boolean;
}

const normalizationRules: NormalizationRule[] = [
  // Dutchie
  {
    platform: 'dutchie',
    extract: (raw) => ({
      name: extractProductName(raw.Name),
      variant: raw.Variants[0]?.Option,
      brand: raw.Brand?.name,
      price: raw.Variants[0]?.PriceRec / 100, // cents to dollars
      thc: averageRange(raw.Potency?.THC),
      thcRange: raw.Potency?.THC,
      category: mapDutchieCategory(raw.Category)
    }),
    validate: (p) => !!p.name && !!p.price
  },
  
  // Jane
  {
    platform: 'jane',
    extract: (raw) => ({
      name: extractProductName(raw.product_name),
      brand: raw.brand_name,
      price: parsePrice(raw.price), // "$55.00" -> 55.00
      thc: parsePercentage(raw.thc_percentage), // "18.5%" -> 18.5
      category: mapJaneCategory(raw.category_id)
    }),
    validate: (p) => !!p.name && !!p.price
  },
  
  // WordPress
  {
    platform: 'wordpress',
    extract: (raw) => {
      const name = raw.title.rendered;
      const { productName, brand, variant } = parseNameString(name);
      
      return {
        name: productName,
        brand,
        variant,
        price: parseFloat(getMeta(raw.meta_data, '_price')),
        thc: parsePercentage(getMeta(raw.meta_data, 'thc')),
        category: mapWPCategory(raw.categories)
      };
    },
    validate: (p) => !!p.name && !!p.price
  }
];

// Main normalization function
async function normalizeProduct(
  raw: any,
  platform: string
): Promise<Product | null> {
  const rule = normalizationRules.find(r => r.platform === platform);
  if (!rule) {
    console.warn(`No normalization rule for platform: ${platform}`);
    return null;
  }
  
  try {
    const extracted = rule.extract(raw);
    
    // Apply common transformations
    const normalized = {
      ...extracted,
      name: cleanProductName(extracted.name),
      brand: cleanBrandName(extracted.brand),
      category: standardizeCategory(extracted.category),
      price: roundPrice(extracted.price),
      thc: roundPercentage(extracted.thc)
    };
    
    // Validate
    if (!rule.validate(normalized)) {
      console.warn(`Validation failed for product:`, normalized);
      return null;
    }
    
    return normalized as Product;
    
  } catch (error) {
    console.error(`Normalization error for platform ${platform}:`, error);
    return null;
  }
}
```

### Normalization Helpers

```typescript
// Price parsing
function parsePrice(priceStr: string): number {
  return parseFloat(priceStr.replace(/[^0-9.]/g, ''));
}

// Percentage parsing
function parsePercentage(pctStr: string): number | null {
  if (!pctStr) return null;
  
  // "18.5%" -> 18.5
  // "18.5-19.2%" -> 18.85 (average)
  // "<20%" -> 20 (max)
  
  const rangeMatch = pctStr.match(/([\d.]+)-([\d.]+)/);
  if (rangeMatch) {
    const [_, min, max] = rangeMatch;
    return (parseFloat(min) + parseFloat(max)) / 2;
  }
  
  const ltMatch = pctStr.match(/<([\d.]+)/);
  if (ltMatch) {
    return parseFloat(ltMatch[1]);
  }
  
  const singleMatch = pctStr.match(/([\d.]+)/);
  return singleMatch ? parseFloat(singleMatch[1]) : null;
}

// Product name cleaning
function cleanProductName(name: string): string {
  return name
    .trim()
    .replace(/\s+/g, ' ') // Normalize whitespace
    .replace(/\(.*?\)$/, '') // Remove trailing parentheses
    .trim();
}

// Brand name cleaning
function cleanBrandName(brand: string | undefined): string | undefined {
  if (!brand) return undefined;
  
  return brand
    .trim()
    .replace(/\b(inc|llc|ltd)\b\.?/i, '') // Remove legal suffixes
    .trim();
}

// Category standardization
const CATEGORY_MAP: Record<string, string> = {
  // Flower
  'flower': 'flower',
  'bud': 'flower',
  'cannabis': 'flower',
  'pre-rolls': 'prerolls',
  'joints': 'prerolls',
  
  // Concentrates
  'concentrate': 'concentrates',
  'wax': 'concentrates',
  'shatter': 'concentrates',
  'dabs': 'concentrates',
  
  // Edibles
  'edible': 'edibles',
  'gummy': 'edibles',
  'gummies': 'edibles',
  'chocolate': 'edibles',
  
  // Vapes
  'vaporizer': 'vapes',
  'cartridge': 'vapes',
  'cart': 'vapes',
  'pen': 'vapes',
  
  // Other
  'topical': 'topicals',
  'tincture': 'tinctures',
  'cbd': 'cbd',
  'accessory': 'accessories'
};

function standardizeCategory(category: string | undefined): string {
  if (!category) return 'other';
  
  const key = category.toLowerCase();
  return CATEGORY_MAP[key] || 'other';
}
```

---

## 2. Entity Resolution

### Problem: Same Product, Different Stores

**Example:**
- Store A: "Blue Dream 3.5g - Alta"
- Store B: "Blue Dream (Eighth) by Alta"
- Store C: "ALTA Blue Dream 1/8oz"

These are the **same product**, but have different:
- Names (punctuation, abbreviations)
- Variants (3.5g vs Eighth vs 1/8oz)
- Prices (different stores)
- Availability (one might be out of stock)

**Goal:** Create a **canonical product** that aggregates across stores.

### Entity Resolution Strategy

```typescript
// Canonical product representation
interface CanonicalProduct {
  id: string; // uuid
  name: string; // "Blue Dream"
  brand: string; // "Alta"
  category: string; // "flower"
  variant: string; // "3.5g"
  
  // Aggregated from all stores
  stores: Array<{
    storeId: string;
    price: number;
    inStock: boolean;
    url: string;
    lastSeen: number;
  }>;
  
  // Derived fields
  minPrice: number;
  maxPrice: number;
  avgPrice: number;
  availableAt: number; // # of stores in stock
  totalStores: number;
}
```

### Matching Algorithm

```typescript
async function resolveEntity(product: Product): Promise<string> {
  // Generate matching signature
  const signature = generateSignature(product);
  
  // Check if canonical product exists
  const existing = await ctx.db
    .query('canonicalProducts')
    .withIndex('by_signature', q => q.eq('signature', signature))
    .first();
  
  if (existing) {
    return existing._id;
  }
  
  // Fuzzy match as fallback
  const candidates = await findCandidates(product);
  
  for (const candidate of candidates) {
    const similarity = calculateSimilarity(product, candidate);
    
    if (similarity > 0.85) { // 85% match threshold
      return candidate._id;
    }
  }
  
  // No match found, create new canonical product
  const canonicalId = await ctx.db.insert('canonicalProducts', {
    signature,
    name: product.name,
    brand: product.brand,
    category: product.category,
    variant: product.variant,
    createdAt: Date.now()
  });
  
  return canonicalId;
}

// Signature generation (exact match)
function generateSignature(product: Product): string {
  const parts = [
    normalizeText(product.brand),
    normalizeText(product.name),
    normalizeVariant(product.variant),
    product.category
  ].filter(Boolean);
  
  return parts.join(':').toLowerCase();
}

function normalizeText(text: string | undefined): string {
  if (!text) return '';
  
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '') // Remove non-alphanumeric
    .trim();
}

function normalizeVariant(variant: string | undefined): string {
  if (!variant) return '';
  
  // Standardize common variants
  const variantMap: Record<string, string> = {
    'eighth': '3.5g',
    '1/8oz': '3.5g',
    'quarter': '7g',
    '1/4oz': '7g',
    'half': '14g',
    '1/2oz': '14g',
    'ounce': '28g',
    '1oz': '28g'
  };
  
  const normalized = variant.toLowerCase().replace(/\s/g, '');
  return variantMap[normalized] || normalized;
}

// Fuzzy matching
async function findCandidates(product: Product): Promise<CanonicalProduct[]> {
  // Query by brand and category (narrowing down)
  return await ctx.db
    .query('canonicalProducts')
    .withIndex('by_brand_category', q => 
      q.eq('brand', product.brand).eq('category', product.category)
    )
    .collect();
}

function calculateSimilarity(
  p1: Product,
  p2: CanonicalProduct
): number {
  // Levenshtein distance for name
  const nameSimilarity = 1 - (
    levenshtein(p1.name.toLowerCase(), p2.name.toLowerCase()) /
    Math.max(p1.name.length, p2.name.length)
  );
  
  // Exact match for brand/category/variant
  const brandMatch = p1.brand === p2.brand ? 1 : 0;
  const categoryMatch = p1.category === p2.category ? 1 : 0;
  const variantMatch = normalizeVariant(p1.variant) === normalizeVariant(p2.variant) ? 1 : 0;
  
  // Weighted average
  return (
    nameSimilarity * 0.4 +
    brandMatch * 0.3 +
    categoryMatch * 0.2 +
    variantMatch * 0.1
  );
}

// Simple Levenshtein implementation
function levenshtein(a: string, b: string): number {
  const matrix = [];
  
  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i];
  }
  
  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  
  return matrix[b.length][a.length];
}
```

### Linking Products to Canonical Entities

```typescript
// Link a store product to canonical product
async function linkProductToCanonical(
  productId: string,
  canonicalId: string
): Promise<void> {
  await ctx.db.insert('productLinks', {
    productId,
    canonicalId,
    linkedAt: Date.now()
  });
}

// Query all store products for a canonical product
export const getStoreProducts = query({
  args: { canonicalId: v.id('canonicalProducts') },
  handler: async (ctx, args) => {
    const links = await ctx.db
      .query('productLinks')
      .withIndex('by_canonical', q => q.eq('canonicalId', args.canonicalId))
      .collect();
    
    const products = await Promise.all(
      links.map(link => ctx.db.get(link.productId))
    );
    
    return products.filter(p => p !== null);
  }
});
```

---

## 3. Aggregation Patterns

### Store-Level Aggregation

```typescript
// Aggregate stats per store
interface StoreStats {
  storeId: string;
  totalProducts: number;
  inStockProducts: number;
  avgPrice: number;
  categories: Record<string, number>; // category -> product count
  lastUpdated: number;
}

export const getStoreStats = query({
  args: { storeId: v.id('stores') },
  handler: async (ctx, args) => {
    const products = await ctx.db
      .query('products')
      .withIndex('by_store', q => q.eq('storeId', args.storeId))
      .collect();
    
    const inStock = products.filter(p => p.inStock);
    
    const categoryCount = products.reduce((acc, p) => {
      acc[p.category] = (acc[p.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const avgPrice = products.reduce((sum, p) => sum + p.price, 0) / products.length;
    
    return {
      storeId: args.storeId,
      totalProducts: products.length,
      inStockProducts: inStock.length,
      avgPrice,
      categories: categoryCount,
      lastUpdated: Math.max(...products.map(p => p.lastScraped))
    };
  }
});
```

### Region-Level Aggregation

```typescript
// Aggregate across stores in a region (e.g., NYC)
interface RegionStats {
  region: string;
  totalStores: number;
  totalProducts: number;
  uniqueProducts: number; // Canonical products
  avgPriceByCategory: Record<string, number>;
  hotProducts: Array<{ name: string; velocity: number }>;
}

export const getRegionStats = query({
  args: { region: v.string() },
  handler: async (ctx, args) => {
    // Get all stores in region
    const stores = await ctx.db
      .query('stores')
      .withIndex('by_region', q => q.eq('region', args.region))
      .collect();
    
    // Get all products from these stores
    const allProducts = await Promise.all(
      stores.map(store => 
        ctx.db.query('products').withIndex('by_store', q => q.eq('storeId', store._id)).collect()
      )
    ).then(results => results.flat());
    
    // Calculate average prices by category
    const categoryPrices = allProducts.reduce((acc, p) => {
      if (!acc[p.category]) acc[p.category] = [];
      acc[p.category].push(p.price);
      return acc;
    }, {} as Record<string, number[]>);
    
    const avgPriceByCategory = Object.entries(categoryPrices).reduce((acc, [cat, prices]) => {
      acc[cat] = prices.reduce((sum, p) => sum + p, 0) / prices.length;
      return acc;
    }, {} as Record<string, number>);
    
    // Get unique canonical products
    const canonicalIds = new Set(
      allProducts.map(p => p.canonicalId).filter(Boolean)
    );
    
    return {
      region: args.region,
      totalStores: stores.length,
      totalProducts: allProducts.length,
      uniqueProducts: canonicalIds.size,
      avgPriceByCategory
    };
  }
});
```

### Time-Series Aggregation

```typescript
// Daily snapshot for trends
interface DailySnapshot {
  date: string; // YYYY-MM-DD
  totalProducts: number;
  inStockProducts: number;
  avgPrice: number;
  topSellingProducts: Array<{ canonicalId: string; unitsSold: number }>;
}

export const createDailySnapshot = internalMutation({
  handler: async (ctx) => {
    const products = await ctx.db.query('products').collect();
    
    const inStock = products.filter(p => p.inStock);
    const avgPrice = products.reduce((sum, p) => sum + p.price, 0) / products.length;
    
    // Calculate top selling (based on quantity changes)
    const topSelling = await getTopSellingProducts(ctx, 1); // last day
    
    const snapshot = {
      date: new Date().toISOString().split('T')[0],
      totalProducts: products.length,
      inStockProducts: inStock.length,
      avgPrice,
      topSellingProducts: topSelling
    };
    
    await ctx.db.insert('dailySnapshots', snapshot);
    
    // Archive to R2
    await archiveSnapshot(snapshot);
  }
});
```

---

## 4. Derived Metrics

### Velocity Scores

```typescript
interface VelocityMetric {
  productId: string;
  score: number; // 0-100
  trend: 'hot' | 'steady' | 'slow' | 'dead';
  unitsPerHour: number;
  restocksPerWeek: number;
  avgRestockQty: number;
  timeInStock: number; // percentage
}

export const calculateVelocityScore = query({
  args: { productId: v.id('products'), windowDays: v.number() },
  handler: async (ctx, args) => {
    const changes = await getProductChanges(ctx, args.productId, args.windowDays);
    
    // Quantity velocity
    const quantityChanges = changes.filter(c => c.field === 'quantity');
    const totalSold = quantityChanges.reduce((sum, c) => 
      Math.max(0, c.oldValue - c.newValue), 0
    );
    const unitsPerHour = totalSold / (args.windowDays * 24);
    
    // Restock frequency
    const restocks = changes.filter(c => 
      c.field === 'quantity' && c.newValue > c.oldValue
    );
    const restocksPerWeek = (restocks.length / args.windowDays) * 7;
    
    // Availability
    const stockChanges = changes.filter(c => c.field === 'inStock');
    const inStockTime = calculateUptime(stockChanges, args.windowDays);
    
    // Calculate score
    const velocityScore = Math.min(unitsPerHour * 10, 50);
    const restockScore = Math.min(restocksPerWeek * 5, 30);
    const availabilityScore = inStockTime * 20; // 0-100% -> 0-20 points
    
    const score = velocityScore + restockScore + availabilityScore;
    
    return {
      productId: args.productId,
      score,
      trend: getTrend(score),
      unitsPerHour,
      restocksPerWeek,
      avgRestockQty: restocks.reduce((sum, r) => sum + (r.newValue - r.oldValue), 0) / restocks.length || 0,
      timeInStock: inStockTime
    };
  }
});
```

### Price Comparison

```typescript
// Compare prices across stores for a canonical product
interface PriceComparison {
  canonicalId: string;
  minPrice: number;
  maxPrice: number;
  avgPrice: number;
  priceRange: number;
  bestDeal: { storeId: string; price: number; storeName: string };
  pricesByStore: Array<{ storeId: string; price: number; inStock: boolean }>;
}

export const getPriceComparison = query({
  args: { canonicalId: v.id('canonicalProducts') },
  handler: async (ctx, args) => {
    const storeProducts = await getStoreProducts(ctx, args.canonicalId);
    
    const prices = storeProducts.map(p => p.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const avgPrice = prices.reduce((sum, p) => sum + p, 0) / prices.length;
    
    const bestDeal = storeProducts.find(p => p.price === minPrice);
    
    return {
      canonicalId: args.canonicalId,
      minPrice,
      maxPrice,
      avgPrice,
      priceRange: maxPrice - minPrice,
      bestDeal: {
        storeId: bestDeal.storeId,
        price: bestDeal.price,
        storeName: (await ctx.db.get(bestDeal.storeId)).name
      },
      pricesByStore: storeProducts.map(p => ({
        storeId: p.storeId,
        price: p.price,
        inStock: p.inStock
      }))
    };
  }
});
```

### Availability Trends

```typescript
// Track how often a product is in stock over time
interface AvailabilityTrend {
  canonicalId: string;
  totalStores: number;
  inStockNow: number;
  avgAvailability7d: number; // % of stores with stock
  availabilityHistory: Array<{ date: string; availability: number }>;
}

export const getAvailabilityTrend = query({
  args: { canonicalId: v.id('canonicalProducts'), days: v.number() },
  handler: async (ctx, args) => {
    const storeProducts = await getStoreProducts(ctx, args.canonicalId);
    const totalStores = storeProducts.length;
    const inStockNow = storeProducts.filter(p => p.inStock).length;
    
    // Get historical data
    const cutoff = Date.now() - (args.days * 86400000);
    const changes = await ctx.db
      .query('productChanges')
      .withIndex('by_changed_at', q => q.gt('changedAt', cutoff))
      .filter(q => 
        q.and(
          storeProducts.map(p => 
            q.eq(q.field('productId'), p._id)
          )
        )
      )
      .filter(q => q.eq(q.field('field'), 'inStock'))
      .collect();
    
    // Group by date
    const dailyAvailability = groupByDate(changes, totalStores);
    
    return {
      canonicalId: args.canonicalId,
      totalStores,
      inStockNow,
      avgAvailability7d: (inStockNow / totalStores) * 100,
      availabilityHistory: dailyAvailability
    };
  }
});
```

---

## 5. LLM-Assisted Transformations

### Use Cases for LLM

1. **Product categorization** (flower, edibles, concentrates, etc.)
2. **Brand extraction** from messy product names
3. **Strain classification** (indica, sativa, hybrid)
4. **Description enhancement** (generate consistent descriptions)
5. **Duplicate detection** (fuzzy matching with semantic understanding)

### Implementation Strategy

**Principle:** LLMs are expensive and slow. Use them only when necessary.

```typescript
// When to use LLM
function shouldUseLLM(product: Product): boolean {
  return (
    !product.category || // Category missing
    !product.brand || // Brand missing
    product.name.length > 50 || // Complex name
    product.name.includes('|') || // Multiple items
    !product.name.match(/\d+g|\d+oz|eighth|quarter/) // No variant info
  );
}

// Batch processing to reduce API calls
async function enrichWithLLM(products: Product[]): Promise<Product[]> {
  const needEnrichment = products.filter(shouldUseLLM);
  
  if (needEnrichment.length === 0) {
    return products;
  }
  
  // Batch into groups of 10
  const batches = chunk(needEnrichment, 10);
  const enriched = [];
  
  for (const batch of batches) {
    const prompt = createBatchPrompt(batch);
    const response = await callLLM(prompt);
    const parsed = parseLLMResponse(response);
    
    enriched.push(...parsed);
    
    // Rate limit
    await sleep(1000);
  }
  
  // Merge enriched data back
  const enrichedMap = new Map(enriched.map(p => [p.externalId, p]));
  
  return products.map(p => 
    enrichedMap.get(p.externalId) || p
  );
}
```

### Prompt Engineering

```typescript
function createBatchPrompt(products: Product[]): string {
  return `
You are a cannabis product data normalization assistant. Extract structured data from the following product names.

For each product, provide:
1. Product name (cleaned)
2. Brand
3. Variant (e.g., "3.5g", "1g cart")
4. Category (flower, edibles, concentrates, vapes, prerolls, topicals, tinctures, other)
5. Subcategory (for flower: indica/sativa/hybrid; for edibles: gummy/chocolate/beverage/etc)

Products:
${products.map((p, i) => `${i + 1}. "${p.name}"`).join('\n')}

Response format (JSON array):
[
  {
    "index": 1,
    "name": "Blue Dream",
    "brand": "Alta",
    "variant": "3.5g",
    "category": "flower",
    "subcategory": "hybrid"
  },
  ...
]
`.trim();
}

async function callLLM(prompt: string): Promise<string> {
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini', // Cheaper, faster
      messages: [
        { role: 'system', content: 'You are a cannabis product data expert.' },
        { role: 'user', content: prompt }
      ],
      temperature: 0.1, // Low temperature for consistency
      max_tokens: 1000
    })
  });
  
  const data = await response.json();
  return data.choices[0].message.content;
}

function parseLLMResponse(response: string): Product[] {
  try {
    // Extract JSON from markdown code blocks if present
    const jsonMatch = response.match(/```json\n([\s\S]+)\n```/);
    const json = jsonMatch ? jsonMatch[1] : response;
    
    return JSON.parse(json);
  } catch (error) {
    console.error('Failed to parse LLM response:', error);
    return [];
  }
}
```

### Caching LLM Results

```typescript
// Cache LLM results to avoid re-processing
const llmCache = new Map<string, any>();

async function enrichWithLLMCached(product: Product): Promise<Product> {
  const cacheKey = `llm:${product.externalId}`;
  
  // Check cache
  const cached = llmCache.get(cacheKey);
  if (cached) {
    return { ...product, ...cached };
  }
  
  // Call LLM
  const enriched = await enrichWithLLM([product]);
  
  // Cache result
  llmCache.set(cacheKey, enriched[0]);
  
  return enriched[0];
}
```

### Cost Optimization

**LLM Costs (GPT-4o-mini):**
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

**Batch processing 10 products:**
- Input: ~500 tokens × $0.00000015 = $0.000075
- Output: ~300 tokens × $0.0000006 = $0.00018
- **Total: ~$0.00026 per batch of 10 = $0.000026 per product**

**For 100,000 products (one-time):**
- 100,000 × $0.000026 = **$2.60 total**
- Plus caching means we never re-process the same product

**Ongoing (new products only):**
- ~100 new products/day × $0.000026 = **$0.0026/day = $0.08/month**

---

## Phase 4 Complete ✅

**Deliverables:**
1. ✅ Data normalization (platform-specific → unified schema)
2. ✅ Entity resolution (matching products across stores via signatures + fuzzy matching)
3. ✅ Aggregation patterns (store-level, region-level, time-series)
4. ✅ Derived metrics (velocity scores, price comparisons, availability trends)
5. ✅ LLM-assisted transformations (categorization, brand extraction, ~$0.08/month)

**Key Insights:**
- Normalization is rule-based per platform (fast, deterministic)
- Entity resolution uses signature matching + Levenshtein distance (85% threshold)
- LLMs are only used for hard cases (~10% of products)
- Batch processing LLM calls reduces cost to ~$0.000026/product
- Caching ensures one-time cost per unique product

**Next Phase:** Mobile-First Delivery (pagination, lazy loading, real-time updates, API design, UI/UX patterns)

---
