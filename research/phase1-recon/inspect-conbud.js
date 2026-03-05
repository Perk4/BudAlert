#!/usr/bin/env node
/**
 * Conbud LES Reconnaissance Script
 * Purpose: Identify API endpoints, network requests, and data structure
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function inspectConbud() {
  console.log('🔍 Starting Conbud LES reconnaissance...\n');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
  });
  
  const page = await context.newPage();
  
  // Track all network requests
  const requests = [];
  const apiRequests = [];
  const graphqlQueries = [];
  
  page.on('request', request => {
    const url = request.url();
    const method = request.method();
    
    requests.push({
      url,
      method,
      resourceType: request.resourceType(),
      timestamp: new Date().toISOString()
    });
    
    // Track API calls
    if (url.includes('api.dutchie.com') || url.includes('graphql')) {
      const postData = request.postData();
      apiRequests.push({
        url,
        method,
        headers: request.headers(),
        postData: postData ? JSON.parse(postData || '{}') : null,
        timestamp: new Date().toISOString()
      });
      
      // Extract GraphQL queries
      if (postData) {
        try {
          const data = JSON.parse(postData);
          if (data.query || data.operationName) {
            graphqlQueries.push({
              operationName: data.operationName,
              query: data.query,
              variables: data.variables,
              timestamp: new Date().toISOString()
            });
          }
        } catch (e) {
          // Not JSON, skip
        }
      }
    }
  });
  
  const responses = [];
  page.on('response', async response => {
    const url = response.url();
    
    if (url.includes('api.dutchie.com') || url.includes('graphql')) {
      try {
        const responseData = await response.json();
        responses.push({
          url,
          status: response.status(),
          headers: response.headers(),
          data: responseData,
          timestamp: new Date().toISOString()
        });
      } catch (e) {
        // Not JSON response
        responses.push({
          url,
          status: response.status(),
          headers: response.headers(),
          error: 'Not JSON',
          timestamp: new Date().toISOString()
        });
      }
    }
  });
  
  try {
    console.log('📍 Navigating to Conbud LES store page...');
    await page.goto('https://conbud.com/stores/conbud-les', {
      waitUntil: 'networkidle',
      timeout: 60000
    });
    
    console.log('⏳ Waiting for page to load...');
    await page.waitForTimeout(5000);
    
    // Try to find product elements
    console.log('🔎 Looking for product elements...');
    const productSelectors = [
      '[data-testid*="product"]',
      '.product',
      '[class*="product"]',
      '[class*="Product"]',
      '[class*="item"]',
      '[class*="Item"]'
    ];
    
    let foundProducts = false;
    for (const selector of productSelectors) {
      try {
        const elements = await page.$$(selector);
        if (elements.length > 0) {
          console.log(`✅ Found ${elements.length} elements matching: ${selector}`);
          foundProducts = true;
        }
      } catch (e) {
        // Selector didn't match
      }
    }
    
    // Check for categories/navigation
    console.log('\n🗂️  Looking for category navigation...');
    const navSelectors = [
      'nav',
      '[role="navigation"]',
      '[class*="category"]',
      '[class*="Category"]',
      '[class*="menu"]',
      '[class*="Menu"]'
    ];
    
    for (const selector of navSelectors) {
      try {
        const elements = await page.$$(selector);
        if (elements.length > 0) {
          console.log(`✅ Found ${elements.length} navigation elements: ${selector}`);
        }
      } catch (e) {
        // Selector didn't match
      }
    }
    
    // Take screenshot
    console.log('\n📸 Taking screenshot...');
    await page.screenshot({ 
      path: 'phase1-recon/conbud-screenshot.png',
      fullPage: true 
    });
    
    // Get page HTML structure
    const bodyHTML = await page.evaluate(() => {
      // Get a simplified structure of the page
      const root = document.querySelector('#__next');
      if (root) {
        return {
          outerHTML: root.outerHTML.substring(0, 5000), // First 5000 chars
          classList: Array.from(root.querySelectorAll('[class]'))
            .slice(0, 20)
            .map(el => el.className),
          dataAttributes: Array.from(root.querySelectorAll('[data-testid], [data-product], [data-id]'))
            .slice(0, 20)
            .map(el => {
              const attrs = {};
              for (const attr of el.attributes) {
                if (attr.name.startsWith('data-')) {
                  attrs[attr.name] = attr.value;
                }
              }
              return attrs;
            })
        };
      }
      return null;
    });
    
    // Save all findings
    const findings = {
      timestamp: new Date().toISOString(),
      url: 'https://conbud.com/stores/conbud-les',
      totalRequests: requests.length,
      apiRequests: apiRequests.length,
      graphqlQueries: graphqlQueries.length,
      requests: requests.filter(r => r.url.includes('dutchie')),
      apiRequests,
      graphqlQueries,
      responses,
      pageStructure: bodyHTML,
      foundProducts
    };
    
    // Write to file
    fs.writeFileSync(
      'phase1-recon/conbud-api-analysis.json',
      JSON.stringify(findings, null, 2)
    );
    
    console.log('\n✅ Reconnaissance complete!');
    console.log(`   Total requests: ${requests.length}`);
    console.log(`   API requests: ${apiRequests.length}`);
    console.log(`   GraphQL queries: ${graphqlQueries.length}`);
    console.log(`   Responses captured: ${responses.length}`);
    console.log('\n📄 Saved to: phase1-recon/conbud-api-analysis.json');
    console.log('📸 Screenshot: phase1-recon/conbud-screenshot.png');
    
    // Print sample GraphQL query if found
    if (graphqlQueries.length > 0) {
      console.log('\n🔍 Sample GraphQL Query:');
      console.log(JSON.stringify(graphqlQueries[0], null, 2));
    }
    
  } catch (error) {
    console.error('❌ Error during reconnaissance:', error);
  } finally {
    await browser.close();
  }
}

inspectConbud().catch(console.error);
