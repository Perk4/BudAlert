# Continuous Scraping Research Engine

## System Overview

A self-improving system that progressively discovers working scraping methods for 500+ NY dispensaries, clusters them by provider, and builds a knowledge base of what works.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SCRAPING RESEARCH ENGINE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  DISPENSARY  │───▶│   PROVIDER   │───▶│   METHOD     │          │
│  │   REGISTRY   │    │   CLUSTER    │    │   LIBRARY    │          │
│  │   (598 NYS)  │    │   ENGINE     │    │  (Pluggable) │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│         │                   │                   │                   │
│         ▼                   ▼                   ▼                   │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │                    TEST ORCHESTRATOR                     │       │
│  │  • Progressive loop spawner                              │       │
│  │  • Parallel test execution                               │       │
│  │  • LLM-assisted failure analysis                         │       │
│  └─────────────────────────────────────────────────────────┘       │
│         │                   │                   │                   │
│         ▼                   ▼                   ▼                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   RESULTS    │    │  KNOWLEDGE   │    │   PROGRESS   │          │
│  │   TRACKER    │◀──▶│    BASE      │◀──▶│   ENGINE     │          │
│  │ (Success/Fail)│    │  (Learnings) │    │ (Next store) │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. Dispensary Registry

### Schema (Convex)

```typescript
// dispensaries table
{
  _id: Id<"dispensaries">,
  
  // Basic info (from NYS data)
  name: string,
  address: string,
  city: string,
  website: string,
  
  // Provider classification
  provider: "dutchie" | "jane" | "blaze" | "weedmaps" | "wordpress" | "custom" | "unknown",
  providerConfidence: number,  // 0-100%
  providerDetectedAt: number,
  
  // Research status
  status: "pending" | "researching" | "solved" | "blocked" | "manual",
  priority: number,  // Higher = research first
  
  // Working method (once found)
  workingMethodId: Id<"methods"> | null,
  workingMethodConfidence: number,
  lastSuccessfulScrape: number,
  
  // Metadata
  menuUrl: string | null,
  hasAgeGate: boolean,
  hasCloudflare: boolean,
  requiresBrowser: boolean,
  
  // Inventory detection
  inventoryMethod: "cart_probe" | "api" | "dropdown" | "badge" | "none" | null,
  inventoryConfidence: number,
}

// methods table (pluggable)
{
  _id: Id<"methods">,
  name: string,
  provider: string,  // Which provider this works for
  type: "http" | "browser" | "api" | "hybrid",
  
  // Implementation
  scriptPath: string,  // Path to scraper script
  configSchema: object,  // Expected config shape
  
  // Stats
  successCount: number,
  failCount: number,
  avgLatency: number,
  
  // Compatibility
  requiresChromium: boolean,
  requiresProxy: boolean,
  bypassesCloudflare: boolean,
}

// testRuns table
{
  _id: Id<"testRuns">,
  dispensaryId: Id<"dispensaries">,
  methodId: Id<"methods">,
  
  // Execution
  startedAt: number,
  completedAt: number,
  status: "running" | "success" | "partial" | "failed" | "timeout",
  
  // Results
  productsFound: number,
  fieldsExtracted: string[],  // ["name", "price", "thc", ...]
  fieldCompleteness: object,  // { name: 100, price: 85, thc: 60 }
  inventoryDetected: boolean,
  
  // Failure analysis
  errorType: string | null,
  errorMessage: string | null,
  llmAnalysis: string | null,  // LLM interpretation of failure
  suggestedFix: string | null,
  
  // Artifacts
  sampleOutput: object,  // First 5 products
  screenshotUrl: string | null,
  htmlSnapshotUrl: string | null,
}

// learnings table (knowledge base)
{
  _id: Id<"learnings">,
  provider: string,
  type: "gotcha" | "patch" | "pattern" | "blocker",
  
  title: string,
  description: string,
  
  // Applicability
  affectsDispensaries: Id<"dispensaries">[],
  affectsMethods: Id<"methods">[],
  
  // Solution (if any)
  solution: string | null,
  solutionCode: string | null,
  
  // Confidence
  confirmedBy: number,  // How many stores confirmed this
  createdAt: number,
  updatedAt: number,
}
```

