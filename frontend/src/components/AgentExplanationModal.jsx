import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import { Sparkles, AlertTriangle, CheckCircle, Activity, BrainCircuit } from 'lucide-react';
import { motion } from 'framer-motion';

const AgentExplanationModal = ({ isOpen, onClose, siteNumber }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (isOpen && siteNumber) {
            fetchExplanation();
        } else {
            setData(null); // Reset on close
        }
    }, [isOpen, siteNumber]);

    const fetchExplanation = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`http://127.0.0.1:8000/agent/explain-site-risk?site_id=${siteNumber}`);
            if (!res.ok) throw new Error("Agent failed to respond");
            const result = await res.json();
            setData(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={`Agent Analysis: Site ${siteNumber}`}>
            <div className="min-h-[300px] flex flex-col">
                {loading ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-slate-400 gap-3">
                        <BrainCircuit className="w-10 h-10 animate-pulse text-indigo-500" />
                        <p className="text-sm font-medium animate-pulse">Analyzing operational patterns...</p>
                    </div>
                ) : error ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-rose-500 gap-2">
                        <AlertTriangle className="w-8 h-8" />
                        <p>{error}</p>
                    </div>
                ) : data ? (
                    <div className="space-y-6">
                        {/* Header Badge */}
                        <div className="flex items-center gap-3 bg-slate-50 dark:bg-slate-800 p-4 rounded-xl border border-slate-100 dark:border-slate-700">
                            <div className={`p-3 rounded-full ${data.risk_level === 'High' ? 'bg-rose-100 text-rose-600' :
                                    data.risk_level === 'Medium' ? 'bg-amber-100 text-amber-600' :
                                        'bg-emerald-100 text-emerald-600'
                                }`}>
                                <Activity className="w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-slate-800 dark:text-white">
                                    {data.risk_level} Risk Assessment
                                </h3>
                                <div className="flex gap-3 text-xs text-slate-500 mt-1">
                                    <span>DQI: <b>{data.metrics.dqi}</b></span>
                                    <span>•</span>
                                    <span>Missing Pages: <b>{data.metrics.missing}</b></span>
                                    <span>•</span>
                                    <span>SAEs: <b>{data.metrics.sae}</b></span>
                                </div>
                            </div>
                        </div>

                        {/* Explanation Content */}
                        <div className="bg-indigo-50 dark:bg-indigo-900/20 p-5 rounded-xl border border-indigo-100 dark:border-indigo-800/50 relative overflow-hidden">
                            <Sparkles className="absolute top-2 right-2 w-12 h-12 text-indigo-200 opacity-20" />
                            <h4 className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300 font-bold mb-2">
                                <BrainCircuit className="w-4 h-4" /> Agent Logic
                            </h4>
                            <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed"
                                dangerouslySetInnerHTML={{ __html: data.explanation.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }}
                            />
                        </div>

                        {/* Recommended Action */}
                        <div>
                            <h4 className="font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
                                <CheckCircle className="w-4 h-4 text-emerald-500" /> Recommended Action
                            </h4>
                            <div className="bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
                                <p className="text-sm font-medium text-slate-600 dark:text-slate-300">
                                    {data.action_item}
                                </p>
                            </div>
                        </div>
                    </div>
                ) : null}
            </div>
        </Modal>
    );
};

export default AgentExplanationModal;
