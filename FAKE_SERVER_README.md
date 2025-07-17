# Fake WebSocket Server for Frontend Testing

## Overview

This fake WebSocket server simulates the exact backend behavior expected by the frontend crypto trading application. It sends properly formatted messages that match the frontend's expectations, allowing you to test the frontend without running the actual backend.

## Features

✅ **Real-time Price Updates** - Simulates live crypto price changes  
✅ **Trade Execution** - Handles buy/sell orders and position management  
✅ **Bot Control** - Start/stop trading bot and manage configuration  
✅ **AI Analysis** - Provides fake AI insights and analysis  
✅ **Position Management** - Track open positions and P&L  
✅ **Error Handling** - Proper error responses for invalid requests  
✅ **Data Persistence** - Maintains state during session  

## Quick Start

### 1. Start the Fake Server

```bash
python start_fake_server.py
```

The server will start on `ws://localhost:8765` and display a startup banner.

### 2. Test the Server

In a new terminal, run the test script:

```bash
python test_fake_server.py
```

This will test all message types and verify the server is working correctly.

### 3. Debug Issues (if needed)

If you encounter problems, run the debug script:

```bash
python debug_fake_server.py
```

This provides detailed logging and step-by-step debugging.

## Message Types Supported

### Frontend → Backend Messages

| Message Type | Description | Example |
|--------------|-------------|---------|
| `get_positions` | Get current positions and balance | `{"type": "get_positions"}` |
| `get_trade_history` | Get trade history | `{"type": "get_trade_history", "limit": 50}` |
| `get_crypto_data` | Get crypto market data | `{"type": "get_crypto_data"}` |
| `execute_trade` | Execute a trade | `{"type": "execute_trade", "symbol": "BTC", "direction": "BUY", "amount": 0.1, "price": 45000}` |
| `close_position` | Close a position | `{"type": "close_position", "symbol": "BTC"}` |
| `start_bot` | Start trading bot | `{"type": "start_bot", "config": {...}}` |
| `stop_bot` | Stop trading bot | `{"type": "stop_bot"}` |
| `get_bot_status` | Get bot status | `{"type": "get_bot_status"}` |
| `update_bot_config` | Update bot config | `{"type": "update_bot_config", "config": {...}}` |
| `get_ai_analysis` | Get AI analysis | `{"type": "get_ai_analysis", "symbol": "BTC"}` |

### Backend → Frontend Messages

| Message Type | Description | Data Structure |
|--------------|-------------|----------------|
| `positions_response` | Current positions and balance | `{"balance": 100000, "positions": {...}}` |
| `trade_history_response` | Trade history | `{"trades": [...]}` |
| `crypto_data_response` | Crypto market data | `{"bitcoin": {...}, "ethereum": {...}}` |
| `trade_executed` | Trade execution confirmation | `{"trade": {...}, "new_balance": 95500, "positions": {...}}` |
| `position_closed` | Position closure confirmation | `{"trade": {...}, "new_balance": 100500, "positions": {...}}` |
| `price_update` | Real-time price update | `{"symbol": "BTC", "price": 45000, "change_24h": 2.5}` |
| `bot_status_response` | Bot status information | `{"enabled": true, "active_trades": 2, ...}` |
| `start_bot_response` | Bot start confirmation | `{"success": true, "message": "Bot started"}` |
| `stop_bot_response` | Bot stop confirmation | `{"success": true, "message": "Bot stopped"}` |
| `ai_insights` | AI analysis results | `{"symbol": "BTC", "claude_analysis": "...", "gpt_refinement": "..."}` |
| `error` | Error message | `{"message": "Error description"}` |

## Testing with Frontend

### 1. Start the Fake Server

```bash
python start_fake_server.py
```

### 2. Start Your Frontend

Start your React frontend application. It should connect to `ws://localhost:8765` automatically.

### 3. Verify Connection

