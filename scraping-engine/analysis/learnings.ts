/**
 * Learning Extraction and Application
 * Automatically extracts knowledge from test runs
 */

import { ConvexHttpClient } from 'convex/browser';
import { api } from '../convex/_generated/api.js';
import { Id } from '../convex/_generated/dataModel.js';

export interface Learning {
  type: 'gotcha' | 'patch' | 'pattern' | 'blocker';
  title: string;
  description: string;
  solution?: string;
  solutionCode?: string;
}

export class LearningExtractor {
  private client: ConvexHttpClient;
  
  constructor(convexUrl: string) {
    this.client = new ConvexHttpClient(convexUrl);
  }
  
  /**
   * Extract learnings from a failed test run
   */
  extractFromFailure(
    provider: string,
    errorType: string,
    errorMessage: string,
    diagnosis: any
  ): Learning | null {
    // Pattern: Cloudflare blocking
    if (errorType === 'cloudflare' || diagnosis?.type === 'cloudflare') {
      return {
        type: 'blocker',
        title: 'Cloudflare protection active',
        description: `${provider} sites are protected by Cloudflare. HTTP methods fail.`,
        solution: 'Use browser-based methods with proper wait times',
      };
    }
    
    // Pattern: API structure changed
    if (errorType === 'api_change' || diagnosis?.type === 'api_change') {
      return {
        type: 'gotcha',
        title: 'GraphQL API structure changed',
        description: `${provider} API query structure has changed`,
        solution: 'Update GraphQL queries to match new structure',
      };
    }
    
    // Pattern: Age gate
    if (errorMessage.toLowerCase().includes('age') || errorMessage.includes('verify')) {
      return {
        type: 'gotcha',
        title: 'Age verification required',
        description: `${provider} requires age verification before showing menu`,
        solution: 'Implement age gate bypass in browser method',
      };
    }
    
    // Pattern: Authentication required
    if (errorType === 'auth_required' || diagnosis?.type === 'auth_required') {
      return {
        type: 'blocker',
        title: 'Login required',
        description: `${provider} requires user login to view menu`,
        solution: 'Manual extraction or user-provided credentials',
      };
    }
    
    // Pattern: Rate limiting
    if (errorMessage.toLowerCase().includes('rate limit') || errorMessage.includes('429')) {
      return {
        type: 'patch',
        title: 'Rate limiting detected',
        description: `${provider} enforces rate limits`,
        solution: 'Add delays between requests',
        solutionCode: 'await sleep(2000); // 2 second delay',
      };
    }
    
    return null;
  }
  
  /**
   * Extract learnings from a successful test run
   */
  extractFromSuccess(
    provider: string,
    method: string,
    fieldCompleteness: any
  ): Learning | null {
    // Pattern: Method works well
    if (fieldCompleteness.overall >= 90) {
      return {
        type: 'pattern',
        title: `${method} works well for ${provider}`,
        description: `${method} achieves ${fieldCompleteness.overall}% completeness`,
      };
    }
    
    // Pattern: Missing fields
    if (fieldCompleteness.overall < 90) {
      const missingFields: string[] = [];
      
      if (fieldCompleteness.price < 80) missingFields.push('price');
      if (fieldCompleteness.brand < 80) missingFields.push('brand');
      if (fieldCompleteness.thc < 80) missingFields.push('thc');
      
      if (missingFields.length > 0) {
        return {
          type: 'gotcha',
          title: `${method} missing some fields`,
          description: `Missing or incomplete: ${missingFields.join(', ')}`,
          solution: 'Add selectors or parsing logic for missing fields',
        };
      }
    }
    
    return null;
  }
  
  /**
   * Record a learning to the knowledge base
   */
  async recordLearning(
    provider: string,
    learning: Learning,
    dispensaryId: Id<'dispensaries'>,
    methodId?: Id<'methods'>
  ): Promise<void> {
    console.log(`[Learning] Recording: ${learning.title}`);
    
    await this.client.mutation(api.learnings.upsert, {
      provider,
      type: learning.type,
      title: learning.title,
      description: learning.description,
      dispensaryId,
      methodId,
      solution: learning.solution,
      solutionCode: learning.solutionCode,
    });
  }
  
  /**
   * Get learnings for a provider
   */
  async getForProvider(provider: string): Promise<any[]> {
    return await this.client.query(api.learnings.getByProvider, { provider });
  }
  
  /**
   * Apply learnings to a scraping method
   */
  applyLearnings(learnings: any[]): Record<string, any> {
    const config: Record<string, any> = {};
    
    for (const learning of learnings) {
      // Apply patches
      if (learning.type === 'patch' && learning.solutionCode) {
        console.log(`[Learning] Applying patch: ${learning.title}`);
        
        // Rate limiting
        if (learning.title.toLowerCase().includes('rate limit')) {
          config.delayBetweenRequests = 2000;
        }
        
        // Timeout adjustments
        if (learning.title.toLowerCase().includes('timeout')) {
          config.timeout = 60000;
        }
      }
      
      // Apply patterns
      if (learning.type === 'pattern') {
        console.log(`[Learning] Considering pattern: ${learning.title}`);
      }
      
      // Warn about blockers
      if (learning.type === 'blocker') {
        console.warn(`[Learning] ⚠️  Blocker: ${learning.title}`);
      }
    }
    
    return config;
  }
}

/**
 * Auto-learning from test results
 */
export async function autoLearn(
  convexUrl: string,
  testRunId: Id<'testRuns'>
): Promise<void> {
  const client = new ConvexHttpClient(convexUrl);
  const extractor = new LearningExtractor(convexUrl);
  
  // Get test run details
  const testRun = await client.query(api.testRuns.get, { id: testRunId } as any);
  
  if (!testRun) {
    console.error('[Auto-Learn] Test run not found');
    return;
  }
  
  // Get dispensary and method
  const dispensary = await client.query(api.dispensaries.get, { id: testRun.dispensaryId });
  
  if (!dispensary) {
    console.error('[Auto-Learn] Dispensary not found');
    return;
  }
  
  let learning: Learning | null = null;
  
  if (testRun.status === 'failed') {
    // Extract from failure
    learning = extractor.extractFromFailure(
      dispensary.provider,
      testRun.errorType || '',
      testRun.errorMessage || '',
      {
        type: testRun.errorType,
        explanation: testRun.llmAnalysis || testRun.errorMessage,
      }
    );
  } else if (testRun.status === 'success') {
    // Extract from success
    const method = await client.query(api.methods.get, { id: testRun.methodId });
    
    if (method) {
      learning = extractor.extractFromSuccess(
        dispensary.provider,
        method.name,
        testRun.fieldCompleteness
      );
    }
  }
  
  // Record learning if found
  if (learning) {
    await extractor.recordLearning(
      dispensary.provider,
      learning,
      testRun.dispensaryId,
      testRun.methodId
    );
    
    console.log(`[Auto-Learn] ✅ Recorded learning: ${learning.title}`);
  } else {
    console.log('[Auto-Learn] No new learning extracted');
  }
}
