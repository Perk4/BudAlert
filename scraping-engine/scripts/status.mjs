#!/usr/bin/env node
/**
 * Status Script
 * Shows current research progress
 */

import { ConvexHttpClient } from 'convex/browser';
import { api } from '../convex/_generated/api.js';

const CONVEX_URL = process.env.CONVEX_URL || process.env.VITE_CONVEX_URL;

if (!CONVEX_URL) {
  console.error('❌ CONVEX_URL environment variable required');
  process.exit(1);
}

const client = new ConvexHttpClient(CONVEX_URL);

async function showStatus() {
  console.log('📊 Scraping Research Engine Status\n');
  
  // Get overall stats
  const stats = await client.query(api.dispensaries.getStats);
  
  console.log('Overall Progress:');
  console.log(`  Total Dispensaries: ${stats.total}`);
  console.log(`  Solved:  ${stats.solved} (${((stats.solved / stats.total) * 100).toFixed(1)}%)`);
  console.log(`  Pending: ${stats.pending} (${((stats.pending / stats.total) * 100).toFixed(1)}%)`);
  console.log(`  Blocked: ${stats.blocked} (${((stats.blocked / stats.total) * 100).toFixed(1)}%)`);
  console.log(`  Researching: ${stats.researching}`);
  
  console.log('\nBy Provider:');
  const providers = Object.entries(stats.byProvider)
    .sort((a, b) => b[1] - a[1]);
  
  for (const [provider, count] of providers) {
    console.log(`  ${provider.padEnd(12)} ${count}`);
  }
  
  console.log('\nBy Status:');
  for (const [status, count] of Object.entries(stats.byStatus)) {
    console.log(`  ${status.padEnd(12)} ${count}`);
  }
  
  // Get method stats
  const methodStats = await client.query(api.methods.getStats);
  
  if (methodStats.length > 0) {
    console.log('\nMethod Performance:');
    for (const method of methodStats) {
      console.log(`  ${method.name.padEnd(30)} ${method.successRate}% (${method.totalRuns} runs)`);
    }
  }
}

showStatus()
  .then(() => {
    process.exit(0);
  })
  .catch(error => {
    console.error('\n❌ Failed:', error.message);
    process.exit(1);
  });
