
import React, { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { ArrowUpRight, ArrowDownRight, Users, FileWarning, Activity, FileText } from 'lucide-react';
import { motion } from 'framer-motion';

const MetricCard = ({ title, value, change, trend, icon: Icon, color }) => (
  <motion.div 
    whileHover={{ y: -5 }}
    className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 flex items-start justify-between transition-colors"
  >
    <div>
      <p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">{title}</p>
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
                        <YAxis dataKey="site" type="category" width={80} tick={{fontSize: 12, fill: '#94a3b8'}} />
                        <Tooltip 
                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', backgroundColor: '#1e293b', color: '#fff' }}
                            cursor={{fill: '#f1f5f9'}}
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

const Overview = ({ searchQuery }) => {
  const [stats, setStats] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [score, setScore] = useState(0);
  const [trends, setTrends] = useState([]);

  useEffect(() => {
    // Fetch all data in parallel
    Promise.all([
        fetch('http://127.0.0.1:8000/stats').then(res => res.json()),
        fetch('http://127.0.0.1:8000/analytics/risk').then(res => res.json()),
        fetch('http://127.0.0.1:8000/analytics/score').then(res => res.json()),
        fetch('http://127.0.0.1:8000/analytics/trend').then(res => res.json())
    ]).then(([statsData, riskData, scoreData, trendData]) => {
        setStats(statsData.data);
        setRiskData(riskData);
        setScore(scoreData.score);
        setTrends(trendData);
    }).catch(err => console.error("API Error", err));
  }, []);

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
            icon={FileWarning} color="text-rose-500 dark:text-rose-400 bg-rose-50 dark:bg-rose-900/20" 
         />
         <MetricCard 
            title="Missing Pages" 
            value={getValue('Missing Pages')} 
            change="-5%" trend="down" 
            icon={FileText} color="text-amber-500 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20" 
         />
         <MetricCard 
            title="Subjects Active" 
            value={getValue('EDC Metrics')} 
            change="+8%" trend="up" 
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
                                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1}/>
                                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.5} />
                        <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{fill: '#94a3b8'}} />
                        <YAxis axisLine={false} tickLine={false} tick={{fill: '#94a3b8'}} />
                        <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', backgroundColor: '#1e293b', color: '#fff' }} />
                        <Area type="monotone" dataKey="sae_count" stroke="#ef4444" strokeWidth={3} fillOpacity={1} fill="url(#colorSae)" />
                    </AreaChart>
                </ResponsiveContainer>
             </div>
         </div>

         {/* Risk Heatmap Component */}
         <RiskHeatmap data={riskData} />
      </div>
    </div>
  );
};

export default Overview;