---

## 2. Provider Clustering Engine

### Auto-Detection Flow

```typescript
async function detectProvider(dispensary: Dispensary): Promise<ProviderResult> {
  const signals = {
    // HTML signatures
    dutchie: ["api.dutchie.com", "dutchie-", "__NEXT_DATA__"],
    jane: ["iheartjane.com", "jane-embed", "jane-menu"],
    blaze: ["blaze.me", "blaze-retail", "blazeInsights"],
    weedmaps: ["weedmaps.com", "wmcdn.com"],
    wordpress: ["wp-content", "wp-json", "woocommerce"],
    shopify: ["cdn.shopify.com", "Shopify.theme"],
  };
  
  // Step 1: Fetch homepage
  const html = await fetch(dispensary.website).then(r => r.text());
  
  // Step 2: Check signatures
  for (const [provider, patterns] of Object.entries(signals)) {
    const matches = patterns.filter(p => html.includes(p));
    if (matches.length > 0) {
      return {
        provider,
        confidence: (matches.length / patterns.length) * 100,
        evidence: matches,
      };
    }
  }
  
  // Step 3: Check menu URL patterns
  const menuUrl = await discoverMenuUrl(dispensary);
  if (menuUrl?.includes("dutchie.com")) return { provider: "dutchie", confidence: 95 };
  if (menuUrl?.includes("iheartjane.com")) return { provider: "jane", confidence: 95 };
  
  // Step 4: LLM classification (fallback)
  const llmResult = await classifyWithLLM(html, dispensary.name);
  
  return {
    provider: llmResult.provider || "unknown",
    confidence: llmResult.confidence || 50,
    evidence: llmResult.reasoning,
  };
}
```

### Clustering Algorithm

```typescript
async function clusterDispensaries() {
  const dispensaries = await db.query("dispensaries").collect();
  
  const clusters: Map<string, Dispensary[]> = new Map();
  
  for (const d of dispensaries) {
    // Skip already solved
    if (d.status === "solved") continue;
    
    // Detect provider if unknown
    if (d.provider === "unknown" || !d.provider) {
      const result = await detectProvider(d);
      await db.patch(d._id, {
        provider: result.provider,
        providerConfidence: result.confidence,
        providerDetectedAt: Date.now(),
      });
      d.provider = result.provider;
    }
    
    // Add to cluster
    if (!clusters.has(d.provider)) {
      clusters.set(d.provider, []);
    }
    clusters.get(d.provider)!.push(d);
  }
  
  return clusters;
}
```

---

## 3. Method Library (Pluggable)

### Method Interface

```typescript
// methods/base.ts
export interface ScrapingMethod {
  name: string;
  provider: string;
  type: "http" | "browser" | "api" | "hybrid";
  
  // Requirements
  requirements: {
    chromium?: boolean;
    proxy?: boolean;
    cookies?: boolean;
    javascript?: boolean;
  };
  
  // Execution
  scrape(config: ScrapeConfig): Promise<ScrapeResult>;
  
  // Inventory detection
  detectInventory?(config: ScrapeConfig): Promise<InventoryResult>;
  
  // Self-diagnosis
  diagnose?(error: Error, html?: string): Promise<Diagnosis>;
}

export interface ScrapeConfig {
  dispensaryId: string;
  url: string;
  menuUrl?: string;
  timeout?: number;
  retries?: number;
  proxy?: string;
}

export interface ScrapeResult {
  success: boolean;
  products: Product[];
  fieldCompleteness: Record<string, number>;
  metadata: {
    scrapeTimeMs: number;
    pagesVisited: number;
    requestsMade: number;
  };
  errors?: string[];
}
```

