import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import useWebSocket from '../hooks/useWebSocket';

// Create WebSocket context
const WebSocketContext = createContext();

//   Add singleton pattern to prevent multiple providers
let providerInstance = null;

// WebSocket provider component
export const WebSocketProvider = ({ children }) => {
  console.log('🔍 WebSocketContext: Provider initialized');
  
  //   Prevent multiple providers
  const instanceRef = useRef(null);
  
  useEffect(() => {
    if (providerInstance && providerInstance !== instanceRef.current) {
      console.warn('🔍 WebSocketContext: Multiple WebSocket providers detected! This may cause connection issues.');
    }
    providerInstance = instanceRef.current = {};
    
    return () => {
      if (providerInstance === instanceRef.current) {
        providerInstance = null;
      }
    };
  }, []);
  
  // Create a single WebSocket connection
  const websocket = useWebSocket();
  
  console.log('🔍 WebSocketContext: WebSocket hook initialized:', {
    isConnected: websocket.isConnected,
    hasData: !!websocket.data,
    dataKeys: Object.keys(websocket.data || {})
  });

  return (
    <WebSocketContext.Provider value={websocket}>
      {children}
    </WebSocketContext.Provider>
  );
};

// Custom hook to use WebSocket context
export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
};

export default WebSocketContext;