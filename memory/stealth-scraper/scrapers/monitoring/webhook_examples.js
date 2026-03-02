#!/usr/bin/env node

/**
 * Webhook Integration Examples for Stealth Scraper Alerts
 * 
 * This file demonstrates how to integrate alerts with popular platforms:
 * - Slack
 * - Discord 
 * - Microsoft Teams
 * - Custom webhook endpoints
 */

const https = require('https');

class WebhookIntegrations {
    
    /**
     * Send alert to Slack webhook
     */
    static async sendSlackAlert(webhookUrl, alert) {
        const payload = {
            attachments: [{
                color: this.getSeverityColor(alert.severity),
                title: `🚨 Stealth Scraper Alert - ${alert.severity.toUpperCase()}`,
                text: alert.message,
                fields: [
                    {
                        title: 'Store',
                        value: alert.store_name,
                        short: true
                    },
                    {
                        title: 'Alert Type',
                        value: alert.alert_type.replace('_', ' '),
                        short: true
                    },
                    {
                        title: 'Time', 
                        value: new Date(alert.timestamp).toLocaleString(),
                        short: false
                    }
                ],
                footer: 'Stealth Scraper Monitoring System',
                footer_icon: 'https://raw.githubusercontent.com/twemoji/twemoji/master/assets/72x72/1f916.png',
                ts: Math.floor(new Date(alert.timestamp).getTime() / 1000)
            }]
        };

        // Add additional fields based on alert type
        if (alert.details) {
            if (alert.alert_type === 'price_change') {
                payload.attachments[0].fields.push({
                    title: 'Price Change',
                    value: `$${alert.details.old_price} → $${alert.details.new_price} (${alert.details.price_change >= 0 ? '+' : ''}$${alert.details.price_change})`,
                    short: false
                });
            } else if (alert.alert_type === 'consecutive_failures') {
                payload.attachments[0].fields.push({
                    title: 'Consecutive Failures',
                    value: `${alert.details.consecutive_failures}/${alert.details.threshold}`,
                    short: true
                });
            }
        }

        return await this.sendWebhook(webhookUrl, payload);
    }

    /**
     * Send alert to Discord webhook
     */
    static async sendDiscordAlert(webhookUrl, alert) {
        const payload = {
            embeds: [{
                title: '🚨 Stealth Scraper Alert',
                description: alert.message,
                color: this.getSeverityColorDiscord(alert.severity),
                fields: [
                    {
                        name: '🏪 Store',
                        value: alert.store_name,
                        inline: true
                    },
                    {
                        name: '⚠️ Severity',
                        value: alert.severity.toUpperCase(),
                        inline: true
                    },
                    {
                        name: '📊 Type',
                        value: alert.alert_type.replace('_', ' '),
                        inline: true
                    }
                ],
                timestamp: alert.timestamp,
                footer: {
                    text: 'Stealth Scraper Monitoring',
                    icon_url: 'https://raw.githubusercontent.com/twemoji/twemoji/master/assets/72x72/1f916.png'
                }
            }]
        };

        // Add alert-specific fields
        if (alert.details) {
            if (alert.alert_type === 'price_change') {
                payload.embeds[0].fields.push({
                    name: '💰 Price Change',
                    value: `$${alert.details.old_price} → $${alert.details.new_price}`,
                    inline: false
                });
            } else if (alert.alert_type === 'stock_out') {
                payload.embeds[0].fields.push({
                    name: '📦 Stock Status',
                    value: '❌ Out of Stock',
                    inline: true
                });
            }
        }

        return await this.sendWebhook(webhookUrl, payload);
    }

    /**
     * Send alert to Microsoft Teams webhook
     */
    static async sendTeamsAlert(webhookUrl, alert) {
        const payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            summary: `Stealth Scraper Alert: ${alert.message}`,
            themeColor: this.getSeverityColor(alert.severity).replace('#', ''),
            title: `🚨 Stealth Scraper Alert - ${alert.severity.toUpperCase()}`,
            text: alert.message,
            sections: [{
                facts: [
                    {
                        name: "Store:",
                        value: alert.store_name
                    },
                    {
                        name: "Alert Type:",
                        value: alert.alert_type.replace('_', ' ')
                    },
                    {
                        name: "Time:",
                        value: new Date(alert.timestamp).toLocaleString()
                    }
                ]
            }],
            potentialAction: [{
                "@type": "OpenUri",
                name: "View Dashboard",
                targets: [{
                    os: "default",
                    uri: "http://your-dashboard-url.com"
                }]
            }]
        };

        return await this.sendWebhook(webhookUrl, payload);
    }

    /**
     * Generic webhook sender
     */
    static async sendWebhook(url, payload) {
        return new Promise((resolve, reject) => {
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
                        resolve({ success: true, response: data });
                    } else {
                        reject(new Error(`HTTP ${res.statusCode}: ${data}`));
                    }
                });
            });

            req.on('error', reject);
            req.write(postData);
            req.end();
        });
    }

    /**
     * Get color for alert severity (Slack format)
     */
    static getSeverityColor(severity) {
        const colors = {
            'info': '#36a64f',      // Green
            'warning': '#ffa500',   // Orange  
            'critical': '#ff0000'   // Red
        };
        return colors[severity] || '#999999';
    }

    /**
     * Get color for alert severity (Discord format - decimal)
     */
    static getSeverityColorDiscord(severity) {
        const colors = {
            'info': 0x36a64f,      // Green
            'warning': 0xffa500,   // Orange
            'critical': 0xff0000   // Red
        };
        return colors[severity] || 0x999999;
    }
}

