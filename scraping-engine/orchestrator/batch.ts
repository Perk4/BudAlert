/**
 * Batch Orchestrator
 * Processes multiple dispensaries in parallel
 */

import { TestOrchestrator } from './runner.js';
import { ConvexHttpClient } from 'convex/browser';
import { api } from '../convex/_generated/api.js';
import { Id } from '../convex/_generated/dataModel.js';

export interface BatchOptions {
  concurrency?: number;
  delayBetweenBatches?: number;
  maxDispensaries?: number;
}

export class BatchOrchestrator {
  private orchestrator: TestOrchestrator;
  private client: ConvexHttpClient;
  private concurrency: number;
  private delayBetweenBatches: number;
  
  constructor(convexUrl: string, options: BatchOptions = {}) {
    this.orchestrator = new TestOrchestrator(convexUrl);
    this.client = new ConvexHttpClient(convexUrl);
    this.concurrency = options.concurrency || 5;
    this.delayBetweenBatches = options.delayBetweenBatches || 5000;
  }
  
  /**
   * Process a cluster of dispensaries by provider
   */
  async processCluster(provider: string, maxDispensaries?: number): Promise<void> {
    console.log(`\n📦 Processing ${provider} cluster`);
    
    // Get pending dispensaries for this provider
    const dispensaries = await this.client.query(api.dispensaries.getByProviderStatus, {
      provider,
      status: 'pending',
      limit: maxDispensaries || 50,
    });
    
    console.log(`   Found ${dispensaries.length} pending dispensaries`);
    
    if (dispensaries.length === 0) {
      console.log('   ✅ No pending dispensaries');
      return;
    }
    
    // Split into batches
    const batches = this.chunk(dispensaries, this.concurrency);
    console.log(`   Processing in ${batches.length} batches (concurrency: ${this.concurrency})`);
    
    let successCount = 0;
    let failCount = 0;
    
    for (let i = 0; i < batches.length; i++) {
      const batch = batches[i];
      console.log(`\n   Batch ${i + 1}/${batches.length} (${batch.length} dispensaries)`);
      
      // Process batch in parallel
      const results = await Promise.allSettled(
        batch.map(d => this.orchestrator.runResearchLoop(d._id as Id<'dispensaries'>))
      );
      
      // Count successes/failures
      for (const result of results) {
        if (result.status === 'fulfilled' && result.value.success) {
          successCount++;
        } else {
          failCount++;
        }
      }
      
      console.log(`   Batch complete: ${successCount} solved, ${failCount} failed`);
      
      // Rate limit between batches
      if (i < batches.length - 1) {
        console.log(`   ⏳ Waiting ${this.delayBetweenBatches}ms before next batch...`);
        await this.sleep(this.delayBetweenBatches);
      }
    }
    
    console.log(`\n✅ Cluster processing complete`);
    console.log(`   Total solved: ${successCount}`);
    console.log(`   Total failed: ${failCount}`);
  }
  
  /**
   * Process all pending dispensaries across all providers
   */
  async processAll(maxPerProvider?: number): Promise<void> {
    console.log('\n🌍 Processing all pending dispensaries');
    
    // Get all dispensaries grouped by provider
    const stats = await this.client.query(api.dispensaries.getStats);
    
    console.log('\n📊 Current Status:');
    console.log(`   Total: ${stats.total}`);
    console.log(`   Solved: ${stats.solved}`);
    console.log(`   Pending: ${stats.pending}`);
    console.log(`   Blocked: ${stats.blocked}`);
    console.log(`   Researching: ${stats.researching}`);
    
    // Get providers sorted by count (largest first)
    const providers = Object.entries(stats.byProvider)
      .sort((a, b) => b[1] - a[1])
      .map(([provider]) => provider);
    
    console.log('\n📦 Providers (by size):');
    for (const provider of providers) {
      console.log(`   ${provider}: ${stats.byProvider[provider]} dispensaries`);
    }
    
    // Process each provider
    for (const provider of providers) {
      if (provider === 'unknown') continue; // Skip unknown for now
      
      await this.processCluster(provider, maxPerProvider);
      
      // Delay between providers
      await this.sleep(10000);
    }
    
    console.log('\n✅ All providers processed');
  }
  
  /**
   * Retry blocked dispensaries when new methods are available
   */
  async retryBlocked(provider?: string): Promise<void> {
    console.log('\n🔄 Retrying blocked dispensaries');
    
    const query = provider
      ? { provider, status: 'blocked' }
      : { status: 'blocked' };
    
    const blocked = await this.client.query(api.dispensaries.list, query as any);
    
    console.log(`   Found ${blocked.length} blocked dispensaries`);
    
    if (blocked.length === 0) {
      console.log('   ✅ No blocked dispensaries to retry');
      return;
    }
    
    // Update status to pending so they'll be retried
    for (const dispensary of blocked) {
      await this.client.mutation(api.dispensaries.update, {
        id: dispensary._id as Id<'dispensaries'>,
        updates: { status: 'pending' },
      });
    }
    
    console.log(`   ✅ Reset ${blocked.length} dispensaries to pending`);
    console.log('   Run processAll to retry them');
  }
  
  /**
   * Chunk array into batches
   */
  private chunk<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }
  
  /**
   * Sleep utility
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
