# Crypto Trading Bot Backend

A modular, scalable backend for the crypto trading bot with AI-powered analysis and automated trading capabilities.

## Architecture

The backend is organized into modular components for better maintainability and scalability:

### Core Modules

- **`config.py`** - Centralized configuration management
- **`database.py`** - MongoDB operations and trade logging
- **`market_data.py`** - Market data collection and caching
- **`news_analysis.py`** - News fetching and sentiment analysis
- **`ai_analysis.py`** - AI-powered trading analysis using multiple LLM models
- **`technical_indicators.py`** - Technical analysis indicators
- **`trading_bot.py`** - Automated trading bot logic
- **`trade_execution.py`** - Paper trading execution and position management
- **`websocket_server.py`** - Main WebSocket server orchestrating all components
- **`main.py`** - Application entry point

## Features

### AI Analysis Pipeline
- **Multi-Model Analysis**: Uses Grok, Claude, and GPT for comprehensive analysis
- **Sentiment Analysis**: Real-time market sentiment evaluation
- **Technical Analysis**: RSI, MACD, Bollinger Bands, and more
- **Confidence Scoring**: Risk-adjusted trading recommendations

### Trading Bot
- **Automated Execution**: AI-driven trade execution
- **Risk Management**: Stop-loss, take-profit, and trailing stops
- **Position Sizing**: Dynamic position sizing based on risk parameters
- **Cooldown Management**: Prevents overtrading with intelligent cooldowns

### Market Data
- **Real-time Prices**: Live price feeds from Binance API
- **Candlestick Data**: Historical data for technical analysis
- **Caching**: Efficient data caching to reduce API calls

### Paper Trading
- **Position Tracking**: Real-time position management
- **Trade History**: Comprehensive trade logging
- **Balance Management**: Paper trading balance tracking

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**:
   Create a `.env` file with your API keys:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key
   CRYPTOPANIC_API_KEY=your_cryptopanic_api_key
   MONGODB_URI=mongodb://localhost:27017/
   ```

3. **Run the Server**:
   ```bash
   python main.py
   ```

## Configuration

All configuration is centralized in `config.py`:

```python
class Config:
    # Server settings
    HOST = "localhost"
    PORT = 8765
    
    # Trading settings
    PAPER_BALANCE = 100000.0
    TARGET_PAIRS = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'BNBUSDT', 'SOLUSDT']
    
    # AI Analysis settings
    ANALYSIS_INTERVAL = 60
    HIGH_CONFIDENCE_THRESHOLD = 0.5
    
    # Bot settings
    DEFAULT_BOT_CONFIG = {
        'max_trades_per_day': 10,
        'trade_amount_usdt': 50,
        'ai_confidence_threshold': 0.1,
        # ... more settings
    }
```

## WebSocket API

The server communicates with the frontend via WebSocket messages:

### Client Messages
- `start_analysis` - Start AI analysis
- `stop_analysis` - Stop AI analysis
- `start_bot` - Start trading bot
- `stop_bot` - Stop trading bot
- `execute_trade` - Execute manual trade
- `close_position` - Close position
- `get_positions` - Get current positions
- `get_balance` - Get current balance

### Server Messages
- `price_update` - Real-time price updates
- `position_update` - Position changes
- `balance_update` - Balance changes
- `bot_trade_executed` - Bot trade execution
- `trade_executed` - Manual trade execution
- `analysis_status` - Analysis status updates

## Module Dependencies

```
websocket_server.py
├── config.py
├── database.py
├── market_data.py
├── news_analysis.py
├── ai_analysis.py
│   └── technical_indicators.py
├── trading_bot.py
└── trade_execution.py
    └── database.py
```

## Error Handling

Each module includes comprehensive error handling:
- API rate limiting
- Network timeouts
- Database connection failures
- Invalid data handling
- Graceful degradation

## Logging

Structured logging throughout the application:
- Console output for development
- File logging for production
- Different log levels (DEBUG, INFO, WARNING, ERROR)
- Emoji indicators for quick visual scanning

## Performance

- **Async/Await**: Non-blocking I/O operations
- **Caching**: Intelligent data caching
- **Rate Limiting**: API call optimization
- **Connection Pooling**: Efficient database connections

## Security

- **Environment Variables**: Secure API key management
- **Input Validation**: All inputs validated
- **Error Sanitization**: No sensitive data in error messages
- **Connection Limits**: WebSocket connection management

## Monitoring

- **Health Checks**: Server status monitoring
- **Performance Metrics**: Trade execution times
- **Error Tracking**: Comprehensive error logging
- **Bot Statistics**: Win rate, profit/loss tracking

## Development

### Adding New Features
1. Create new module in appropriate directory
2. Update imports in `websocket_server.py`
3. Add WebSocket message handlers
4. Update configuration if needed
5. Add tests and documentation

### Testing
```bash
# Run individual module tests
python -m pytest tests/test_market_data.py

# Run all tests
python -m pytest tests/
```

## Deployment

### Production Setup
1. Use production MongoDB instance
2. Set up proper logging
3. Configure environment variables
4. Set up monitoring and alerts
5. Use process manager (PM2, systemd)

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## Troubleshooting

### Common Issues
1. **API Rate Limits**: Check rate limiting configuration
2. **Database Connection**: Verify MongoDB connection string
3. **WebSocket Connection**: Check firewall and port settings
4. **Memory Usage**: Monitor for memory leaks in long-running sessions

### Debug Mode
Set log level to DEBUG in config:
```python
LOG_LEVEL = "DEBUG"
```

## Contributing

1. Follow the modular architecture
2. Add comprehensive error handling
3. Include logging for all operations
4. Update documentation
5. Add tests for new features

## License

This project is licensed under the MIT License. 