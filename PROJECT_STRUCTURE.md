# Crypto Trading Bot - Clean Project Structure

## Project Overview
A React frontend + Python WebSocket backend crypto trading bot with AI analysis capabilities.

## Directory Structure

```
crypto-trading-v1/
├── .git/                    # Git repository
├── .gitignore              # Git ignore rules
├── README.md               # Main project documentation
├── requirements.txt        # Python dependencies
├── package.json           # Node.js dependencies
├── package-lock.json      # Node.js lock file
├── node_modules/          # Node.js packages
├── venv/                  # Python virtual environment
├── build/                 # React build output
├── public/                # React public assets
├── src/                   # React frontend source code
│   ├── components/        # React components
│   ├── pages/            # React pages
│   ├── hooks/            # Custom React hooks
│   ├── contexts/         # React contexts
│   └── ...
└── backend/              # Python backend source code
    ├── websocket_server.py
    ├── ai_analysis.py
    ├── trading_bot.py
    ├── market_data.py
    ├── trade_execution.py
    ├── config.py
    └── ...
```

## Core Files

### Frontend (React)
- **src/App.js** - Main React application
- **src/components/** - Reusable UI components
- **src/pages/** - Page components (Trading, Dashboard, etc.)
- **src/hooks/useWebSocket.js** - WebSocket connection hook
- **src/contexts/WebSocketContext.js** - Shared WebSocket context

### Backend (Python)
- **backend/websocket_server.py** - Main WebSocket server
- **backend/ai_analysis.py** - AI analysis functionality
- **backend/trading_bot.py** - Trading bot logic
- **backend/market_data.py** - Market data fetching
- **backend/trade_execution.py** - Trade execution logic
- **backend/config.py** - Configuration settings

### Configuration
- **requirements.txt** - Python dependencies
- **package.json** - Node.js dependencies
- **.gitignore** - Git ignore rules

## How to Run

### Backend
```bash
cd backend
python websocket_server.py
```

### Frontend
```bash
npm start
```

## Features
- Real-time crypto price data
- AI-powered trading analysis
- Paper trading functionality
- WebSocket communication
- Trading bot automation
- Technical indicators
- Position management

## Dependencies
- **Frontend**: React, WebSocket, TradingView charts
- **Backend**: Python, asyncio, websockets, aiohttp, MongoDB
- **AI**: OpenRouter API (Claude, GPT, Grok)
- **Data**: Binance API for market data 