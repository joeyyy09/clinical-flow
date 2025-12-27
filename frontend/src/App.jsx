
import React, { useState, useEffect } from 'react';
import AppLayout from './components/Layout';
import Overview from './pages/Overview';
import RiskMonitor from './pages/RiskMonitor';
import DataIngestion from './pages/DataIngestion';
import Reports from './pages/Reports';
import { Bot, Activity, RefreshCw } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import { motion, AnimatePresence } from 'framer-motion';

const AgentPage = () => (
    <div className="flex flex-col h-[80vh] bg-white rounded-3xl shadow-xl overflow-hidden border border-slate-200">
        <div className="bg-slate-50 p-8 text-center border-b border-slate-100">
            <div className="inline-flex p-4 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-2xl shadow-lg mb-4">
                <Bot className="w-12 h-12 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-slate-800">Agentic Intelligence Hub</h2>
            <p className="text-slate-500 mt-2 max-w-lg mx-auto">
                Ask complex questions about your data, generate cross-study hypotheses, or automate routine compliance checks.
            </p>
        </div>
        <div className="flex-1 bg-slate-50/50 p-8 flex justify-center">
             <div className="w-full max-w-2xl bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden h-full flex flex-col">
                 <ChatInterface minimized={false} />
             </div>
        </div>
    </div>
);

const LoginScreen = ({ onLogin }) => {
    const [email, setEmail] = useState('dr.smith@clinicalflow.com');
    const [password, setPassword] = useState('password');
    const [loading, setLoading] = useState(false);

    const handleLogin = (e) => {
        e.preventDefault();
        setLoading(true);
        setTimeout(() => {
            setLoading(false);
            onLogin();
        }, 1200);
    };

    return (
        <div className="fixed inset-0 bg-slate-900 z-[100] flex items-center justify-center">
            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md"
            >
                <div className="flex justify-center mb-8">
                    <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                        <Activity className="text-white w-7 h-7" />
                    </div>
                </div>
                <h2 className="text-2xl font-bold text-slate-800 text-center mb-2">Welcome Back</h2>
                <p className="text-slate-500 text-center mb-8">Enter your credentials to access ClinicalFlow.</p>
                
                <form onSubmit={handleLogin} className="space-y-4">
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Email</label>
                        <input 
                            type="email" value={email} onChange={e => setEmail(e.target.value)}
                            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-medium"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Password</label>
                        <input 
                            type="password" value={password} onChange={e => setPassword(e.target.value)}
                            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-medium"
                        />
                    </div>
                    <button 
                        type="submit" disabled={loading}
                        className="w-full bg-blue-600 text-white rounded-lg py-3 font-bold shadow-lg shadow-blue-500/30 hover:bg-blue-700 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex justify-center items-center gap-2"
                    >
                        {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
                        {loading ? 'Authenticating...' : 'Sign In'}
                    </button>
                    <p className="text-center text-xs text-slate-400 mt-4">
                        Secure Connection • 256-bit Encryption
                    </p>
                </form>
            </motion.div>
        </div>
    );
};

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  
  // Lifted Reports State for Persistence
  const [reports, setReports] = useState([]);
  const [reportsLoaded, setReportsLoaded] = useState(false);

  // Check valid session on load (mock)
  useEffect(() => {
      const session = localStorage.getItem('clinicalflow_session');
      if (session) setIsAuthenticated(true);
      
      // Load initial reports
      if (!reportsLoaded) {
          fetch('http://127.0.0.1:8000/reports')
            .then(res => res.json())
            .then(data => {
                setReports(data);
                setReportsLoaded(true);
            })
            .catch(err => console.error(err));
      }
  }, [reportsLoaded]);

  // Dark Mode Effect
  useEffect(() => {
      if (darkMode) {
          document.documentElement.classList.add('dark');
      } else {
          document.documentElement.classList.remove('dark');
      }
  }, [darkMode]);

  const handleLogin = () => {
      localStorage.setItem('clinicalflow_session', 'true');
      setIsAuthenticated(true);
  };

  const handleLogout = () => {
      localStorage.removeItem('clinicalflow_session');
      setIsAuthenticated(false);
  };

  const renderContent = () => {
      switch(activeTab) {
          case 'dashboard': return <Overview searchQuery={searchQuery} />;
          case 'risk': return <RiskMonitor searchQuery={searchQuery} />;
          case 'data': return <DataIngestion />;
          case 'reports': return <Reports searchQuery={searchQuery} reports={reports} setReports={setReports} />;
          case 'agent': return <AgentPage />;
          default: return <Overview searchQuery={searchQuery} />;
      }
  };

  return (
    <>
      <AnimatePresence>
          {!isAuthenticated && <LoginScreen onLogin={handleLogin} />}
      </AnimatePresence>
      
      {isAuthenticated && (
        <AppLayout 
            activeTab={activeTab} 
            setActiveTab={setActiveTab} 
            searchQuery={searchQuery} 
            setSearchQuery={setSearchQuery}
            onLogout={handleLogout}
            darkMode={darkMode}
            setDarkMode={setDarkMode}
        >
            {renderContent()}
        </AppLayout>
      )}
    </>
  );
}

export default App;
