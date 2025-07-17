"""
Database operations for the crypto trading bot
"""
import logging
from datetime import datetime
from typing import Dict, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages MongoDB operations for trade logging"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.trades_collection: Optional[Collection] = None
        self.setup_connection()
    
    def setup_connection(self):
        """Setup MongoDB connection"""
        try:
            self.client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client[Config.MONGODB_DB_NAME]
            self.trades_collection = self.db[Config.MONGODB_COLLECTION_NAME]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("MongoDB connected successfully")
            
            # Create indexes for better query performance
            self.trades_collection.create_index([("symbol", 1), ("timestamp", -1)])
            self.trades_collection.create_index([("trade_id", 1)], unique=True)
            self.trades_collection.create_index([("status", 1)])
            
        except Exception as e:
            logger.warning(f" MongoDB not available: {e}")
            logger.info(" Trade logging will be local only (no MongoDB)")
            self.client = None
            self.db = None
            self.trades_collection = None
    
    async def log_trade(self, trade_data: Dict) -> bool:
        """Log trade data to MongoDB"""
        if not self.trades_collection:
            logger.info(" MongoDB not available, skipping trade logging")
            return False
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in trade_data:
                trade_data['timestamp'] = datetime.now().isoformat()
            
            # Add trade_id if not present
            if 'trade_id' not in trade_data:
                trade_data['trade_id'] = f"trade_{int(datetime.now().timestamp())}_{trade_data.get('symbol', 'UNKNOWN')}"
            
            # Insert trade record
            result = self.trades_collection.insert_one(trade_data)
            logger.info(f" Trade logged to MongoDB with ID: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f" Error logging trade to MongoDB: {e}")
            return False
    
    async def log_closed_trade(self, symbol: str, position: Dict, close_price: float, 
                              close_value: float, profit_loss: float, entry_details: Dict = None) -> bool:
        """Log comprehensive trade details when a position is closed"""
        try:
            # Calculate comprehensive trade data
            entry_price = position.get('avg_price', 0)
            entry_value = position.get('amount', 0) * entry_price
            
            # Create comprehensive trade log
            trade_log = {
                'trade_id': f"closed_trade_{int(datetime.now().timestamp())}_{symbol}",
                'symbol': symbol,
                'status': 'closed',
                'position_type': position.get('direction', 'unknown'),
                'entry_details': entry_details or {
                    'price': entry_price,
                    'amount': position.get('amount', 0),
                    'value': entry_value,
                    'timestamp': position.get('timestamp', datetime.now().isoformat())
                },
                'exit_details': {
                    'price': close_price,
                    'value': close_value,
                    'timestamp': datetime.now().isoformat()
                },
                'profit_loss': profit_loss,
                'profit_loss_percent': (profit_loss / entry_value * 100) if entry_value > 0 else 0,
                'duration_seconds': 0,  # Calculate if entry timestamp available
                'timestamp': datetime.now().isoformat()
            }
            
            return await self.log_trade(trade_log)
            
        except Exception as e:
            logger.error(f" Error logging closed trade: {e}")
            return False
    
    async def get_recent_trades(self, symbol: str = None, limit: int = 100) -> list:
        """Get recent trades from database"""
        if not self.trades_collection:
            return []
        
        try:
            query = {}
            if symbol:
                query['symbol'] = symbol
            
            cursor = self.trades_collection.find(query).sort('timestamp', -1).limit(limit)
            return list(cursor)
            
        except Exception as e:
            logger.error(f" Error fetching recent trades: {e}")
            return []
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed") 