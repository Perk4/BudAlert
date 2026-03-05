#!/usr/bin/env node

/**
 * Import NYS Dispensaries into Convex
 * 
 * Prerequisites:
 * - Convex must be initialized (npx convex dev)
 * - Environment variables must be set
 * 
 * Usage:
 *   node scripts/import-nys-dispensaries.js
 */

const fs = require('fs');
const path = require('path');

// Configuration
const DATA_FILE = '/tmp/dispensaries.json';
const BATCH_SIZE = 50; // Process in batches to avoid timeouts

async function main() {
  try {
    // Check if Convex is available
    let ConvexHttpClient;
    try {
      const convex = require('convex/browser');
      ConvexHttpClient = convex.ConvexHttpClient;
    } catch (err) {
      console.error('Error: Convex SDK not installed.');
      console.error('Run: npm install convex');
      process.exit(1);
    }

    // Get Convex URL from environment
    const convexUrl = process.env.VITE_CONVEX_URL || process.env.NEXT_PUBLIC_CONVEX_URL;
    if (!convexUrl) {
      console.error('Error: VITE_CONVEX_URL or NEXT_PUBLIC_CONVEX_URL not set');
      console.error('Run: npx convex dev');
      process.exit(1);
    }

    console.log(`Connecting to Convex: ${convexUrl}`);
    const client = new ConvexHttpClient(convexUrl);

    // Read data file
    console.log(`Reading data from: ${DATA_FILE}`);
    const rawData = fs.readFileSync(DATA_FILE, 'utf8');
    const dispensaries = JSON.parse(rawData);

    console.log(`Found ${dispensaries.length} dispensaries`);

    // Add scraped_at timestamp
    const scrapedAt = Date.now();
    const prepared = dispensaries.map(d => ({
      ...d,
      scraped_at: scrapedAt,
    }));

    // Process in batches
    let totalInserted = 0;
    let totalUpdated = 0;
    const allErrors = [];

    for (let i = 0; i < prepared.length; i += BATCH_SIZE) {
      const batch = prepared.slice(i, i + BATCH_SIZE);
      console.log(`Processing batch ${Math.floor(i / BATCH_SIZE) + 1}/${Math.ceil(prepared.length / BATCH_SIZE)}...`);

      try {
        const result = await client.mutation('nysDispensaries:batchUpsert', {
          dispensaries: batch,
        });

        totalInserted += result.inserted;
        totalUpdated += result.updated;
        allErrors.push(...result.errors);

        console.log(`  Inserted: ${result.inserted}, Updated: ${result.updated}`);
      } catch (err) {
        console.error(`  Batch error:`, err.message);
        allErrors.push(`Batch ${i}-${i + BATCH_SIZE}: ${err.message}`);
      }
    }

    // Summary
    console.log('\n=== Import Complete ===');
    console.log(`Total dispensaries: ${prepared.length}`);
    console.log(`Inserted: ${totalInserted}`);
    console.log(`Updated: ${totalUpdated}`);
    console.log(`Errors: ${allErrors.length}`);

    if (allErrors.length > 0) {
      console.log('\nErrors:');
      allErrors.forEach(err => console.log(`  - ${err}`));
    }

    client.close();
  } catch (err) {
    console.error('Fatal error:', err);
    process.exit(1);
  }
}

main();
