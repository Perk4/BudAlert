# Phase 5: Mobile-First Delivery

**Date:** 2026-03-05  
**Focus:** Mobile-optimized data delivery, API design, real-time updates, UI/UX patterns

---

## Executive Summary

Mobile-first delivery for a data-heavy app (100K+ products) requires:
- **Efficient data loading:** Pagination, lazy loading, infinite scroll
- **Real-time updates:** Live inventory changes without refresh
- **Offline support:** Browsing cached data when network fails
- **Fast perceived performance:** Skeleton screens, optimistic updates
- **Smart filtering:** Search, category filters, price ranges

**Key Challenge:** Deliver smooth UX with massive dataset on mobile network.

---

## 1. Data Delivery Patterns

### Problem: Too Much Data

**Naive approach:** Load all 100K products → 100 MB+ → 30 seconds on 4G → crash mobile browser

**Solution:** Progressive loading with aggressive caching.

### Pattern 1: Cursor-Based Pagination

```typescript
// API design
export const getProducts = query({
  args: {
    cursor: v.optional(v.string()),
    limit: v.number(), // Default: 20
    category: v.optional(v.string()),
    storeId: v.optional(v.id('stores')),
    inStockOnly: v.optional(v.boolean())
  },
  handler: async (ctx, args) => {
    let query = ctx.db.query('products');
    
    // Apply filters
    if (args.storeId) {
      query = query.withIndex('by_store', q => q.eq('storeId', args.storeId));
    } else if (args.category) {
      query = query.withIndex('by_category', q => q.eq('category', args.category));
    }
    
    // Apply cursor
    if (args.cursor) {
      query = query.withIndex('by_id', q => q.gt('_id', args.cursor));
    }
    
    // Fetch
    const results = await query.take(args.limit + 1); // +1 to check if more exist
    
    const hasMore = results.length > args.limit;
    const products = hasMore ? results.slice(0, args.limit) : results;
    const nextCursor = hasMore ? products[products.length - 1]._id : null;
    
    // Filter in-memory if needed (Convex doesn't support complex filters)
    const filtered = args.inStockOnly 
      ? products.filter(p => p.inStock)
      : products;
    
    return {
      products: filtered,
      nextCursor,
      hasMore
    };
  }
});
```

**Client-side (React/React Native):**
```typescript
function ProductList() {
  const [products, setProducts] = useState([]);
  const [cursor, setCursor] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const loadMore = async () => {
    if (loading) return;
    
    setLoading(true);
    const result = await convex.query(api.products.getProducts, {
      cursor,
      limit: 20,
      inStockOnly: true
    });
    
    setProducts([...products, ...result.products]);
    setCursor(result.nextCursor);
    setLoading(false);
  };
  
  return (
    <FlatList
      data={products}
      renderItem={({ item }) => <ProductCard product={item} />}
      onEndReached={loadMore}
      onEndReachedThreshold={0.5}
      ListFooterComponent={loading ? <Spinner /> : null}
    />
  );
}
```

### Pattern 2: Virtual Scrolling (Web)

**For web app:** Use react-window or react-virtualized to render only visible items.

```typescript
import { FixedSizeList as List } from 'react-window';

function ProductVirtualList({ products }) {
  const Row = ({ index, style }) => (
    <div style={style}>
      <ProductCard product={products[index]} />
    </div>
  );
  
  return (
    <List
      height={800}
      itemCount={products.length}
      itemSize={120}
      width="100%"
    >
      {Row}
    </List>
  );
}
```

### Pattern 3: Lazy Loading Images

```typescript
function ProductCard({ product }) {
  return (
    <View>
      <Image
        source={{ uri: product.imageUrl }}
        placeholder={PLACEHOLDER_IMAGE}
        loading="lazy" // Native lazy loading
        onError={(e) => e.target.src = FALLBACK_IMAGE}
      />
      <Text>{product.name}</Text>
      <Text>${product.price}</Text>
    </View>
  );
}
```

### Pattern 4: Data Prefetching

