# Getting Started with the Scraping Research Engine

This guide will walk you through setting up and running the scraping research engine from scratch.

## Prerequisites

- Node.js 18+ installed
- npm or yarn
- A Convex account (free tier works)

## Step-by-Step Setup

### 1. Install Dependencies

```bash
cd ~/clawd/budalert/scraping-engine
npm install
```

This will install:
- Convex (database/backend)
- Playwright (browser automation)
- Axios (HTTP requests)
- Cheerio (HTML parsing)
- TypeScript & build tools

### 2. Initialize Convex

```bash
npm run convex:dev
```

**What this does:**
1. Prompts you to create/select a Convex project
2. Deploys the schema to Convex
3. Starts a local dev server that watches for changes
4. Outputs your `CONVEX_URL`

**Important:** Keep this terminal open! It watches for schema changes.

Example output:
```
✔ Deployment URL: https://happy-tiger-123.convex.cloud
```

### 3. Configure Environment

Create a `.env.local` file:

```bash
cat > .env.local << EOF
CONVEX_URL=https://your-project.convex.cloud
VITE_CONVEX_URL=https://your-project.convex.cloud

# Optional: For seeding from parent database
PARENT_CONVEX_URL=https://parent-project.convex.cloud
EOF
```

Or export in your shell:

```bash
export CONVEX_URL="https://your-project.convex.cloud"
export VITE_CONVEX_URL="https://your-project.convex.cloud"
```

### 4. Build TypeScript

```bash
npm run build
```

This compiles all `.ts` files to `.js` in the `dist/` directory.

### 5. Seed Dispensaries

**Option A: From parent database** (if you have access to main BudAlert Convex)

```bash
export PARENT_CONVEX_URL="https://your-parent.convex.cloud"
npm run seed:nys
```

This will load all 598 NYS dispensaries from the parent database.

**Option B: Mock data** (for testing)

```bash
npm run seed:nys
```

Without `PARENT_CONVEX_URL`, this creates 3 mock dispensaries for testing.

### 6. Register Methods

```bash
npm run register:methods
```

This registers all scraping methods in the database:
- Dutchie GraphQL
- Dutchie Browser
- Blaze HTTP
- WordPress Browser
- Universal Generic

### 7. Check Initial Status

```bash
npm run status
```

You should see:
```
📊 Scraping Research Engine Status

Overall Progress:
  Total Dispensaries: 598
  Solved:  0 (0.0%)
  Pending: 598 (100.0%)
  Blocked: 0 (0.0%)
  Researching: 0

By Provider:
  unknown      598

Method Performance:
  dutchie-graphql                 0.0% (0 runs)
  dutchie-browser-intercept       0.0% (0 runs)
  ...
```

## Running Research

### Test a Single Provider

```bash
npm run research:cluster -- --provider=dutchie
```

This will:
1. Find all pending Dutchie dispensaries
2. Test each method progressively
3. Record results
4. Mark as solved or blocked

### Detect Providers First

Before researching, you may want to detect providers:

```bash
# Detect providers for all dispensaries
npm run cluster:detect

# Check results
npm run cluster:stats
```

This will group dispensaries by their detected platform.

### Research All Providers

```bash
npm run research:all
```

This processes all providers in order of size (largest first).

Options:
```bash
# Limit dispensaries per provider
npm run research:all -- --max=10

# Set concurrency
CONCURRENCY=3 npm run research:all
```

### Monitor Progress

```bash
# Check status
npm run status

# Watch continuously
watch -n 30 npm run status
```

## Continuous Operation

For long-term operation:

```bash
npm run continuous
```

This runs in a loop:
1. Check degraded stores
2. Process pending stores
3. Retry blocked stores
4. Sleep for 1 hour
5. Repeat

**Stop with:** Ctrl+C (graceful shutdown)

## Troubleshooting

### "CONVEX_URL not set"

Make sure you've exported the environment variable:

```bash
export CONVEX_URL="https://your-project.convex.cloud"
```

Or create `.env.local` (see step 3).

### "Module not found"

Run the build step:

```bash
npm run build
```

### "Convex schema not deployed"

Make sure `npm run convex:dev` is running in another terminal.

### Methods failing

Check the test runs in Convex dashboard:
1. Go to https://dashboard.convex.dev
2. Select your project
3. Browse `testRuns` table
4. Check `errorMessage` and `llmAnalysis`

### Browser issues (Playwright)

Install Playwright browsers:

```bash
npx playwright install chromium
```

## Next Steps

Once you have some successful scrapes:

1. **Check results:**
   ```bash
   npm run status
   ```

2. **Review learnings:**
   Browse the `learnings` table in Convex dashboard

3. **Retry blocked stores:**
   ```bash
   npm run retry:blocked
   ```

4. **Export data:**
   Use Convex dashboard to export `testRuns` or `learnings`

## Development Tips

### Adding a new method

1. Create file: `methods/yourprovider/yourmethod.ts`
2. Implement `ScrapingMethod` interface
3. Add to registry: `methods/registry.ts`
4. Re-run: `npm run register:methods`

### Testing a method locally

```typescript
import { YourMethod } from './methods/yourprovider/yourmethod';

const method = new YourMethod();
const result = await method.scrape({
  dispensaryId: 'test',
  url: 'https://example.com',
  timeout: 30000,
});

console.log(result);
```

### Debugging

Enable verbose logging:

```bash
DEBUG=* npm run research:cluster -- --provider=dutchie
```

### Updating schema

1. Edit `convex/schema.ts`
2. The dev server will auto-deploy
3. Check Convex dashboard for migration status

## Support

- Check README.md for architecture
- Browse existing methods in `methods/`
- Review test runs in Convex dashboard
- Check learnings table for known issues

## Production Deployment

See [PRODUCTION.md](./PRODUCTION.md) (coming soon) for:
- Deploying to Convex production
- Running continuous engine as a service
- Monitoring and alerting
- Scaling considerations
