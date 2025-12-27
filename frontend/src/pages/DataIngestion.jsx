
import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, CheckCircle, Database, Play, RefreshCw, Upload } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const DataIngestion = () => {
    const [status, setStatus] = useState('idle'); // idle, uploading, processing, complete, error
    const [progress, setProgress] = useState(0);
    const [logs, setLogs] = useState([]);
    const [lastSync, setLastSync] = useState(null);
    const fileInputRef = useRef(null);

    useEffect(() => {
        const storedSync = localStorage.getItem('last_ingestion_sync');
        if (storedSync) setLastSync(storedSync);
    }, []);

    const addLog = (message) => {
        const timestamp = new Date().toLocaleTimeString();
        setLogs(prev => [`[${timestamp}] ${message}`, ...prev]);
    };

    const handleFileSelect = (event) => {
        const file = event.target.files[0];
        if (file) {
            startPipeline(file.name);
        }
    };

    const triggerFileInput = () => {
        if(fileInputRef.current) fileInputRef.current.click();
    };

    const startPipeline = async (filename) => {
        setStatus('uploading');
        setProgress(0);
        setLogs([]);
        addLog(`Started ingestion pipeline for ${filename}...`);

        const file = fileInputRef.current?.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Upload Phase
            setProgress(30);
            addLog("Uploading file to secure storage...");
            
            const response = await fetch('http://127.0.0.1:8000/ingest/file', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                setProgress(60);
                setStatus('processing');
                addLog("Upload complete. Triggering ingestion engine...");
                
                // Simulate processing delay for UX (since usage is async on backend)
                setTimeout(() => {
                    setProgress(85);
                    addLog("Parsing entities and updating vector index...");
                    
                    setTimeout(() => {
                        setProgress(100);
                        setStatus('complete');
                        addLog("Ingestion complete. Knowledge base updated.");
                        
                        const now = new Date().toLocaleString();
                        setLastSync(now);
                        localStorage.setItem('last_ingestion_sync', now);
                    }, 1500);
                }, 1500);

            } else {
                setStatus('error');
                addLog("Error: Upload failed.");
            }
        } catch (error) {
            console.error(error);
            setStatus('error');
            addLog("Error: Connection failed.");
        }
    };

    return (
        <div className="max-w-6xl mx-auto pb-10">
            <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                accept=".xlsx,.csv,.json" 
                onChange={handleFileSelect} 
            />

            <div className="mb-8 flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Data Ingestion Pipeline</h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-2">Manage clinical trial datasets and update the knowledge base.</p>
                </div>
                 <div className="text-right">
                    <p className="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1">Last Synchronization</p>
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 px-3 py-1 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm inline-block">
                        {lastSync || "Never"}
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-8">
                {/* Visual Pipeline Status */}
                <div className="col-span-2 space-y-6">
                    {/* Upload Card */}
                    <motion.div 
                        whileHover={{ scale: 1.01 }}
                        className="bg-white dark:bg-slate-800 p-8 rounded-3xl border border-slate-200 dark:border-slate-700 shadow-xl overflow-hidden relative transition-colors"
                    >
                        <div className="absolute top-0 left-0 w-full h-1 bg-slate-100 dark:bg-slate-700">
                            <motion.div 
                                className="h-full bg-blue-500"
                                initial={{ width: 0 }}
                                animate={{ width: `${progress}%` }}
                            />
                        </div>

                        <div className="flex flex-col items-center justify-center text-center py-8">
                            <div className="w-20 h-20 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center mb-6 shadow-inner transition-colors">
                                {status === 'uploading' || status === 'processing' ? (
                                    <RefreshCw className="w-10 h-10 animate-spin" />
                                ) : status === 'complete' ? (
                                    <CheckCircle className="w-10 h-10" />
                                ) : (
                                    <Database className="w-10 h-10" />
                                )}
                            </div>
                            <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">
                                {status === 'idle' ? 'Ready to Ingest' : 
                                 status === 'complete' ? 'Ingestion Successful' : 
                                 'Processing Data...'}
                            </h3>
                            <p className="text-slate-500 dark:text-slate-400 max-w-md mb-8">
                                {status === 'idle' ? 'Upload new clinical study reports (Excel/PDF) to update the risk monitoring engine.' : 
                                 status === 'complete' ? 'New data is now available in Risk Monitor and Agent Copilot.' :
                                 `Current operation: ${progress < 50 ? 'Uploading files...' : 'Vectorizing content...'}`}
                            </p>
                            
                            <button 
                                onClick={triggerFileInput}
                                disabled={status === 'uploading' || status === 'processing'}
                                className="bg-slate-900 dark:bg-blue-600 text-white px-8 py-4 rounded-xl font-bold shadow-lg shadow-slate-900/20 dark:shadow-blue-500/20 hover:bg-slate-800 dark:hover:bg-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3"
                            >
                                {status === 'idle' || status === 'complete' ? <UploadCloud className="w-5 h-5" /> : <RefreshCw className="w-5 h-5 animate-spin" />}
                                {status === 'idle' || status === 'complete' ? 'Start Pipeline' : 'Processing...'}
                            </button>
                        </div>
                    </motion.div>

                    {/* Logs Terminal */}
                    <div className="bg-slate-900 rounded-2xl p-6 shadow-2xl overflow-hidden font-mono text-sm h-64 flex flex-col border border-slate-800">
                        <div className="flex items-center gap-2 mb-4 border-b border-slate-700 pb-2">
                            <div className="w-3 h-3 rounded-full bg-red-500"></div>
                            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                            <div className="w-3 h-3 rounded-full bg-green-500"></div>
                            <span className="text-slate-400 ml-2 text-xs">pipeline_logs.sh</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-2">
                            {logs.length === 0 && (
                                <p className="text-slate-600 italic">Waiting for input...</p>
                            )}
                            <AnimatePresence>
                                {logs.map((log, i) => (
                                    <motion.p 
                                        key={i}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        className="text-green-400"
                                    >
                                        <span className="text-blue-400">$</span> {log}
                                    </motion.p>
                                ))}
                            </AnimatePresence>
                        </div>
                    </div>
                </div>

                {/* Info / Config */}
                <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm h-fit transition-colors">
                    <h4 className="font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                        <Database className="w-4 h-4 text-blue-500" /> Pipeline Configuration
                    </h4>
                    
                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-1">Data Source</label>
                            <select className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-700 dark:text-slate-300 focus:outline-none focus:border-blue-500">
                                <option>Manual Upload (Excel/CSV)</option>
                                <option>S3 Bucket (Automated)</option>
                                <option>EDC Connector (API)</option>
                            </select>
                        </div>
                        
                        <div>
                            <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-1">Processing Mode</label>
                            <div className="flex gap-2">
                                <button className="flex-1 py-1.5 text-xs font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800 rounded-lg">Incremental</button>
                                <button className="flex-1 py-1.5 text-xs font-medium text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700 rounded-lg">Full Refresh</button>
                            </div>
                        </div>

                        <div className="pt-4 border-t border-slate-100 dark:border-slate-700">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Vector DB Active</span>
                            </div>
                            <p className="text-xs text-slate-400">
                                Connection stable. Latency: 24ms.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DataIngestion;
