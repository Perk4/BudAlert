# Scraping Research Engine

A self-improving system that progressively discovers working scraping methods for 500+ NY dispensaries, clusters them by provider, and builds a knowledge base of what works.

## Overview

This engine:
- **Auto-detects** which platform each dispensary uses (Dutchie, Blaze, WordPress, etc.)
- **Tests methods** progressively until one works
- **Records results** and learns from failures
- **Builds knowledge** about what works for each provider
- **Runs continuously** to maintain working scrapers

## Quick Start

### 1. Install Dependencies

```bash
cd scraping-engine
npm install
```

### 2. Set Up Convex

```bash
# Start Convex dev server
npm run convex:dev
```

This will:
- Create a new Convex project (if needed)
- Deploy the schema
- Give you a CONVEX_URL

### 3. Set Environment Variables

```bash
export CONVEX_URL="https://your-convex-url.convex.cloud"
export PARENT_CONVEX_URL="https://parent-convex-url.convex.cloud"  # Optional
```

### 4. Seed Dispensaries

```bash
# From parent database (if available)
npm run seed:nys

# Or create mock data for testing
# (automatically used if PARENT_CONVEX_URL not set)
```

### 5. Register Methods

```bash
# Build TypeScript
npm run build

# Register scraping methods
node scripts/register-methods.mjs
```

### 6. Run Detection & Research

```bash
# Detect providers for all dispensaries
npm run cluster:detect

# View cluster statistics
npm run cluster:stats

# Research a specific provider
npm run research:cluster -- --provider=dutchie

# Research all providers
npm run research:all

# Check progress
npm run status
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  SCRAPING RESEARCH ENGINE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ DISPENSARIES │─▶│   PROVIDER   │─▶│   METHODS    │      │
│  │  (598 NYS)   │  │   DETECTOR   │  │  (Pluggable) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  ┌──────────────────────────────────────────────┐           │
│  │          TEST ORCHESTRATOR                   │           │
│  │  • Progressive method testing                │           │
│  │  • Parallel execution                        │           │
│  │  • Failure diagnosis                         │           │
│  └──────────────────────────────────────────────┘           │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  TEST RUNS   │  │  LEARNINGS   │  │  CONTINUOUS  │      │
│  │   TRACKER    │◀─│ KNOWLEDGE DB │◀─│    ENGINE    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## npm Scripts

### Development
- `npm run dev` - Start Convex dev server
- `npm run build` - Compile TypeScript
- `npm run type-check` - Check types without building

### Seeding & Setup
- `npm run seed:nys` - Load NYS dispensaries
- `node scripts/register-methods.mjs` - Register methods

### Clustering
- `npm run cluster:detect` - Detect providers
- `npm run cluster:stats` - Show cluster stats

### Research
- `npm run research:cluster -- --provider=dutchie` - Research one provider
- `npm run research:all` - Research all providers
- `npm run status` - Show progress

### Operation
- `npm run continuous` - Run continuous background engine
- `npm run retry:blocked -- --provider=dutchie` - Retry blocked stores

## Methods

### Dutchie
- **dutchie-graphql** - Direct API (fast, requires session)
- **dutchie-browser-intercept** - Browser with network capture (most reliable)

### Blaze
- **blaze-http** - HTTP scraper (simple, works for most)

### WordPress
- **wordpress-browser** - Browser to bypass Cloudflare

### Universal
- **universal-generic-html** - Fallback for unknown platforms

## Continuous Operation

Run the engine continuously:

```bash
npm run continuous
```

This will:
1. Check for degraded stores (methods stopped working)
2. Process pending stores
3. Retry blocked stores when new methods available
4. Sleep for 1 hour
5. Repeat

## Environment Variables

- `CONVEX_URL` - Convex deployment URL (required)
- `PARENT_CONVEX_URL` - Parent database for seeding (optional)
- `CONCURRENCY` - Parallel scrapes (default: 5)
- `DELAY_MS` - Delay between batches (default: 5000)
- `CHECK_INTERVAL_MS` - Continuous engine interval (default: 3600000 = 1hr)
- `MAX_PER_CYCLE` - Max dispensaries per cycle (default: 50)

## Database Schema

### dispensaries
- Basic info (name, address, website)
- Provider classification
- Research status (pending/researching/solved/blocked)
- Working method (once found)
- Priority score

### methods
- Method registry
- Success/fail stats
- Requirements (chromium, proxy, etc.)

### testRuns
- Execution results
- Products found
- Field completeness
- Error diagnosis

### learnings
- Knowledge base
- Gotchas, patterns, blockers
- Solutions and patches

## Adding New Methods

1. Create method file in `methods/{provider}/{name}.ts`
2. Implement `ScrapingMethod` interface
3. Register in `methods/registry.ts`
4. Run `node scripts/register-methods.mjs`

Example:

```typescript
export class MyMethod implements ScrapingMethod {
  name = 'my-method';
  provider = 'my-provider';
  type = 'http';
  
  requirements = {
    chromium: false,
    cookies: false,
  };
  
  async scrape(config: ScrapeConfig): Promise<ScrapeResult> {
    // Implementation
  }
}
```

## Development Workflow

1. **Add dispensaries** - `npm run seed:nys`
2. **Detect providers** - `npm run cluster:detect`
3. **Register methods** - `node scripts/register-methods.mjs`
4. **Test a cluster** - `npm run research:cluster -- --provider=dutchie`
5. **Check results** - `npm run status`
6. **Fix issues** - Add learnings, update methods
7. **Retry blocked** - `npm run retry:blocked`
8. **Run continuous** - `npm run continuous`

## Next Steps

- [ ] Integrate with main BudAlert system
- [ ] Add LLM-assisted failure analysis
- [ ] Implement inventory detection
- [ ] Add monitoring dashboard
- [ ] Deploy to production

## License

MIT
