# Examples & Use Cases

## Basic Examples

### 1. Research a Single Dispensary

```typescript
import { TestOrchestrator } from './orchestrator/runner';
import { Id } from './convex/_generated/dataModel';

const orchestrator = new TestOrchestrator(process.env.CONVEX_URL!);
const dispensaryId = 'your-dispensary-id' as Id<'dispensaries'>;

const result = await orchestrator.runResearchLoop(dispensaryId);

console.log(result);
// {
//   success: true,
//   method: 'dutchie-graphql',
//   triedMethods: 1,
//   productsFound: 234,
//   fieldCompleteness: { overall: 95, ... }
// }
```

### 2. Detect Provider for a Website

```typescript
import { ProviderDetector } from './clustering/detector';

const detector = new ProviderDetector();
const result = await detector.detect('https://conbud.com');

console.log(result);
// {
//   provider: 'dutchie',
//   confidence: 90,
//   evidence: ['api.dutchie.com', 'dutchie-', '__NEXT_DATA__'],
//   menuUrl: 'https://conbud.com/embedded-menu/...'
// }
```

### 3. Test a Method Directly

```typescript
import { DutchieGraphQLMethod } from './methods/dutchie/graphql';

const method = new DutchieGraphQLMethod();
const result = await method.scrape({
  dispensaryId: 'test',
  url: 'https://conbud.com',
  timeout: 30000,
});

console.log(`Found ${result.products.length} products`);
console.log(`Overall completeness: ${result.fieldCompleteness.overall}%`);
```

### 4. Detect Inventory

```typescript
import { chromium } from 'playwright';
import { InventoryDetector } from './inventory/detector';

const browser = await chromium.launch();
const page = await browser.newPage();

const detector = new InventoryDetector();
const result = await detector.detect(page, 'https://example.com/product/123');

console.log(result);
// {
//   method: 'api',
//   confidence: 95,
//   inventoryData: Map { 'product-123' => 42, ... }
// }

await browser.close();
```

### 5. Extract Learnings

```typescript
import { LearningExtractor } from './analysis/learnings';

const extractor = new LearningExtractor(process.env.CONVEX_URL!);

const learning = extractor.extractFromFailure(
  'dutchie',
  'cloudflare',
  'Cloudflare challenge failed',
  { type: 'cloudflare', confidence: 95 }
);

if (learning) {
  console.log(learning.title);
  // "Cloudflare protection active"
  
  console.log(learning.solution);
  // "Use browser-based methods with proper wait times"
}
```

## Advanced Examples

### Batch Process with Custom Logic

```typescript
import { BatchOrchestrator } from './orchestrator/batch';

const batch = new BatchOrchestrator(process.env.CONVEX_URL!, {
  concurrency: 3,
  delayBetweenBatches: 10000,
});

// Custom filter
const highPriorityOnly = true;

if (highPriorityOnly) {
  // Process high-priority NYC dispensaries first
  await batch.processCluster('dutchie', 10);
  await batch.processCluster('blaze', 10);
}

// Then process all
await batch.processAll();
```

### Custom Method Implementation

```typescript
import {
  ScrapingMethod,
  ScrapeConfig,
  ScrapeResult,
  calculateFieldCompleteness,
} from './methods/base';

export class CustomAPIMethod implements ScrapingMethod {
  name = 'custom-api-v1';
  provider = 'custom-provider';
  type = 'api' as const;
  
  requirements = {
    chromium: false,
    cookies: true,
  };
  
  async scrape(config: ScrapeConfig): Promise<ScrapeResult> {
    const startTime = Date.now();
    
    try {
      // Your custom logic
      const response = await fetch(`${config.url}/api/products`);
      const data = await response.json();
      
      const products = data.items.map(item => ({
        id: item.id,
        name: item.name,
        price: item.price,
        // ... other fields
      }));
      
      return {
        success: true,
        products,
        fieldCompleteness: calculateFieldCompleteness(products),
        metadata: {
          scrapeTimeMs: Date.now() - startTime,
          pagesVisited: 1,
          requestsMade: 1,
          method: this.name,
        },
      };
    } catch (error) {
      return {
        success: false,
        products: [],
        fieldCompleteness: calculateFieldCompleteness([]),
        metadata: {
          scrapeTimeMs: Date.now() - startTime,
          pagesVisited: 0,
          requestsMade: 1,
          method: this.name,
        },
        errors: [error.message],
      };
    }
  }
}
```

### Custom Learning Rules

```typescript
import { LearningExtractor } from './analysis/learnings';

class CustomLearningExtractor extends LearningExtractor {
  extractFromFailure(provider, errorType, errorMessage, diagnosis) {
    // Call parent
    const baseLearning = super.extractFromFailure(
      provider,
      errorType,
      errorMessage,
      diagnosis
    );
    
    if (baseLearning) return baseLearning;
    
    // Custom rules
    if (errorMessage.includes('403 Forbidden')) {
      return {
        type: 'blocker',
        title: 'IP blocked',
        description: `${provider} has blocked this IP`,
        solution: 'Use proxy or residential IP',
      };
    }
    
    if (errorMessage.includes('CAPTCHA')) {
      return {
        type: 'blocker',
        title: 'CAPTCHA required',
        description: `${provider} requires CAPTCHA solving`,
        solution: 'Implement CAPTCHA solver or manual mode',
      };
    }
    
    return null;
  }
}
```

