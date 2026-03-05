#!/usr/bin/env node

import fs from 'fs/promises';
import axios from 'axios';
import { JSDOM } from 'jsdom';

// Rate limiter
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Common menu URL patterns
const MENU_PATTERNS = [
  '/menu',
  '/shop',
  '/products',
  '/order',
  '/order-online',
  '/store',
  '/cannabis',
];

// Menu provider patterns
const PROVIDER_PATTERNS = {
  dutchie: ['dutchie.com', 'dutchie'],
  jane: ['iheartjane.com', 'jane.com'],
  blaze: ['blaze.me', 'blaze'],
  weedmaps: ['weedmaps.com'],
  leafly: ['leafly.com'],
  meadow: ['getmeadow.com', 'meadow'],
  treez: ['treez.io'],
};

async function fetchHTML(url, timeout = 10000) {
  try {
    const response = await axios.get(url, {
      timeout,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      },
      maxRedirects: 5,
    });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to fetch ${url}: ${error.message}`);
  }
}

function extractMenuURLs(html, baseUrl) {
  const dom = new JSDOM(html);
  const document = dom.window.document;
  const links = Array.from(document.querySelectorAll('a[href]'));
  
  const menuURLs = new Set();
  
  // Search for links containing menu keywords
  links.forEach(link => {
    const href = link.getAttribute('href');
    const text = link.textContent.toLowerCase();
    
    if (!href) return;
    
    // Keywords to look for
    const menuKeywords = ['menu', 'shop', 'order', 'products', 'store', 'buy'];
    const hasMenuKeyword = menuKeywords.some(keyword => 
      href.toLowerCase().includes(keyword) || text.includes(keyword)
    );
    
    if (hasMenuKeyword) {
      try {
        const fullUrl = new URL(href, baseUrl).toString();
        menuURLs.add(fullUrl);
      } catch (e) {
        // Invalid URL, skip
      }
    }
  });
  
  return Array.from(menuURLs);
}

function detectProvider(html, url) {
  const htmlStr = typeof html === 'string' ? html : String(html || '');
  const lowerHTML = htmlStr.toLowerCase();
  const lowerURL = url.toLowerCase();
  
  for (const [provider, patterns] of Object.entries(PROVIDER_PATTERNS)) {
    for (const pattern of patterns) {
      if (lowerHTML.includes(pattern) || lowerURL.includes(pattern)) {
        return provider;
      }
    }
  }
  
  return 'unknown';
}

async function discoverMenuURL(dispensary) {
  const result = {
    entity_name: dispensary.entity_name,
    website: dispensary.website,
    menuUrl: null,
    menuProvider: null,
    menuValidated: false,
    discoveryMethod: null,
    notes: '',
  };
  
  if (!dispensary.website) {
    result.notes = 'No website provided';
    return result;
  }
  
  try {
    const baseUrl = dispensary.website;
    
    // Step 1: Try common menu paths
    for (const path of MENU_PATTERNS) {
      try {
        const menuUrl = new URL(path, baseUrl).toString();
        const response = await axios.head(menuUrl, {
          timeout: 5000,
          maxRedirects: 5,
          validateStatus: (status) => status < 400,
        });
        
        if (response.status < 400) {
          result.menuUrl = menuUrl;
          result.menuValidated = true;
          result.discoveryMethod = 'common_path';
          result.notes = `Found via ${path}`;
          
          // Fetch the page to detect provider
          const html = await fetchHTML(menuUrl);
          result.menuProvider = detectProvider(html, menuUrl);
          return result;
        }
      } catch (e) {
        // Path doesn't exist, continue
      }
      
      await sleep(500); // Rate limit
    }
    
    // Step 2: Fetch homepage and scan for menu links
    const html = await fetchHTML(baseUrl);
    const menuURLs = extractMenuURLs(html, baseUrl);
    
    if (menuURLs.length > 0) {
      // Pick the most likely menu URL (prioritize shorter, simpler paths)
      const sortedURLs = menuURLs.sort((a, b) => a.length - b.length);
      result.menuUrl = sortedURLs[0];
      result.discoveryMethod = 'link_scan';
      result.menuProvider = detectProvider(html, result.menuUrl);
      result.notes = `Found ${menuURLs.length} potential menu links`;
      
      // Validate the link
      try {
        await axios.head(result.menuUrl, { timeout: 5000, maxRedirects: 5 });
        result.menuValidated = true;
      } catch (e) {
        result.notes += '; validation failed';
      }
    } else {
      // Detect provider from homepage
      result.menuProvider = detectProvider(html, baseUrl);
      result.notes = 'No menu links found on homepage';
    }
    
  } catch (error) {
    result.notes = `Error: ${error.message}`;
  }
  
  return result;
}

async function processDispensaries(dispensaries, outputPath) {
  const results = [];
  let processed = 0;
  
  for (const dispensary of dispensaries) {
    console.log(`[${processed + 1}/${dispensaries.length}] Processing ${dispensary.entity_name}...`);
    
    const result = await discoverMenuURL(dispensary);
    results.push(result);
    processed++;
    
    // Progress update every 10 stores
    if (processed % 10 === 0) {
      console.log(`Progress: ${processed}/${dispensaries.length} (${Math.round(processed/dispensaries.length*100)}%)`);
    }
    
    // Rate limit: 1 request per second
    await sleep(1000);
  }
  
  // Save results
  await fs.writeFile(outputPath, JSON.stringify(results, null, 2));
  
  // Print stats
  const found = results.filter(r => r.menuUrl).length;
  const validated = results.filter(r => r.menuValidated).length;
  
  console.log('\n=== STATS ===');
  console.log(`Total processed: ${results.length}`);
  console.log(`Menu URLs found: ${found} (${Math.round(found/results.length*100)}%)`);
  console.log(`Validated: ${validated} (${Math.round(validated/results.length*100)}%)`);
  console.log(`Output saved to: ${outputPath}`);
  
  return results;
}

// CLI usage
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const args = process.argv.slice(2);
  
  if (args.length < 2) {
    console.log('Usage: ./discover-menus.mjs <input.json> <output.json>');
    process.exit(1);
  }
  
  const [inputPath, outputPath] = args;
  
  const dispensaries = JSON.parse(await fs.readFile(inputPath, 'utf-8'));
  await processDispensaries(dispensaries, outputPath);
}

export { discoverMenuURL, processDispensaries };
