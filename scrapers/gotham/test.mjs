/**
 * Gotham NYC Scraper Test Script
 * 
 * Tests the scraper against the live site and validates the data
 */

import { GothamScraper } from './scraper.mjs';
import fs from 'fs';

async function test() {
  console.log('🧪 Testing Gotham NYC Scraper\n');
  console.log('━'.repeat(60));
  
  const scraper = new GothamScraper();
  
  try {
    // Run scraper
    console.log('\n📊 Running scraper...\n');
    const products = await scraper.scrape();
    
    console.log('\n━'.repeat(60));
    console.log('\n📈 RESULTS:\n');
    console.log(`   Total products: ${products.length}`);
    
    // Validation checks
    const withPrice = products.filter(p => p.price != null);
    const withName = products.filter(p => p.name);
    const withCategory = products.filter(p => p.category);
    const withBrand = products.filter(p => p.brand);
    const withImage = products.filter(p => p.image);
    const withUrl = products.filter(p => p.url);
    const withThc = products.filter(p => p.thc?.value);
    const inStock = products.filter(p => p.inStock);
    
    console.log(`\n   ✅ With name: ${withName.length} (${(withName.length/products.length*100).toFixed(1)}%)`);
    console.log(`   ✅ With price: ${withPrice.length} (${(withPrice.length/products.length*100).toFixed(1)}%)`);
    console.log(`   ⚠️  With category: ${withCategory.length} (${(withCategory.length/products.length*100).toFixed(1)}%)`);
    console.log(`   ⚠️  With brand: ${withBrand.length} (${(withBrand.length/products.length*100).toFixed(1)}%)`);
    console.log(`   ⚠️  With image: ${withImage.length} (${(withImage.length/products.length*100).toFixed(1)}%)`);
    console.log(`   ⚠️  With URL: ${withUrl.length} (${(withUrl.length/products.length*100).toFixed(1)}%)`);
    console.log(`   ⚠️  With THC data: ${withThc.length} (${(withThc.length/products.length*100).toFixed(1)}%)`);
    console.log(`   ℹ️  In stock: ${inStock.length} (${(inStock.length/products.length*100).toFixed(1)}%)`);
    
    // Category breakdown
    console.log('\n   📊 Category breakdown:');
    const categories = {};
    products.forEach(p => {
      categories[p.category] = (categories[p.category] || 0) + 1;
    });
    Object.entries(categories)
      .sort((a, b) => b[1] - a[1])
      .forEach(([cat, count]) => {
        console.log(`      ${cat}: ${count}`);
      });
    
    // Sample products
    console.log('\n   📦 Sample products:\n');
    products.slice(0, 3).forEach((p, i) => {
      console.log(`   ${i + 1}. ${p.name}`);
      console.log(`      Price: ${p.priceFormatted || p.price || 'N/A'}`);
      console.log(`      Category: ${p.category || 'N/A'}`);
      console.log(`      Brand: ${p.brand || 'N/A'}`);
      if (p.thc?.value) console.log(`      THC: ${p.thc.formatted}`);
      if (p.cbd?.value) console.log(`      CBD: ${p.cbd.formatted}`);
      console.log(`      Stock: ${p.inStock ? 'In Stock' : 'Out of Stock'}`);
      console.log();
    });
    
    // Save to file
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `gotham-products-${timestamp}.json`;
    
    fs.writeFileSync(
      filename,
      JSON.stringify(products, null, 2)
    );
    
    console.log(`   💾 Saved to: ${filename}`);
    
    // Data quality score
    const requiredFields = withName.length + withPrice.length;
    const optionalFields = withCategory.length + withBrand.length + withImage.length + withUrl.length + withThc.length;
    const maxRequired = products.length * 2;
    const maxOptional = products.length * 5;
    
    const qualityScore = ((requiredFields / maxRequired) * 0.6 + (optionalFields / maxOptional) * 0.4) * 100;
    
    console.log(`\n   📊 Data Quality Score: ${qualityScore.toFixed(1)}%`);
    
    if (qualityScore >= 80) {
      console.log('   ✅ Excellent data quality!');
    } else if (qualityScore >= 60) {
      console.log('   ⚠️  Good data quality, some fields missing');
    } else {
      console.log('   ❌ Low data quality, many fields missing');
    }
    
    console.log('\n━'.repeat(60));
    console.log('\n✅ Test completed successfully!\n');
    
    return products;
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error('\nStack trace:');
    console.error(error.stack);
    process.exit(1);
  }
}

// Run test
test()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