**Predict what user will view next:**
```typescript
function useProductPrefetch() {
  const [visibleProducts, setVisibleProducts] = useState([]);
  
  useEffect(() => {
    // Prefetch next page when user reaches 80% of current list
    const prefetchIndex = Math.floor(visibleProducts.length * 0.8);
    const prefetchProduct = visibleProducts[prefetchIndex];
    
    if (prefetchProduct) {
      // Prefetch product details
      convex.query(api.products.getDetails, { 
        productId: prefetchProduct._id 
      });
    }
  }, [visibleProducts]);
}
```

---

## 2. API Design

### GraphQL vs REST vs Convex Subscriptions

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **REST** | Simple, cacheable, standard | Overfetching, no real-time | ❌ Skip |
| **GraphQL** | Flexible queries, no overfetching | Complex setup, caching harder | ⚠️ Overkill |
| **Convex Reactive** | Real-time by default, TypeScript, simple | Vendor lock-in | ✅ **Use this** |

**Recommendation:** Use Convex reactive queries for real-time updates out of the box.

### Convex Query Design

**Product Listing:**
```typescript
// Efficient listing with minimal data
export const listProducts = query({
  args: {
    storeId: v.optional(v.id('stores')),
    category: v.optional(v.string()),
    cursor: v.optional(v.string()),
    limit: v.number()
  },
  handler: async (ctx, args) => {
    // Return only fields needed for list view
    const products = await queryProducts(ctx, args);
    
    return products.map(p => ({
      id: p._id,
      name: p.name,
      brand: p.brand,
      price: p.price,
      imageUrl: p.imageUrl,
      inStock: p.inStock,
      velocity: p.velocityScore // Pre-calculated
    }));
  }
});

// Product details (full data)
export const getProductDetails = query({
  args: { productId: v.id('products') },
  handler: async (ctx, args) => {
    const product = await ctx.db.get(args.productId);
    
    // Fetch related data
    const store = await ctx.db.get(product.storeId);
    const canonical = product.canonicalId 
      ? await ctx.db.get(product.canonicalId)
      : null;
    
    // Get price comparison
    const priceComparison = canonical
      ? await getPriceComparison(ctx, canonical._id)
      : null;
    
    // Get velocity metrics
    const velocity = await calculateVelocityScore(ctx, args.productId, 7);
    
    return {
      ...product,
      store,
      canonical,
      priceComparison,
      velocity
    };
  }
});
```

### Search & Filtering

**Challenge:** Convex doesn't have full-text search built-in.

**Solutions:**

**Option 1: Convex + Algolia (Hybrid)**
```typescript
// Algolia for search, Convex for data
async function searchProducts(query: string): Promise<Product[]> {
  // Search in Algolia
  const algoliaResults = await algolia.search(query);
  const productIds = algoliaResults.hits.map(hit => hit.objectID);
  
  // Fetch full data from Convex
  const products = await Promise.all(
    productIds.map(id => convex.query(api.products.get, { id }))
  );
  
  return products;
}
```

**Option 2: Client-Side Filtering (Small Datasets)**
```typescript
// For filtering visible products (already loaded)
function useProductFilter(products: Product[], filters: Filters) {
  return useMemo(() => {
    return products.filter(p => {
      if (filters.category && p.category !== filters.category) return false;
      if (filters.minPrice && p.price < filters.minPrice) return false;
      if (filters.maxPrice && p.price > filters.maxPrice) return false;
      if (filters.inStockOnly && !p.inStock) return false;
      if (filters.search && !p.name.toLowerCase().includes(filters.search.toLowerCase())) return false;
      return true;
    });
  }, [products, filters]);
}
```

**Option 3: Convex Indexes (Limited)**
```typescript
// Pre-filter with indexes, then filter in memory
export const searchProducts = query({
  args: {
    category: v.string(),
    minPrice: v.number(),
    maxPrice: v.number()
  },
  handler: async (ctx, args) => {
    // Use category index to narrow down
    const products = await ctx.db
      .query('products')
      .withIndex('by_category', q => q.eq('category', args.category))
      .collect();
    
    // Filter price in memory
    return products.filter(p => 
      p.price >= args.minPrice && p.price <= args.maxPrice
    );
  }
});
```

---

## 3. Real-Time Updates

### Convex Reactive Queries

