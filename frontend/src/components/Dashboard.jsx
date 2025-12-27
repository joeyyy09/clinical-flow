
import React from 'react';
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// Simple definition since I don't want to install shadcn/ui fully right now, keeping it robust but simple
const SimpleCard = ({ title, children, className="" }) => (
  <div className={`bg-white shadow rounded-lg p-4 ${className}`}>
    <h3 className="text-lg font-semibold mb-2">{title}</h3>
    {children}
  </div>
);

const Dashboard = ({ stats }) => {
  if (!stats || !stats.data) return <div className="p-4">Loading stats...</div>;

  const { data } = stats;

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Clinical Decisions Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {data.map((item, index) => (
          <SimpleCard key={index} title={item.Metric} className="border-l-4 border-blue-500">
            <div className="text-4xl font-bold text-gray-900">{item.Value}</div>
          </SimpleCard>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SimpleCard title="Data Distribution">
             <div className="h-64 flex items-center justify-center text-gray-500">
                Ask the AI Agent for detailed charts!
             </div>
        </SimpleCard>
        
        <SimpleCard title="Recent Activity">
           <ul className="space-y-2">
             <li className="flex justify-between text-sm"><span>Data Ingestion</span> <span className="text-green-600">Completed</span></li>
             <li className="flex justify-between text-sm"><span>Model Training</span> <span className="text-gray-400">Idle</span></li>
           </ul>
        </SimpleCard>
      </div>
    </div>
  );
};

export default Dashboard;
