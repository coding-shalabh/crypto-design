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
        self.filter_logs_collection: Optional[Collection] = None # New collection for filter logs
        self.bot_state_collection: Optional[Collection] = None # New collection for bot state
        self.positions_collection: Optional[Collection] = None # New collection for positions
        self.setup_connection()
    
    def setup_connection(self):
        """Setup MongoDB connection"""
        try:
            self.client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client[Config.MONGODB_DB_NAME]
            self.trades_collection = self.db[Config.MONGODB_COLLECTION_NAME]
            self.filter_logs_collection = self.db["filter_logs"] # Assign new collection
            self.bot_state_collection = self.db["bot_state"] # Assign bot state collection
            self.positions_collection = self.db["positions"] # Assign positions collection
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("MongoDB connected successfully")
            
            # Create indexes for better query performance
            self.trades_collection.create_index([("symbol", 1), ("timestamp", -1)])
            self.trades_collection.create_index([("trade_id", 1)], unique=True)
            self.trades_collection.create_index([("status", 1)])
            self.filter_logs_collection.create_index([("symbol", 1), ("timestamp", -1)]) # Index for filter logs
            self.bot_state_collection.create_index([("user_id", 1)]) # Index for bot state
            self.positions_collection.create_index([("symbol", 1), ("user_id", 1)]) # Index for positions
            
        except Exception as e:
            logger.warning(f" MongoDB not available: {e}")
            logger.info(" Trade logging will be local only (no MongoDB)")
            self.client = None
            self.db = None
            self.trades_collection = None
            self.filter_logs_collection = None
            self.bot_state_collection = None
            self.positions_collection = None

    async def log_trade(self, trade_data: Dict, user_id: int = 28) -> bool:
        """Log trade data to MongoDB"""
        #   FIXED: Check for None instead of bool evaluation
        if self.trades_collection is None:
            logger.info(" MongoDB not available, skipping trade logging")
            return False
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in trade_data:
                trade_data['timestamp'] = datetime.now().isoformat()
            
            # Add trade_id if not present
            if 'trade_id' not in trade_data:
                trade_data['trade_id'] = f"trade_{int(datetime.now().timestamp())}_{trade_data.get('symbol', 'UNKNOWN')}"
            
            #   FIXED: Create a copy to avoid modifying original data
            trade_data_copy = trade_data.copy()
            
            # Add user ID
            trade_data_copy['user_id'] = user_id
            
            # Insert trade record
            result = self.trades_collection.insert_one(trade_data_copy)
            
            #   FIXED: Convert ObjectId to string for logging
            object_id_str = str(result.inserted_id)
            logger.info(f" Trade logged to MongoDB with ID: {object_id_str} for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f" Error logging trade to MongoDB: {e}")
            return False

    async def log_closed_trade(self, symbol: str, position: Dict, close_price: float, 
                              close_value: float, profit_loss: float, entry_details: Dict = None, user_id: int = 28) -> bool:
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
            
            return await self.log_trade(trade_log, user_id)
            
        except Exception as e:
            logger.error(f" Error logging closed trade: {e}")
            return False
    
    async def log_analysis(self, analysis_data: Dict, user_id: int = 28) -> bool:
        """Log analysis data to MongoDB"""
        if self.db is None:
            logger.info(" MongoDB not available, skipping analysis logging")
            return False
        
        try:
            # Create analysis collection if it doesn't exist
            if not hasattr(self, 'analysis_collection'):
                self.analysis_collection = self.db.analysis_logs
            
            # Add timestamp if not present
            if 'timestamp' not in analysis_data:
                analysis_data['timestamp'] = datetime.now().isoformat()
            
            # Add analysis_id if not present
            if 'analysis_id' not in analysis_data:
                analysis_data['analysis_id'] = f"analysis_{int(datetime.now().timestamp())}_{analysis_data.get('symbol', 'UNKNOWN')}"
            
            # Create a copy to avoid modifying original data
            analysis_data_copy = analysis_data.copy()
            
            # Add user ID
            analysis_data_copy['user_id'] = user_id
            
            # Insert analysis record
            result = self.analysis_collection.insert_one(analysis_data_copy)
            
            object_id_str = str(result.inserted_id)
            logger.info(f" Analysis logged to MongoDB with ID: {object_id_str} for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f" Error logging analysis to MongoDB: {e}")
            return False
    
    async def get_recent_trades(self, symbol: str = None, limit: int = 100, user_id: int = 28) -> list:
        """Get recent trades from database"""
        if self.trades_collection is None:
            return []
        
        try:
            query = {'user_id': user_id}
            if symbol:
                query['symbol'] = symbol
            
            cursor = self.trades_collection.find(query).sort('timestamp', -1).limit(limit)
            trades = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for trade in trades:
                if '_id' in trade:
                    trade['_id'] = str(trade['_id'])
            
            return trades
            
        except Exception as e:
            logger.error(f" Error fetching recent trades: {e}")
            return []
    
    async def log_filter_details(self, filter_data: Dict, user_id: int = 28) -> bool:
        """Log detailed filter outcomes and confidence scores to MongoDB"""
        if self.filter_logs_collection is None:
            logger.info("MongoDB not available, skipping filter log logging")
            return False
        
        try:
            if 'timestamp' not in filter_data:
                filter_data['timestamp'] = datetime.now().isoformat()
            
            filter_data_copy = filter_data.copy()
            # Add user ID
            filter_data_copy['user_id'] = user_id
            
            result = self.filter_logs_collection.insert_one(filter_data_copy)
            logger.debug(f"Filter details logged to MongoDB with ID: {result.inserted_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error logging filter details to MongoDB: {e}")
            return False
    
    async def get_recent_filter_logs(self, limit: int = 50, user_id: int = 28) -> list:
        """Get recent filter logs from database"""
        if self.filter_logs_collection is None:
            return []
        
        try:
            cursor = self.filter_logs_collection.find({'user_id': user_id}).sort('timestamp', -1).limit(limit)
            logs = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for log in logs:
                if '_id' in log:
                    log['_id'] = str(log['_id'])
            
            return logs
            
        except Exception as e:
            logger.error(f"Error fetching recent filter logs: {e}")
            return []

    async def save_bot_state(self, bot_state: Dict, user_id: int = 28) -> bool:
        """Save bot state to MongoDB"""
        if self.bot_state_collection is None:
            logger.info("MongoDB not available, skipping bot state save")
            return False
        
        try:
            bot_state_copy = bot_state.copy()
            bot_state_copy['user_id'] = user_id
            bot_state_copy['timestamp'] = datetime.now().isoformat()
            
            # Use upsert to replace existing state
            result = self.bot_state_collection.replace_one(
                {'user_id': user_id},
                bot_state_copy,
                upsert=True
            )
            
            logger.info(f"Bot state saved to MongoDB for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving bot state to MongoDB: {e}")
            return False
    
    async def load_bot_state(self, user_id: int = 28) -> Dict:
        """Load bot state from MongoDB"""
        if self.bot_state_collection is None:
            logger.info("MongoDB not available, returning empty bot state")
            return {}
        
        try:
            result = self.bot_state_collection.find_one({'user_id': user_id})
            if result:
                # Remove MongoDB-specific fields
                if '_id' in result:
                    del result['_id']
                if 'user_id' in result:
                    del result['user_id']
                if 'timestamp' in result:
                    del result['timestamp']
                
                logger.info(f"Bot state loaded from MongoDB for user {user_id}")
                return result
            else:
                logger.info(f"No bot state found in MongoDB for user {user_id}")
                return {}
            
        except Exception as e:
            logger.error(f"Error loading bot state from MongoDB: {e}")
            return {}
    
    async def clear_bot_state(self, user_id: int = 28) -> bool:
        """Clear bot state from MongoDB"""
        if self.bot_state_collection is None:
            logger.info("MongoDB not available, skipping bot state clear")
            return False
        
        try:
            result = self.bot_state_collection.delete_one({'user_id': user_id})
            logger.info(f"Bot state cleared from MongoDB for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing bot state from MongoDB: {e}")
            return False
    
    async def save_positions(self, positions: Dict, user_id: int = 28) -> bool:
        """Save positions to MongoDB"""
        if self.positions_collection is None:
            logger.info("MongoDB not available, skipping positions save")
            return False
        
        try:
            # Clear existing positions for this user
            self.positions_collection.delete_many({'user_id': user_id})
            
            # Insert new positions
            if positions:
                position_docs = []
                for symbol, position in positions.items():
                    position_doc = position.copy()
                    position_doc['user_id'] = user_id
                    position_doc['symbol'] = symbol
                    position_doc['timestamp'] = datetime.now().isoformat()
                    position_docs.append(position_doc)
                
                self.positions_collection.insert_many(position_docs)
                logger.info(f"Saved {len(position_docs)} positions to MongoDB for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving positions to MongoDB: {e}")
            return False
    
    async def load_positions(self, user_id: int = 28) -> Dict:
        """Load positions from MongoDB"""
        if self.positions_collection is None:
            logger.info("MongoDB not available, returning empty positions")
            return {}
        
        try:
            cursor = self.positions_collection.find({'user_id': user_id})
            positions = {}
            
            for doc in cursor:
                symbol = doc.get('symbol')
                if symbol:
                    # Remove MongoDB-specific fields
                    if '_id' in doc:
                        del doc['_id']
                    if 'user_id' in doc:
                        del doc['user_id']
                    if 'timestamp' in doc:
                        del doc['timestamp']
                    
                    positions[symbol] = doc
            
            logger.info(f"Loaded {len(positions)} positions from MongoDB for user {user_id}")
            return positions
            
        except Exception as e:
            logger.error(f"Error loading positions from MongoDB: {e}")
            return {}
    
    async def clear_positions(self, user_id: int = 28) -> bool:
        """Clear positions from MongoDB"""
        if self.positions_collection is None:
            logger.info("MongoDB not available, skipping positions clear")
            return False
        
        try:
            result = self.positions_collection.delete_many({'user_id': user_id})
            logger.info(f"Cleared {result.deleted_count} positions from MongoDB for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing positions from MongoDB: {e}")
            return False
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed") 