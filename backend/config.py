"""
Configuration settings for the crypto trading bot backend
"""
import os
from dotenv import load_dotenv
from typing import Dict, List

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration for the trading bot"""
    
    # Server Configuration
    HOST = "localhost"
    PORT = 8765
    
    # Trading Configuration
    PAPER_BALANCE = 100000.0  # Starting balance
    TARGET_PAIRS = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'BNBUSDT', 'SOLUSDT']
    
    # AI Analysis Configuration
    ANALYSIS_INTERVAL = 60  # 1 minute between analyses
    HIGH_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence score
    OPPORTUNITY_COOLDOWN_DURATION = 900  # 15 minutes in seconds
    TRADE_REVERSAL_THRESHOLD = 0.02  # 2% price movement
    
    # News and API Configuration
    GROK_NEWS_INTERVAL = 1800  # 30 minutes for Grok internet search
    CRYPTOPANIC_NEWS_INTERVAL = 60  # 1 minute for CryptoPanic news
    GENERAL_API_INTERVAL = 60  # 1 minute for other API requests
    
    # Trade Acceptance System
    TRADE_WAIT_TIME = 1800  # 30 minutes in seconds
    
    # Bot Configuration
    DEFAULT_BOT_CONFIG = {
        'max_trades_per_day': 10,
        'trade_amount_usdt': 50,
        'profit_target_usd': 2,
        'stop_loss_usd': 1,
        'trailing_enabled': True,
        'trailing_trigger_usd': 1,
        'trailing_distance_usd': 0.5,
        'trade_interval_secs': 60,
        'max_concurrent_trades': 3,
        'cooldown_secs': 300,
        'allowed_pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
        'ai_confidence_threshold': 0.5,
        'run_time_minutes': 180,
        'test_mode': False,
        'risk_per_trade_percent': 1.0,
        'slippage_tolerance_percent': 0.1,
        'signal_sources': ['gpt', 'claude'],
        'manual_approval_mode': False
    }
    
    # API Keys
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    CRYPTOPANIC_API_KEY = os.getenv('CRYPTOPANIC_API_KEY')
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    MONGODB_DB_NAME = 'crypto_trading'
    MONGODB_COLLECTION_NAME = 'trades'
    
    # Logging Configuration
    LOG_LEVEL = "INFO"
    
    @classmethod
    def get_bot_config(cls) -> Dict:
        """Get bot configuration with environment overrides"""
        config = cls.DEFAULT_BOT_CONFIG.copy()
        
        # Allow environment variable overrides
        if os.getenv('BOT_CONFIDENCE_THRESHOLD'):
            config['ai_confidence_threshold'] = float(os.getenv('BOT_CONFIDENCE_THRESHOLD'))
        
        if os.getenv('BOT_TRADE_AMOUNT'):
            config['trade_amount_usdt'] = float(os.getenv('BOT_TRADE_AMOUNT'))
        
        return config 