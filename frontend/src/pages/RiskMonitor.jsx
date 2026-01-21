
import React, { useEffect, useState } from 'react';
import { AlertTriangle, TrendingUp, Activity, CheckCircle, Search, Filter, Sparkles, ArrowUpDown, Clock, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import Modal from '../components/Modal';
import CommentModal from '../components/CommentModal';
import SiteDetailsModal from '../components/SiteDetailsModal';

import { useClinicalData } from '../hooks/useClinicalData';

/**
 * RiskMonitor Page
 * 
 * A surveillance dashboard that tracks site performance metrics like 
 * DQI, SAE counts, and query resolution rates.
 * Provides advanced filtering, sorting, and automated risk report generation.
 * 
 * @param {Object} props
 * @param {string} props.searchQuery - The current search query from the global header.
 */
const RiskMonitor = ({ searchQuery = "" }) => {
    const { riskData, loading, fetchRiskMonitorData, generateReport } = useClinicalData();
    const [filterOpen, setFilterOpen] = useState(false);
    const [selectedStudy, setSelectedStudy] = useState('All');
    const [commentModalOpen, setCommentModalOpen] = useState(false);
    const [detailsModalOpen, setDetailsModalOpen] = useState(false);
    const [selectedSite, setSelectedSite] = useState(null);

    useEffect(() => {
        fetchRiskMonitorData();
    }, [fetchRiskMonitorData]);

    const handleGenerateReport = async () => {
        const success = await generateReport();
        if (!success) {
            alert("Failed to generate report");
        }
    };

    const filteredData = riskData.filter(site => {
        if (!site) return false;
        const matchesSearch =
            (site.site?.toLowerCase().includes(searchQuery.toLowerCase()) || false) ||
            (site.country?.toLowerCase().includes(searchQuery.toLowerCase()) || false) ||
            (site.risk_level?.toLowerCase().includes(searchQuery.toLowerCase()) || false);

        const matchesStudy = selectedStudy === 'All' || site.study_id === selectedStudy;

        return matchesSearch && matchesStudy;
    });

    const [sortConfig, setSortConfig] = useState({ key: 'dqi', direction: 'ascending' });

    const sortedData = React.useMemo(() => {
        let sortableItems = [...filteredData];
        if (sortConfig !== null) {
            sortableItems.sort((a, b) => {
                if (a[sortConfig.key] < b[sortConfig.key]) {
                    return sortConfig.direction === 'ascending' ? -1 : 1;
                }
                if (a[sortConfig.key] > b[sortConfig.key]) {
                    return sortConfig.direction === 'ascending' ? 1 : -1;
                }
                return 0;
            });
        }
        return sortableItems;
    }, [filteredData, sortConfig]);

    const requestSort = (key) => {
        let direction = 'ascending';
        if (sortConfig.key === key && sortConfig.direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ key, direction });
    };

    const getSiteRiskStatus = (level) => {
        switch (level) {
            case 'High': return { color: 'bg-rose-100 dark:bg-rose-900/30 text-rose-600 dark:text-rose-400', icon: AlertCircle };
            case 'Medium': return { color: 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400', icon: Clock };
            case 'Low': return { color: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400', icon: CheckCircle };
            default: return { color: 'bg-slate-100 dark:bg-slate-900/30 text-slate-600 dark:text-slate-400', icon: Activity };
        }
    };

    const getMLRiskStatus = (level) => {
        switch (level) {
            case 'High': return { color: 'text-rose-500', icon: Sparkles };
            case 'Medium': return { color: 'text-amber-500', icon: Sparkles };
            case 'Low': return { color: 'text-emerald-500', icon: Sparkles };
            default: return { color: 'text-slate-400', icon: Sparkles };
        }
    };

    if (loading) return <div className="p-8 text-slate-400">Loading risk analysis engine...</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between mb-2">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800 dark:text-white">Risk Monitor</h2>
                    <p className="text-slate-500 dark:text-slate-400 text-sm">Real-time surveillance of operational bottlenecks and safety signals.</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setFilterOpen(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                    >
                        <Filter className="w-4 h-4" />
                        {selectedStudy === 'All' ? 'Filter by Study' : selectedStudy}
                    </button>
                    <button
                        onClick={handleGenerateReport}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 shadow-lg shadow-blue-500/30 transition-all hover:scale-105 active:scale-95"
                    >
                        Generate Risk Report
                    </button>
                </div>
            </div>

            {/* Risk Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-rose-100 dark:border-rose-900/30 shadow-sm flex items-start gap-3">
                    <div className="p-2.5 bg-rose-50 dark:bg-rose-900/20 rounded-xl text-rose-500">
                        <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div>
                        <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Critical Sites</p>
                        <h3 className="text-xl font-bold text-slate-800 dark:text-white">{riskData.filter(r => r.risk_level === 'High').length}</h3>
                    </div>
                </div>
                <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-amber-100 dark:border-amber-900/30 shadow-sm flex items-start gap-3">
                    <div className="p-2.5 bg-amber-50 dark:bg-amber-900/20 rounded-xl text-amber-500">
                        <Activity className="w-5 h-5" />
                    </div>
                    <div>
                        <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Under Surveillance</p>
                        <h3 className="text-xl font-bold text-slate-800 dark:text-white">{riskData.filter(r => r.risk_level === 'Medium').length}</h3>
                    </div>
                </div>
                <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-emerald-100 dark:border-emerald-900/30 shadow-sm flex items-start gap-3">
                    <div className="p-2.5 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl text-emerald-500">
                        <CheckCircle className="w-5 h-5" />
                    </div>
                    <div>
                        <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Clean Sites</p>
                        <h3 className="text-xl font-bold text-slate-800 dark:text-white">{riskData.filter(r => (r.clean_patient_rate || 0) > 80).length}</h3>
                    </div>
                </div>
                <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-blue-100 dark:border-blue-900/30 shadow-sm flex items-start gap-3">
                    <div className="p-2.5 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-blue-500">
                        <TrendingUp className="w-5 h-5" />
                    </div>
                    <div>
                        <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Avg Readiness</p>
                        <h3 className="text-xl font-bold text-slate-800 dark:text-white">
                            {riskData.length > 0 ? Math.round(riskData.reduce((acc, curr) => acc + (curr.milestone_readiness || 0), 0) / riskData.length) : 0}%
                        </h3>
                    </div>
                </div>
            </div>

            {/* Detailed Table */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden min-h-[400px] transition-colors">
                <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center bg-slate-50/50 dark:bg-slate-800/50">
                    <h3 className="font-semibold text-slate-700 dark:text-slate-200">Scientific Operational Metrics</h3>
                    <div className="text-xs text-slate-400">Total Analyzed: {filteredData.length} Sites</div>
                </div>
                {filteredData.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 font-medium">
                                <tr>
                                    <th className="px-6 py-3 cursor-pointer" onClick={() => requestSort('site')}>Site ID</th>
                                    <th className="px-6 py-3 cursor-pointer" onClick={() => requestSort('dqi')}>DQI</th>
                                    <th className="px-6 py-3">Clean Patient %</th>
                                    <th className="px-6 py-3">Readiness</th>
                                    <th className="px-6 py-3">SAEs</th>
                                    <th className="px-6 py-3">Deviations</th>
                                    <th className="px-6 py-3">Heuristic Risk</th>
                                    <th className="px-6 py-3">AI Prediction</th>
                                    <th className="px-6 py-3">Recommendation</th>
                                    <th className="px-6 py-3">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                                {sortedData.map((site, index) => (
                                    <motion.tr
                                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: index * 0.05 }}
                                        key={index} className="hover:bg-slate-50/80 dark:hover:bg-slate-700/50 transition-colors"
                                    >
                                        <td className="px-6 py-4 font-medium text-slate-700 dark:text-slate-200">{site.site}</td>
                                        <td className="px-6 py-4">
                                            <span className={`font-bold ${(site.dqi || 0) < 50 ? 'text-rose-500' : (site.dqi || 0) < 80 ? 'text-amber-500' : 'text-emerald-500'}`}>
                                                {site.dqi}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-1 w-24">
                                                <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                                    <div className={`h-full bg-emerald-500`} style={{ width: `${site.clean_patient_rate}%` }} />
                                                </div>
                                                <span className="text-[10px] text-slate-500">{site.clean_patient_rate}% Clean</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-1 w-24">
                                                <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                                    <div className={`h-full bg-blue-500`} style={{ width: `${site.milestone_readiness}%` }} />
                                                </div>
                                                <span className="text-[10px] text-slate-500">{site.milestone_readiness}% Ready</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-slate-500 dark:text-slate-400 font-medium">{site.sae_count}</td>
                                        <td className="px-6 py-4 text-slate-500 dark:text-slate-400">{site.protocol_deviations}</td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${getSiteRiskStatus(site.risk_level).color}`}>
                                                {site.risk_level}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-1">
                                                <Sparkles className={`w-3 h-3 ${getMLRiskStatus(site.predicted_risk).color}`} />
                                                <span className={`text-[10px] font-bold ${getMLRiskStatus(site.predicted_risk).color}`}>
                                                    {site.predicted_risk}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-slate-500 dark:text-slate-400 text-xs italic">{site.recommendation}</td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-1">
                                                <button onClick={() => { setSelectedSite(site.site); setCommentModalOpen(true); }} className="text-blue-600 hover:text-blue-800 text-[10px] font-bold uppercase tracking-wider">Comment</button>
                                                <button onClick={() => { setSelectedSite(site.site); setDetailsModalOpen(true); }} className="text-indigo-600 hover:text-indigo-800 text-[10px] font-bold uppercase tracking-wider">Patients</button>
                                            </div>
                                        </td>
                                    </motion.tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="p-12 text-center text-slate-400">
                        <Search className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p>No sites match your search criteria.</p>
                        <button onClick={() => window.location.reload()} className="text-blue-600 dark:text-blue-400 text-sm mt-2 hover:underline">
                            Clear filters
                        </button>
                    </div>
                )}
            </div>

            <Modal isOpen={filterOpen} onClose={() => setFilterOpen(false)} title="Filter by Study">
                <div className="space-y-2">
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">Select a study to isolate specific site risks.</p>
                    {['All', 'Study 101 (Oncology)', 'Study 202 (Cardio)', 'Study 303 (Neuro)'].map((study) => (
                        <button
                            key={study}
                            onClick={() => { setSelectedStudy(study); setFilterOpen(false); }}
                            className={`w-full text-left px-4 py-3 rounded-lg border text-sm font-medium transition-colors ${selectedStudy === study
                                    ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-500 text-blue-700 dark:text-blue-400'
                                    : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
                                }`}
                        >
                            {study}
                        </button>
                    ))}
                </div>
            </Modal>

            <CommentModal
                isOpen={commentModalOpen}
                onClose={() => setCommentModalOpen(false)}
                siteNumber={selectedSite}
            />

            <SiteDetailsModal
                isOpen={detailsModalOpen}
                onClose={() => setDetailsModalOpen(false)}
                siteNumber={selectedSite}
            />
        </div>
    );
};

export default RiskMonitor;