// Example usage and testing
async function demonstrateIntegrations() {
    console.log('🔗 Webhook Integration Examples\n');

    // Sample alert data
    const sampleAlert = {
        alert_id: 'demo_alert_123',
        timestamp: new Date().toISOString(),
        severity: 'critical',
        store_name: 'dispensary_example',
        alert_type: 'price_change',
        message: 'Blue Dream 3.5g price dropped from $50 to $40',
        details: {
            old_price: 50.0,
            new_price: 40.0,
            price_change: -10.0,
            product_name: 'Blue Dream 3.5g'
        }
    };

    console.log('📋 Sample Alert Data:');
    console.log(JSON.stringify(sampleAlert, null, 2));

    console.log('\n📤 Generated Webhook Payloads:\n');

    // Demonstrate Slack payload
    console.log('1️⃣ SLACK PAYLOAD:');
    const slackPayload = {
        attachments: [{
            color: WebhookIntegrations.getSeverityColor(sampleAlert.severity),
            title: `🚨 Stealth Scraper Alert - ${sampleAlert.severity.toUpperCase()}`,
            text: sampleAlert.message,
            fields: [
                { title: 'Store', value: sampleAlert.store_name, short: true },
                { title: 'Alert Type', value: sampleAlert.alert_type.replace('_', ' '), short: true },
                { title: 'Price Change', value: `$${sampleAlert.details.old_price} → $${sampleAlert.details.new_price}`, short: false }
            ],
            footer: 'Stealth Scraper Monitoring System',
            ts: Math.floor(new Date(sampleAlert.timestamp).getTime() / 1000)
        }]
    };
    console.log(JSON.stringify(slackPayload, null, 2));

    console.log('\n2️⃣ DISCORD PAYLOAD:');
    const discordPayload = {
        embeds: [{
            title: '🚨 Stealth Scraper Alert',
            description: sampleAlert.message,
            color: WebhookIntegrations.getSeverityColorDiscord(sampleAlert.severity),
            fields: [
                { name: '🏪 Store', value: sampleAlert.store_name, inline: true },
                { name: '⚠️ Severity', value: sampleAlert.severity.toUpperCase(), inline: true },
                { name: '💰 Price Change', value: `$${sampleAlert.details.old_price} → $${sampleAlert.details.new_price}`, inline: false }
            ],
            timestamp: sampleAlert.timestamp,
            footer: { text: 'Stealth Scraper Monitoring' }
        }]
    };
    console.log(JSON.stringify(discordPayload, null, 2));

    console.log('\n📖 SETUP INSTRUCTIONS:\n');
    
    console.log('🔧 SLACK SETUP:');
    console.log('1. Go to https://api.slack.com/apps');
    console.log('2. Create new app → Incoming Webhooks');
    console.log('3. Activate incoming webhooks → Add New Webhook');
    console.log('4. Select channel → Copy webhook URL');
    console.log('5. Update alert_config.json:');
    console.log(`   "webhook": {
     "enabled": true,
     "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
     "format": "slack"
   }`);

    console.log('\n🔧 DISCORD SETUP:');
    console.log('1. Go to Discord channel → Settings → Integrations');
    console.log('2. Create Webhook → Copy webhook URL');
    console.log('3. Update alert_config.json:');
    console.log(`   "webhook": {
     "enabled": true,
     "url": "https://discord.com/api/webhooks/123456789/your-webhook-token",
     "format": "discord"
   }`);

    console.log('\n🧪 TEST WEBHOOK:');
    console.log('node webhook_examples.js --test-webhook https://your-webhook-url-here');
}

// CLI interface for testing
async function main() {
    const args = process.argv.slice(2);
    
    if (args.includes('--help') || args.includes('-h')) {
        console.log(`
Webhook Integration Examples

Usage: 
  node webhook_examples.js                    Show payload examples
  node webhook_examples.js --test-webhook URL Test webhook URL
  node webhook_examples.js --help             Show this help

Examples:
  node webhook_examples.js --test-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
  node webhook_examples.js --test-webhook https://discord.com/api/webhooks/123/abc
        `);
        return;
    }

    const testWebhookIndex = args.findIndex(arg => arg === '--test-webhook');
    if (testWebhookIndex !== -1 && args[testWebhookIndex + 1]) {
        const webhookUrl = args[testWebhookIndex + 1];
        console.log(`🧪 Testing webhook: ${webhookUrl}`);
        
        const testAlert = {
            alert_id: `test_${Date.now()}`,
            timestamp: new Date().toISOString(),
            severity: 'warning',
            store_name: 'test_store',
            alert_type: 'test_webhook',
            message: 'This is a test alert from webhook_examples.js',
            details: { test: true }
        };

        try {
            let result;
            if (webhookUrl.includes('slack.com')) {
                result = await WebhookIntegrations.sendSlackAlert(webhookUrl, testAlert);
            } else if (webhookUrl.includes('discord.com')) {
                result = await WebhookIntegrations.sendDiscordAlert(webhookUrl, testAlert);
            } else {
                result = await WebhookIntegrations.sendWebhook(webhookUrl, testAlert);
            }
            
            console.log('✅ Webhook test successful!');
            console.log(`Response: ${result.response}`);
        } catch (error) {
            console.log(`❌ Webhook test failed: ${error.message}`);
        }
    } else {
        await demonstrateIntegrations();
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = WebhookIntegrations;