**Built-in reactivity:**
```typescript
// React component automatically re-renders when data changes
function ProductList() {
  // This query subscribes to changes
  const products = useQuery(api.products.listProducts, {
    storeId: currentStore,
    inStockOnly: true,
    limit: 20
  });
  
  // When a product changes in the database, this component re-renders
  return (
    <FlatList data={products} renderItem={...} />
  );
}
```

**Behind the scenes:**
1. Client subscribes to query
2. Convex server watches query dependencies
3. When data changes, server pushes update to client
4. React re-renders automatically

### Push Notifications

**Use cases:**
- New product added to favorite store
- Price drop on watched product
- Product back in stock

**Implementation:**

**Server-side (Convex):**
```typescript
// Trigger on product change
export const onProductChange = internalMutation({
  args: { productId: v.id('products'), changeType: v.string() },
  handler: async (ctx, args) => {
    const product = await ctx.db.get(args.productId);
    
    // Find users watching this product
    const watchers = await ctx.db
      .query('watchlist')
      .withIndex('by_product', q => q.eq('productId', args.productId))
      .collect();
    
    // Send push notifications
    for (const watcher of watchers) {
      await sendPushNotification({
        userId: watcher.userId,
        title: getNotificationTitle(args.changeType, product),
        body: getNotificationBody(args.changeType, product),
        data: { productId: args.productId }
      });
    }
  }
});

function getNotificationTitle(changeType: string, product: Product): string {
  switch (changeType) {
    case 'restock': return `${product.name} back in stock!`;
    case 'price_drop': return `Price drop on ${product.name}`;
    case 'new_product': return `New product at ${product.storeName}`;
    default: return 'Product update';
  }
}
```

**Client-side (React Native + Expo):**
```typescript
import * as Notifications from 'expo-notifications';

// Register for push notifications
async function registerForPushNotifications() {
  const { status } = await Notifications.requestPermissionsAsync();
  
  if (status !== 'granted') {
    return null;
  }
  
  const token = await Notifications.getExpoPushTokenAsync();
  
  // Save token to Convex
  await convex.mutation(api.users.savePushToken, {
    token: token.data
  });
  
  return token;
}

// Handle notification tap
Notifications.addNotificationResponseReceivedListener(response => {
  const { productId } = response.notification.request.content.data;
  
  // Navigate to product details
  navigation.navigate('ProductDetails', { productId });
});
```

### WebSocket Alternative (for non-Convex setups)

```typescript
// Server (Express + WebSocket)
import { WebSocketServer } from 'ws';

const wss = new WebSocketServer({ port: 8080 });

wss.on('connection', (ws) => {
  ws.on('message', (message) => {
    const { action, productId } = JSON.parse(message);
    
    if (action === 'watch') {
      // Subscribe client to product updates
      subscribeToProduct(ws, productId);
    }
  });
});

function notifyClients(productId: string, update: any) {
  wss.clients.forEach(client => {
    if (client.watchedProducts?.includes(productId)) {
      client.send(JSON.stringify(update));
    }
  });
}
```

---

## 4. Offline Support

### Service Worker (Web)

```typescript
// service-worker.ts
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }
      
      return fetch(event.request).then(response => {
        // Cache successful responses
        if (response.ok) {
          const cache = await caches.open('budalert-v1');
          cache.put(event.request, response.clone());
        }
        return response;
      });
    })
  );
});
```

### AsyncStorage (React Native)

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// Cache products for offline viewing
async function cacheProducts(products: Product[]) {
  await AsyncStorage.setItem('cached_products', JSON.stringify(products));
}

// Load cached products when offline
async function loadCachedProducts(): Promise<Product[]> {
  const cached = await AsyncStorage.getItem('cached_products');
  return cached ? JSON.parse(cached) : [];
}