### Method Registry

```typescript
// methods/registry.ts
const methodRegistry: Map<string, ScrapingMethod[]> = new Map();

// Register methods per provider
methodRegistry.set("dutchie", [
  new DutchieGraphQLMethod(),
  new DutchieBrowserInterceptMethod(),
  new DutchiePublicAPIMethod(),
]);

methodRegistry.set("blaze", [
  new BlazeAPIMethod(),
  new BlazeBrowserMethod(),
  new BlazeHybridMethod(),
]);

methodRegistry.set("wordpress", [
  new WordPressRESTMethod(),
  new WordPressJSONLDMethod(),
  new WordPressCurlMethod(),
  new WordPressBrowserMethod(),
]);

methodRegistry.set("jane", [
  new JaneEmbedMethod(),
  new JaneAPIMethod(),
]);

// Universal fallbacks
methodRegistry.set("universal", [
  new BrowserScreenshotOCRMethod(),
  new GenericHTMLMethod(),
  new LLMAssistedMethod(),
]);

export function getMethodsForProvider(provider: string): ScrapingMethod[] {
  const specific = methodRegistry.get(provider) || [];
  const universal = methodRegistry.get("universal") || [];
  return [...specific, ...universal];
}
```

### Adding New Methods

```typescript
// methods/new/dutchie-v2.ts
export class DutchieV2Method implements ScrapingMethod {
  name = "dutchie-v2-graphql";
  provider = "dutchie";
  type = "api" as const;
  
  requirements = {
    chromium: false,  // API method, no browser
    cookies: true,    // Needs session cookie
  };
  
  async scrape(config: ScrapeConfig): Promise<ScrapeResult> {
    // Implementation
  }
}

// Register at startup
methodRegistry.get("dutchie")!.push(new DutchieV2Method());
```

---

## 4. Test Orchestrator

### Progressive Loop Design

```typescript
// orchestrator/runner.ts
export class TestOrchestrator {
  
  async runResearchLoop(dispensaryId: string) {
    const dispensary = await db.get(dispensaryId);
    const methods = getMethodsForProvider(dispensary.provider);
    
    // Update status
    await db.patch(dispensaryId, { status: "researching" });
    
    for (const method of methods) {
      console.log(`Testing ${method.name} on ${dispensary.name}`);
      
      const result = await this.testMethod(dispensary, method);
      
      // Record result
      await db.insert("testRuns", {
        dispensaryId,
        methodId: method.id,
        ...result,
      });
      
      // Check if good enough
      if (result.status === "success" && result.fieldCompleteness.overall >= 90) {
        console.log(`✅ Found working method: ${method.name}`);
        
        await db.patch(dispensaryId, {
          status: "solved",
          workingMethodId: method.id,
          workingMethodConfidence: result.fieldCompleteness.overall,
        });
        
        // Try inventory detection
        if (method.detectInventory) {
          const inventoryResult = await method.detectInventory(config);
          await db.patch(dispensaryId, {
            inventoryMethod: inventoryResult.method,
            inventoryConfidence: inventoryResult.confidence,
          });
        }
        
        return { success: true, method: method.name };
      }
      
      // Analyze failure
      if (result.status === "failed") {
        const diagnosis = await this.diagnoseFailure(result, dispensary, method);
        await this.recordLearning(diagnosis);
      }
    }
    
    // No method worked
    await db.patch(dispensaryId, { status: "blocked" });
    return { success: false, triedMethods: methods.length };
  }
  
  async diagnoseFailure(result: TestResult, dispensary: Dispensary, method: ScrapingMethod) {
    // Use LLM to analyze
    const prompt = `
      Scraping failed for ${dispensary.name} using ${method.name}.
      
      Error: ${result.errorMessage}
      HTML snippet: ${result.htmlSnapshot?.substring(0, 2000)}
      
      Possible issues:
      1. Cloudflare/bot detection
      2. Age gate blocking
      3. API changed
      4. Wrong provider detected
      5. Network/timeout
      
      Diagnose the issue and suggest a fix.
    `;
    
    const analysis = await llm.complete(prompt);
    return {
      type: analysis.issueType,
      description: analysis.explanation,
      suggestedFix: analysis.fix,
      confidence: analysis.confidence,
    };
  }
}
```

