
import React, { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { ArrowUpRight, ArrowDownRight, Users, FileWarning, Activity, FileText, Brain, Target, ShieldCheck, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { MissingVisitsWidget, LabQualityWidget, SAEReviewWidget } from '../components/DataQualityWidgets';
import { CodingStatusWidget, EDRRWidget, AuditLogWidget } from '../components/Phase2Widgets';
import { CRAPerformanceWidget, MissingLabDataWidget, UnderperformingSitesWidget } from '../components/CRAPerformanceWidgets';

/**
 * MetricCard Component
 * 
 * A reusable card for displaying key performance indicators (KPIs).
 * UI includes the metric value, a trend indicator (up/down), and an icon.
 */
const MetricCard = ({ title, value, change, trend, icon: Icon, color, description }) => (
  <motion.div
    whileHover={{ y: -5 }}
    className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 flex items-start justify-between transition-colors group relative"
  >
    <div>
      <div className="flex items-center gap-2 mb-1">
        <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">{title}</p>
        {description && (
          <div className="group/tooltip relative">
            <div className="w-4 h-4 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center text-[10px] cursor-help">?</div>
            <div className="absolute left-full top-0 ml-2 w-48 p-2 bg-slate-800 text-white text-xs rounded-lg opacity-0 group-hover/tooltip:opacity-100 pointer-events-none z-50 transition-opacity">
              {description}
            </div>
          </div>
        )}
      </div>
      <h3 className="text-3xl font-bold text-slate-800 dark:text-white tracking-tight">{value}</h3>
      <div className={`flex items-center gap-1 mt-2 text-xs font-semibold ${trend === 'up' ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
        {trend === 'up' ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
        <span>{change}</span>
        <span className="text-slate-400 dark:text-slate-500 font-normal ml-1">vs last month</span>
      </div>
    </div>
    <div className={`p-3 rounded-xl ${color} bg-opacity-10`}>
      <Icon className={`w-6 h-6 ${color.replace('bg-', 'text-')}`} />
    </div>
  </motion.div>
);

/**
 * RiskHeatmap Component
 * 
 * Visualizes site risk scores using a vertical bar chart.
 * Uses color-coding (red, amber, emerald) based on the risk score magnitude.
 */
const RiskHeatmap = ({ data }) => {
  if (!data) return <div className="h-64 flex items-center justify-center text-slate-400">Loading Risk Map...</div>;

  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors">
      <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4">Site Risk Heatmap</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
            <XAxis type="number" hide />
            <YAxis dataKey="site" type="category" width={80} tick={{ fontSize: 12, fill: '#94a3b8' }} />
            <Tooltip
              contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', backgroundColor: '#1e293b', color: '#fff' }}
              cursor={{ fill: '#f1f5f9' }}
            />
            <Bar dataKey="risk_score" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.risk_score > 50 ? '#f43f5e' : entry.risk_score > 20 ? '#fbbf24' : '#10b981'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
import { InteractiveConfusionMatrix, InteractiveFeatureImportance } from '../components/MLWidgets';

const MLStatus = () => {
  const { mlStatus, fetchMLStatus } = useClinicalData();

  useEffect(() => {
    fetchMLStatus();
  }, [fetchMLStatus]);

  if (!mlStatus) return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors mt-6 h-48 flex items-center justify-center">
      <div className="flex flex-col items-center gap-2 text-slate-400">
        <Brain className="w-8 h-8 animate-pulse text-indigo-400" />
        <span className="text-sm font-medium">Loading Predictive Model...</span>
      </div>
    </div>
  );

  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors mt-6">

      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
          <Brain className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-800 dark:text-white">Predictive Model Performance</h3>
          <p className="text-xs text-slate-500">ML Engine: {mlStatus.model_type} | Last Trained: {mlStatus.last_trained}</p>
        </div>
        <div className="ml-auto flex items-center gap-2 px-3 py-1 bg-emerald-100 dark:bg-emerald-900/20 rounded-full">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span className="text-xs font-bold text-emerald-600">Model Validated</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-4 flex items-center gap-2">
            <Target className="w-4 h-4" /> Feature Drivers (Importance)
          </h4>
          {/* Interactive Widget for Feature Importance */}
          {mlStatus.metrics ? (
            <InteractiveFeatureImportance data={mlStatus.metrics.feature_importance} />
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-400 bg-slate-50 rounded-xl">
              Loading Metrics...
            </div>
          )}
        </div>
        <div>
          <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-4 flex items-center gap-2">
            <Sparkles className="w-4 h-4" /> Confusion Matrix (Validation)
          </h4>
          {/* Interactive Widget for Confusion Matrix */}
          {mlStatus.metrics ? (
            <div className="h-[300px]">
              <InteractiveConfusionMatrix data={mlStatus.metrics.confusion_matrix} />
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-400 bg-slate-50 rounded-xl">
              Loading Metrics...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
;


import { useClinicalData } from '../hooks/useClinicalData';

/**
 * Overview Page
 * 
 * The primary dashboard landing page.
 * Aggregates high-level stats, trends, and risk heatmaps.
 * Fetches data for DQI score, SAE trends, and site risks in parallel.
 */
const Overview = ({ searchQuery }) => {
  const { stats, riskData, score, trends, fetchOverviewData } = useClinicalData();

  useEffect(() => {
    fetchOverviewData();
  }, [fetchOverviewData]);

  const getValue = (name) => {
    if (!stats) return '...';
    const item = stats.find(s => s.Metric === name);
    return item ? item.Value : 0;
  }

  return (
    <div className="space-y-6">
      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Study Health Score (Gauge style card) */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
          className="bg-gradient-to-br from-blue-600 to-indigo-700 dark:from-blue-700 dark:to-indigo-900 text-white p-6 rounded-2xl shadow-lg flex flex-col justify-between"
        >
          <div>
            <p className="text-blue-200 text-sm font-medium">Data Quality Index</p>
            <h2 className="text-5xl font-bold mt-2">{score}<span className="text-2xl text-blue-300 font-normal">/100</span></h2>
          </div>
          <div className="mt-4 bg-white/20 h-2 rounded-full overflow-hidden">
            <div className="bg-white h-full rounded-full transition-all duration-1000" style={{ width: `${score}%` }}></div>
          </div>
          <p className="text-xs text-blue-200 mt-2">DQI aggregates SAEs, Missing Pages & Latency</p>
        </motion.div>

        <MetricCard
          title="Total SAEs"
          value={getValue('SAE Records')}
          change="+12%" trend="up"
          description="Serious Adverse Events reported across all sites. High numbers may indicate safety signals."
          icon={FileWarning} color="text-rose-500 dark:text-rose-400 bg-rose-50 dark:bg-rose-900/20"
        />
        <MetricCard
          title="Missing Pages"
          value={getValue('Missing Pages')}
          change="-5%" trend="down"
          description="CRF pages not yet entered into the EDC system. Gaps delay data analysis."
          icon={FileText} color="text-amber-500 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20"
        />
        <MetricCard
          title="Subjects Active"
          value={getValue('EDC Metrics')}
          change="+8%" trend="up"
          description="Total patients currently enrolled and active in the study."
          icon={Users} color="text-blue-500 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-slate-800 dark:text-white">SAE Trend Analysis</h3>
            <select className="text-sm border-none bg-slate-50 dark:bg-slate-700 rounded-lg p-2 text-slate-600 dark:text-slate-300 outline-none">
              <option>Last 6 Months</option>
            </select>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends}>
                <defs>
                  <linearGradient id="colorSae" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.5} />
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', backgroundColor: '#1e293b', color: '#fff' }} />
                <Area type="monotone" dataKey="sae_count" stroke="#ef4444" strokeWidth={3} fillOpacity={1} fill="url(#colorSae)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Heatmap Component */}
        <RiskHeatmap data={riskData} />
      </div>

      <MLStatus />

      {/* Data Quality Monitoring Widgets */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <MissingVisitsWidget />
        <LabQualityWidget />
        <SAEReviewWidget />
      </div>

      {/* Detailed Coding & Audit Widgets */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <CodingStatusWidget />
        <EDRRWidget />
        <AuditLogWidget />
      </div>

      {/* CRA Performance & Lab Data Gaps */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6 pb-12">
        <CRAPerformanceWidget />
        <MissingLabDataWidget />
      </div>

      <div className="w-full mt-6 pb-12">
        <UnderperformingSitesWidget />
      </div>
    </div>
  );
};

export default Overview;
