"""
IRCTC Tatkal Automation Bot - Configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-super-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1', 'yes']
    TESTING = os.environ.get('TESTING', 'False').lower() in ['true', '1', 'yes']
    
    # Server Configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///irctc_bot.db')
    
    # Encryption Configuration
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'your-encryption-key-32-characters!')
    
    # IRCTC Configuration
    IRCTC_BASE_URL = os.environ.get('IRCTC_BASE_URL', 'https://www.irctc.co.in')
    IRCTC_LOGIN_URL = f"{IRCTC_BASE_URL}/nget/train-search"
    BROWSER_TIMEOUT = int(os.environ.get('BROWSER_TIMEOUT', 300))  # 5 minutes
    PAGE_LOAD_TIMEOUT = int(os.environ.get('PAGE_LOAD_TIMEOUT', 30))  # 30 seconds
    
    # Playwright Configuration
    PLAYWRIGHT_HEADLESS = os.environ.get('PLAYWRIGHT_HEADLESS', 'True').lower() in ['true', '1', 'yes']
    PLAYWRIGHT_SLOW_MO = int(os.environ.get('PLAYWRIGHT_SLOW_MO', 100))  # Slow down by 100ms
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    
    # File Paths
    CONFIG_DIR = os.environ.get('CONFIG_DIR', 'config')
    LOGS_DIR = os.environ.get('LOGS_DIR', 'logs')
    TEMP_DIR = os.environ.get('TEMP_DIR', 'temp')
    
    # Security Configuration
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hour
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 3))
    
    # Timing Configuration
    TATKAL_AC_TIME = os.environ.get('TATKAL_AC_TIME', '10:00')
    TATKAL_NON_AC_TIME = os.environ.get('TATKAL_NON_AC_TIME', '11:00')
    NTP_SERVER = os.environ.get('NTP_SERVER', 'pool.ntp.org')
    
    # Performance Configuration
    MAX_CONCURRENT_BOOKINGS = int(os.environ.get('MAX_CONCURRENT_BOOKINGS', 1))
    REQUEST_DELAY = float(os.environ.get('REQUEST_DELAY', 0.5))  # 500ms
    RETRY_ATTEMPTS = int(os.environ.get('RETRY_ATTEMPTS', 3))
    
    # Email Configuration (Optional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # SMS Configuration (Optional)
    SMS_API_KEY = os.environ.get('SMS_API_KEY')
    SMS_API_URL = os.environ.get('SMS_API_URL')
    
    # Cloud Configuration
    AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')  # Mumbai region
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    # Monitoring Configuration
    ENABLE_METRICS = os.environ.get('ENABLE_METRICS', 'True').lower() in ['true', '1', 'yes']
    METRICS_PORT = int(os.environ.get('METRICS_PORT', 9090))
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create required directories
        os.makedirs(Config.CONFIG_DIR, exist_ok=True)
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        os.makedirs(Config.TEMP_DIR, exist_ok=True)
        
        # Set Flask configuration
        app.config['SECRET_KEY'] = Config.SECRET_KEY
        app.config['DEBUG'] = Config.DEBUG
        
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    PLAYWRIGHT_HEADLESS = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    PLAYWRIGHT_HEADLESS = True
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False
    DATABASE_URL = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}