### Parallel Processing

```typescript
// orchestrator/batch.ts
export class BatchOrchestrator {
  private concurrency = 5;  // Process 5 stores at once
  
  async processCluster(provider: string) {
    const dispensaries = await db.query("dispensaries")
      .filter(d => d.provider === provider && d.status === "pending")
      .order("priority", "desc")
      .take(50);
    
    const chunks = chunk(dispensaries, this.concurrency);
    
    for (const batch of chunks) {
      await Promise.all(
        batch.map(d => this.orchestrator.runResearchLoop(d._id))
      );
      
      // Rate limit between batches
      await sleep(5000);
    }
  }
  
  async processAll() {
    const clusters = await clusterDispensaries();
    
    // Process by cluster, prioritizing largest first
    const sorted = [...clusters.entries()]
      .sort((a, b) => b[1].length - a[1].length);
    
    for (const [provider, dispensaries] of sorted) {
      console.log(`\n📦 Processing ${provider} cluster (${dispensaries.length} stores)`);
      await this.processCluster(provider);
    }
  }
}
```

---

## 5. Inventory Detection System

### Hacky Inventory Methods

```typescript
// inventory/methods.ts

export class InventoryDetector {
  
  // Method 1: Cart Probing
  async probeCart(page: Page, productUrl: string): Promise<number | null> {
    await page.goto(productUrl);
    
    // Try adding max quantity
    const quantityInput = await page.$('input[name="quantity"]');
    if (quantityInput) {
      await quantityInput.fill("999");
      await page.click('button[type="submit"]');
      
      // Check for error message with actual limit
      const error = await page.$eval('.error', el => el.textContent);
      const match = error?.match(/only (\d+) available/i);
      if (match) return parseInt(match[1]);
    }
    
    return null;
  }
  
  // Method 2: Dropdown Options
  async checkDropdown(page: Page): Promise<number | null> {
    const options = await page.$$eval('select[name="quantity"] option', 
      opts => opts.map(o => parseInt(o.value))
    );
    return options.length > 0 ? Math.max(...options) : null;
  }
  
  // Method 3: Stock Badge Detection
  async detectBadge(html: string): Promise<string | null> {
    const patterns = [
      /(\d+)\s*(?:left|remaining|in stock)/i,
      /(?:low stock|limited|few left)/i,
      /(?:out of stock|sold out)/i,
    ];
    
    for (const pattern of patterns) {
      const match = html.match(pattern);
      if (match) return match[0];
    }
    
    return null;
  }
  
  // Method 4: API Response Inspection
  async interceptInventory(page: Page, url: string): Promise<object | null> {
    const inventoryData: any[] = [];
    
    page.on('response', async (response) => {
      const data = await response.json().catch(() => null);
      if (data) {
        // Look for inventory-like fields
        const found = findInventoryFields(data);
        if (found) inventoryData.push(found);
      }
    });
    
    await page.goto(url);
    await page.waitForTimeout(5000);
    
    return inventoryData.length > 0 ? inventoryData : null;
  }
  
  // Method 5: DOM Attribute Sniffing
  async sniffAttributes(page: Page): Promise<Map<string, number>> {
    return await page.$$eval('[data-quantity], [data-stock], [data-inventory]', 
      els => {
        const map = new Map();
        els.forEach(el => {
          const productId = el.getAttribute('data-product-id');
          const qty = el.getAttribute('data-quantity') || 
                      el.getAttribute('data-stock') ||
                      el.getAttribute('data-inventory');
          if (productId && qty) map.set(productId, parseInt(qty));
        });
        return map;
      }
    );
  }
}
```

