import React, { useState, useEffect } from 'react';
import { Bell, Check, Clock, User, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const NotificationCenter = ({ currentUserHandle = "@Sarah" }) => {
    const [alerts, setAlerts] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchAlerts();
        }
    }, [isOpen]);

    const fetchAlerts = async () => {
        setLoading(true);
        try {
            const res = await fetch(`http://127.0.0.1:8000/alerts/${currentUserHandle}`);
            const data = await res.json();
            setAlerts(data);
        } catch (error) {
            console.error("Failed to fetch alerts", error);
        } finally {
            setLoading(false);
        }
    };

    const markAsRead = async (id) => {
        try {
            await fetch(`http://127.0.0.1:8000/alerts/${id}/read`, { method: 'POST' });
            setAlerts(alerts.map(a => a.id === id ? { ...a, is_read: 1 } : a));
        } catch (error) {
            console.error("Failed to mark alert as read", error);
        }
    };

    const unreadCount = alerts.filter(a => !a.is_read).length;

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative p-2 text-slate-500 hover:text-blue-600 transition-colors bg-white dark:bg-slate-800 rounded-full border border-slate-200 dark:border-slate-700 shadow-sm"
            >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-rose-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full border-2 border-white dark:border-slate-900">
                        {unreadCount}
                    </span>
                )}
            </button>

            <AnimatePresence>
                {isOpen && (
                    <>
                        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
                        <motion.div
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                            className="absolute right-0 mt-3 w-80 bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 z-50 overflow-hidden"
                        >
                            <div className="p-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-800/50">
                                <h3 className="font-bold text-slate-800 dark:text-white">Collaboration Alerts</h3>
                                <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-slate-600"><X className="w-4 h-4" /></button>
                            </div>

                            <div className="max-h-[400px] overflow-y-auto">
                                {loading && alerts.length === 0 ? (
                                    <div className="p-8 text-center text-slate-400 text-sm italic">Scanning for mentions...</div>
                                ) : alerts.length === 0 ? (
                                    <div className="p-12 text-center text-slate-400">
                                        <Bell className="w-10 h-10 mx-auto mb-2 opacity-20" />
                                        <p className="text-sm">No notifications yet.</p>
                                    </div>
                                ) : (
                                    <div className="divide-y divide-slate-50 dark:divide-slate-700">
                                        {alerts.map((alert) => (
                                            <div key={alert.id} className={`p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${!alert.is_read ? 'bg-blue-50/30 dark:bg-blue-900/10' : ''}`}>
                                                <div className="flex justify-between items-start mb-1">
                                                    <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 flex items-center gap-1 uppercase tracking-wider">
                                                        <User className="w-3 h-3" /> Mentioned
                                                    </span>
                                                    <span className="text-[10px] text-slate-400 flex items-center gap-1">
                                                        <Clock className="w-3 h-3" /> {new Date(alert.created_at).toLocaleTimeString()}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed mb-2">
                                                    {alert.message}
                                                </p>
                                                {!alert.is_read && (
                                                    <button
                                                        onClick={() => markAsRead(alert.id)}
                                                        className="text-[10px] font-bold text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
                                                    >
                                                        <Check className="w-3 h-3" /> Mark as Read
                                                    </button>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
};

export default NotificationCenter;
