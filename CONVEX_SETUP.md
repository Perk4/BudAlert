# Convex Setup for NYS Dispensaries

## Current Status

✅ Schema created (`convex/schema.ts`)
✅ Mutations created (`convex/nysDispensaries.ts`)
✅ Data loader created (`convex/loadDispensaries.ts`)
✅ Import script created (`scripts/import-nys-dispensaries.js`)
✅ Data prepared (`/tmp/nys_dispensaries_prepared.json` - 599 dispensaries)

⏳ **Next Steps Required:**

## 1. Initialize Convex

```bash
cd ~/clawd/budalert

# Install Convex if not already installed
npm install convex

# Initialize Convex (creates convex.json and .env.local)
npx convex dev
```

This will:
- Create a new Convex project (if needed)
- Generate `convex.json`
- Create `.env.local` with your deployment URL
- Start the development server

## 2. Import the Data

Once Convex is running:

```bash
# Option A: Using the Node.js script
node scripts/import-nys-dispensaries.js

# Option B: Using npx convex import (if you prefer)
# Note: You'll need to format the data for Convex's import format
npx convex import nysDispensaries /tmp/nys_dispensaries_prepared.json
```

## 3. Verify the Import

You can verify the data was loaded by:

### Using Convex Dashboard
1. Go to your Convex dashboard
2. Navigate to Data
3. Check the `nysDispensaries` table

### Using queries (in your app or via console)
```typescript
// Count all dispensaries
const count = await convex.query("nysDispensaries:count");
console.log(`Total dispensaries: ${count}`);

// Get statistics
const stats = await convex.query("nysDispensaries:getStats");
console.log(stats);
```

## Data Structure

Each dispensary record includes:
- `entity_name`: Business name (string, required)
- `address`: Street address (string, optional)
- `city`: City name (string, required)
- `zip_code`: ZIP code (string, optional)
- `website`: Dispensary website (string, optional)
- `is_microbusiness`: Microbusiness flag (boolean)
- `is_delivery_only`: Delivery-only flag (boolean)
- `scraped_at`: Unix timestamp (number)

## Available Queries

- `list()` - Get all dispensaries
- `count()` - Count all dispensaries
- `getStats()` - Get summary statistics
- `getByCity(city)` - Get dispensaries by city
- `getByZip(zip_code)` - Get dispensaries by ZIP code

## Available Mutations

- `upsert(dispensary)` - Insert or update a single dispensary
- `batchUpsert(dispensaries[])` - Insert or update multiple dispensaries

## Data Source

Scraped from: https://cannabis.ny.gov/dispensary-location-verification
Last scraped: 2026-03-05
Total records: 599 dispensaries
