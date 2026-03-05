#!/usr/bin/env node
/**
 * Research All Script
 * Processes all pending dispensaries across all providers
 */

import { BatchOrchestrator } from '../dist/orchestrator/batch.js';

const CONVEX_URL = process.env.CONVEX_URL || process.env.VITE_CONVEX_URL;

if (!CONVEX_URL) {
  console.error('❌ CONVEX_URL environment variable required');
  process.exit(1);
}

console.log('🔬 Starting research for all pending dispensaries');
console.log(`   Convex URL: ${CONVEX_URL}`);
console.log('');

const orchestrator = new BatchOrchestrator(CONVEX_URL, {
  concurrency: parseInt(process.env.CONCURRENCY || '5'),
  delayBetweenBatches: parseInt(process.env.DELAY_MS || '5000'),
});

const maxPerProvider = process.argv.includes('--max')
  ? parseInt(process.argv[process.argv.indexOf('--max') + 1])
  : undefined;

orchestrator.processAll(maxPerProvider)
  .then(() => {
    console.log('\n✅ Research complete');
    process.exit(0);
  })
  .catch(error => {
    console.error('\n❌ Research failed:', error.message);
    process.exit(1);
  });
