
import React, { useEffect, useState } from 'react';
import { AlertTriangle, TrendingUp, Activity, CheckCircle, Search, Filter } from 'lucide-react';
import { motion } from 'framer-motion';
import Modal from '../components/Modal';

const RiskMonitor = ({ searchQuery }) => {
  const [riskData, setRiskData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterOpen, setFilterOpen] = useState(false);
  const [selectedStudy, setSelectedStudy] = useState('All');

  useEffect(() => {
    fetch('http://localhost:8000/analytics/risk-monitor')
      .then(res => res.json())
      .then(data => {
          setRiskData(data);
          setLoading(false);
      })
      .catch(err => console.error("Risk API Error", err));
  }, []);

  const filteredData = riskData.filter(site => {
      const matchesSearch = 
        site.site.toLowerCase().includes(searchQuery.toLowerCase()) || 
        site.country.toLowerCase().includes(searchQuery.toLowerCase()) ||
        site.risk_level.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesStudy = selectedStudy === 'All' || site.study_id === selectedStudy;
      
      return matchesSearch && matchesStudy;
  });

  const handleGenerateReport = async () => {
    try {
        const response = await fetch('http://127.0.0.1:8000/reports/generate', {
            method: 'POST',
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = "risk_assessment_report.pdf";
            document.body.appendChild(a);
            a.click();
            a.remove();
        } else {
            alert("Failed to generate report");
        }
    } catch (error) {
        console.error("Report generation failed", error);
        alert("Error generating report");
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
         <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-rose-100 dark:border-rose-900/30 shadow-sm flex items-start gap-4 transition-colors">
            <div className="p-3 bg-rose-50 dark:bg-rose-900/20 rounded-xl text-rose-500 dark:text-rose-400">
                <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
                <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">High Risk Sites</p>
                <h3 className="text-2xl font-bold text-slate-800 dark:text-white">{riskData.filter(r => r.risk_level === 'High').length}</h3>
                <p className="text-xs text-rose-500 dark:text-rose-400 mt-1 font-medium">Immediate Action Required</p>
            </div>
         </div>
         <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-amber-100 dark:border-amber-900/30 shadow-sm flex items-start gap-4 transition-colors">
            <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl text-amber-500 dark:text-amber-400">
                <Activity className="w-6 h-6" />
            </div>
            <div>
                <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Medium Risk Sites</p>
                <h3 className="text-2xl font-bold text-slate-800 dark:text-white">{riskData.filter(r => r.risk_level === 'Medium').length}</h3>
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-1 font-medium">Monitor Closely</p>
            </div>
         </div>
         <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm flex items-start gap-4 transition-colors">
            <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl text-emerald-500 dark:text-emerald-400">
                <CheckCircle className="w-6 h-6" />
            </div>
            <div>
                <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Low Risk Sites</p>
                <h3 className="text-2xl font-bold text-slate-800 dark:text-white">{riskData.filter(r => r.risk_level === 'Low').length}</h3>
                <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1 font-medium">Performing Well</p>
            </div>
         </div>
      </div>

      {/* Detailed Table */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden min-h-[400px] transition-colors">
         <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center bg-slate-50/50 dark:bg-slate-800/50">
             <h3 className="font-semibold text-slate-700 dark:text-slate-200">Detailed Site Analysis</h3>
             <div className="text-xs text-slate-400 italic">Showing {filteredData.length} records</div>
         </div>
         {filteredData.length > 0 ? (
             <table className="w-full text-sm text-left">
                 <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 font-medium">
                     <tr>
                         <th className="px-6 py-3">Site ID</th>
                         <th className="px-6 py-3">Country</th>
                         <th className="px-6 py-3">Missing Pages</th>
                         <th className="px-6 py-3">SAE Count</th>
                         <th className="px-6 py-3">Risk Level</th>
                         <th className="px-6 py-3">AI Recommendation</th>
                     </tr>
                 </thead>
                 <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                     {filteredData.map((site, index) => (
                         <motion.tr 
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: index * 0.05 }}
                            key={index} className="hover:bg-slate-50/80 dark:hover:bg-slate-700/50 transition-colors"
                         >
                             <td className="px-6 py-4 font-medium text-slate-700 dark:text-slate-200">{site.site}</td>
                             <td className="px-6 py-4 text-slate-500 dark:text-slate-400">{site.country}</td>
                             <td className="px-6 py-4 text-slate-500 dark:text-slate-400">{site.missing_pages}</td>
                             <td className="px-6 py-4 text-slate-500 dark:text-slate-400">{site.sae_count}</td>
                             <td className="px-6 py-4">
                                 <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                                     site.risk_level === 'High' ? 'bg-rose-100 dark:bg-rose-900/30 text-rose-600 dark:text-rose-400' :
                                     site.risk_level === 'Medium' ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400' :
                                     'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400'
                                 }`}>
                                     {site.risk_level}
                                 </span>
                             </td>
                             <td className="px-6 py-4 text-slate-500 dark:text-slate-400 text-xs italic">{site.recommendation}</td>
                         </motion.tr>
                     ))}
                 </tbody>
             </table>
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
                    className={`w-full text-left px-4 py-3 rounded-lg border text-sm font-medium transition-colors ${
                        selectedStudy === study 
                            ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-500 text-blue-700 dark:text-blue-400' 
                            : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
                    }`}
                  >
                      {study}
                  </button>
              ))}
          </div>
      </Modal>
    </div>
  );
};

export default RiskMonitor;
