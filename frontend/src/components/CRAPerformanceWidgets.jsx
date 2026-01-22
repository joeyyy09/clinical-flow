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
 * MissingLabDataWidget
 * Displays a list of recent missing lab data issues
 */
export const MissingLabDataWidget = () => {
    const [labs, setLabs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${BASE_URL}/analytics/lab-gaps`)
            .then(res => res.json())
            .then(data => {
                setLabs(data || []);
                setLoading(false);
            })
            .catch(err => setLoading(false));
    }, []);

    if (loading) return null;
    if (labs.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700"
        >
            <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-amber-100 dark:bg-amber-900/20 rounded-lg">
                    <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">Lab Data Gaps</h3>
                    <p className="text-xs text-slate-500">Missing Names & Ranges</p>
                </div>
            </div>

            <div className="overflow-hidden">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-slate-500 uppercase bg-slate-50 dark:bg-slate-700/50">
                        <tr>
                            <th className="px-3 py-2">Site</th>
                            <th className="px-3 py-2">Test Name</th>
                            <th className="px-3 py-2">Issue</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                        {labs.slice(0, 10).map((item, i) => (
                            <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                                <td className="px-3 py-2 font-medium text-slate-800 dark:text-slate-200">{item.site_number}</td>
                                <td className="px-3 py-2 text-slate-600 dark:text-slate-400 truncate max-w-[100px]" title={item.test_name}>{item.test_name}</td>
                                <td className="px-3 py-2 text-amber-600 font-medium text-xs truncate max-w-[120px]" title={item.issue}>{item.issue}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                <div className="mt-3 text-center">
                    <span className="text-xs text-slate-400">Showing top 10 of {labs.length} issues</span>
                </div>
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

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {sites.map((site, i) => (
                    <div key={i} className="p-4 bg-rose-50 dark:bg-rose-900/10 rounded-xl border border-rose-100 dark:border-rose-900/20 hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start mb-2">
                            <div className="font-bold text-slate-800 dark:text-white text-lg">Site {site.site_id}</div>
                            <div className="text-xs px-2 py-1 bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 rounded-md font-bold">
                                DQI: {site.dqi}%
                            </div>
                        </div>
                        <div className="text-sm text-slate-500 mb-3 truncate">CRA Responsible: <span className="font-medium text-slate-700 dark:text-slate-300">{site.cra_name || "Unassigned"}</span></div>
                        <div className="flex items-center gap-2 text-rose-600 dark:text-rose-400 text-sm font-bold bg-white dark:bg-slate-800 p-2 rounded-lg border border-rose-100 dark:border-rose-900/30">
                            <AlertCircle className="w-4 h-4" />
                            {site.pending_queries} Pending Queries
                        </div>
                    </div>
                ))}
                {sites.length === 0 && (
                    <div className="col-span-full text-center text-slate-400 py-12 bg-slate-50 dark:bg-slate-900 rounded-xl border border-dashed border-slate-200 dark:border-slate-700">
                        <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-emerald-500" />
                        <p>All sites performing well</p>
                    </div>
                )}
            </div>
        </motion.div>
    );
};
