
import React, { useState } from 'react';
import { Send, Bot, X, Maximize2, Minimize2, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ChatInterface = ({ minimized = false }) => {
  const [isOpen, setIsOpen] = useState(!minimized);
  const [messages, setMessages] = useState([
    { role: 'agent', content: 'Hello! I am your Clinical AI Copilot. I can help you analyze risks, draft reports, or query data.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [chartData, setChartData] = useState(null);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setChartData(null); 

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg.content }),
      });
      const data = await response.json();
      
      setMessages(prev => [...prev, { role: 'agent', content: data.answer }]);
      if (data.chart_type) setChartData(data);
      
    } catch (error) {
      setMessages(prev => [...prev, { role: 'agent', content: 'Connection error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen && minimized) {
      return (
          <button 
            onClick={() => setIsOpen(true)}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-3 rounded-full shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
          >
              <Bot className="w-5 h-5" />
              <span className="font-semibold">Ask AI Copilot</span>
          </button>
      )
  }

  return (
    <div className={`flex flex-col bg-white dark:bg-slate-800 transition-colors ${minimized ? 'h-[500px] shadow-none !border-none' : 'h-full rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm'}`}>
      {/* Header */}
      <div className="p-4 border-b dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 flex items-center justify-between transition-colors">
        <div className="flex items-center gap-2">
            <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-1.5 rounded-lg">
                <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
                <h2 className="font-bold text-slate-800 dark:text-white text-sm">Agent Copilot</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">Powered by GenAI</p>
            </div>
        </div>
        {minimized && (
            <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                <X className="w-5 h-5" />
            </button>
        )}
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50 dark:bg-slate-900/50 transition-colors">
        {messages.map((msg, idx) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            key={idx} 
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[85%] rounded-2xl p-3 text-sm shadow-sm transition-colors ${
              msg.role === 'user' 
                ? 'bg-blue-600 text-white rounded-br-none' 
                : 'bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-100 dark:border-slate-600 rounded-bl-none'
            }`}>
              <p>{msg.content}</p>
            </div>
          </motion.div>
        ))}
        {loading && (
            <div className="flex gap-1 ml-2">
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-100"></span>
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-200"></span>
            </div>
        )}
        
        {chartData && (
             <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="p-4 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl shadow-sm mx-4 transition-colors">
                 <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase">Analysis Visualization</p>
                 <div className="h-32 bg-slate-50 dark:bg-slate-800/50 rounded border border-dashed border-slate-300 dark:border-slate-500 flex items-center justify-center text-slate-400 text-xs">
                     Charts rendered here
                 </div>
             </motion.div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t dark:border-slate-700 bg-white dark:bg-slate-800 transition-colors">
        <div className="flex gap-2 relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask me anything about the data..."
            className="flex-1 bg-slate-100 dark:bg-slate-700 border-none rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-700 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 transition-colors"
          />
          <button 
            onClick={sendMessage}
            disabled={loading}
            className="absolute right-2 top-2 bottom-2 bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-lg shadow-blue-500/30"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