Check that the frontend shows:
- ✅ Connection status as "Connected"
- 📊 Initial data loaded (positions, trades, crypto data)
- 💰 Balance displayed
- 📈 Real-time price updates

### 4. Test Features

Try these features in the frontend:
- **Trading**: Execute buy/sell orders
- **Bot Control**: Start/stop the trading bot
- **Positions**: View and close positions
- **Charts**: View price charts (data will be fake)
- **AI Analysis**: Request AI insights

## Troubleshooting

### Connection Issues

**Problem**: Frontend can't connect to server  
**Solution**: 
1. Check if server is running: `netstat -ano | findstr :8765`
2. Kill any existing processes: `taskkill /PID <PID> /F`
3. Restart server: `python start_fake_server.py`

### Missing Data

**Problem**: Frontend shows no data  
**Solution**:
1. Run test script: `python test_fake_server.py`
2. Check server logs for errors
3. Verify WebSocket URL in frontend is `ws://localhost:8765`

### Message Format Errors

**Problem**: Frontend shows errors about message format  
**Solution**:
1. Run debug script: `python debug_fake_server.py`
2. Check `fake_server_debug.log` for details
3. Verify message formats match frontend expectations

### Performance Issues

**Problem**: Slow or unresponsive updates  
**Solution**:
1. Check server CPU/memory usage
2. Reduce update frequency in server code
3. Close unnecessary browser tabs

## Server Configuration

### Update Intervals

You can modify these intervals in `fake_server_for_frontend_testing.py`:

```python
# Price update interval (seconds)
await asyncio.sleep(5)  # Line ~450

# Bot trade simulation interval (seconds)  
await asyncio.sleep(30)  # Line ~480
```

### Initial Data

Modify the `_initialize_fake_data()` method to change:
- Starting balance
- Initial crypto prices
- Fake trade history
- Bot configuration

### Crypto Symbols

Add/remove crypto symbols in the `crypto_symbols` list:

```python
self.crypto_symbols = [
    'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'AVAX', 'MATIC',
    'LINK', 'UNI', 'ATOM', 'LTC', 'BCH', 'XLM', 'VET', 'FIL'
]
```

## File Structure

```
├── fake_server_for_frontend_testing.py  # Main fake server
├── test_fake_server.py                  # Test script
├── debug_fake_server.py                 # Debug script
├── start_fake_server.py                 # Startup script
├── FAKE_SERVER_README.md                # This file
└── fake_server_debug.log                # Debug log (generated)
```

## Development

### Adding New Message Types

1. Add handler in `handle_message()` method
2. Add test in `test_fake_server.py`
3. Add validation in `debug_fake_server.py`
4. Update this README

### Modifying Data Structures

1. Update the relevant initialization method
2. Modify response formatting
3. Update tests to match new structure
4. Test with frontend

## Security Notes

⚠️ **This is a testing server only!**
- No real trading occurs
- No real money is involved
- No real API keys needed
- Data is completely fake
- Do not use in production

## Support

If you encounter issues:

1. **Check logs**: Look at server console output
2. **Run tests**: `python test_fake_server.py`
3. **Debug**: `python debug_fake_server.py`
4. **Check frontend**: Verify WebSocket connection
5. **Restart**: Kill and restart the server

## Example Usage

### Complete Testing Workflow

```bash
# Terminal 1: Start fake server
python start_fake_server.py

# Terminal 2: Test server
python test_fake_server.py

# Terminal 3: Debug if needed
python debug_fake_server.py

# Browser: Test frontend
# Open your React app and verify it connects and shows data
```

### Manual Testing with WebSocket Client

You can also test manually using a WebSocket client:

```javascript
// Connect to server
const ws = new WebSocket('ws://localhost:8765');

// Send test message
ws.send(JSON.stringify({
    type: 'get_positions'
}));

// Listen for response
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

This fake server provides a complete testing environment for your frontend without needing the actual backend running! 