---

## 6. Progress Engine

### State Machine

```
┌─────────┐     detect      ┌────────────┐     test      ┌─────────────┐
│ PENDING │────────────────▶│ RESEARCHING│──────────────▶│   SOLVED    │
└─────────┘                 └────────────┘               └─────────────┘
                                  │                            │
                                  │ all methods fail           │ method stops working
                                  ▼                            ▼
                            ┌─────────┐                  ┌──────────┐
                            │ BLOCKED │◀─────────────────│ DEGRADED │
                            └─────────┘   needs new      └──────────┘
                                  │       method
                                  │
                                  ▼
                            ┌─────────┐
                            │ MANUAL  │ (needs human)
                            └─────────┘
```

### Priority Scoring

```typescript
function calculatePriority(dispensary: Dispensary): number {
  let score = 0;
  
  // Boost popular cities
  if (dispensary.city === "New York") score += 50;
  if (dispensary.city === "Brooklyn") score += 40;
  
  // Boost stores with known provider (easier to solve)
  if (dispensary.providerConfidence > 80) score += 30;
  
  // Boost stores similar to solved ones
  const solved = getSolvedWithSameProvider(dispensary.provider);
  if (solved.length > 0) score += 20;
  
  // Deprioritize blocked stores
  if (dispensary.status === "blocked") score -= 50;
  
  // Boost stores with website (vs delivery-only)
  if (dispensary.website) score += 10;
  
  return score;
}
```

### Continuous Operation

```typescript
// engine/continuous.ts
export class ContinuousEngine {
  private running = false;
  
  async start() {
    this.running = true;
    
    while (this.running) {
      // 1. Check for degraded stores (methods stopped working)
      await this.recheckDegraded();
      
      // 2. Process pending stores
      await this.processPending();
      
      // 3. Try new methods on blocked stores
      await this.retryBlocked();
      
      // 4. Sleep before next cycle
      await sleep(60 * 60 * 1000);  // 1 hour
    }
  }
  
  async recheckDegraded() {
    const solved = await db.query("dispensaries")
      .filter(d => d.status === "solved")
      .collect();
    
    for (const d of solved) {
      // Re-run working method
      const result = await this.orchestrator.testMethod(d, d.workingMethodId);
      
      if (result.status !== "success") {
        await db.patch(d._id, { status: "degraded" });
        
        // Try to find new working method
        await this.orchestrator.runResearchLoop(d._id);
      }
    }
  }
  
  async retryBlocked() {
    // When new methods are added, retry blocked stores
    const blocked = await db.query("dispensaries")
      .filter(d => d.status === "blocked")
      .collect();
    
    for (const d of blocked) {
      const methods = getMethodsForProvider(d.provider);
      const tried = await getTriedMethods(d._id);
      
      // Check for new untried methods
      const untried = methods.filter(m => !tried.includes(m.id));
      
      if (untried.length > 0) {
        await this.orchestrator.runResearchLoop(d._id);
      }
    }
  }
}
```

---

## 7. Knowledge Base

### Learning Types

```typescript
type LearningType = 
  | "gotcha"    // Something unexpected (e.g., "Dutchie stores in NYC have extra rate limiting")
  | "patch"     // A workaround that fixed a problem
  | "pattern"   // A reusable pattern (e.g., "All Blaze stores use /menu/location format")
  | "blocker";  // An unsolvable issue (e.g., "This store requires login")
```

### Auto-Learning