// Component with offline support
function ProductList() {
  const [products, setProducts] = useState([]);
  const [isOnline, setIsOnline] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    async function loadProducts() {
      try {
        // Try to fetch from network
        const freshProducts = await convex.query(api.products.listProducts, {...});
        setProducts(freshProducts);
        setIsOnline(true);
        
        // Cache for offline use
        await cacheProducts(freshProducts);
      } catch (error) {
        // Network failed, load cached data
        const cachedProducts = await loadCachedProducts();
        setProducts(cachedProducts);
        setIsOnline(false);
      } finally {
        setIsLoading(false);
      }
    }
    
    loadProducts();
  }, []);
  
  return (
    <View>
      {!isOnline && <Banner>Viewing cached data (offline)</Banner>}
      <FlatList data={products} renderItem={...} />
    </View>
  );
}
```

### Background Sync

```typescript
// Pre-fetch for offline use
async function prefetchForOffline(storeIds: string[]) {
  for (const storeId of storeIds) {
    const products = await convex.query(api.products.listProducts, {
      storeId,
      limit: 100
    });
    
    // Cache products and images
    await cacheProducts(storeId, products);
    await cacheImages(products.map(p => p.imageUrl));
  }
}
```

---

## 5. UI/UX Patterns

### Pattern 1: Infinite Scroll

```typescript
function InfiniteScrollList() {
  const [products, setProducts] = useState([]);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  
  const loadMore = async () => {
    const newProducts = await convex.query(api.products.listProducts, {
      cursor: products[products.length - 1]?._id,
      limit: 20
    });
    
    setProducts([...products, ...newProducts.products]);
    setHasMore(newProducts.hasMore);
  };
  
  return (
    <FlatList
      data={products}
      renderItem={({ item }) => <ProductCard product={item} />}
      onEndReached={loadMore}
      onEndReachedThreshold={0.5}
      ListFooterComponent={hasMore ? <Spinner /> : <Text>End of list</Text>}
    />
  );
}
```

### Pattern 2: Skeleton Screens

```typescript
function ProductListSkeleton() {
  return (
    <View>
      {[...Array(5)].map((_, i) => (
        <View key={i} style={styles.skeletonCard}>
          <SkeletonPlaceholder>
            <View style={{ flexDirection: 'row' }}>
              <View style={{ width: 80, height: 80, borderRadius: 8 }} />
              <View style={{ marginLeft: 12 }}>
                <View style={{ width: 200, height: 20, marginBottom: 8 }} />
                <View style={{ width: 100, height: 16 }} />
              </View>
            </View>
          </SkeletonPlaceholder>
        </View>
      ))}
    </View>
  );
}

function ProductList() {
  const products = useQuery(api.products.listProducts, {...});
  
  if (products === undefined) {
    return <ProductListSkeleton />;
  }
  
  return <FlatList data={products} renderItem={...} />;
}
```

### Pattern 3: Optimistic Updates

```typescript
function ProductCard({ product }) {
  const [isInWatchlist, setIsInWatchlist] = useState(product.isInWatchlist);
  
  const toggleWatchlist = async () => {
    // Optimistic update
    setIsInWatchlist(!isInWatchlist);
    
    try {
      await convex.mutation(api.watchlist.toggle, {
        productId: product._id
      });
    } catch (error) {
      // Revert on error
      setIsInWatchlist(isInWatchlist);
      alert('Failed to update watchlist');
    }
  };
  
  return (
    <TouchableOpacity onPress={toggleWatchlist}>
      <Icon name={isInWatchlist ? 'heart-filled' : 'heart-outline'} />
    </TouchableOpacity>
  );
}
```

### Pattern 4: Smart Search

```typescript
function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  
  // Debounce search
  useEffect(() => {
    const timeoutId = setTimeout(async () => {
      if (query.length > 2) {
        setIsSearching(true);
        const searchResults = await convex.query(api.products.search, { query });
        setResults(searchResults);
        setIsSearching(false);
      } else {
        setResults([]);
      }
    }, 300); // Wait 300ms after user stops typing
    
    return () => clearTimeout(timeoutId);
  }, [query]);
  
  return (
    <View>
      <TextInput
        value={query}
        onChangeText={setQuery}
        placeholder="Search products..."
      />
      {isSearching && <Spinner />}
      {results.length > 0 && (
        <FlatList data={results} renderItem={...} />
      )}
    </View>
  );
}
```

### Pattern 5: Pull-to-Refresh

```typescript
function ProductList() {
  const [refreshing, setRefreshing] = useState(false);
  const products = useQuery(api.products.listProducts, {...});
  
  const onRefresh = async () => {
    setRefreshing(true);
    
    // Convex will automatically refetch
    // Just need to wait a moment for UI feedback
    await new Promise(resolve => setTimeout(resolve, 500));
    
    setRefreshing(false);
  };
  
  return (
    <FlatList
      data={products}
      renderItem={({ item }) => <ProductCard product={item} />}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    />
  );
}
```

### Pattern 6: Filters & Sorting

```typescript
function ProductFilters({ onFilterChange }) {
  const [category, setCategory] = useState('all');
  const [sortBy, setSortBy] = useState('name');
  const [inStockOnly, setInStockOnly] = useState(false);
  
  useEffect(() => {
    onFilterChange({ category, sortBy, inStockOnly });
  }, [category, sortBy, inStockOnly]);
  
  return (
    <View style={styles.filtersContainer}>
      <Picker
        selectedValue={category}
        onValueChange={setCategory}
      >
        <Picker.Item label="All Categories" value="all" />
        <Picker.Item label="Flower" value="flower" />
        <Picker.Item label="Edibles" value="edibles" />
        <Picker.Item label="Concentrates" value="concentrates" />
      </Picker>
      
      <Picker
        selectedValue={sortBy}
        onValueChange={setSortBy}
      >
        <Picker.Item label="Name" value="name" />
        <Picker.Item label="Price (Low to High)" value="price_asc" />
        <Picker.Item label="Price (High to Low)" value="price_desc" />
        <Picker.Item label="Velocity" value="velocity" />
      </Picker>
      
      <Switch
        value={inStockOnly}
        onValueChange={setInStockOnly}
      />
      <Text>In Stock Only</Text>
    </View>
  );
}
```

---

## Performance Optimization

### Bundle Size Optimization

```typescript
// Lazy load heavy components
const ProductDetails = lazy(() => import('./ProductDetails'));
const PriceChart = lazy(() => import('./PriceChart'));