## Production Patterns

### Monitoring Dashboard

```typescript
import { ConvexHttpClient } from 'convex/browser';
import { api } from './convex/_generated/api';

async function getMonitoringData(convexUrl: string) {
  const client = new ConvexHttpClient(convexUrl);
  
  const stats = await client.query(api.dispensaries.getStats);
  const methodStats = await client.query(api.methods.getStats);
  const recentFailures = await client.query(api.testRuns.getRecentFailures, {
    limit: 10,
  });
  
  return {
    coverage: (stats.solved / stats.total) * 100,
    pending: stats.pending,
    blocked: stats.blocked,
    topMethods: methodStats
      .sort((a, b) => parseFloat(b.successRate) - parseFloat(a.successRate))
      .slice(0, 5),
    recentIssues: recentFailures,
  };
}
```

### Auto-Retry on New Methods

```typescript
import { BatchOrchestrator } from './orchestrator/batch';
import { registerMethod } from './methods/registry';

async function addMethodAndRetry(newMethod, convexUrl) {
  // Register the new method
  registerMethod(newMethod.provider, newMethod);
  
  // Persist to database
  const client = new ConvexHttpClient(convexUrl);
  await client.mutation(api.methods.register, {
    name: newMethod.name,
    provider: newMethod.provider,
    type: newMethod.type,
    // ... other fields
  });
  
  // Retry blocked stores for this provider
  const batch = new BatchOrchestrator(convexUrl);
  await batch.retryBlocked(newMethod.provider);
}
```

### Scheduled Research

```bash
# Run research every 6 hours (crontab)
0 */6 * * * cd /path/to/scraping-engine && npm run research:all >> research.log 2>&1

# Daily status report
0 9 * * * cd /path/to/scraping-engine && npm run status | mail -s "Daily Scraping Status" admin@example.com
```

## Debugging Patterns

### Verbose Method Testing

```typescript
import { DutchieGraphQLMethod } from './methods/dutchie/graphql';

async function debugMethod() {
  const method = new DutchieGraphQLMethod();
  
  console.log('Testing method:', method.name);
  console.log('Requirements:', method.requirements);
  
  const startTime = Date.now();
  const result = await method.scrape({
    dispensaryId: 'test',
    url: 'https://conbud.com',
    timeout: 30000,
  });
  
  console.log('Success:', result.success);
  console.log('Products:', result.products.length);
  console.log('Time:', Date.now() - startTime, 'ms');
  console.log('Completeness:', result.fieldCompleteness);
  
  if (!result.success) {
    console.log('Errors:', result.errors);
  }
  
  // Save sample products
  console.log('Sample products:');
  console.log(JSON.stringify(result.products.slice(0, 3), null, 2));
}
```

### Check Method Coverage

```typescript
async function checkCoverage(convexUrl: string) {
  const client = new ConvexHttpClient(convexUrl);
  const stats = await client.query(api.dispensaries.getStats);
  
  console.log('Coverage by Provider:');
  
  for (const [provider, total] of Object.entries(stats.byProvider)) {
    const solved = await client.query(api.dispensaries.getByProviderStatus, {
      provider,
      status: 'solved',
    });
    
    const coverage = (solved.length / total) * 100;
    console.log(`  ${provider}: ${coverage.toFixed(1)}% (${solved.length}/${total})`);
  }
}
```

## Integration Examples

### Export to JSON

```typescript
import { ConvexHttpClient } from 'convex/browser';
import { writeFileSync } from 'fs';

async function exportResults(convexUrl: string, outputFile: string) {
  const client = new ConvexHttpClient(convexUrl);
  
  const solved = await client.query(api.dispensaries.list, {
    status: 'solved',
  });
  
  const results = await Promise.all(
    solved.map(async (disp) => {
      const testRuns = await client.query(api.testRuns.getByDispensary, {
        dispensaryId: disp._id,
      });
      
      const successfulRun = testRuns.find(r => r.status === 'success');
      
      return {
        dispensary: disp.name,
        provider: disp.provider,
        method: successfulRun?.metadata?.method,
        productsFound: successfulRun?.productsFound,
        completeness: successfulRun?.fieldCompleteness.overall,
      };
    })
  );
  
  writeFileSync(outputFile, JSON.stringify(results, null, 2));
  console.log(`Exported ${results.length} results to ${outputFile}`);
}
```

### Webhook Notifications

```typescript
async function notifyOnCompletion(dispensaryId, result) {
  if (result.success) {
    await fetch('https://your-webhook.com/scrape-complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dispensaryId,
        method: result.method,
        productsFound: result.productsFound,
        timestamp: new Date().toISOString(),
      }),
    });
  }
}
```
