
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { motion } from 'framer-motion';

/**
 * InteractiveConfusionMatrix
 * 
 * Renders a 3x3 Grid showing predicted vs actual risk.
 * Cells are colored based on density.
 */
export const InteractiveConfusionMatrix = ({ data }) => {
    if (!data || !data.length) return <div className="text-slate-400 text-sm">No validation data available</div>;

    // Flatten the matrix for easier max calculation
    const flattened = data.flat();
    const maxVal = Math.max(...flattened) || 1;

    // Labels for the axes
    const labels = ['Low', 'Med', 'High'];

    return (
        <div className="flex flex-col h-full w-full items-center justify-center p-2">
            <div className="flex flex-row items-center justify-center gap-4">
                {/* Y Axis Label */}
                <div className="w-6 flex items-center justify-center">
                    <div className="-rotate-90 text-[10px] font-bold text-slate-400 uppercase tracking-widest whitespace-nowrap">
                        Actual Risk
                    </div>
                </div>

                {/* Matrix Grid */}
                <div className="flex flex-col">
                    <div className="grid grid-cols-3 gap-1 md:gap-2 relative">
                        {data.map((row, actualIdx) => (
                            row.map((count, predIdx) => {
                                // Calculate intensity (0.1 to 1.0)
                                const intensity = count === 0 ? 0.05 : 0.2 + (count / maxVal) * 0.8;
                                const isHigh = intensity > 0.6;

                                return (
                                    <motion.div
                                        key={`${actualIdx}-${predIdx}`}
                                        whileHover={{ scale: 1.05, zIndex: 10 }}
                                        className="w-16 h-16 md:w-20 md:h-20 rounded-lg flex flex-col items-center justify-center text-center cursor-help transition-all relative group border border-slate-100 dark:border-slate-700/50"
                                        style={{ backgroundColor: `rgba(59, 130, 246, ${intensity})` }}
                                    >
                                        <span className={`text-lg md:text-xl font-bold ${isHigh ? 'text-white' : 'text-slate-700 dark:text-slate-200'}`}>
                                            {count}
                                        </span>

                                        {/* Tooltip */}
                                        <div className="absolute bottom-full mb-2 hidden group-hover:block z-50 w-48 bg-slate-900 text-white text-xs rounded-lg p-3 shadow-xl pointer-events-none text-left">
                                            <div className="font-semibold mb-1">Prediction Detail</div>
                                            <div className="grid grid-cols-2 gap-x-2 gap-y-1 opacity-90">
                                                <span>Actual:</span>
                                                <span className="font-medium text-right">{labels[actualIdx]}</span>
                                                <span>Predicted:</span>
                                                <span className="font-medium text-right">{labels[predIdx]}</span>
                                                <span className="col-span-2 border-t border-slate-700 my-1"></span>
                                                <span>Count:</span>
                                                <span className="font-medium text-right">{count} sites</span>
                                            </div>
                                        </div>
                                    </motion.div>
                                );
                            })
                        ))}
                    </div>

                    {/* X Axis Labels */}
                    <div className="grid grid-cols-3 gap-2 mt-2 text-center">
                        {labels.map(l => (
                            <span key={l} className="text-[10px] font-bold text-slate-400 uppercase">{l}</span>
                        ))}
                    </div>
                    <div className="text-center text-[10px] text-slate-400 mt-1 uppercase tracking-widest">Predicted Risk</div>
                </div>
            </div>

            {/* Footer Explanation */}
            <div className="mt-4 text-center px-4 max-w-xs">
                <p className="text-[10px] text-slate-400 italic">
                    *Diagonal boxes show correct predictions.
                </p>
            </div>
        </div>
    );
};

/**
 * InteractiveFeatureImportance
 * 
 * Renders a horizontal bar chart of feature drivers.
 */
export const InteractiveFeatureImportance = ({ data }) => {
    if (!data || !data.length) return <div className="text-slate-400 text-sm">No feature data available</div>;

    // Take top 8 features and reverse for top-to-bottom rendering
    const chartData = [...data].sort((a, b) => b.importance - a.importance).slice(0, 8);

    return (
        <ResponsiveContainer width="100%" height={300}>
            <BarChart layout="vertical" data={chartData} margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <XAxis type="number" hide />
                <YAxis
                    dataKey="feature"
                    type="category"
                    width={100}
                    tick={{ fontSize: 11, fill: '#94a3b8' }}
                    tickFormatter={(val) => val.replace(/_/g, ' ').replace('count', '#')}
                />
                <Tooltip
                    cursor={{ fill: '#f1f5f9', opacity: 0.4 }}
                    contentStyle={{ borderRadius: '8px', border: 'none', backgroundColor: '#1e293b', color: '#fff' }}
                    formatter={(val) => [val.toFixed(3), 'Impact Score']}
                />
                <Bar dataKey="importance" radius={[0, 4, 4, 0]} barSize={20}>
                    {chartData.map((entry, index) => (
                        // Gradient from Indigo to Emerald based on rank
                        <Cell key={`cell-${index}`} fill={index < 3 ? '#6366f1' : index < 6 ? '#8b5cf6' : '#10b981'} />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
};