function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <ProductDetails />
    </Suspense>
  );
}
```

### Image Optimization

```typescript
// Use CDN with auto-resizing
function getOptimizedImageUrl(url: string, width: number): string {
  // Cloudflare Images, Imgix, or similar
  return `https://cdn.budalert.com/images?url=${url}&w=${width}&format=webp`;
}

function ProductImage({ product, size = 'thumbnail' }) {
  const sizes = {
    thumbnail: 80,
    small: 200,
    medium: 400,
    large: 800
  };
  
  const imageUrl = getOptimizedImageUrl(product.imageUrl, sizes[size]);
  
  return <Image source={{ uri: imageUrl }} style={{ width: sizes[size] }} />;
}
```

### Network Request Batching

```typescript
// Batch multiple product detail requests
async function getMultipleProducts(productIds: string[]): Promise<Product[]> {
  // Instead of N requests, make 1
  return await convex.query(api.products.getBatch, { productIds });
}

// Convex query
export const getBatch = query({
  args: { productIds: v.array(v.id('products')) },
  handler: async (ctx, args) => {
    return await Promise.all(
      args.productIds.map(id => ctx.db.get(id))
    );
  }
});
```

---

## Phase 5 Complete ✅

**Deliverables:**
1. ✅ Data delivery patterns (cursor pagination, virtual scrolling, lazy loading, prefetching)
2. ✅ API design (Convex reactive queries for real-time updates)
3. ✅ Real-time updates (WebSocket-like via Convex subscriptions, push notifications)
4. ✅ Offline support (service workers, AsyncStorage, background sync)
5. ✅ UI/UX patterns (infinite scroll, skeleton screens, optimistic updates, smart search)
6. ✅ Performance optimizations (lazy loading, image CDN, request batching)

**Key Insights:**
- **Convex reactive queries** handle real-time updates automatically (no WebSocket needed)
- **Cursor-based pagination** for efficient large dataset browsing
- **Offline-first** with AsyncStorage caching for React Native
- **Skeleton screens** for perceived performance
- **Push notifications** for engagement (restock alerts, price drops)
- **Image CDN** (Cloudflare Images) for auto-resizing and WebP conversion

**Next Phase:** Cost Optimization (scraping infrastructure, storage, compute, delivery costs, recommendations)

---