```typescript
async function extractLearnings(testRun: TestRun, diagnosis: Diagnosis) {
  // Check if this learning already exists
  const existing = await db.query("learnings")
    .filter(l => l.provider === testRun.provider && l.title === diagnosis.title)
    .first();
  
  if (existing) {
    // Update confidence
    await db.patch(existing._id, {
      confirmedBy: existing.confirmedBy + 1,
      affectsDispensaries: [...existing.affectsDispensaries, testRun.dispensaryId],
    });
  } else {
    // Create new learning
    await db.insert("learnings", {
      provider: testRun.provider,
      type: diagnosis.type,
      title: diagnosis.title,
      description: diagnosis.description,
      solution: diagnosis.suggestedFix,
      affectsDispensaries: [testRun.dispensaryId],
      confirmedBy: 1,
      createdAt: Date.now(),
    });
  }
}
```

### Applying Learnings

```typescript
async function applyLearnings(dispensary: Dispensary, method: ScrapingMethod) {
  const learnings = await db.query("learnings")
    .filter(l => l.provider === dispensary.provider && l.type === "patch")
    .collect();
  
  // Apply patches to method config
  for (const learning of learnings) {
    if (learning.solutionCode) {
      method.applyPatch(learning.solutionCode);
    }
  }
  
  return method;
}
```

---

## 8. LLM Integration

### Progressive Research Loops

```typescript
// When all automatic methods fail, spawn an LLM research loop
async function spawnResearchLoop(dispensary: Dispensary) {
  const context = {
    dispensary,
    failedMethods: await getFailedMethods(dispensary._id),
    similarSolved: await getSimilarSolved(dispensary),
    learnings: await getRelevantLearnings(dispensary.provider),
  };
  
  const task = `
    Research scraping approach for ${dispensary.name}.
    
    ## Context
    - Provider: ${dispensary.provider} (${dispensary.providerConfidence}% confidence)
    - Website: ${dispensary.website}
    - Menu URL: ${dispensary.menuUrl}
    
    ## Failed Methods
    ${context.failedMethods.map(m => `- ${m.name}: ${m.errorMessage}`).join('\n')}
    
    ## Similar Solved Stores
    ${context.similarSolved.map(s => `- ${s.name}: ${s.workingMethod}`).join('\n')}
    
    ## Known Issues for ${dispensary.provider}
    ${context.learnings.map(l => `- ${l.title}: ${l.description}`).join('\n')}
    
    ## Tasks
    1. Visit the website and analyze the page structure
    2. Check network requests for API endpoints
    3. Identify why existing methods failed
    4. Propose a new scraping approach
    5. Implement and test the approach
    6. Document findings as learnings
    
    Report results with working code if successful.
  `;
  
  return await spawnSubagent({
    label: `research-${dispensary.slug}`,
    task,
    model: "claude-sonnet-4-5",
  });
}
```

### Failure Analysis

```typescript
async function analyzeFailureWithLLM(testRun: TestRun): Promise<Diagnosis> {
  const prompt = `
    Analyze this scraping failure:
    
    Store: ${testRun.dispensaryName}
    Method: ${testRun.methodName}
    Error: ${testRun.errorMessage}
    
    HTML (first 5000 chars):
    ${testRun.htmlSnapshot?.substring(0, 5000)}
    
    Network log:
    ${testRun.networkLog?.slice(0, 20).map(r => `${r.method} ${r.url} -> ${r.status}`).join('\n')}
    
    Classify the issue:
    1. cloudflare - Bot detection
    2. age_gate - Age verification required  
    3. api_change - API structure changed
    4. wrong_provider - Misclassified provider
    5. network - Network/timeout issue
    6. structure_change - HTML structure changed
    7. auth_required - Login required
    8. other - Something else
    
    Provide:
    - issueType: one of the above
    - explanation: what happened
    - fix: how to fix it
    - confidence: 0-100
  `;
  
  const response = await llm.complete(prompt, { json: true });
  return response as Diagnosis;
}
```

---

## 9. Repository Structure

