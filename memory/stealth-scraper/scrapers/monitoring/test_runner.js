#!/usr/bin/env node

/**
 * Simple Alert Test Runner for Stealth Scraper
 * 
 * Simulates alert scenarios and tests webhook integration
 * Run with: node test_runner.js
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

class AlertTestRunner {
    constructor() {
        this.testResults = [];
        this.testDir = path.join(__dirname, 'test_results');
        
        // Ensure test directory exists
        if (!fs.existsSync(this.testDir)) {
            fs.mkdirSync(this.testDir, { recursive: true });
        }
        
        this.loadTestScenarios();
    }
    
    loadTestScenarios() {
        try {
            const scenariosPath = path.join(__dirname, 'manual_alert_tests.json');
            const data = fs.readFileSync(scenariosPath, 'utf8');
            this.scenarios = JSON.parse(data);
            console.log('✅ Loaded test scenarios');
        } catch (error) {
            console.error('❌ Failed to load test scenarios:', error.message);
            process.exit(1);
        }
    }
    
    async simulateInventoryChanges(scenario) {
        console.log(`\n🧪 Simulating: ${scenario.name}`);
        console.log(`   ${scenario.description}`);
        
        const oldProducts = scenario.test_data?.old_products || [];
        const newProducts = scenario.test_data?.new_products || [];
        
        // Simulate change detection logic
        const changes = this.detectChanges(oldProducts, newProducts);
        
        console.log(`   📋 Detected ${changes.length} changes:`);
        changes.forEach(change => {
            console.log(`      • ${change.type}: ${change.product_name}`);
            if (change.type === 'price_change') {
                console.log(`        Price: $${change.old_price} → $${change.new_price} (${change.price_change >= 0 ? '+' : ''}$${change.price_change.toFixed(2)})`);
            }
        });
        
        return {
            scenario_name: scenario.name,
            changes_detected: changes.length,
            changes: changes,
            success: changes.length > 0
        };
    }
    
    detectChanges(oldProducts, newProducts) {
        const changes = [];
        
        // Create maps for easier comparison
        const oldMap = new Map(oldProducts.map(p => [p.id, p]));
        const newMap = new Map(newProducts.map(p => [p.id, p]));
        
        // Check for price and stock changes
        for (const [id, newProduct] of newMap) {
            const oldProduct = oldMap.get(id);
            
            if (oldProduct) {
                // Price change
                const oldPrice = parseFloat(oldProduct.price);
                const newPrice = parseFloat(newProduct.price);
                const priceDiff = newPrice - oldPrice;
                
                if (Math.abs(priceDiff) >= 0.01) { // Price change threshold
                    changes.push({
                        type: 'price_change',
                        product_id: id,
                        product_name: newProduct.name,
                        old_price: oldPrice,
                        new_price: newPrice,
                        price_change: priceDiff
                    });
                }
                
                // Stock change
                if (oldProduct.in_stock !== newProduct.in_stock) {
                    changes.push({
                        type: newProduct.in_stock ? 'stock_in' : 'stock_out',
                        product_id: id,
                        product_name: newProduct.name,
                        old_stock: oldProduct.in_stock,
                        new_stock: newProduct.in_stock
                    });
                }
            } else {
                // New product
                changes.push({
                    type: 'new_product',
                    product_id: id,
                    product_name: newProduct.name,
                    price: newProduct.price
                });
            }
        }
        
        // Check for removed products
        for (const [id, oldProduct] of oldMap) {
            if (!newMap.has(id)) {
                changes.push({
                    type: 'removed_product',
                    product_id: id,
                    product_name: oldProduct.name,
                    old_price: oldProduct.price
                });
            }
        }
        
        return changes;
    }
    
    async testWebhookIntegration() {
        console.log('\n🕸️ Testing Webhook Integration');
        
        try {
            // Create a test webhook endpoint using webhook.site
            const webhookResponse = await this.createWebhookEndpoint();
            
            if (!webhookResponse.success) {
                console.log('   ❌ Failed to create webhook endpoint');
                return { success: false, error: webhookResponse.error };
            }
            
            const webhookUrl = webhookResponse.url;
            console.log(`   📡 Test webhook URL: ${webhookUrl}`);
            
            // Create test alert payload
            const testAlert = {
                alert_id: `test_${Date.now()}`,
                timestamp: new Date().toISOString(),
                severity: 'critical',
                store_name: 'test_store',
                alert_type: 'consecutive_failures',
                message: 'test_store has 3 consecutive failures',
                details: {
                    consecutive_failures: 3,
                    threshold: 3,
                    platform: 'test'
                }
            };
            
            // Format for Slack
            const slackPayload = this.formatSlackMessage(testAlert);
            
            // Send webhook
            const webhookResult = await this.sendWebhook(webhookUrl, slackPayload);
            
            if (webhookResult.success) {
                console.log('   ✅ Test alert sent to webhook');
                console.log(`   🔍 Check webhook for received payload: ${webhookUrl}`);
                return {
                    success: true,
                    webhook_url: webhookUrl,
                    payload: slackPayload
                };
            } else {
                console.log(`   ❌ Failed to send webhook: ${webhookResult.error}`);
                return { success: false, error: webhookResult.error };
            }
            
        } catch (error) {
            console.log(`   💥 Webhook test error: ${error.message}`);
            return { success: false, error: error.message };
        }
    }
    
    async createWebhookEndpoint() {
        return new Promise((resolve) => {
            const postData = JSON.stringify({});
            
            const options = {
                hostname: 'webhook.site',
                path: '/token',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(postData)
                }
            };
            
            const req = https.request(options, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    try {
                        if (res.statusCode === 201) {
                            const result = JSON.parse(data);
                            resolve({
                                success: true,
                                url: `https://webhook.site/${result.uuid}`,
                                uuid: result.uuid
                            });
                        } else {
                            resolve({ success: false, error: `HTTP ${res.statusCode}` });
                        }
                    } catch (err) {
                        resolve({ success: false, error: err.message });
                    }
                });
            });
            
            req.on('error', (err) => {
                resolve({ success: false, error: err.message });
            });
            
            req.write(postData);
            req.end();
        });
    }
    
    async sendWebhook(url, payload) {
        return new Promise((resolve) => {
            const postData = JSON.stringify(payload);
            const urlObj = new URL(url);
            
            const options = {
                hostname: urlObj.hostname,
                path: urlObj.pathname,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(postData)
                }
            };
            
            const req = https.request(options, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    if (res.statusCode === 200) {
                        resolve({ success: true });
                    } else {
                        resolve({ success: false, error: `HTTP ${res.statusCode}` });
                    }
                });
            });
            
            req.on('error', (err) => {
                resolve({ success: false, error: err.message });
            });
            
            req.write(postData);
            req.end();
        });
    }
    
    formatSlackMessage(alert) {
        const colorMap = {
            'info': '#36a64f',
            'warning': '#ffa500', 
            'critical': '#ff0000'
        };
        
        return {
            attachments: [{
                color: colorMap[alert.severity] || '#999999',
                title: `Stealth Scraper Alert - ${alert.severity.toUpperCase()}`,
                text: alert.message,
                fields: [
                    {
                        title: 'Store',
                        value: alert.store_name,
                        short: true
                    },
                    {
                        title: 'Type',
                        value: alert.alert_type,
                        short: true
                    },
                    {
                        title: 'Time',
                        value: new Date(alert.timestamp).toUTCString(),
                        short: false
                    }
                ],
                footer: 'Stealth Scraper Monitoring',
                ts: Math.floor(new Date(alert.timestamp).getTime() / 1000)
            }]
        };
    }
    
    simulateConsoleAlert(alert) {
        const severityEmoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'critical': '🚨'
        };
        
        const emoji = severityEmoji[alert.severity] || '❗';
        console.log(`${emoji} ${alert.severity.toUpperCase()}: ${alert.message}`);
        
        return { success: true, output: `Console alert displayed` };
    }
    
    testAlertSuppression() {
        console.log('\n🔕 Testing Alert Suppression');
        
        const suppressionTests = [
            {
                name: 'Minor Price Change',
                old_price: 50.00,
                new_price: 50.01,
                should_alert: false
            },
            {
                name: 'Significant Price Change', 
                old_price: 50.00,
                new_price: 40.00,
                should_alert: true
            }
        ];
        
        const results = [];
        
        suppressionTests.forEach(test => {
            const priceDiff = Math.abs(test.new_price - test.old_price);
            const shouldAlert = priceDiff >= 0.01; // Threshold
            const testPassed = shouldAlert === test.should_alert;
            
            console.log(`   ${testPassed ? '✅' : '❌'} ${test.name}: $${test.old_price} → $${test.new_price}`);
            console.log(`      Expected: ${test.should_alert ? 'ALERT' : 'NO ALERT'}, Got: ${shouldAlert ? 'ALERT' : 'NO ALERT'}`);
            
            results.push({
                name: test.name,
                passed: testPassed,
                expected: test.should_alert,
                actual: shouldAlert
            });
        });
        
        return results;
    }
    
    async runAllTests() {
        console.log('🚀 Starting Alert Testing Framework');
        console.log(`   Test directory: ${this.testDir}`);
        
        const startTime = Date.now();
        
        // Test inventory change scenarios
        console.log('\n📋 Testing Inventory Change Scenarios...');
        for (const [key, scenario] of Object.entries(this.scenarios.alert_test_scenarios)) {
            try {
                const result = await this.simulateInventoryChanges(scenario);
                this.testResults.push(result);
            } catch (error) {
                console.log(`   💥 Error in ${scenario.name}: ${error.message}`);
                this.testResults.push({
                    scenario_name: scenario.name,
                    success: false,
                    error: error.message
                });
            }
        }
        
        // Test webhook integration
        const webhookResult = await this.testWebhookIntegration();
        this.testResults.push({
            scenario_name: 'Webhook Integration Test',
            ...webhookResult
        });
        
        // Test alert suppression
        const suppressionResults = this.testAlertSuppression();
        this.testResults.push({
            scenario_name: 'Alert Suppression Test',
            success: suppressionResults.every(r => r.passed),
            suppression_results: suppressionResults
        });
        
        // Test console alerts
        console.log('\n📺 Testing Console Alerts...');
        const testAlert = {
            severity: 'critical',
            message: 'Test console alert output',
            timestamp: new Date().toISOString()
        };
        const consoleResult = this.simulateConsoleAlert(testAlert);
        this.testResults.push({
            scenario_name: 'Console Alert Test',
            ...consoleResult
        });
        
        // Generate summary
        this.generateTestSummary(Date.now() - startTime);
    }
    
    generateTestSummary(duration) {
        console.log('\n' + '='.repeat(60));
        console.log('📊 ALERT TESTING SUMMARY');
        console.log('='.repeat(60));
        
        const totalTests = this.testResults.length;
        const passedTests = this.testResults.filter(r => r.success).length;
        const failedTests = totalTests - passedTests;
        
        console.log(`Total Tests: ${totalTests}`);
        console.log(`Passed: ${passedTests} ✅`);
        console.log(`Failed: ${failedTests} ❌`);
        console.log(`Success Rate: ${((passedTests/totalTests)*100).toFixed(1)}%`);
        console.log(`Duration: ${(duration/1000).toFixed(2)}s`);
        
        if (failedTests > 0) {
            console.log('\n❌ Failed Tests:');
            this.testResults.filter(r => !r.success).forEach(result => {
                console.log(`  • ${result.scenario_name}`);
                if (result.error) {
                    console.log(`    Error: ${result.error}`);
                }
            });
        }
        
        // Save detailed results
        const resultsFile = path.join(this.testDir, `alert_test_results_${Date.now()}.json`);
        const detailedResults = {
            timestamp: new Date().toISOString(),
            duration_ms: duration,
            summary: {
                total_tests: totalTests,
                passed_tests: passedTests,
                failed_tests: failedTests,
                success_rate: (passedTests/totalTests)*100
            },
            results: this.testResults
        };
        
        fs.writeFileSync(resultsFile, JSON.stringify(detailedResults, null, 2));
        console.log(`\n📁 Detailed results saved to: ${resultsFile}`);
        
        return detailedResults;
    }
}

// CLI interface
async function main() {
    const args = process.argv.slice(2);
    const runner = new AlertTestRunner();
    
    if (args.includes('--help') || args.includes('-h')) {
        console.log(`
Alert Testing Framework

Usage: node test_runner.js [options]

Options:
  --webhook     Test webhook integration only
  --suppression Test alert suppression only
  --console     Test console alerts only
  --all         Run all tests (default)
  --help, -h    Show this help
        `);
        process.exit(0);
    }
    
    if (args.includes('--webhook')) {
        await runner.testWebhookIntegration();
    } else if (args.includes('--suppression')) {
        runner.testAlertSuppression();
    } else if (args.includes('--console')) {
        runner.simulateConsoleAlert({
            severity: 'critical',
            message: 'Test console alert',
            timestamp: new Date().toISOString()
        });
    } else {
        await runner.runAllTests();
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = AlertTestRunner;