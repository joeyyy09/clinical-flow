import React, { useEffect, useState } from 'react';
import { AlertTriangle, Beaker, Calendar } from 'lucide-react';
import { motion } from 'framer-motion';

const BASE_URL = 'http://127.0.0.1:8000';

/**
 * MissingVisitsWidget
 * Displays overdue visits from the Visit Projection Tracker
 */
export const MissingVisitsWidget = () => {
    const [visits, setVisits] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${BASE_URL}/analytics/missing-visits`)
            .then(res => res.json())
            .then(data => {
                setVisits(data.slice(0, 5)); // Top 5 most overdue
                setLoading(false);
            })
            .catch(err => {
                console.error('Error fetching missing visits:', err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div className="text-slate-400">Loading visits...</div>;

    const totalOverdue = visits.reduce((sum, v) => sum + v.days_outstanding, 0);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700"
        >
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-amber-100 dark:bg-amber-900/20 rounded-lg">
                        <Calendar className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-slate-800 dark:text-white">Overdue Visits</h3>
                        <p className="text-xs text-slate-500">Most urgent follow-ups</p>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">{visits.length}</div>
                    <div className="text-xs text-slate-500">{totalOverdue} days total</div>
                </div>
            </div>

            <div className="space-y-2">
                {visits.map((visit, idx) => (
                    <div
                        key={idx}
                        className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg"
                    >
                        <div className="flex-1">
                            <div className="text-sm font-medium text-slate-700 dark:text-slate-200">
                                {visit.subject} - {visit.visit}
                            </div>
                            <div className="text-xs text-slate-500">
                                Site {visit.site} | {visit.country}
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-sm font-bold text-amber-600 dark:text-amber-400">
                                {visit.days_outstanding}d
                            </div>
                            <div className="text-xs text-slate-500">overdue</div>
                        </div>
                    </div>
                ))}
            </div>

            {visits.length === 0 && (
                <div className="text-center text-slate-400 py-8">
                    ✓ All visits on schedule
                </div>
            )}
        </motion.div>
    );
};

/**
 * LabQualityWidget
 * Displays lab data gaps from Missing Lab Names/Ranges
 */
export const LabQualityWidget = () => {
    const [labGaps, setLabGaps] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${BASE_URL}/analytics/lab-gaps`)
            .then(res => res.json())
            .then(data => {
                setLabGaps(data.slice(0, 5)); // Top 5 issues
                setLoading(false);
            })
            .catch(err => {
                console.error('Error fetching lab gaps:', err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div className="text-slate-400">Loading lab data...</div>;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700"
        >
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                        <Beaker className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-slate-800 dark:text-white">Lab Quality Gaps</h3>
                        <p className="text-xs text-slate-500">Missing names/ranges</p>
                    </div>
                </div>
                <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {labGaps.length}
                </div>
            </div>

            <div className="space-y-2">
                {labGaps.map((lab, idx) => (
                    <div
                        key={idx}
                        className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg"
                    >
                        <div className="flex items-start justify-between mb-1">
                            <div className="text-sm font-medium text-slate-700 dark:text-slate-200">
                                {lab.test_name || 'Unknown Test'}
                            </div>
                            <span className="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full">
                                {lab.lab_category}
                            </span>
                        </div>
                        <div className="text-xs text-slate-500">
                            Site {lab.site_number} | {lab.subject}
                        </div>
                        <div className="text-xs text-rose-600 dark:text-rose-400 mt-1">
                            {lab.issue}
                        </div>
                    </div>
                ))}
            </div>

            {labGaps.length === 0 && (
                <div className="text-center text-slate-400 py-8">
                    ✓ No lab data gaps detected
                </div>
            )}
        </motion.div>
    );
};

/**
 * SAEReviewWidget
 * Displays SAE review status from DM and Safety dashboards
 */
export const SAEReviewWidget = () => {
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${BASE_URL}/analytics/sae-reviews`)
            .then(res => res.json())
            .then(data => {
                setReviews(data.slice(0, 5)); // Top 5 recent reviews
                setLoading(false);
            })
            .catch(err => {
                console.error('Error fetching SAE reviews:', err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div className="text-slate-400">Loading SAE reviews...</div>;

    const pendingCount = reviews.filter(r => r.review_status?.includes('Pending')).length;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700"
        >
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-rose-100 dark:bg-rose-900/20 rounded-lg">
                        <AlertTriangle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-slate-800 dark:text-white">SAE Reviews</h3>
                        <p className="text-xs text-slate-500">DM & Safety tracking</p>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-2xl font-bold text-rose-600 dark:text-rose-400">{pendingCount}</div>
                    <div className="text-xs text-slate-500">pending</div>
                </div>
            </div>

            <div className="space-y-2">
                {reviews.map((sae, idx) => (
                    <div
                        key={idx}
                        className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg"
                    >
                        <div className="flex items-start justify-between mb-1">
                            <div className="text-sm font-medium text-slate-700 dark:text-slate-200">
                                {sae.patient_id}
                            </div>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${sae.review_status?.includes('Complete')
                                ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300'
                                : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
                                }`}>
                                {sae.review_status || 'Unknown'}
                            </span>
                        </div>
                        <div className="text-xs text-slate-500">
                            Site {sae.site} | {sae.discrepancy_id}
                        </div>
                        <div className="text-xs text-slate-400 mt-1">
                            {sae.form_name}
                        </div>
                    </div>
                ))}
            </div>

            {reviews.length === 0 && (
                <div className="text-center text-slate-400 py-8">
                    ✓ No SAE reviews in queue
                </div>
            )}
        </motion.div>
    );
};
