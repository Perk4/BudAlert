/**
 * Continuous Engine
 * Runs scraping research continuously in the background
 */

import { BatchOrchestrator } from './batch.js';
import { ConvexHttpClient } from 'convex/browser';
import { api } from '../convex/_generated/api.js';

export interface ContinuousOptions {
  checkInterval?: number; // ms between cycles
  maxDispensariesPerCycle?: number;
}

export class ContinuousEngine {
  private batchOrchestrator: BatchOrchestrator;
  private client: ConvexHttpClient;
  private running: boolean = false;
  private checkInterval: number;
  private maxDispensariesPerCycle: number;
  
  constructor(convexUrl: string, options: ContinuousOptions = {}) {
    this.batchOrchestrator = new BatchOrchestrator(convexUrl);
    this.client = new ConvexHttpClient(convexUrl);
    this.checkInterval = options.checkInterval || 60 * 60 * 1000; // 1 hour
    this.maxDispensariesPerCycle = options.maxDispensariesPerCycle || 50;
  }
  
  /**
   * Start continuous operation
   */
  async start(): Promise<void> {
    this.running = true;
    
    console.log('🔄 Starting continuous scraping engine');
    console.log(`   Check interval: ${this.checkInterval}ms`);
    console.log(`   Max per cycle: ${this.maxDispensariesPerCycle}`);
    
    while (this.running) {
      console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      console.log(`🕐 Cycle started at ${new Date().toISOString()}`);
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      
      try {
        // 1. Check for degraded stores (methods stopped working)
        await this.recheckDegraded();
        
        // 2. Process pending stores
        await this.batchOrchestrator.processAll(this.maxDispensariesPerCycle);
        
        // 3. Try new methods on blocked stores (if any new methods registered)
        await this.retryBlockedIfNewMethods();
        
      } catch (error: any) {
        console.error('❌ Cycle error:', error.message);
      }
      
      console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      console.log(`⏳ Sleeping for ${this.checkInterval}ms...`);
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
      
      await this.sleep(this.checkInterval);
    }
  }
  
  /**
   * Stop continuous operation
   */
  stop(): void {
    console.log('🛑 Stopping continuous engine');
    this.running = false;
  }
  
  /**
   * Recheck solved dispensaries to detect degradation
   */
  private async recheckDegraded(): Promise<void> {
    console.log('\n🔍 Checking for degraded stores...');
    
    const solved = await this.client.query(api.dispensaries.list, {
      status: 'solved',
      limit: 10, // Check 10 random solved stores per cycle
    });
    
    if (solved.length === 0) {
      console.log('   No solved stores to check');
      return;
    }
    
    console.log(`   Checking ${solved.length} solved stores`);
    
    // In production, we'd re-run their working method
    // and check if it still works
    
    // For now, just log
    console.log('   ⚠️  Degradation check not yet implemented');
  }
  
  /**
   * Retry blocked stores if new methods have been registered
   */
  private async retryBlockedIfNewMethods(): Promise<void> {
    console.log('\n🔄 Checking for new methods to retry blocked stores...');
    
    // In production, we'd:
    // 1. Check when methods were last registered
    // 2. Check when blocked stores were last tried
    // 3. If new methods available, retry
    
    // For now, skip
    console.log('   ⚠️  New method detection not yet implemented');
  }
  
  /**
   * Sleep utility
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
