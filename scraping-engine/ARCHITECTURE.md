# Architecture Documentation

## System Overview

The Scraping Research Engine is a progressive, self-improving system designed to discover and maintain working scraping methods for hundreds of dispensaries.

## Core Principles

1. **Progressive Discovery** - Try simple methods first, escalate to complex
2. **Learn from Failures** - Build knowledge base automatically
3. **Provider Clustering** - Group similar sites for efficiency
4. **Continuous Operation** - Monitor and adapt over time
5. **Pluggable Methods** - Easy to add new scraping approaches

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  • Status Dashboard (future)                                │
│  • Learning Browser (future)                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          TestOrchestrator (runner.ts)                │   │
│  │  • Progressive method testing                        │   │
│  │  • Failure diagnosis                                 │   │
│  │  • Learning extraction                               │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │        BatchOrchestrator (batch.ts)                  │   │
│  │  • Parallel execution                                │   │
│  │  • Rate limiting                                     │   │
│  │  • Cluster processing                                │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │       ContinuousEngine (continuous.ts)               │   │
│  │  • Background operation                              │   │
│  │  • Degradation detection                             │   │
│  │  • Auto-retry                                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Method Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Dutchie    │  │    Blaze     │  │  WordPress   │      │
│  │  - GraphQL   │  │  - HTTP      │  │  - Browser   │      │
│  │  - Browser   │  │  - Browser   │  │  - API       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Universal Fallbacks                       │   │
│  │  - Generic HTML                                      │   │
│  │  - Screenshot OCR (future)                           │   │
│  │  - LLM-assisted (future)                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Support Systems                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │      ProviderDetector (clustering/detector.ts)       │   │
│  │  • HTML signature matching                           │   │
│  │  • URL pattern recognition                           │   │
│  │  • LLM classification (future)                       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │     InventoryDetector (inventory/detector.ts)        │   │
│  │  • Cart probing                                      │   │
│  │  • API interception                                  │   │
│  │  • DOM attribute sniffing                            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    LearningExtractor (analysis/learnings.ts)         │   │
│  │  • Failure pattern detection                         │   │
│  │  • Success pattern extraction                        │   │
│  │  • Auto-patching                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Layer (Convex)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │dispensaries  │  │   methods    │  │  testRuns    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐                                           │
│  │  learnings   │   (Knowledge Base)                        │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Seeding Phase

```
NYS Data → seed-nys.mjs → Convex dispensaries table
                           (598 records, all status=pending)
```

### 2. Provider Detection Phase

```
Dispensary → ProviderDetector → HTML/URL analysis
                              → Provider classification
                              → Update dispensary.provider
```

### 3. Research Phase

```
Pending Dispensary → TestOrchestrator
                  → Get methods for provider
                  → Test each method progressively
                  → Record testRun
                  → Extract learning (if failed)
                  → Update dispensary.status
                  → (solved | blocked)
```

### 4. Continuous Phase

```
ContinuousEngine (loop every 1 hour)
  → Check degraded (re-test solved stores)
  → Process pending
  → Retry blocked (if new methods)
  → Sleep
```

## State Machine

### Dispensary States

```
        ┌─────────┐
        │ PENDING │ (initial state)
        └────┬────┘
             │ detect provider
             ▼
      ┌────────────┐
      │RESEARCHING │ (testing methods)
      └─┬────────┬─┘
        │        │
  method works   all fail
        │        │
        ▼        ▼
   ┌────────┐ ┌─────────┐
   │ SOLVED │ │ BLOCKED │
   └───┬────┘ └────┬────┘
       │           │
       │ degrades  │ new method
       │           │ available
       ▼           ▼
   ┌─────────┐ ┌─────────┐
   │DEGRADED │ │ PENDING │
   └─────────┘ └─────────┘
```

## Method Selection Strategy

For a given dispensary:

1. Get provider (e.g., "dutchie")
2. Get methods for provider from registry
3. Filter out already-tried methods
4. Order by:
   - Success rate
   - Speed (avgLatencyMs)
   - Complexity (HTTP > API > Browser)
5. Test progressively until one succeeds

## Learning System

### Learning Types

1. **Gotcha** - Unexpected issue
   - Example: "Dutchie stores in NYC have extra rate limiting"

2. **Patch** - Workaround
   - Example: "Add 2s delay between requests"
   - Can include code: `await sleep(2000)`

3. **Pattern** - Reusable insight
   - Example: "All Blaze stores use /menu/location format"

4. **Blocker** - Unsolvable
   - Example: "This store requires login"

### Learning Flow

```
Test Run → Failure
        → Diagnose (method.diagnose() or generic)
        → Extract learning pattern
        → Check if exists (by title)
        → If exists: increment confirmBy, add dispensary
        → If new: create learning
        → Future tests: apply learnings to method config
```

## Scalability Considerations

### Current Design (MVP)

- **Concurrency:** 5 parallel scrapes
- **Rate limiting:** 5s between batches
- **State:** In Convex database
- **Execution:** Single process

### Future Scaling

- **Distributed execution:** Multiple workers
- **Queue system:** Redis/Bull for job management
- **Caching:** Method results for similar sites
- **Method pooling:** Reuse browser contexts

## Security & Ethics

### Rate Limiting

- Default: 5 concurrent requests
- 5s delay between batches
- Per-provider delays in learnings

### User Agents

- Real browser UA strings
- Rotate if detected

### Respect Robots.txt

- Check before scraping (future)
- Honor crawl-delay

### Data Privacy

- Only public menu data
- No PII collection
- No authentication bypassing

## Extension Points

### Adding a New Provider

1. Create signature in `clustering/signatures.ts`
2. Create method in `methods/{provider}/`
3. Register in `methods/registry.ts`
4. Run `npm run register:methods`

### Adding a New Method Type

1. Implement `ScrapingMethod` interface
2. Add to provider's method array
3. Register in database

### Custom Failure Analysis

1. Extend `LearningExtractor`
2. Override `extractFromFailure()`
3. Add custom patterns

### Custom Inventory Detection

1. Extend `InventoryDetector`
2. Add new detection method
3. Call from `detect()`

## Technology Stack

- **Runtime:** Node.js 18+
- **Language:** TypeScript
- **Database:** Convex (realtime, serverless)
- **Browser:** Playwright (Chromium)
- **HTTP:** Axios
- **Parsing:** Cheerio
- **Build:** TypeScript compiler

## Performance Metrics

### Target Metrics

- **Coverage:** 80%+ of dispensaries solved
- **Completeness:** 90%+ field completeness
- **Latency:** <30s per dispensary
- **Reliability:** <5% failure rate on solved stores

### Current Metrics

- Coverage: TBD (run research first)
- Completeness: TBD
- Latency: TBD
- Reliability: TBD

## Future Enhancements

1. **LLM Integration**
   - Spawn research loops for unknown sites
   - Auto-generate selectors
   - Classify failures

2. **Dashboard**
   - Real-time progress
   - Method performance
   - Learning browser

3. **Advanced Inventory**
   - Historical tracking
   - Velocity calculation
   - Alert triggers

4. **Multi-Region**
   - Support non-NYS states
   - International sites

5. **API Mode**
   - REST API for integration
   - Webhook notifications
   - Real-time subscriptions
