/**
 * Test Orchestrator
 * Manages progressive testing of methods against dispensaries
 */

import { ConvexHttpClient } from 'convex/browser';
import { api } from '../convex/_generated/api.js';
import { Id } from '../convex/_generated/dataModel.js';
import { getMethodsForProvider } from '../methods/registry.js';
import { ScrapingMethod, ScrapeConfig } from '../methods/base.js';

export interface TestResult {
  success: boolean;
  method?: string;
  triedMethods: number;
  productsFound: number;
  fieldCompleteness: any;
  error?: string;
}

export class TestOrchestrator {
  private client: ConvexHttpClient;
  
  constructor(convexUrl: string) {
    this.client = new ConvexHttpClient(convexUrl);
  }
  
  /**
   * Run research loop for a single dispensary
   * Tests methods progressively until one works
   */
  async runResearchLoop(dispensaryId: Id<'dispensaries'>): Promise<TestResult> {
    console.log(`\n🔬 Starting research loop for dispensary: ${dispensaryId}`);
    
    // Get dispensary details
    const dispensary = await this.client.query(api.dispensaries.get, { id: dispensaryId });
    
    if (!dispensary) {
      throw new Error(`Dispensary not found: ${dispensaryId}`);
    }
    
    console.log(`   Name: ${dispensary.name}`);
    console.log(`   Provider: ${dispensary.provider} (${dispensary.providerConfidence}% confidence)`);
    console.log(`   Status: ${dispensary.status}`);
    
    // Update status to researching
    await this.client.mutation(api.dispensaries.update, {
      id: dispensaryId,
      updates: { status: 'researching' },
    });
    
    // Get methods for this provider
    const methods = getMethodsForProvider(dispensary.provider);
    console.log(`   Available methods: ${methods.length}`);
    
    if (methods.length === 0) {
      console.log('   ⚠️  No methods available for this provider');
      
      await this.client.mutation(api.dispensaries.update, {
        id: dispensaryId,
        updates: { status: 'blocked' },
      });
      
      return {
        success: false,
        triedMethods: 0,
        productsFound: 0,
        fieldCompleteness: null,
        error: 'No methods available',
      };
    }
    
    // Get methods already tried
    const triedMethodIds = await this.client.query(api.testRuns.getTriedMethods, {
      dispensaryId,
    });
    
    console.log(`   Already tried: ${triedMethodIds.length} methods`);
    
    // Filter out already tried methods
    // (In production, we'd need to map method instances to DB IDs properly)
    
    // Test each method
    for (const method of methods) {
      console.log(`\n   📋 Testing method: ${method.name}`);
      
      const result = await this.testMethod(dispensary, method);
      
      // Record test run
      const testRunId = await this.recordTestRun(dispensaryId, method, result);
      
      console.log(`      Status: ${result.status}`);
      console.log(`      Products found: ${result.productsFound}`);
      console.log(`      Field completeness: ${result.fieldCompleteness.overall}%`);
      
      // Check if good enough (>90% completeness)
      if (result.status === 'success' && result.fieldCompleteness.overall >= 90) {
        console.log(`   ✅ Found working method: ${method.name}`);
        
        // Update dispensary status
        await this.client.mutation(api.dispensaries.update, {
          id: dispensaryId,
          updates: {
            status: 'solved',
            lastSuccessfulScrape: Date.now(),
          },
        });
        
        // Update method stats
        // (Would need method ID from registry)
        
        return {
          success: true,
          method: method.name,
          triedMethods: methods.indexOf(method) + 1,
          productsFound: result.productsFound,
          fieldCompleteness: result.fieldCompleteness,
        };
      }
      
      // Analyze failure
      if (result.status === 'failed') {
        const diagnosis = await this.diagnoseFailure(result, dispensary, method);
        await this.recordLearning(diagnosis, dispensaryId);
      }
    }
    
    // No method worked
    console.log(`   ❌ No working method found after ${methods.length} attempts`);
    
    await this.client.mutation(api.dispensaries.update, {
      id: dispensaryId,
      updates: { status: 'blocked' },
    });
    
    return {
      success: false,
      triedMethods: methods.length,
      productsFound: 0,
      fieldCompleteness: null,
    };
  }
  
