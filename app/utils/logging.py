"""
IRCTC Tatkal Automation Bot - Logging Utilities
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
import json

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset color
    }
    
    def format(self, record):
        # Add color to the log level
        if hasattr(record, 'levelname'):
            level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{level_color}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
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
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)

def setup_logger(name, log_file=None, level=logging.INFO, console_output=True, 
                 json_format=False, max_bytes=10485760, backup_count=5):
    """
    Set up a logger with file and console handlers
    
    Args:
        name (str): Logger name
        log_file (str): Path to log file (optional)
        level: Logging level
        console_output (bool): Whether to output to console
        json_format (bool): Whether to use JSON formatting
        max_bytes (int): Maximum file size before rotation
        backup_count (int): Number of backup files to keep
        
    Returns:
        logging.Logger: Configured logger
    """
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create formatters
    if json_format:
        formatter = JSONFormatter()
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # File handler with rotation
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger

def setup_application_logging(config):
    """
    Set up application-wide logging configuration
    
    Args:
        config: Application configuration object
    """
    
    # Create logs directory
    logs_dir = Path(config.LOGS_DIR)
    logs_dir.mkdir(exist_ok=True)
    
    # Set up main application logger
    app_logger = setup_logger(
        'irctc_app',
        log_file=logs_dir / 'app.log',
        level=getattr(logging, config.LOG_LEVEL.upper()),
        json_format=config.ENVIRONMENT == 'production'
    )
    
    # Set up bot-specific logger
    bot_logger = setup_logger(
        'irctc_bot',
        log_file=logs_dir / 'bot.log',
        level=getattr(logging, config.LOG_LEVEL.upper()),
        json_format=config.ENVIRONMENT == 'production'
    )
    
    # Set up error logger
    error_logger = setup_logger(
        'errors',
        log_file=logs_dir / 'errors.log',
        level=logging.ERROR,
        console_output=False,
        json_format=True
    )
    
    # Set up performance logger
    perf_logger = setup_logger(
        'performance',
        log_file=logs_dir / 'performance.log',
        level=logging.INFO,
        console_output=False,
        json_format=True
    )
    
    return {
        'app': app_logger,
        'bot': bot_logger,
        'errors': error_logger,
        'performance': perf_logger
    }

class PerformanceLogger:
    """Context manager for logging performance metrics"""
    
    def __init__(self, operation_name, logger=None):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger('performance')
        self.start_time = None
        
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting operation: {self.operation_name}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        status = "completed" if exc_type is None else "failed"
        
        self.logger.info(
            f"Operation {status}: {self.operation_name}",
            extra={
                'operation': self.operation_name,
                'duration_seconds': duration,
                'status': status,
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
        )

class BookingLogger:
    """Specialized logger for booking operations"""
    
    def __init__(self, booking_id, logger=None):
        self.booking_id = booking_id
        self.logger = logger or logging.getLogger('booking')
        self.start_time = datetime.now()
        
    def log_step(self, step_name, status="in_progress", details=None):
        """Log a booking step"""
        self.logger.info(
            f"Booking {self.booking_id} - {step_name}: {status}",
            extra={
                'booking_id': self.booking_id,
                'step': step_name,
                'status': status,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
        )
        
    def log_captcha_request(self, captcha_type):
        """Log captcha request"""
        self.log_step(
            'captcha_request',
            status='waiting_for_user',
            details={'captcha_type': captcha_type}
        )
        
    def log_otp_request(self):
        """Log OTP request"""
        self.log_step(
            'otp_request',
            status='waiting_for_user'
        )
        
    def log_payment_redirect(self, gateway):
        """Log payment gateway redirect"""
        self.log_step(
            'payment_redirect',
            status='redirected',
            details={'gateway': gateway}
        )
        
    def log_booking_result(self, status, pnr=None, error=None):
        """Log final booking result"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        details = {
            'total_duration_seconds': duration,
            'pnr': pnr,
            'error': error
        }
        
        self.log_step(
            'booking_complete',
            status=status,
            details=details
        )

def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        # Log function entry
        logger.debug(f"Entering function: {func.__name__}")
        
        try:
            # Call the function
            result = func(*args, **kwargs)
            
            # Log successful exit
            logger.debug(f"Exiting function: {func.__name__}")
            
            return result
            
        except Exception as e:
            # Log exception
            logger.error(
                f"Exception in function {func.__name__}: {str(e)}",
                exc_info=True
            )
            raise
            
    return wrapper

def log_system_info():
    """Log system information at startup"""
    import platform
    import psutil
    
    logger = logging.getLogger('system')
    
    system_info = {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'disk_free_gb': round(psutil.disk_usage('/').free / (1024**3), 2)
    }
    
    logger.info("System information", extra=system_info)

def cleanup_old_logs(log_dir, days_to_keep=30):
    """Clean up log files older than specified days"""
    log_path = Path(log_dir)
    cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
    
    logger = logging.getLogger('maintenance')
    
    for log_file in log_path.glob('*.log*'):
        if log_file.stat().st_mtime < cutoff_date:
            try:
                log_file.unlink()
                logger.info(f"Deleted old log file: {log_file}")
            except Exception as e:
                logger.error(f"Failed to delete log file {log_file}: {e}")

# Example usage
if __name__ == "__main__":
    # Test the logging setup
    logger = setup_logger('test_logger', 'logs/test.log')
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test performance logging
    with PerformanceLogger('test_operation', logger):
        import time
        time.sleep(1)  # Simulate some work
        
    print("Logging test completed!")