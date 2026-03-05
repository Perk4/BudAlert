#!/usr/bin/env node
/**
 * Register Methods Script
 * Registers all scraping methods in the Convex database
 */

import { ConvexHttpClient } from 'convex/browser';
import { api } from '../convex/_generated/api.js';

const CONVEX_URL = process.env.CONVEX_URL || process.env.VITE_CONVEX_URL;

if (!CONVEX_URL) {
  console.error('❌ CONVEX_URL environment variable required');
  process.exit(1);
}

const client = new ConvexHttpClient(CONVEX_URL);

const methods = [
  // Dutchie methods
  {
    name: 'dutchie-graphql',
    provider: 'dutchie',
    type: 'api',
    scriptPath: 'methods/dutchie/graphql.ts',
    requiresChromium: false,
    requiresProxy: false,
    bypassesCloudflare: false,
    description: 'Direct GraphQL API - fast and lightweight',
  },
  {
    name: 'dutchie-browser-intercept',
    provider: 'dutchie',
    type: 'browser',
    scriptPath: 'methods/dutchie/browser.ts',
    requiresChromium: true,
    requiresProxy: false,
    bypassesCloudflare: true,
    description: 'Browser with network interception - most reliable',
  },
  
  // Blaze methods
  {
    name: 'blaze-http',
    provider: 'blaze',
    type: 'http',
    scriptPath: 'methods/blaze/api.ts',
    requiresChromium: false,
    requiresProxy: false,
    bypassesCloudflare: false,
    description: 'HTTP scraper with cheerio parsing',
  },
  
  // WordPress methods
  {
    name: 'wordpress-browser',
    provider: 'wordpress',
    type: 'browser',
    scriptPath: 'methods/wordpress/browser.ts',
    requiresChromium: true,
    requiresProxy: false,
    bypassesCloudflare: true,
    description: 'Browser method to bypass Cloudflare',
  },
  
  // Universal fallback
  {
    name: 'universal-generic-html',
    provider: 'universal',
    type: 'http',
    scriptPath: 'methods/universal/generic.ts',
    requiresChromium: false,
    requiresProxy: false,
    bypassesCloudflare: false,
    description: 'Generic HTML parser - last resort',
  },
];

async function registerMethods() {
  console.log('📝 Registering scraping methods\n');
  
  let registered = 0;
  
  for (const method of methods) {
    try {
      await client.mutation(api.methods.register, method);
      console.log(`   ✅ ${method.name}`);
      registered++;
    } catch (error) {
      console.error(`   ❌ ${method.name}:`, error.message);
    }
  }
  
  console.log(`\n✅ Registered ${registered}/${methods.length} methods`);
  
  // Show stats
  const stats = await client.query(api.methods.getStats);
  
  console.log('\n📊 Method Registry:');
  for (const method of stats) {
    console.log(`   ${method.name.padEnd(30)} [${method.provider}]`);
  }
}

registerMethods()
  .then(() => {
    process.exit(0);
  })
  .catch(error => {
    console.error('\n❌ Registration failed:', error.message);
    process.exit(1);
  });
