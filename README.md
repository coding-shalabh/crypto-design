# Crypto Trading Dashboard

A modern, responsive React application that displays real-time cryptocurrency data using WebSocket connections.

## Features

- **Real-time Data**: Live cryptocurrency prices and market data via WebSocket
- **Search Functionality**: Filter cryptocurrencies by name or symbol
- **Multiple Views**: Switch between grid and list layouts
- **Global Statistics**: Market cap, volume, active coins, and BTC dominance
- **Responsive Design**: Mobile-friendly interface
- **Keyboard Shortcuts**: 
  - `Ctrl/Cmd + K`: Focus search
  - `Ctrl/Cmd + 1`: Grid view
  - `Ctrl/Cmd + 2`: List view
- **Connection Status**: Visual indicator for WebSocket connection
- **Error Handling**: Graceful error handling with retry functionality

## Technologies Used

- **React 18**: Modern React with hooks
- **CSS3**: Custom styling with CSS variables
- **WebSocket**: Real-time data from Binance
- **CoinGecko API**: Initial cryptocurrency data
- **Font Awesome**: Icons
- **Inter Font**: Modern typography

## Getting Started

### Prerequisites

- Node.js (version 14 or higher)
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd crypto-trading-dashboard
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

4. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

### Available Scripts

- `npm start`: Runs the app in development mode
- `npm test`: Launches the test runner
- `npm run build`: Builds the app for production
- `npm run eject`: Ejects from Create React App (not recommended)

## Project Structure

```
src/
├── components/          # React components
│   ├── Header.js       # App header with connection status
│   ├── Controls.js     # Search and view controls
│   ├── StatsOverview.js # Global statistics cards
│   ├── CryptoGrid.js   # Grid container for crypto cards
│   ├── CryptoCard.js   # Individual cryptocurrency card
│   ├── Loading.js      # Loading spinner
│   └── ErrorMessage.js # Error display component
├── hooks/              # Custom React hooks
│   └── useCryptoData.js # Main data management hook
├── App.js              # Main application component
├── App.css             # App-specific styles
├── index.js            # React entry point
└── index.css           # Global styles
```

## API Integration

### CoinGecko API
- **Endpoint**: `https://api.coingecko.com/api/v3/coins/markets`
- **Purpose**: Initial cryptocurrency data loading
- **Data**: Market cap, volume, price changes, rankings

### Binance WebSocket
- **Endpoint**: `wss://stream.binance.com:9443/ws/!ticker@arr`
- **Purpose**: Real-time price updates
- **Data**: Live prices, volume, market cap updates

## Features in Detail

### Real-time Updates
The application connects to Binance WebSocket to receive live price updates for all supported cryptocurrencies. Updates are processed and displayed with smooth animations.

### Search and Filter
Users can search for cryptocurrencies by name or symbol. The search is case-insensitive and updates results in real-time.

### Responsive Design
The application is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones

### Accessibility
- Semantic HTML structure
- Keyboard navigation support
- Screen reader friendly
- High contrast mode support
- Reduced motion support

## Customization

### Styling
The application uses CSS custom properties (variables) for easy theming. Main variables are defined in `src/index.css`:

```css
:root {
  --primary-color: #6366f1;
  --secondary-color: #10b981;
  --background: #0f172a;
  --surface: #1e293b;
  /* ... more variables */
}
```

### Adding New Features
The modular component structure makes it easy to add new features:
1. Create new components in `src/components/`
2. Add corresponding CSS files
3. Import and use in `App.js`

## Deployment

### Build for Production
```bash
npm run build
```

This creates a `build` folder with optimized production files.

### Deploy to Netlify
1. Push your code to GitHub
2. Connect your repository to Netlify
3. Set build command: `npm run build`
4. Set publish directory: `build`

### Deploy to Vercel
1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel`
3. Follow the prompts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- [CoinGecko](https://coingecko.com/) for cryptocurrency data
- [Binance](https://binance.com/) for WebSocket API
- [Font Awesome](https://fontawesome.com/) for icons
- [Inter Font](https://rsms.me/inter/) for typography 