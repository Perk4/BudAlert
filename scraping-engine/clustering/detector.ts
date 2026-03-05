/**
 * Provider Detection Engine
 * Automatically detects which platform a dispensary uses
 */

import axios from 'axios';
import { PROVIDER_SIGNATURES, MENU_URL_PATTERNS } from './signatures.js';

export interface ProviderResult {
  provider: string;
  confidence: number;
  evidence: string[];
  menuUrl?: string;
}

export class ProviderDetector {
  private timeout: number;
  
  constructor(options: { timeout?: number } = {}) {
    this.timeout = options.timeout || 15000;
  }
  
  /**
   * Detect provider for a dispensary
   */
  async detect(website: string): Promise<ProviderResult> {
    try {
      // Step 1: Fetch homepage
      const html = await this.fetchPage(website);
      
      // Step 2: Check signatures
      const signatureResult = this.checkSignatures(html, website);
      if (signatureResult.confidence >= 80) {
        return signatureResult;
      }
      
      // Step 3: Check for menu URL patterns
      const menuUrl = this.discoverMenuUrl(html, website);
      if (menuUrl) {
        const menuProvider = this.detectFromMenuUrl(menuUrl);
        if (menuProvider) {
          return {
            ...menuProvider,
            menuUrl,
          };
        }
      }
      
      // Step 4: Return best guess or unknown
      if (signatureResult.confidence > 0) {
        return {
          ...signatureResult,
          menuUrl,
        };
      }
      
      return {
        provider: 'unknown',
        confidence: 0,
        evidence: [],
      };
      
    } catch (error: any) {
      console.error(`[Detector] Failed to detect provider for ${website}:`, error.message);
      
      return {
        provider: 'unknown',
        confidence: 0,
        evidence: [`Error: ${error.message}`],
      };
    }
  }
  
  /**
   * Fetch page HTML
   */
  private async fetchPage(url: string): Promise<string> {
    const response = await axios.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      },
      timeout: this.timeout,
      maxRedirects: 5,
    });
    
    return response.data;
  }
  
  /**
   * Check HTML against provider signatures
   */
  private checkSignatures(html: string, url: string): ProviderResult {
    const matches: Map<string, { count: number; weight: number; patterns: string[] }> = new Map();
    
    for (const signature of PROVIDER_SIGNATURES) {
      let matchCount = 0;
      const matchedPatterns: string[] = [];
      
      // Check HTML patterns
      for (const pattern of signature.patterns) {
        if (html.includes(pattern)) {
          matchCount++;
          matchedPatterns.push(pattern);
        }
      }
      
      // Check URL patterns
      if (signature.urlPatterns) {
        for (const urlPattern of signature.urlPatterns) {
          if (urlPattern.test(url)) {
            matchCount++;
            matchedPatterns.push(`URL: ${urlPattern.source}`);
          }
        }
      }
      
      if (matchCount > 0) {
        matches.set(signature.provider, {
          count: matchCount,
          weight: signature.weight,
          patterns: matchedPatterns,
        });
      }
    }
    
    // Find best match
    let bestProvider = 'unknown';
    let bestConfidence = 0;
    let bestEvidence: string[] = [];
    
    for (const [provider, data] of matches.entries()) {
      const signature = PROVIDER_SIGNATURES.find(s => s.provider === provider)!;
      const totalPatterns = signature.patterns.length + (signature.urlPatterns?.length || 0);
      const matchRatio = data.count / totalPatterns;
      const confidence = Math.round(matchRatio * data.weight * 100);
      
      if (confidence > bestConfidence) {
        bestProvider = provider;
        bestConfidence = confidence;
        bestEvidence = data.patterns;
      }
    }
    
    return {
      provider: bestProvider,
      confidence: bestConfidence,
      evidence: bestEvidence,
    };
  }
  
  /**
   * Discover menu URL from HTML
   */
  private discoverMenuUrl(html: string, baseUrl: string): string | null {
    const menuPatterns = [
      /href=["']([^"']*\/menu[^"']*)["']/i,
      /href=["']([^"']*dutchie[^"']*)["']/i,
      /href=["']([^"']*iheartjane[^"']*)["']/i,
    ];
    
    for (const pattern of menuPatterns) {
      const match = html.match(pattern);
      if (match) {
        const menuPath = match[1];
        
        // Convert to absolute URL
        try {
          const url = new URL(menuPath, baseUrl);
          return url.href;
        } catch (e) {
          continue;
        }
      }
    }
    
    return null;
  }
  
  /**
   * Detect provider from menu URL
   */
  private detectFromMenuUrl(menuUrl: string): ProviderResult | null {
    for (const [provider, patterns] of Object.entries(MENU_URL_PATTERNS)) {
      for (const pattern of patterns) {
        if (pattern.test(menuUrl)) {
          return {
            provider,
            confidence: 95,
            evidence: [`Menu URL: ${menuUrl}`],
          };
        }
      }
    }
    
    return null;
  }
}

/**
 * Cluster dispensaries by provider
 */
export interface DispensaryCluster {
  provider: string;
  dispensaries: Array<{
    id: string;
    name: string;
    website: string;
    confidence: number;
  }>;
}

export async function clusterDispensaries(
  dispensaries: Array<{ id: string; name: string; website?: string; provider?: string }>
): Promise<Map<string, DispensaryCluster>> {
  const detector = new ProviderDetector();
  const clusters = new Map<string, DispensaryCluster>();
  
  for (const dispensary of dispensaries) {
    // Skip if already has provider with high confidence
    if (dispensary.provider && dispensary.provider !== 'unknown') {
      if (!clusters.has(dispensary.provider)) {
        clusters.set(dispensary.provider, {
          provider: dispensary.provider,
          dispensaries: [],
        });
      }
      
      clusters.get(dispensary.provider)!.dispensaries.push({
        id: dispensary.id,
        name: dispensary.name,
        website: dispensary.website || '',
        confidence: 100,
      });
      continue;
    }
    
    // Skip if no website
    if (!dispensary.website) {
      if (!clusters.has('unknown')) {
        clusters.set('unknown', {
          provider: 'unknown',
          dispensaries: [],
        });
      }
      
      clusters.get('unknown')!.dispensaries.push({
        id: dispensary.id,
        name: dispensary.name,
        website: '',
        confidence: 0,
      });
      continue;
    }
    
    // Detect provider
    const result = await detector.detect(dispensary.website);
    
    if (!clusters.has(result.provider)) {
      clusters.set(result.provider, {
        provider: result.provider,
        dispensaries: [],
      });
    }
    
    clusters.get(result.provider)!.dispensaries.push({
      id: dispensary.id,
      name: dispensary.name,
      website: dispensary.website,
      confidence: result.confidence,
    });
    
    // Rate limiting
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  return clusters;
}
