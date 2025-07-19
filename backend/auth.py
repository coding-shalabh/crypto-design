"""
Authentication system for crypto trading platform
"""
import hashlib
import jwt
import time
import secrets
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

from database import DatabaseManager

logger = logging.getLogger(__name__)

class AuthManager:
    """Handle user authentication and session management"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.secret_key = secrets.token_urlsafe(32)  # In production, use environment variable
        self.token_expiry_hours = 24
        
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return salt + pwd_hash.hex()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt = password_hash[:32]
            stored_hash = password_hash[32:]
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return pwd_hash.hex() == stored_hash
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def generate_token(self, user_id: str) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user_id if valid"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload.get('user_id')
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    async def register_user(self, username: str, email: str, password: str) -> Dict:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = await self.db.find_user_by_username(username)
            if existing_user:
                return {'success': False, 'message': 'Username already exists'}
            
            existing_email = await self.db.find_user_by_email(email)
            if existing_email:
                return {'success': False, 'message': 'Email already registered'}
            
            # Create new user
            user_data = {
                'username': username,
                'email': email,
                'password_hash': self.hash_password(password),
                'created_at': datetime.utcnow(),
                'portfolio_balance': 100000.0,  # Starting balance
                'total_pnl': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'is_active': True,
                'last_login': None
            }
            
            user_id = await self.db.create_user(user_data)
            if user_id:
                token = self.generate_token(str(user_id))
                return {
                    'success': True,
                    'message': 'User registered successfully',
                    'token': token,
                    'user': {
                        'id': str(user_id),
                        'username': username,
                        'email': email,
                        'portfolio_balance': user_data['portfolio_balance']
                    }
                }
            else:
                return {'success': False, 'message': 'Failed to create user'}
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {'success': False, 'message': 'Registration failed'}
    
    async def login_user(self, username: str, password: str) -> Dict:
        """Authenticate user login"""
        try:
            user = await self.db.find_user_by_username(username)
            if not user:
                return {'success': False, 'message': 'Invalid username or password'}
            
            if not user.get('is_active', True):
                return {'success': False, 'message': 'Account is deactivated'}
            
            if not self.verify_password(password, user['password_hash']):
                return {'success': False, 'message': 'Invalid username or password'}
            
            # Update last login
            await self.db.update_user_last_login(user['_id'])
            
            token = self.generate_token(str(user['_id']))
            return {
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': str(user['_id']),
                    'username': user['username'],
                    'email': user['email'],
                    'portfolio_balance': user.get('portfolio_balance', 100000.0),
                    'total_pnl': user.get('total_pnl', 0.0),
                    'total_trades': user.get('total_trades', 0),
                    'winning_trades': user.get('winning_trades', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {'success': False, 'message': 'Login failed'}
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile data"""
        try:
            user = await self.db.find_user_by_id(user_id)
            if user:
                return {
                    'id': str(user['_id']),
                    'username': user['username'],
                    'email': user['email'],
                    'portfolio_balance': user.get('portfolio_balance', 100000.0),
                    'total_pnl': user.get('total_pnl', 0.0),
                    'total_trades': user.get('total_trades', 0),
                    'winning_trades': user.get('winning_trades', 0),
                    'created_at': user.get('created_at'),
                    'last_login': user.get('last_login')
                }
            return None
        except Exception as e:
            logger.error(f"Get profile error: {e}")
            return None
    
    async def update_user_balance(self, user_id: str, new_balance: float) -> bool:
        """Update user's portfolio balance"""
        try:
            return await self.db.update_user_balance(user_id, new_balance)
        except Exception as e:
            logger.error(f"Update balance error: {e}")
            return False
    
    async def update_user_trading_stats(self, user_id: str, pnl_change: float, is_winning_trade: bool) -> bool:
        """Update user's trading statistics"""
        try:
            return await self.db.update_user_trading_stats(user_id, pnl_change, is_winning_trade)
        except Exception as e:
            logger.error(f"Update trading stats error: {e}")
            return False