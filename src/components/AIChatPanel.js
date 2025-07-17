import React, { useState, useEffect, useRef } from 'react';
import './AIChatPanel.css';

const AIChatPanel = ({ aiInsights, onRequestAnalysis, symbol, isConnected }) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [userInput, setUserInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (aiInsights) {
      addAIMessage(aiInsights);
    }
  }, [aiInsights]);

  const addAIMessage = (insights) => {
    const newMessage = {
      id: Date.now(),
      type: 'ai',
      timestamp: new Date(),
      content: formatAIInsights(insights)
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const addUserMessage = (content) => {
    const newMessage = {
      id: Date.now(),
      type: 'user',
      timestamp: new Date(),
      content
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const formatAIInsights = (insights) => {
    const { claude_analysis, gpt_refinement, symbol: analysisSymbol } = insights;
    
    let formattedContent = `🤖 **AI Analysis for ${analysisSymbol}**\n\n`;
    
    // Claude Analysis
    if (claude_analysis && !claude_analysis.error) {
      const tradeIdea = claude_analysis.trade_idea || {};
      const reasoning = claude_analysis.reasoning || {};
      
      formattedContent += `**🔍 Claude's Deep Analysis:**\n`;
      formattedContent += `• **Direction:** ${tradeIdea.direction || 'Neutral'}\n`;
      formattedContent += `• **Confidence:** ${((tradeIdea.confidence_score || 0) * 100).toFixed(1)}%\n`;
      formattedContent += `• **Risk Level:** ${reasoning.risk_assessment || 'Medium'}\n`;
      
      if (reasoning.key_factors) {
        formattedContent += `• **Key Factors:** ${reasoning.key_factors.join(', ')}\n`;
      }
      
      if (reasoning.market_context) {
        formattedContent += `• **Market Context:** ${reasoning.market_context}\n`;
      }
      
      formattedContent += `\n`;
    }
    
    // GPT Refinement
    if (gpt_refinement && !gpt_refinement.error) {
      const refinedPlan = gpt_refinement.refined_trade_plan || {};
      const confidence = gpt_refinement.confidence_assessment || {};
      
      formattedContent += `**🎯 GPT's Trade Plan:**\n`;
      formattedContent += `• **Action:** ${refinedPlan.direction || 'Hold'}\n`;
      formattedContent += `• **Entry Price:** $${refinedPlan.entry_price?.toLocaleString() || 'N/A'}\n`;
      formattedContent += `• **Stop Loss:** $${refinedPlan.stop_loss?.toLocaleString() || 'N/A'}\n`;
      formattedContent += `• **Take Profit:** $${refinedPlan.take_profit?.toLocaleString() || 'N/A'}\n`;
      formattedContent += `• **Risk/Reward:** ${refinedPlan.risk_reward_ratio || 'N/A'}\n`;
      formattedContent += `• **Position Size:** ${refinedPlan.position_size_percent || 0}%\n`;
      formattedContent += `• **Overall Confidence:** ${((confidence.overall_confidence || 0) * 100).toFixed(1)}%\n`;
      
      if (confidence.risk_level) {
        formattedContent += `• **Risk Assessment:** ${confidence.risk_level}\n`;
      }
      
      if (gpt_refinement.execution_notes) {
        formattedContent += `\n**📝 Execution Notes:**\n${gpt_refinement.execution_notes}\n`;
      }
    }
    
    return formattedContent;
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!userInput.trim() || !isConnected) return;
    
    const userMessage = userInput.trim();
    addUserMessage(userMessage);
    setUserInput('');
    setIsLoading(true);
    
    // Handle different types of user requests
    if (userMessage.toLowerCase().includes('analyze') || userMessage.toLowerCase().includes('analysis')) {
      if (onRequestAnalysis && symbol) {
        onRequestAnalysis(symbol);
      }
    } else if (userMessage.toLowerCase().includes('help') || userMessage.toLowerCase().includes('commands')) {
      addAIMessage({
        claude_analysis: { error: null },
        gpt_refinement: { error: null },
        symbol: 'HELP',
        custom_message: `**Available Commands:**\n• "Analyze [symbol]" - Get AI analysis for a symbol\n• "What's the market sentiment?" - Get current sentiment\n• "Show me trade history" - View recent trades\n• "What's my portfolio status?" - Check positions and balance\n• "Help" - Show this help message`
      });
    } else {
      // Default AI response
      addAIMessage({
        claude_analysis: { error: null },
        gpt_refinement: { error: null },
        symbol: 'GENERAL',
        custom_message: `I understand you said: "${userMessage}". To get specific trading analysis, try saying "Analyze ${symbol}" or ask for help with "Help".`
      });
    }
    
    setIsLoading(false);
  };

  const handleQuickAnalysis = () => {
    if (onRequestAnalysis && symbol) {
      setIsLoading(true);
      onRequestAnalysis(symbol);
      setTimeout(() => setIsLoading(false), 2000);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="ai-chat-panel">
      <div className="chat-header">
        <h3>🤖 AI Trading Assistant</h3>
        <div className="chat-controls">
          <button 
            className="quick-analysis-btn"
            onClick={handleQuickAnalysis}
            disabled={!isConnected || isLoading}
          >
            {isLoading ? 'Analyzing...' : 'Quick Analysis'}
          </button>
          <button className="clear-chat-btn" onClick={clearChat}>
            Clear
          </button>
        </div>
      </div>
      
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-chat">
            <div className="empty-icon">🤖</div>
            <p>Welcome to the AI Trading Assistant!</p>
            <p>Ask me to analyze markets, get trading insights, or type "Help" for commands.</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-header">
              <span className="message-author">
                {message.type === 'ai' ? '🤖 AI Assistant' : '👤 You'}
              </span>
              <span className="message-time">
                {message.timestamp.toLocaleTimeString()}
              </span>
            </div>
            <div className="message-content">
              {message.content}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message ai">
            <div className="message-header">
              <span className="message-author">🤖 AI Assistant</span>
              <span className="message-time">Now</span>
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
                Analyzing market data...
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          placeholder={isConnected ? "Ask for analysis or type 'Help' for commands..." : "Connecting to server..."}
          disabled={!isConnected}
          className="chat-input"
        />
        <button 
          type="submit" 
          disabled={!isConnected || !userInput.trim() || isLoading}
          className="send-button"
        >
          Send
        </button>
      </form>
      
      {!isConnected && (
        <div className="connection-warning">
          ⚠️ Not connected to trading server. Please check your connection.
        </div>
      )}
    </div>
  );
};

export default AIChatPanel; 