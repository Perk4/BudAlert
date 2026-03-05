#!/usr/bin/env node
/**
 * Seed NYS Dispensaries
 * Loads 598 NYS dispensaries from parent Convex database
 */

import { ConvexHttpClient } from 'convex/browser';
import { api } from '../convex/_generated/api.js';

const CONVEX_URL = process.env.CONVEX_URL || process.env.VITE_CONVEX_URL;
const PARENT_CONVEX_URL = process.env.PARENT_CONVEX_URL;

if (!CONVEX_URL) {
  console.error('❌ CONVEX_URL environment variable required');
  process.exit(1);
}

if (!PARENT_CONVEX_URL) {
  console.warn('⚠️  PARENT_CONVEX_URL not set, using mock data');
}

const client = new ConvexHttpClient(CONVEX_URL);

async function seedFromParent() {
  console.log('📥 Loading NYS dispensaries from parent database...');
  
  const parentClient = new ConvexHttpClient(PARENT_CONVEX_URL);
  
  // Load from parent nysDispensaries table
  const nysDispensaries = await parentClient.query('nysDispensaries:list' as any);
  
  console.log(`   Found ${nysDispensaries.length} dispensaries in parent DB`);
  
  let created = 0;
  
  for (const disp of nysDispensaries) {
    // Calculate priority based on city
    let priority = 0;
    if (disp.city === 'New York') priority = 50;
    else if (disp.city === 'Brooklyn') priority = 40;
    else if (disp.city === 'Queens') priority = 30;
    else if (disp.city === 'Bronx') priority = 25;
    else if (disp.city === 'Manhattan') priority = 45;
    
    // Boost if has website
    if (disp.website) priority += 10;
    
    await client.mutation(api.dispensaries.create, {
      name: disp.entity_name,
      address: disp.address,
      city: disp.city,
      zipCode: disp.zip_code,
      website: disp.website,
      provider: 'unknown',
      priority,
    });
    
    created++;
    
    if (created % 50 === 0) {
      console.log(`   Created ${created}/${nysDispensaries.length}`);
    }
  }
  
  console.log(`✅ Seeded ${created} dispensaries`);
}

async function seedMockData() {
  console.log('📥 Creating mock dispensaries for testing...');
  
  const mockDispensaries = [
    {
      name: 'Conbud LES',
      city: 'New York',
      website: 'https://conbud.com',
      provider: 'dutchie',
      priority: 100,
    },
    {
      name: 'Housing Works Broadway',
      city: 'New York',
      address: 'Broadway',
      website: 'https://hwcannabis.co',
      provider: 'blaze',
      priority: 90,
    },
    {
      name: 'Gotham NYC',
      city: 'New York',
      website: 'https://gotham.nyc',
      provider: 'wordpress',
      priority: 85,
    },
  ];
  
  for (const disp of mockDispensaries) {
    await client.mutation(api.dispensaries.create, disp as any);
  }
  
  console.log(`✅ Created ${mockDispensaries.length} mock dispensaries`);
}

async function main() {
  console.log('🌱 NYS Dispensary Seeding\n');
  
  // Check if already seeded
  const existing = await client.query(api.dispensaries.list, { limit: 1 });
  
  if (existing.length > 0) {
    console.log('⚠️  Database already contains dispensaries');
    console.log('   Delete existing data before re-seeding');
    process.exit(0);
  }
  
  if (PARENT_CONVEX_URL) {
    await seedFromParent();
  } else {
    await seedMockData();
  }
  
  // Show stats
  const stats = await client.query(api.dispensaries.getStats);
  
  console.log('\n📊 Database Statistics:');
  console.log(`   Total: ${stats.total}`);
  console.log(`   By Status:`);
  for (const [status, count] of Object.entries(stats.byStatus)) {
    console.log(`     ${status}: ${count}`);
  }
  console.log(`   By Provider:`);
  for (const [provider, count] of Object.entries(stats.byProvider)) {
    console.log(`     ${provider}: ${count}`);
  }
}

main()
  .then(() => {
    process.exit(0);
  })
  .catch(error => {
    console.error('\n❌ Seeding failed:', error.message);
    process.exit(1);
  });
