
import React, { useEffect, useState } from 'react';
import { AlertTriangle, TrendingUp, Activity, CheckCircle, Search, Filter, Sparkles, ArrowUpDown, Clock, AlertCircle, Brain } from 'lucide-react';
import { motion } from 'framer-motion';
import Modal from '../components/Modal';
import CommentModal from '../components/CommentModal';
import SiteDetailsModal from '../components/SiteDetailsModal';
import AgentExplanationModal from '../components/AgentExplanationModal';
import MLInsightsPanel from '../components/MLInsightsPanel';

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
    const { riskData, readiness, loading, fetchRiskMonitorData, generateReport } = useClinicalData();
    const [filterOpen, setFilterOpen] = useState(false);
    const [selectedStudy, setSelectedStudy] = useState('All');
    const [commentModalOpen, setCommentModalOpen] = useState(false);
    const [detailsModalOpen, setDetailsModalOpen] = useState(false);
    const [agentModalOpen, setAgentModalOpen] = useState(false);
    const [ mlInsightsOpen, setMlInsightsOpen ] = useState( false );
    const [selectedSite, setSelectedSite] = useState(null);
    const [ mlInsightsSite, setMlInsightsSite ] = useState( null );
    const [currentPage, setCurrentPage] = useState(1);
    const pageSize = 25;

    useEffect(() => {
        fetchRiskMonitorData();
    }, [fetchRiskMonitorData]);

    useEffect(() => {
        // Reset to first page when search or study filter changes
        setCurrentPage(1);
    }, [searchQuery, selectedStudy]);

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
                const aVal = a[sortConfig.key] ?? 0;
                const bVal = b[sortConfig.key] ?? 0;
                if (aVal < bVal) {
                    return sortConfig.direction === 'ascending' ? -1 : 1;
                }
                if (aVal > bVal) {
                    return sortConfig.direction === 'ascending' ? 1 : -1;
                }
                return 0;
            });
        }
        return sortableItems;
    }, [filteredData, sortConfig]);

    const paginatedData = React.useMemo(() => {
        const start = (currentPage - 1) * pageSize;
        return sortedData.slice(start, start + pageSize);
    }, [sortedData, currentPage, pageSize]);

    const totalPages = Math.ceil(sortedData.length / pageSize);

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

    const getRecommendation = (risk, missing, sae, deviations) => {
        if (risk === "High") {
            if (deviations > 5) return "Investigative Audit: High Protocol Deviations detected.";
            if (missing > 50) return "Data Clean-up Drive: Significant backlog of missing pages.";
            if (sae > 10) return "Medical Monitoring: Urgent SAE review required.";
            return "Enhanced Surveillance: Multiple high-risk indicators identified.";
        } else if (risk === "Medium") {
            if (missing > 20) return "Targeted SDV: Focus on missing core CRF pages.";
            return "Remote Monitoring: Review unreviewed SAEs and queries.";
        } else {
            return "Routine Surveillance: Site performance within nominal range.";
        }
    };

    const getActionStatus = (status) => {
        if (!status || status === 'No Action') return { color: 'text-slate-400 italic', label: '-' };
        if (status === 'Urgent') return { color: 'bg-rose-100 text-rose-700 border border-rose-200', label: 'Urgent' };
        if (status === 'Review') return { color: 'bg-amber-100 text-amber-700 border border-amber-200', label: 'Review' };
        if (status === 'Resolved') return { color: 'bg-emerald-100 text-emerald-700 border border-emerald-200', label: 'Resolved' };
        if (status === 'Info') return { color: 'bg-blue-50 text-blue-600 border border-blue-200', label: 'Info' };
        return { color: 'bg-slate-100 text-slate-600', label: status };
    };

    if (loading) return (
        <div className="space-y-6 animate-pulse">
            {/* Header skeleton */}
            <div className="flex items-center justify-between mb-2">
                <div>
                    <div className="h-7 w-40 bg-slate-200 dark:bg-slate-700 rounded-lg mb-2" />
                    <div className="h-4 w-72 bg-slate-100 dark:bg-slate-800 rounded" />
                </div>
                <div className="flex gap-2">
                    <div className="h-9 w-32 bg-slate-200 dark:bg-slate-700 rounded-lg" />
                    <div className="h-9 w-40 bg-blue-200 dark:bg-blue-900/40 rounded-lg" />
                </div>
            </div>
            {/* Summary cards skeleton */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm h-20" />
                ))}
            </div>
            {/* Table skeleton */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700 h-12 bg-slate-50 dark:bg-slate-800/50" />
                <div className="divide-y divide-slate-100 dark:divide-slate-700">
                    {[...Array(8)].map((_, i) => (
                        <div key={i} className="flex gap-4 px-6 py-4">
                            <div className="h-4 w-20 bg-slate-200 dark:bg-slate-700 rounded" />
                            <div className="h-4 w-10 bg-slate-100 dark:bg-slate-800 rounded" />
                            <div className="h-4 w-24 bg-slate-100 dark:bg-slate-800 rounded" />
                            <div className="h-4 flex-1 bg-slate-100 dark:bg-slate-800 rounded" />
                            <div className="h-4 w-16 bg-slate-200 dark:bg-slate-700 rounded" />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );

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
                <div className={ `bg-white dark:bg-slate-800 p-5 rounded-2xl border ${ readiness?.is_ready ? 'border-emerald-100 dark:border-emerald-900/30 shadow-emerald-100/50' : 'border-blue-100 dark:border-blue-900/30' } shadow-sm flex items-start gap-3 transition-all duration-500` }>
                    <div className={ `p-2.5 rounded-xl ${ readiness?.is_ready ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-500' : 'bg-blue-50 dark:bg-blue-900/20 text-blue-500' }` }>
                        { readiness?.is_ready ? <CheckCircle className="w-5 h-5" /> : <TrendingUp className="w-5 h-5" /> }
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Study Readiness</p>
                            { readiness?.is_ready ?
                                <span className="bg-emerald-500 text-white text-[8px] font-bold px-1 rounded">READY</span> :
                                <span className="bg-amber-500 text-white text-[8px] font-bold px-1 rounded">IN PROGRESS</span>
                            }
                        </div>
                        <h3 className={ `text-xl font-bold ${ readiness?.is_ready ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-800 dark:text-white' }` }>
                            { readiness?.readiness_score || 0 }%
                        </h3>
                        <p className="text-[10px] text-slate-400 mt-1">
                            Threshold: { readiness?.threshold || 95 }% for Interim Analysis
                        </p>
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
                                    <th className="px-6 py-3">Latest Action</th>
                                    <th className="px-6 py-3">SAEs</th>
                                    <th className="px-6 py-3">Deviations</th>
                                    <th className="px-6 py-3">Heuristic Risk</th>
                                    <th className="px-6 py-3">AI Prediction</th>
                                    <th className="px-6 py-3">Status</th>
                                    <th className="px-6 py-3">Recommendation</th>
                                    <th className="px-6 py-3">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                                {paginatedData.map((site, index) => (
                                    <motion.tr
                                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: Math.min(index, 10) * 0.03 }}
                                        key={site.site} className="hover:bg-slate-50/80 dark:hover:bg-slate-700/50 transition-colors"
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
                                        <td className="px-6 py-4">
                                            <span className={ `px-2 py-0.5 rounded-full text-[10px] font-bold ${ site.action_status === 'Resolved' ? 'bg-emerald-100 text-emerald-700' :
                                                    site.action_status === 'Urgent' ? 'bg-rose-100 text-rose-700' :
                                                        'bg-blue-100 text-blue-700'
                                                }` }>
                                                { site.action_status || 'Open' }
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-slate-500 dark:text-slate-400 font-medium">{site.sae_count}</td>
                                        <td className="px-6 py-4 text-slate-500 dark:text-slate-400">{site.protocol_deviations}</td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${getSiteRiskStatus(site.risk_level).color}`}>
                                                {site.risk_level}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <button
                                                onClick={ () => { setMlInsightsSite( site.site ); setMlInsightsOpen( true ); } }
                                                className="flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors group"
                                                title="Click for ML prediction details"
                                            >
                                                <Brain className={ `w-3 h-3 ${ getMLRiskStatus( site.predicted_risk ).color } group-hover:text-indigo-500` } />
                                                <span className={ `text-[10px] font-bold ${ getMLRiskStatus( site.predicted_risk ).color } group-hover:text-indigo-600` }>
                                                    {site.predicted_risk}
                                                </span>
                                                <Sparkles className="w-2.5 h-2.5 text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </button>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide ${getActionStatus(site.action_status).color}`}>
                                                {getActionStatus(site.action_status).label}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-slate-500 dark:text-slate-400 text-xs italic">
                                            {getRecommendation(site.risk_level, site.missing_pages, site.sae_count, site.protocol_deviations)}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-1">
                                                <button onClick={() => { setSelectedSite(site.site); setCommentModalOpen(true); }} className="text-blue-600 hover:text-blue-800 text-[10px] font-bold uppercase tracking-wider">Comment</button>
                                                <button onClick={() => { setSelectedSite(site.site); setDetailsModalOpen(true); }} className="text-indigo-600 hover:text-indigo-800 text-[10px] font-bold uppercase tracking-wider">Patients</button>
                                                <button onClick={() => { setSelectedSite(site.site); setAgentModalOpen(true); }} className="text-violet-600 hover:text-violet-800 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1"><Sparkles className="w-3 h-3" /> Explain</button>
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
                
                {/* Pagination Controls */}
                {filteredData.length > pageSize && (
                    <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-700 flex items-center justify-between bg-white dark:bg-slate-800">
                        <div className="text-xs text-slate-500">
                            Showing <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> to <span className="font-medium">{Math.min(currentPage * pageSize, sortedData.length)}</span> of <span className="font-medium">{sortedData.length}</span> sites
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                                disabled={currentPage === 1}
                                className="px-3 py-1 border border-slate-200 dark:border-slate-700 rounded text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50"
                            >
                                Previous
                            </button>
                            <div className="flex items-center gap-1">
                                {[...Array(Math.min(5, totalPages))].map((_, i) => {
                                    let pageNum;
                                    if (totalPages <= 5) pageNum = i + 1;
                                    else if (currentPage <= 3) pageNum = i + 1;
                                    else if (currentPage >= totalPages - 2) pageNum = totalPages - 4 + i;
                                    else pageNum = currentPage - 2 + i;
                                    
                                    return (
                                        <button
                                            key={pageNum}
                                            onClick={() => setCurrentPage(pageNum)}
                                            className={`w-8 h-8 rounded text-xs font-medium transition-colors ${currentPage === pageNum ? 'bg-blue-600 text-white' : 'hover:bg-slate-100 dark:hover:bg-slate-700'}`}
                                        >
                                            {pageNum}
                                        </button>
                                    );
                                })}
                            </div>
                            <button
                                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                                disabled={currentPage === totalPages}
                                className="px-3 py-1 border border-slate-200 dark:border-slate-700 rounded text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50"
                            >
                                Next
                            </button>
                        </div>
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

            <AgentExplanationModal
                isOpen={agentModalOpen}
                onClose={() => setAgentModalOpen(false)}
                siteNumber={selectedSite}
            />

            <MLInsightsPanel
                siteId={ mlInsightsSite }
                isOpen={ mlInsightsOpen }
                onClose={ () => { setMlInsightsOpen( false ); setMlInsightsSite( null ); } }
            />
        </div>
    );
};

export default RiskMonitor;