  /**
   * Test a single method on a dispensary
   */
  private async testMethod(dispensary: any, method: ScrapingMethod): Promise<any> {
    const startTime = Date.now();
    
    try {
      const config: ScrapeConfig = {
        dispensaryId: dispensary._id,
        url: dispensary.website || '',
        menuUrl: dispensary.menuUrl,
        timeout: 30000,
        retries: 2,
      };
      
      const result = await method.scrape(config);
      
      return {
        status: result.success ? 'success' : 'failed',
        productsFound: result.products.length,
        fieldsExtracted: this.getExtractedFields(result.products),
        fieldCompleteness: result.fieldCompleteness,
        inventoryDetected: false, // TODO: Implement inventory detection
        errorMessage: result.errors?.[0],
        sampleOutput: result.products.slice(0, 5),
        metadata: result.metadata,
      };
    } catch (error: any) {
      return {
        status: 'failed',
        productsFound: 0,
        fieldsExtracted: [],
        fieldCompleteness: {
          overall: 0,
          name: 0,
          price: 0,
          brand: 0,
          category: 0,
          thc: 0,
          inStock: 0,
        },
        inventoryDetected: false,
        errorType: error.name,
        errorMessage: error.message,
      };
    }
  }
  
  /**
   * Get list of fields that were extracted
   */
  private getExtractedFields(products: any[]): string[] {
    if (products.length === 0) return [];
    
    const fields = new Set<string>();
    const sample = products[0];
    
    if (sample.name) fields.add('name');
    if (sample.price !== null) fields.add('price');
    if (sample.brand) fields.add('brand');
    if (sample.category) fields.add('category');
    if (sample.thc) fields.add('thc');
    if (sample.cbd) fields.add('cbd');
    if (sample.weight) fields.add('weight');
    
    return Array.from(fields);
  }
  
  /**
   * Record test run to database
   */
  private async recordTestRun(
    dispensaryId: Id<'dispensaries'>,
    method: ScrapingMethod,
    result: any
  ): Promise<Id<'testRuns'>> {
    // In production, we'd need to resolve the method ID from the registry
    // For now, create a placeholder method ID
    
    // This is a simplified version - in production we'd:
    // 1. Look up method in methods table
    // 2. Create if doesn't exist
    // 3. Use the ID
    
    console.log('      ⚠️  Test run recording skipped (method ID resolution needed)');
    return 'placeholder' as any;
  }
  
  /**
   * Diagnose why a method failed
   */
  private async diagnoseFailure(
    result: any,
    dispensary: any,
    method: ScrapingMethod
  ): Promise<any> {
    // Use method's diagnose function if available
    if (method.diagnose) {
      const error = new Error(result.errorMessage || 'Unknown error');
      return await method.diagnose(error);
    }
    
    // Basic diagnosis
    const message = (result.errorMessage || '').toLowerCase();
    
    if (message.includes('timeout')) {
      return {
        type: 'network',
        explanation: 'Request timed out',
        suggestedFix: 'Increase timeout or check network',
        confidence: 90,
      };
    }
    
    if (message.includes('cloudflare')) {
      return {
        type: 'cloudflare',
        explanation: 'Cloudflare protection detected',
        suggestedFix: 'Use browser-based method',
        confidence: 95,
      };
    }
    
    return {
      type: 'other',
      explanation: result.errorMessage || 'Unknown error',
      suggestedFix: null,
      confidence: 50,
    };
  }
  
  /**
   * Record learning to knowledge base
   */
  private async recordLearning(diagnosis: any, dispensaryId: Id<'dispensaries'>): Promise<void> {
    // Only record high-confidence learnings
    if (diagnosis.confidence < 70) return;
    
    console.log(`      📚 Recording learning: ${diagnosis.type}`);
    
    // This would call the learnings.upsert mutation
    // Skipped for now due to method ID resolution
  }
}
