import React, { useEffect, useState } from 'react';
import { ShieldCheck, AlertOctagon, FileMinus, Search } from 'lucide-react';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const BASE_URL = 'http://127.0.0.1:8000';

const COLORS = ['#10b981', '#f59e0b', '#ef4444'];

/**
 * CodingStatusWidget
 * Displays pie charts for MedDRA and WHODrug coding status
 */
export const CodingStatusWidget = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${BASE_URL}/analytics/coding-status`)
            .then(res => res.json())
            .then(data => {
                setData(data);
                setLoading(false);
            })
            .catch(err => {
                console.error('Error fetching coding status:', err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div className="text-slate-400">Loading coding metrics...</div>;
    if (!data) return null;

    const meddraData = [
        { name: 'Coded', value: data.meddra.coded },
        { name: 'Uncoded', value: data.meddra.uncoded }
    ];

    const whoData = [
        { name: 'Coded', value: data.whodrug.coded },
        { name: 'Uncoded', value: data.whodrug.uncoded }
    ];

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 col-span-1 lg:col-span-2"
        >
            <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-emerald-100 dark:bg-emerald-900/20 rounded-lg">
                    <ShieldCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">Medical Coding Status</h3>
                    <p className="text-xs text-slate-500">MedDRA & WHODrug Progress</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* MedDRA */}
                <div className="flex flex-col items-center">
                    <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">MedDRA (Medical History)</h4>
                    <div className="h-48 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={meddraData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={40}
                                    outerRadius={60}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    <Cell key="coded" fill="#10b981" />
                                    <Cell key="uncoded" fill="#ef4444" />
                                </Pie>
                                <Tooltip />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="text-center mt-2">
                        <div className="text-2xl font-bold text-slate-800 dark:text-white">{((data.meddra.coded / data.meddra.total) * 100).toFixed(1)}%</div>
                        <div className="text-xs text-slate-500">Completion Rate</div>
                    </div>
                </div>

                {/* WHODrug */}
                <div className="flex flex-col items-center">
                    <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">WHODrug (Medication)</h4>
                    <div className="h-48 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={whoData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={40}
                                    outerRadius={60}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    <Cell key="coded" fill="#3b82f6" />
                                    <Cell key="uncoded" fill="#f59e0b" />
                                </Pie>
                                <Tooltip />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="text-center mt-2">
                        <div className="text-2xl font-bold text-slate-800 dark:text-white">{((data.whodrug.coded / data.whodrug.total) * 100).toFixed(1)}%</div>
                        <div className="text-xs text-slate-500">Completion Rate</div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

/**
 * EDRRWidget
 * List of top subjects with open issues
 */
export const EDRRWidget = () => {
    const [issues, setIssues] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${BASE_URL}/analytics/edrr-status`)
            .then(res => res.json())
            .then(data => {
                setIssues(data);
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
                <div className="p-2 bg-orange-100 dark:bg-orange-900/20 rounded-lg">
                    <AlertOctagon className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">EDRR Issues</h3>
                    <p className="text-xs text-slate-500">3rd Party Data Reconciliation</p>
                </div>
            </div>

            <div className="overflow-hidden">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-slate-500 uppercase bg-slate-50 dark:bg-slate-700/50">
                        <tr>
                            <th className="px-3 py-2">Subject</th>
                            <th className="px-3 py-2 text-right">Open Issues</th>
                        </tr>
                    </thead>
                    <tbody>
                        {issues.map((item, i) => (
                            <tr key={i} className="border-b border-slate-100 dark:border-slate-700">
                                <td className="px-3 py-2 font-medium text-slate-800 dark:text-slate-200">{item.subject}</td>
                                <td className="px-3 py-2 text-right text-orange-600 font-bold">{item.count}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </motion.div>
    );
};

/**
 * AuditLogWidget
 * Recent inactivated forms
 */
export const AuditLogWidget = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${BASE_URL}/analytics/inactivated-audit`)
            .then(res => res.json())
            .then(data => {
                setLogs(data.slice(0, 5));
                setLoading(false);
            })
            .catch(err => setLoading(false));
    }, []);

    if (loading) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 col-span-1 lg:col-span-3"
        >
            <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg">
                    <FileMinus className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">Inactivated Forms Log</h3>
                    <p className="text-xs text-slate-500">Recent Audit Trail</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {logs.map((log, i) => (
                    <div key={i} className="p-3 bg-slate-50 dark:bg-slate-700/30 rounded-lg border border-slate-100 dark:border-slate-700">
                        <div className="text-xs text-slate-400 mb-1">{log.site} • {log.subject}</div>
                        <div className="font-medium text-slate-700 dark:text-slate-200 truncate" title={log.form}>{log.form}</div>
                        <div className="mt-2 text-xs px-2 py-1 bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 rounded inline-block">
                            {log.action}
                        </div>
                    </div>
                ))}
            </div>
        </motion.div>
    );
};