```
scraping-engine/
├── package.json
├── convex/
│   ├── schema.ts           # Database schema
│   ├── dispensaries.ts     # Dispensary CRUD
│   ├── methods.ts          # Method registry
│   ├── testRuns.ts         # Test execution
│   └── learnings.ts        # Knowledge base
├── methods/
│   ├── base.ts             # Method interface
│   ├── registry.ts         # Method registry
│   ├── dutchie/
│   │   ├── graphql.ts
│   │   ├── browser.ts
│   │   └── api.ts
│   ├── blaze/
│   │   ├── api.ts
│   │   └── browser.ts
│   ├── wordpress/
│   │   ├── rest.ts
│   │   ├── jsonld.ts
│   │   └── curl.ts
│   ├── jane/
│   │   └── embed.ts
│   └── universal/
│       ├── generic-html.ts
│       ├── screenshot-ocr.ts
│       └── llm-assisted.ts
├── inventory/
│   ├── detector.ts         # Inventory detection
│   ├── cart-probe.ts
│   ├── dropdown.ts
│   └── api-sniff.ts
├── orchestrator/
│   ├── runner.ts           # Test orchestrator
│   ├── batch.ts            # Parallel processing
│   └── continuous.ts       # Continuous engine
├── clustering/
│   ├── detector.ts         # Provider detection
│   └── signatures.ts       # Provider signatures
├── analysis/
│   ├── llm.ts              # LLM integration
│   ├── diagnosis.ts        # Failure analysis
│   └── learnings.ts        # Knowledge extraction
├── api/
│   ├── routes.ts           # API endpoints
│   └── webhooks.ts         # Status callbacks
├── dashboard/              # Monitoring UI
│   ├── pages/
│   │   ├── overview.tsx
│   │   ├── dispensaries.tsx
│   │   ├── methods.tsx
│   │   └── learnings.tsx
│   └── components/
├── scripts/
│   ├── seed.ts             # Seed NYS dispensaries
│   ├── cluster.ts          # Run clustering
│   └── research.ts         # Start research loop
└── docker/
    ├── Dockerfile
    ├── docker-compose.yml
    └── fly.toml
```

---

## 10. Getting Started

### 1. Initialize

```bash
# Clone and setup
git clone <repo>
cd scraping-engine
npm install
npx convex dev

# Seed NYS dispensaries
npm run seed:nys
```

### 2. Run Clustering

```bash
# Detect providers for all stores
npm run cluster:detect

# View clusters
npm run cluster:stats
# Output:
# dutchie: 187 stores
# blaze: 95 stores
# wordpress: 78 stores
# jane: 45 stores
# unknown: 193 stores
```

### 3. Start Research

```bash
# Process specific cluster
npm run research:cluster -- --provider=dutchie

# Process all (continuous)
npm run research:all

# Check progress
npm run status
# Output:
# Solved: 234 (39%)
# Researching: 12 (2%)
# Blocked: 45 (8%)
# Pending: 307 (51%)
```

### 4. Add New Method

```typescript
// methods/dutchie/graphql-v2.ts
export class DutchieGraphQLV2 implements ScrapingMethod {
  // ... implementation
}

// Register in methods/registry.ts
methodRegistry.get("dutchie")!.push(new DutchieGraphQLV2());

// Retry blocked stores with new method
npm run retry:blocked -- --provider=dutchie
```

---

## 11. Monitoring Dashboard

### Key Metrics

- **Coverage**: % of stores with working method
- **Success Rate**: % of recent scrapes succeeding
- **Inventory Coverage**: % of stores with inventory detection
- **Method Efficiency**: Which methods work best per provider
- **Learnings Growth**: New insights per week

### Alerts

- Method degradation (success rate drops)
- New blockers discovered
- High-value stores failing
- Cluster without any working method

---

## Next Steps

1. **Set up Convex project** with schema
2. **Seed 598 NYS dispensaries** from existing data
3. **Run provider clustering** to group stores
4. **Port existing scrapers** to method format
5. **Start progressive research** on largest cluster
6. **Build dashboard** for monitoring
7. **Add inventory detection** methods
8. **Enable continuous operation**
