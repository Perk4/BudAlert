/**
 * Quick test for Housing Works scraper
 * Tests basic functionality without full scrape
 */

const { chromium } = require('playwright');

const CONFIG = {
  baseUrl: 'https://hwcannabis.co',
  menuUrl: 'https://hwcannabis.co/menu/broadway/',
  timeout: 30000
};

async function quickTest() {
  console.log('🧪 Housing Works Scraper Quick Test\n');
  
  let browser, page;
  const results = {
    siteAccessible: false,
    productsFound: false,
    productCount: 0,
    sampleProducts: [],
    apiEndpoints: [],
    errors: []
  };

  try {
    // Launch browser
    console.log('1️⃣  Launching browser...');
    browser = await chromium.launch({ 
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    });
    
    page = await context.newPage();
    console.log('   ✅ Browser launched\n');

    // Track API requests
    console.log('2️⃣  Setting up network tracking...');
    page.on('request', request => {
      const url = request.url();
      if (url.includes('api') || url.includes('graphql') || url.includes('products')) {
        results.apiEndpoints.push({
          method: request.method(),
          url: url.substring(0, 100)
        });
      }
    });
    console.log('   ✅ Network tracking enabled\n');

    // Navigate to menu
    console.log('3️⃣  Navigating to menu page...');
    console.log(`   URL: ${CONFIG.menuUrl}`);
    
    await page.goto(CONFIG.menuUrl, {
      waitUntil: 'networkidle',
      timeout: CONFIG.timeout
    });
    
    results.siteAccessible = true;
    console.log('   ✅ Site loaded successfully\n');

    // Wait for page to settle
    console.log('4️⃣  Waiting for content to render...');
    await page.waitForTimeout(5000);
    console.log('   ✅ Content settled\n');

    // Try to find products
    console.log('5️⃣  Looking for products...');
    const selectors = [
      '.product',
      '.product-item',
      '.menu-item',
      '[data-product]',
      '.product-card'
    ];

    for (const selector of selectors) {
      try {
        const count = await page.locator(selector).count();
        if (count > 0) {
          console.log(`   ✅ Found ${count} products using selector: ${selector}`);
          results.productsFound = true;
          results.productCount = count;
          
          // Extract first 3 products as samples
          const products = await page.locator(selector).all();
          for (let i = 0; i < Math.min(3, products.length); i++) {
            try {
              const name = await products[i].locator('.product-name, h3, .name').first().textContent();
              const price = await products[i].locator('.price, .product-price').first().textContent();
              
              results.sampleProducts.push({
                name: name?.trim(),
                price: price?.trim()
              });
            } catch (e) {
              // Skip if can't extract
            }
          }
          
          break;
        }
      } catch (e) {
        // Try next selector
      }
    }

    if (!results.productsFound) {
      console.log('   ⚠️  No products found with standard selectors');
      
      // Save page HTML for debugging
      const html = await page.content();
      require('fs').writeFileSync('debug-page.html', html);
      console.log('   📄 Saved page HTML to debug-page.html');
    }
    
    console.log('');

    // Check for categories
    console.log('6️⃣  Looking for category navigation...');
    const categorySelectors = [
      '.category-menu a',
      '.menu-nav a',
      'nav a'
    ];
    
    for (const selector of categorySelectors) {
      try {
        const count = await page.locator(selector).count();
        if (count > 0) {
          console.log(`   ✅ Found ${count} navigation links using: ${selector}`);
          break;
        }
      } catch (e) {
        // Try next
      }
    }
    console.log('');

  } catch (error) {
    results.errors.push(error.message);
    console.error('❌ Test failed:', error.message);
  } finally {
    if (browser) {
      await browser.close();
      console.log('🔒 Browser closed\n');
    }
  }

  // Print results
  console.log('📊 TEST RESULTS\n');
  console.log('═'.repeat(50));
  console.log(`Site Accessible:     ${results.siteAccessible ? '✅ YES' : '❌ NO'}`);
  console.log(`Products Found:      ${results.productsFound ? '✅ YES' : '❌ NO'}`);
  console.log(`Product Count:       ${results.productCount}`);
  console.log(`API Endpoints:       ${results.apiEndpoints.length}`);
  console.log(`Errors:              ${results.errors.length}`);
  console.log('═'.repeat(50));
  
  if (results.sampleProducts.length > 0) {
    console.log('\n📦 Sample Products:\n');
    results.sampleProducts.forEach((p, i) => {
      console.log(`${i + 1}. ${p.name}`);
      console.log(`   Price: ${p.price}\n`);
    });
  }
  
  if (results.apiEndpoints.length > 0) {
    console.log('📡 API Endpoints Detected:\n');
    const unique = [...new Set(results.apiEndpoints.map(e => `${e.method} ${e.url}`))];
    unique.slice(0, 5).forEach(endpoint => {
      console.log(`   ${endpoint}`);
    });
    if (unique.length > 5) {
      console.log(`   ... and ${unique.length - 5} more`);
    }
  }
  
  if (results.errors.length > 0) {
    console.log('\n❌ Errors:\n');
    results.errors.forEach(err => console.log(`   - ${err}`));
  }
  
  console.log('\n' + '═'.repeat(50));
  
  // Save results
  require('fs').writeFileSync(
    'test-results.json',
    JSON.stringify(results, null, 2)
  );
  console.log('💾 Full results saved to test-results.json\n');
  
  return results;
}

// Run test
quickTest()
  .then(results => {
    if (results.siteAccessible && results.productsFound) {
      console.log('✅ TEST PASSED - Scraper should work!');
      process.exit(0);
    } else {
      console.log('⚠️  TEST INCOMPLETE - Manual review needed');
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('❌ TEST FAILED:', error);
    process.exit(1);
  });
