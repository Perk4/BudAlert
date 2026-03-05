#!/usr/bin/env node
/**
 * Research Cluster Script
 * Processes dispensaries for a specific provider
 */

import { BatchOrchestrator } from '../dist/orchestrator/batch.js';

const CONVEX_URL = process.env.CONVEX_URL || process.env.VITE_CONVEX_URL;

if (!CONVEX_URL) {
  console.error('❌ CONVEX_URL environment variable required');
  process.exit(1);
}

// Get provider from --provider flag
const providerIndex = process.argv.indexOf('--provider');
if (providerIndex === -1 || !process.argv[providerIndex + 1]) {
  console.error('❌ --provider flag required');
  console.error('Usage: npm run research:cluster -- --provider=dutchie');
  process.exit(1);
}

const provider = process.argv[providerIndex + 1];

console.log(`🔬 Starting research for ${provider} cluster`);
console.log(`   Convex URL: ${CONVEX_URL}`);
console.log('');

const orchestrator = new BatchOrchestrator(CONVEX_URL, {
  concurrency: parseInt(process.env.CONCURRENCY || '5'),
});

const maxDispensaries = process.argv.includes('--max')
  ? parseInt(process.argv[process.argv.indexOf('--max') + 1])
  : undefined;

orchestrator.processCluster(provider, maxDispensaries)
  .then(() => {
    console.log('\n✅ Cluster research complete');
    process.exit(0);
  })
  .catch(error => {
    console.error('\n❌ Research failed:', error.message);
    process.exit(1);
  });
