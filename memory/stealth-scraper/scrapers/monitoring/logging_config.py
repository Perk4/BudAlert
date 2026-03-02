#!/usr/bin/env python3
"""
Unified Logging Configuration for Stealth Scraper

Provides consistent logging format, aggregation, and rotation
across all scraper components.
"""

import logging
import logging.handlers
import json
import datetime
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record):
        # Base log entry
        log_entry = {
            'timestamp': datetime.datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add any extra fields
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage']:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for console output"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class ScraperLoggerAdapter(logging.LoggerAdapter):
    """Custom adapter that adds scraper-specific context"""
    
    def __init__(self, logger, store_name: str, platform: str = None):
        super().__init__(logger, {'store_name': store_name, 'platform': platform})
    
    def process(self, msg, kwargs):
        # Add store context to every log message
        extra = kwargs.setdefault('extra', {})
        extra.update(self.extra)
        return msg, kwargs


class LoggingConfig:
    """Main logging configuration manager"""
    
    def __init__(self, log_dir: str = None, app_name: str = 'stealth_scraper'):
        self.log_dir = Path(log_dir) if log_dir else Path(__file__).parent / 'logs'
        self.app_name = app_name
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log files
        self.unified_log = self.log_dir / f'{app_name}_unified.log'
        self.error_log = self.log_dir / f'{app_name}_errors.log'
        
        # Configure root logger
        self._configure_logging()
    
    def _configure_logging(self):
        """Configure the root logger and handlers"""
        
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Set root level
        root_logger.setLevel(logging.INFO)
        
        # Unified log file handler (structured JSON)
        unified_handler = logging.handlers.RotatingFileHandler(
            self.unified_log,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        unified_handler.setLevel(logging.INFO)
        unified_handler.setFormatter(StructuredFormatter())
        
        # Error log file handler (human-readable)
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(HumanReadableFormatter())
        
        # Console handler (human-readable, warnings and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(HumanReadableFormatter())
        
        # Add handlers to root logger
        root_logger.addHandler(unified_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)
        
        # Suppress noisy third-party loggers
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name"""
        return logging.getLogger(f'{self.app_name}.{name}')
    
    def get_scraper_logger(self, store_name: str, platform: str = None) -> ScraperLoggerAdapter:
        """Get a scraper-specific logger with context"""
        base_logger = self.get_logger(f'scraper.{store_name}')
        return ScraperLoggerAdapter(base_logger, store_name, platform)
    
    def log_scraper_run(self, store_name: str, success: bool, duration_ms: int, 
                       products_extracted: int = 0, error: str = None, 
                       metadata: Dict[str, Any] = None):
        """Log a scraper run result with structured data"""
        logger = self.get_logger('scraper_runs')
        
        extra = {
            'store_name': store_name,
            'success': success,
            'duration_ms': duration_ms,
            'products_extracted': products_extracted,
            'run_type': 'scraper_run'
        }
        
        if error:
            extra['error'] = error
        
        if metadata:
            extra['metadata'] = metadata
        
        level = logging.INFO if success else logging.ERROR
        message = f"{store_name}: {'SUCCESS' if success else 'FAILED'} in {duration_ms}ms"
        
        if success and products_extracted > 0:
            message += f" - {products_extracted} products"
        
        logger.log(level, message, extra=extra)
    
    def log_health_check(self, store_name: str, overall_status: str, 
                        site_reachable: bool, extraction_successful: bool,
                        latency_ms: int, error: str = None):
        """Log a health check result"""
        logger = self.get_logger('health_checks')
        
        extra = {
            'store_name': store_name,
            'overall_status': overall_status,
            'site_reachable': site_reachable,
            'extraction_successful': extraction_successful,
            'latency_ms': latency_ms,
            'check_type': 'health_check'
        }
        
        if error:
            extra['error'] = error
        
        level_map = {
            'healthy': logging.INFO,
            'warning': logging.WARNING,
            'critical': logging.ERROR,
            'unknown': logging.WARNING
        }
        level = level_map.get(overall_status, logging.INFO)
        
        message = f"{store_name}: Health check {overall_status.upper()}"
        logger.log(level, message, extra=extra)
    
    def log_alert(self, alert_type: str, severity: str, store_name: str, 
                 message: str, details: Dict[str, Any] = None):
        """Log an alert"""
        logger = self.get_logger('alerts')
        
        extra = {
            'alert_type': alert_type,
            'severity': severity,
            'store_name': store_name,
            'event_type': 'alert'
        }
        
        if details:
            extra['alert_details'] = details
        
        level_map = {
            'info': logging.INFO,
            'warning': logging.WARNING,
            'critical': logging.ERROR
        }
        level = level_map.get(severity, logging.WARNING)
        
        logger.log(level, f"ALERT [{severity.upper()}]: {message}", extra=extra)
    
    def setup_daily_log_files(self):
        """Create daily-specific log files for detailed tracking"""
        today = datetime.date.today().isoformat()
        daily_log_dir = self.log_dir / 'daily'
        daily_log_dir.mkdir(exist_ok=True)
        
        # Daily scraper activity log
        daily_file = daily_log_dir / f'scraper_activity_{today}.log'
        daily_handler = logging.FileHandler(daily_file, encoding='utf-8')
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(HumanReadableFormatter())
        
        # Add to scraper loggers
        scraper_logger = logging.getLogger(f'{self.app_name}.scraper_runs')
        scraper_logger.addHandler(daily_handler)
        
        return str(daily_file)
    
    def configure_log_rotation(self):
        """Configure automatic log rotation and cleanup"""
        # This would typically be called by a cron job or similar
        import glob
        import time
        
        # Remove logs older than 30 days
        cutoff_time = time.time() - (30 * 24 * 60 * 60)
        
        for log_file in glob.glob(str(self.log_dir / '*.log*')):
            try:
                if os.path.getmtime(log_file) < cutoff_time:
                    os.remove(log_file)
                    print(f"Removed old log file: {log_file}")
            except OSError:
                pass  # File might be in use
        
        # Compress old log files
        for log_file in glob.glob(str(self.log_dir / '*.log')):
            try:
                if os.path.getmtime(log_file) < cutoff_time:
                    import gzip
                    import shutil
                    
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(f'{log_file}.gz', 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    os.remove(log_file)
                    print(f"Compressed log file: {log_file}")
            except (OSError, ImportError):
                pass


# Global logging instance
_logging_config = None

def get_logging_config(log_dir: str = None) -> LoggingConfig:
    """Get or create the global logging configuration"""
    global _logging_config
    
    if _logging_config is None:
        _logging_config = LoggingConfig(log_dir)
    
    return _logging_config

def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger"""
    return get_logging_config().get_logger(name)

def get_scraper_logger(store_name: str, platform: str = None) -> ScraperLoggerAdapter:
    """Convenience function to get a scraper logger"""
    return get_logging_config().get_scraper_logger(store_name, platform)


def main():
    """CLI interface for logging configuration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stealth Scraper Logging Configuration')
    parser.add_argument('--setup', action='store_true', help='Setup logging configuration')
    parser.add_argument('--rotate', action='store_true', help='Rotate and cleanup old logs')
    parser.add_argument('--test', action='store_true', help='Test logging functionality')
    parser.add_argument('--log-dir', help='Specify log directory')
    
    args = parser.parse_args()
    
    config = LoggingConfig(args.log_dir)
    
    if args.setup:
        daily_log = config.setup_daily_log_files()
        print(f"Logging configured. Daily log: {daily_log}")
        
    elif args.rotate:
        config.configure_log_rotation()
        print("Log rotation and cleanup completed")
        
    elif args.test:
        # Test all logging functionality
        logger = config.get_logger('test')
        scraper_logger = config.get_scraper_logger('test-store', 'Test Platform')
        
        logger.info("Testing unified logging system")
        scraper_logger.info("Testing scraper logger")
        
        config.log_scraper_run(
            store_name='test-store',
            success=True,
            duration_ms=1500,
            products_extracted=25,
            metadata={'test': True}
        )
        
        config.log_health_check(
            store_name='test-store',
            overall_status='healthy',
            site_reachable=True,
            extraction_successful=True,
            latency_ms=2000
        )
        
        config.log_alert(
            alert_type='test_alert',
            severity='info',
            store_name='test-store',
            message='This is a test alert',
            details={'test': True}
        )
        
        print("Test logging completed. Check log files.")
        
    else:
        print("Use --setup, --rotate, or --test")


if __name__ == '__main__':
    main()