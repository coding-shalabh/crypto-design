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
    
    # Add these optimized settings to your existing Config class in backend/config.py

    # 🔧 FIXED: WebSocket Server Optimization Settings
    WEBSOCKET_SETTINGS = {
        'ping_interval': 20,        # Send ping every 20 seconds
        'ping_timeout': 10,         # Wait 10 seconds for pong response
        'close_timeout': 10,        # Wait 10 seconds for close handshake
        'max_size': 2**20,          # 1MB max message size
        'max_queue': 32,            # Max queue size for incoming messages
        'compression': None,        # Disable compression for better performance
        'max_connections': 50,      # Maximum concurrent connections
        'connection_timeout': 10,   # Connection handshake timeout
    }
    
    # 🔧 FIXED: Background Task Settings
    TASK_SETTINGS = {
        'market_data_interval': 30,     # Update market data every 30 seconds
        'price_broadcast_interval': 5,  # Broadcast prices every 5 seconds
        'connection_monitor_interval': 30,  # Monitor connections every 30 seconds
        'health_check_interval': 60,    # Health check every minute
        'heartbeat_interval': 30,       # Send heartbeat every 30 seconds
        'max_missed_heartbeats': 3,     # Max missed heartbeats before disconnect
    }
    
    # 🔧 FIXED: Rate Limiting Settings
    RATE_LIMITS = {
        'messages_per_second': 10,      # Max messages per second per client
        'messages_per_minute': 600,     # Max messages per minute per client
        'broadcast_throttle': 5,        # Min seconds between broadcasts
        'api_call_throttle': 1,         # Min seconds between API calls
    }
    
    # 🔧 FIXED: Memory Management Settings
    MEMORY_SETTINGS = {
        'max_trade_history': 100,       # Max trades in memory
        'max_analysis_cache': 50,       # Max cached analyses
        'max_log_entries': 1000,        # Max log entries in memory
        'cleanup_interval': 300,        # Cleanup every 5 minutes
    }
    
    # 🔧 FIXED: Error Recovery Settings
    ERROR_RECOVERY = {
        'max_reconnect_attempts': 10,   # Max reconnection attempts
        'base_reconnect_delay': 1000,   # Base delay in milliseconds
        'max_reconnect_delay': 30000,   # Max delay in milliseconds
        'task_restart_delay': 5,        # Delay before restarting failed tasks
        'error_threshold': 5,           # Max errors before circuit breaker
    }
    
    @classmethod
    def get_websocket_settings(cls) -> Dict:
        """Get WebSocket server settings"""
        return cls.WEBSOCKET_SETTINGS.copy()
    
    @classmethod
    def get_task_settings(cls) -> Dict:
        """Get background task settings"""
        return cls.TASK_SETTINGS.copy()
    
    @classmethod
    def get_rate_limits(cls) -> Dict:
        """Get rate limiting settings"""
        return cls.RATE_LIMITS.copy()
    
    @classmethod
    def get_memory_settings(cls) -> Dict:
        """Get memory management settings"""
        return cls.MEMORY_SETTINGS.copy()
    
    @classmethod
    def get_error_recovery_settings(cls) -> Dict:
        """Get error recovery settings"""
        return cls.ERROR_RECOVERY.copy()