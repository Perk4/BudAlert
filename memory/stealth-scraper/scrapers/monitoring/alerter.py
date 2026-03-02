#!/usr/bin/env python3
"""
Alerting System for Stealth Scraper

Monitors health check results and dashboard metrics to send alerts when:
1. Store extraction failure (3 consecutive)
2. Success rate drops below 80%
3. No successful extraction in 6 hours
4. Sudden product count drop (>50%)

Supports multiple alert channels:
- Console/log output
- Webhook (Slack, Discord, etc.)
- Email (via sendgrid/ses stub)
"""

import json
import os
import datetime
import asyncio
import aiohttp
import smtplib
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import sqlite3

from dashboard import DashboardAggregator
from metrics import MetricsCalculator


@dataclass
class Alert:
    """Represents a single alert"""
    alert_id: str
    timestamp: datetime.datetime
    severity: str  # 'info', 'warning', 'critical'
    store_name: str
    alert_type: str
    message: str
    details: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime.datetime] = None


@dataclass
class AlertRule:
    """Configuration for an alert rule"""
    rule_id: str
    name: str
    severity: str
    enabled: bool
    conditions: Dict[str, Any]
    cooldown_minutes: int = 60  # Minimum time between same alerts


class AlertManager:
    """Main alerting system"""
    
    def __init__(self, scrapers_dir: str = None):
        self.scrapers_dir = scrapers_dir or os.path.join(os.path.dirname(__file__), '..')
        self.monitoring_dir = os.path.join(self.scrapers_dir, 'monitoring')
        self.dashboard = DashboardAggregator(scrapers_dir)
        self.metrics = MetricsCalculator(scrapers_dir)
        
        # Alert configuration
        self.config = self._load_alert_config()
        
        # Alert database
        self.alerts_db_path = os.path.join(self.monitoring_dir, 'alerts.db')
        self._init_alerts_database()
        
        # Setup logging
        self.setup_logging()
        
        # Define alert rules
        self.alert_rules = self._define_alert_rules()
    
    def setup_logging(self):
        """Configure logging for alerts"""
        self.logger = logging.getLogger('alerter')
        self.logger.setLevel(logging.INFO)
        
        # Create handler if not exists
        if not self.logger.handlers:
            log_dir = os.path.join(self.monitoring_dir, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, f'alerts_{datetime.date.today().isoformat()}.log')
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _load_alert_config(self) -> Dict[str, Any]:
        """Load alerting configuration from file or use defaults"""
        config_path = os.path.join(self.monitoring_dir, 'alert_config.json')
        
        default_config = {
            'channels': {
                'console': {'enabled': True},
                'webhook': {
                    'enabled': False,
                    'url': '',
                    'format': 'slack'  # 'slack', 'discord', 'generic'
                },
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'from_email': '',
                    'to_emails': []
                }
            },
            'thresholds': {
                'consecutive_failure_limit': 3,
                'success_rate_warning': 80,
                'success_rate_critical': 50,
                'max_hours_without_success': 6,
                'product_count_drop_percentage': 50
            },
            'cooldowns': {
                'consecutive_failures': 30,  # minutes
                'success_rate': 60,
                'no_extraction': 120,
                'product_drop': 60
            }
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                        elif isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                if subkey not in loaded_config[key]:
                                    loaded_config[key][subkey] = subvalue
                    return loaded_config
            except Exception as e:
                self.logger.error(f"Failed to load alert config: {e}, using defaults")
        
        # Save default config
        os.makedirs(self.monitoring_dir, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _init_alerts_database(self):
        """Initialize alerts database"""
        with sqlite3.connect(self.alerts_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME NOT NULL,
                    severity TEXT NOT NULL,
                    store_name TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    resolved BOOLEAN DEFAULT 0,
                    resolution_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_alert_store_type 
                ON alerts(store_name, alert_type, timestamp)
            ''')
    
    def _define_alert_rules(self) -> List[AlertRule]:
        """Define the alert rules based on requirements"""
        thresholds = self.config['thresholds']
        cooldowns = self.config['cooldowns']
        
        return [
            AlertRule(
                rule_id='consecutive_failures',
                name='Consecutive Extraction Failures',
                severity='critical',
                enabled=True,
                conditions={
                    'consecutive_failures': thresholds['consecutive_failure_limit']
                },
                cooldown_minutes=cooldowns['consecutive_failures']
            ),
            AlertRule(
                rule_id='low_success_rate',
                name='Low Success Rate',
                severity='warning',
                enabled=True,
                conditions={
                    'success_rate_threshold': thresholds['success_rate_warning']
                },
                cooldown_minutes=cooldowns['success_rate']
            ),
            AlertRule(
                rule_id='critical_success_rate',
                name='Critical Success Rate',
                severity='critical',
                enabled=True,
                conditions={
                    'success_rate_threshold': thresholds['success_rate_critical']
                },
                cooldown_minutes=cooldowns['success_rate']
            ),
            AlertRule(
                rule_id='no_recent_extractions',
                name='No Recent Successful Extractions',
                severity='critical',
                enabled=True,
                conditions={
                    'max_hours_without_success': thresholds['max_hours_without_success']
                },
                cooldown_minutes=cooldowns['no_extraction']
            ),
            AlertRule(
                rule_id='product_count_drop',
                name='Sudden Product Count Drop',
                severity='warning',
                enabled=True,
                conditions={
                    'drop_percentage': thresholds['product_count_drop_percentage']
                },
                cooldown_minutes=cooldowns['product_drop']
            )
        ]
    
    def check_consecutive_failures(self, store_name: str) -> Optional[Alert]:
        """Check for consecutive failure alert condition"""
        rule = next((r for r in self.alert_rules if r.rule_id == 'consecutive_failures'), None)
        if not rule or not rule.enabled:
            return None
            
        status = self.dashboard.get_store_status(store_name)
        
        if status.consecutive_failures >= rule.conditions['consecutive_failures']:
            # Check cooldown
            if self._is_in_cooldown(store_name, 'consecutive_failures', rule.cooldown_minutes):
                return None
                
            alert = Alert(
                alert_id=f"{store_name}_consecutive_failures_{int(datetime.datetime.now().timestamp())}",
                timestamp=datetime.datetime.now(),
                severity=rule.severity,
                store_name=store_name,
                alert_type='consecutive_failures',
                message=f"{store_name} has {status.consecutive_failures} consecutive failures",
                details={
                    'consecutive_failures': status.consecutive_failures,
                    'threshold': rule.conditions['consecutive_failures'],
                    'last_error': status.last_error,
                    'platform': status.platform
                }
            )
            return alert
        
        return None
    
    def check_success_rate(self, store_name: str) -> Optional[Alert]:
        """Check for success rate alert conditions"""
        metrics = self.metrics.calculate_store_metrics(store_name)
        
        # Check critical level first
        critical_rule = next((r for r in self.alert_rules if r.rule_id == 'critical_success_rate'), None)
        if critical_rule and critical_rule.enabled:
            if metrics.success_rate_24h < critical_rule.conditions['success_rate_threshold']:
                if not self._is_in_cooldown(store_name, 'critical_success_rate', critical_rule.cooldown_minutes):
                    return Alert(
                        alert_id=f"{store_name}_critical_success_rate_{int(datetime.datetime.now().timestamp())}",
                        timestamp=datetime.datetime.now(),
                        severity=critical_rule.severity,
                        store_name=store_name,
                        alert_type='critical_success_rate',
                        message=f"{store_name} has critically low success rate: {metrics.success_rate_24h:.1f}%",
                        details={
                            'success_rate_24h': metrics.success_rate_24h,
                            'threshold': critical_rule.conditions['success_rate_threshold'],
                            'platform': metrics.platform
                        }
                    )
        
        # Check warning level
        warning_rule = next((r for r in self.alert_rules if r.rule_id == 'low_success_rate'), None)
        if warning_rule and warning_rule.enabled:
            if metrics.success_rate_24h < warning_rule.conditions['success_rate_threshold']:
                if not self._is_in_cooldown(store_name, 'low_success_rate', warning_rule.cooldown_minutes):
                    return Alert(
                        alert_id=f"{store_name}_low_success_rate_{int(datetime.datetime.now().timestamp())}",
                        timestamp=datetime.datetime.now(),
                        severity=warning_rule.severity,
                        store_name=store_name,
                        alert_type='low_success_rate',
                        message=f"{store_name} has low success rate: {metrics.success_rate_24h:.1f}%",
                        details={
                            'success_rate_24h': metrics.success_rate_24h,
                            'threshold': warning_rule.conditions['success_rate_threshold'],
                            'platform': metrics.platform
                        }
                    )
        
        return None
    
    def check_no_recent_extractions(self, store_name: str) -> Optional[Alert]:
        """Check for no recent successful extractions"""
        rule = next((r for r in self.alert_rules if r.rule_id == 'no_recent_extractions'), None)
        if not rule or not rule.enabled:
            return None
            
        status = self.dashboard.get_store_status(store_name)
        
        if status.last_successful_run:
            hours_since_success = (datetime.datetime.now() - status.last_successful_run).total_seconds() / 3600
            
            if hours_since_success > rule.conditions['max_hours_without_success']:
                if not self._is_in_cooldown(store_name, 'no_recent_extractions', rule.cooldown_minutes):
                    return Alert(
                        alert_id=f"{store_name}_no_recent_extractions_{int(datetime.datetime.now().timestamp())}",
                        timestamp=datetime.datetime.now(),
                        severity=rule.severity,
                        store_name=store_name,
                        alert_type='no_recent_extractions',
                        message=f"{store_name} has no successful extractions for {hours_since_success:.1f} hours",
                        details={
                            'hours_since_success': hours_since_success,
                            'threshold_hours': rule.conditions['max_hours_without_success'],
                            'last_successful_run': status.last_successful_run.isoformat() if status.last_successful_run else None,
                            'platform': status.platform
                        }
                    )
        
        return None
    
    def check_product_count_drop(self, store_name: str) -> Optional[Alert]:
        """Check for sudden product count drops"""
        rule = next((r for r in self.alert_rules if r.rule_id == 'product_count_drop'), None)
        if not rule or not rule.enabled:
            return None
            
        # Get current and historical product counts
        metrics = self.metrics.calculate_store_metrics(store_name)
        current_products = metrics.products_extracted_24h
        
        if current_products == 0:
            return None  # This will be caught by other rules
        
        # Get yesterday's count for comparison
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        yesterday_metrics = self.metrics.calculate_store_metrics(store_name, yesterday)
        previous_products = yesterday_metrics.products_extracted_24h
        
        if previous_products > 0:
            drop_percentage = ((previous_products - current_products) / previous_products) * 100
            
            if drop_percentage > rule.conditions['drop_percentage']:
                if not self._is_in_cooldown(store_name, 'product_count_drop', rule.cooldown_minutes):
                    return Alert(
                        alert_id=f"{store_name}_product_count_drop_{int(datetime.datetime.now().timestamp())}",
                        timestamp=datetime.datetime.now(),
                        severity=rule.severity,
                        store_name=store_name,
                        alert_type='product_count_drop',
                        message=f"{store_name} product count dropped {drop_percentage:.1f}%: {previous_products} → {current_products}",
                        details={
                            'current_products': current_products,
                            'previous_products': previous_products,
                            'drop_percentage': drop_percentage,
                            'threshold_percentage': rule.conditions['drop_percentage'],
                            'platform': metrics.platform
                        }
                    )
        
        return None
    
    def _is_in_cooldown(self, store_name: str, alert_type: str, cooldown_minutes: int) -> bool:
        """Check if we're in cooldown period for this alert type"""
        cooldown_cutoff = datetime.datetime.now() - datetime.timedelta(minutes=cooldown_minutes)
        
        with sqlite3.connect(self.alerts_db_path) as conn:
            result = conn.execute('''
                SELECT COUNT(*) FROM alerts 
                WHERE store_name = ? AND alert_type = ? AND timestamp > ?
            ''', (store_name, alert_type, cooldown_cutoff.isoformat())).fetchone()
            
            return result[0] > 0 if result else False
    
    def save_alert(self, alert: Alert):
        """Save alert to database"""
        with sqlite3.connect(self.alerts_db_path) as conn:
            conn.execute('''
                INSERT INTO alerts 
                (alert_id, timestamp, severity, store_name, alert_type, message, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id,
                alert.timestamp.isoformat(),
                alert.severity,
                alert.store_name,
                alert.alert_type,
                alert.message,
                json.dumps(alert.details)
            ))
    
    async def send_alert(self, alert: Alert):
        """Send alert through all configured channels"""
        self.logger.info(f"Sending alert: {alert.message}")
        
        # Console/log output
        if self.config['channels']['console']['enabled']:
            self.send_console_alert(alert)
        
        # Webhook
        if self.config['channels']['webhook']['enabled']:
            await self.send_webhook_alert(alert)
        
        # Email
        if self.config['channels']['email']['enabled']:
            await self.send_email_alert(alert)
    
    def send_console_alert(self, alert: Alert):
        """Send alert to console/logs"""
        severity_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'critical': '🚨'
        }
        
        emoji = severity_emoji.get(alert.severity, '❗')
        print(f"{emoji} {alert.severity.upper()}: {alert.message}")
        self.logger.warning(f"{alert.severity.upper()}: {alert.message} | Details: {alert.details}")
    
    async def send_webhook_alert(self, alert: Alert):
        """Send alert via webhook (Slack, Discord, etc.)"""
        webhook_config = self.config['channels']['webhook']
        
        if not webhook_config.get('url'):
            return
        
        try:
            # Format message based on webhook type
            if webhook_config['format'] == 'slack':
                payload = self._format_slack_message(alert)
            elif webhook_config['format'] == 'discord':
                payload = self._format_discord_message(alert)
            else:
                payload = {'text': alert.message}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_config['url'],
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"Webhook alert sent successfully")
                    else:
                        self.logger.error(f"Webhook alert failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
    
    def _format_slack_message(self, alert: Alert) -> Dict[str, Any]:
        """Format alert for Slack"""
        color_map = {
            'info': '#36a64f',
            'warning': '#ffa500',
            'critical': '#ff0000'
        }
        
        return {
            "attachments": [{
                "color": color_map.get(alert.severity, '#999999'),
                "title": f"Stealth Scraper Alert - {alert.severity.upper()}",
                "text": alert.message,
                "fields": [
                    {
                        "title": "Store",
                        "value": alert.store_name,
                        "short": True
                    },
                    {
                        "title": "Type",
                        "value": alert.alert_type,
                        "short": True
                    },
                    {
                        "title": "Time",
                        "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                        "short": False
                    }
                ],
                "footer": "Stealth Scraper Monitoring",
                "ts": int(alert.timestamp.timestamp())
            }]
        }
    
    def _format_discord_message(self, alert: Alert) -> Dict[str, Any]:
        """Format alert for Discord"""
        color_map = {
            'info': 0x36a64f,
            'warning': 0xffa500,
            'critical': 0xff0000
        }
        
        return {
            "embeds": [{
                "title": f"Stealth Scraper Alert",
                "description": alert.message,
                "color": color_map.get(alert.severity, 0x999999),
                "fields": [
                    {
                        "name": "Store",
                        "value": alert.store_name,
                        "inline": True
                    },
                    {
                        "name": "Severity",
                        "value": alert.severity.upper(),
                        "inline": True
                    },
                    {
                        "name": "Type",
                        "value": alert.alert_type,
                        "inline": True
                    }
                ],
                "timestamp": alert.timestamp.isoformat()
            }]
        }
    
    async def send_email_alert(self, alert: Alert):
        """Send alert via email"""
        email_config = self.config['channels']['email']
        
        if not all([email_config.get('username'), email_config.get('password'), 
                   email_config.get('from_email'), email_config.get('to_emails')]):
            return
        
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = ', '.join(email_config['to_emails'])
            msg['Subject'] = f"Stealth Scraper Alert - {alert.severity.upper()}: {alert.store_name}"
            
            body = f"""
Stealth Scraper Alert

Store: {alert.store_name}
Severity: {alert.severity.upper()}
Type: {alert.alert_type}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message: {alert.message}

Details: {json.dumps(alert.details, indent=2)}

--
Stealth Scraper Monitoring System
            """.strip()
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Email alert sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    async def check_all_stores(self) -> List[Alert]:
        """Check all stores for alert conditions"""
        alerts = []
        
        # Get all active stores
        active_stores = [name for name, config in self.dashboard.stores_config.items() 
                        if config.get('active', False)]
        
        for store_name in active_stores:
            # Check all alert conditions for this store
            potential_alerts = [
                self.check_consecutive_failures(store_name),
                self.check_success_rate(store_name),
                self.check_no_recent_extractions(store_name),
                self.check_product_count_drop(store_name)
            ]
            
            # Filter out None values
            store_alerts = [alert for alert in potential_alerts if alert is not None]
            alerts.extend(store_alerts)
        
        return alerts
    
    async def run_alert_check_cycle(self) -> List[Alert]:
        """Run complete alert checking cycle"""
        self.logger.info("Starting alert check cycle")
        
        # Check for alerts
        alerts = await self.check_all_stores()
        
        # Process and send alerts
        for alert in alerts:
            # Save to database
            self.save_alert(alert)
            
            # Send through all channels
            await self.send_alert(alert)
        
        if alerts:
            self.logger.info(f"Processed {len(alerts)} alerts")
        else:
            self.logger.info("No alerts triggered")
        
        return alerts


async def main():
    """CLI interface for alerter"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stealth Scraper Alerter')
    parser.add_argument('--check', action='store_true', help='Run alert check cycle')
    parser.add_argument('--test', help='Send test alert for store')
    parser.add_argument('--config', action='store_true', help='Show alert configuration')
    
    args = parser.parse_args()
    
    alerter = AlertManager()
    
    if args.config:
        print(json.dumps(alerter.config, indent=2))
    elif args.test:
        # Send test alert
        test_alert = Alert(
            alert_id=f"test_{int(datetime.datetime.now().timestamp())}",
            timestamp=datetime.datetime.now(),
            severity='info',
            store_name=args.test,
            alert_type='test',
            message=f"Test alert for {args.test}",
            details={'test': True}
        )
        await alerter.send_alert(test_alert)
        print(f"Test alert sent for {args.test}")
    elif args.check:
        alerts = await alerter.run_alert_check_cycle()
        print(f"Alert check completed. {len(alerts)} alerts triggered.")
    else:
        print("Use --check to run alert check, --test <store> to send test alert, or --config to show configuration")


if __name__ == '__main__':
    asyncio.run(main())