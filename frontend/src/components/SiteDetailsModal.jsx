
import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import { User, CheckCircle, AlertCircle, FileText, Activity } from 'lucide-react';

const SiteDetailsModal = ({ isOpen, onClose, siteNumber }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen && siteNumber) {
            fetchData();
        }
    }, [isOpen, siteNumber]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const res = await fetch(`http://127.0.0.1:8000/sites/${siteNumber}/patients`);
            const json = await res.json();
            setData(json);
        } catch (error) {
            console.error("Failed to fetch site details", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={`Site Analysis: ${siteNumber}`}>
            {loading ? (
                <div className="p-8 text-center text-slate-400">Loading patient data...</div>
            ) : data ? (
                <div className="space-y-6">
                    {/* Summary Stats */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl border border-blue-100 dark:border-blue-800">
                            <p className="text-blue-600 dark:text-blue-400 text-xs font-semibold uppercase">Total Subjects</p>
                            <h4 className="text-2xl font-bold text-slate-800 dark:text-white mt-1">{data.total_patients}</h4>
                        </div>
                        <div className="bg-emerald-50 dark:bg-emerald-900/20 p-4 rounded-xl border border-emerald-100 dark:border-emerald-800">
                            <p className="text-emerald-600 dark:text-emerald-400 text-xs font-semibold uppercase">Clean Patient Rate</p>
                            <h4 className="text-2xl font-bold text-slate-800 dark:text-white mt-1">{data.clean_patient_rate}%</h4>
                            <p className="text-[10px] text-emerald-600/70">{(data.topics.filter(p => p.is_clean).length)} / {data.total_patients} subjects clean</p>
                        </div>
                    </div>

                    {/* Patient List */}
                    <div>
                        <h4 className="font-semibold text-slate-700 dark:text-slate-200 mb-3 flex items-center gap-2">
                            <User className="w-4 h-4" /> Patient Roster
                        </h4>
                        <div className="max-h-[300px] overflow-y-auto space-y-2 pr-2">
                            {data.topics.map((patient, i) => (
                                <div key={i} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-100 dark:border-slate-700">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-full ${patient.is_clean ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'}`}>
                                            {patient.is_clean ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                                        </div>
                                        <div>
                                            <p className="font-medium text-slate-700 dark:text-slate-200 text-sm">{patient.subject_id}</p>
                                            <p className="text-xs text-slate-400">Last Visit: {patient.last_visit}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3 text-xs">
                                        {!patient.is_clean && (
                                            <>
                                                {patient.missing_pages > 0 && (
                                                    <span className="flex items-center gap-1 text-amber-600 bg-amber-50 px-2 py-1 rounded">
                                                        <FileText className="w-3 h-3" /> {patient.missing_pages} Pages Missing
                                                    </span>
                                                )}
                                                {patient.sae_pending > 0 && (
                                                    <span className="flex items-center gap-1 text-rose-600 bg-rose-50 px-2 py-1 rounded">
                                                        <Activity className="w-3 h-3" /> {patient.sae_pending} SAE Pending
                                                    </span>
                                                )}
                                            </>
                                        )}
                                        {patient.is_clean && <span className="text-emerald-600 font-medium">Ready for Lock</span>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            ) : (
                <div className="text-center text-slate-400">No patient data available.</div>
            )}
        </Modal>
    );
};

export default SiteDetailsModal;
