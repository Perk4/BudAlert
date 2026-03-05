#!/usr/bin/env node
/**
 * Retry Blocked Script
 * Resets blocked dispensaries to pending for retry
 */

import { BatchOrchestrator } from '../dist/orchestrator/batch.js';

const CONVEX_URL = process.env.CONVEX_URL || process.env.VITE_CONVEX_URL;

if (!CONVEX_URL) {
  console.error('❌ CONVEX_URL environment variable required');
  process.exit(1);
}

const providerIndex = process.argv.indexOf('--provider');
const provider = providerIndex !== -1 ? process.argv[providerIndex + 1] : undefined;

console.log('🔄 Retrying blocked dispensaries');
if (provider) {
  console.log(`   Provider: ${provider}`);
}
console.log('');

const orchestrator = new BatchOrchestrator(CONVEX_URL);

orchestrator.retryBlocked(provider)
  .then(() => {
    console.log('\n✅ Blocked dispensaries reset to pending');
    process.exit(0);
  })
  .catch(error => {
    console.error('\n❌ Failed:', error.message);
    process.exit(1);
  });
