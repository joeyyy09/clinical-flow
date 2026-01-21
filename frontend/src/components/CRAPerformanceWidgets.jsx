import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { Activity, AlertCircle, CheckCircle2, UserCheck } from 'lucide-react';

const BASE_URL = 'http://127.0.0.1:8000';

/**
 * CRAPerformanceWidget
 * Displays a bar chart of Resolved vs Pending queries per CRA
 */
export const CRAPerformanceWidget = () => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${BASE_URL}/analytics/cra/performance`)
            .then(res => res.json())
            .then(data => {
                setData(data);
                setLoading(false);
            })
            .catch(err => setLoading(false));
    }, []);

    if (loading) return <div className="text-slate-400">Loading CRA performance...</div>;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 col-span-1 lg:col-span-2"
        >
            <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                    <UserCheck className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">CRA Performance</h3>
                    <p className="text-xs text-slate-500">Query Resolution Progress by CRA</p>
                </div>
            </div>

            <div className="h-64 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                        <XAxis dataKey="cra_name" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                        <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                        <Tooltip 
                            contentStyle={{ borderRadius: '12px', border: 'none', backgroundColor: '#1e293b', color: '#fff' }}
                        />
                        <Legend iconType="circle" />
                        <Bar dataKey="resolved_queries" name="Resolved" fill="#10b981" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="pending_queries" name="Pending" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </motion.div>
    );
};

/**
 * CRAActivityFeed
 * Displays a list of recent CRA actions
 */
export const CRAActivityFeed = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${BASE_URL}/analytics/cra/logs`)
            .then(res => res.json())
            .then(data => {
                setLogs(data);
                setLoading(false);
            })
            .catch(err => setLoading(false));
    }, []);

    if (loading) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700"
        >
            <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-indigo-100 dark:bg-indigo-900/20 rounded-lg">
                    <Activity className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">CRA Activity Logs</h3>
                    <p className="text-xs text-slate-500">Recent on-site/remote actions</p>
                </div>
            </div>

            <div className="space-y-4 max-h-72 overflow-y-auto pr-2">
                {logs.map((log) => (
                    <div key={log.id} className="relative pl-6 border-l-2 border-slate-100 dark:border-slate-700 pb-2">
                        <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-white dark:bg-slate-800 border-2 border-indigo-500"></div>
                        <div className="text-xs text-slate-400 mb-1">{new Date(log.timestamp).toLocaleString()}</div>
                        <div className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                            {log.cra_name} <span className="text-slate-500 font-normal">performed</span> {log.action}
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                            Site: {log.site_id} | {log.details}
                        </div>
                    </div>
                ))}
                {logs.length === 0 && (
                    <div className="text-center text-slate-400 py-8">No recent activity logs</div>
                )}
            </div>
        </motion.div>
    );
};

/**
 * UnderperformingSitesWidget
 * Highlights sites that need attention (High queries or Low DQI)
 */
export const UnderperformingSitesWidget = () => {
    const [sites, setSites] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${BASE_URL}/analytics/cra/underperforming`)
            .then(res => res.json())
            .then(data => {
                setSites(data);
                setLoading(false);
            })
            .catch(err => setLoading(false));
    }, []);

    if (loading) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700"
        >
            <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-rose-100 dark:bg-rose-900/20 rounded-lg">
                    <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">Critical Sites</h3>
                    <p className="text-xs text-slate-500">Underperforming sites & focus areas</p>
                </div>
            </div>

            <div className="space-y-3">
                {sites.map((site, i) => (
                    <div key={i} className="p-3 bg-rose-50 dark:bg-rose-900/10 rounded-xl border border-rose-100 dark:border-rose-900/20">
                        <div className="flex justify-between items-start mb-1">
                            <div className="font-bold text-slate-800 dark:text-white">Site {site.site_id}</div>
                            <div className="text-xs px-2 py-1 bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 rounded-md font-bold">
                                DQI: {site.dqi}%
                            </div>
                        </div>
                        <div className="text-xs text-slate-500 mb-2">CRA Responsible: {site.cra_name}</div>
                        <div className="flex items-center gap-1 text-rose-600 dark:text-rose-400 text-xs font-semibold">
                            <AlertCircle className="w-3 h-3" />
                            {site.pending_queries} Pending Queries
                        </div>
                    </div>
                ))}
                {sites.length === 0 && (
                    <div className="text-center text-slate-400 py-8">✓ All sites performing well</div>
                )}
            </div>
        </motion.div>
    );
};
