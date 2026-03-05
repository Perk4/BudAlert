#!/usr/bin/env node
/**
 * Continuous Engine Runner
 * Runs scraping research continuously in the background
 */

import { ContinuousEngine } from '../dist/orchestrator/continuous.js';

const CONVEX_URL = process.env.CONVEX_URL || process.env.VITE_CONVEX_URL;

if (!CONVEX_URL) {
  console.error('❌ CONVEX_URL environment variable required');
  process.exit(1);
}

const engine = new ContinuousEngine(CONVEX_URL, {
  checkInterval: parseInt(process.env.CHECK_INTERVAL_MS || '3600000'), // 1 hour
  maxDispensariesPerCycle: parseInt(process.env.MAX_PER_CYCLE || '50'),
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\nReceived SIGINT, shutting down gracefully...');
  engine.stop();
  setTimeout(() => process.exit(0), 2000);
});

process.on('SIGTERM', () => {
  console.log('\n\nReceived SIGTERM, shutting down gracefully...');
  engine.stop();
  setTimeout(() => process.exit(0), 2000);
});

console.log('🔄 Starting continuous scraping engine');
console.log(`   Convex URL: ${CONVEX_URL}`);
console.log('   Press Ctrl+C to stop\n');

engine.start()
  .catch(error => {
    console.error('\n❌ Engine error:', error.message);
    process.exit(1);
  });
