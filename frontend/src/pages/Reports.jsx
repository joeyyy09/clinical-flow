
import React from 'react';
import { FileText, Download, Clock } from 'lucide-react';
import { motion } from 'framer-motion';

const Reports = ({ searchQuery, reports, setReports }) => {
    const [ generating, setGenerating ] = React.useState( null );
    
    const handleGenerate = async ( reportType = 'risk' ) =>
    {
        setGenerating( reportType );
        try {
            const response = await fetch( `http://127.0.0.1:8000/reports/generate?report_type=${ reportType }`, {
                method: 'POST',
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${ reportType }_report_${ new Date().toISOString().split( 'T' )[ 0 ] }.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
            } else {
                alert("Failed to generate report");
            }
        } catch (error) {
            console.error("Report generation failed", error);
            alert("Error generating report");
        } finally
        {
            setGenerating( null );
        }
    };

    const filteredReports = reports.filter(r => 
        r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.type.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-10">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Report Generation</h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-2">Create and download regulatory compliance and safety reports powered by AI.</p>
                </div>
                <button 
                    onClick={ () => handleGenerate( 'risk' ) }
                    disabled={ generating !== null }
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-blue-500/30 flex items-center gap-2 transition-all hover:scale-105 active:scale-95"
                >
                    <FileText className={ `w-5 h-5 ${ generating === 'risk' ? 'animate-pulse' : '' }` } />
                    { generating === 'risk' ? 'Generating...' : 'Generate Risk Report' }
                </button>
            </div>

            {filteredReports.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredReports.map((report) => (
                        <motion.div 
                            whileHover={{ y: -5 }}
                            key={report.id} 
                            className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col h-56 group cursor-pointer relative transition-colors"
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 text-blue-500 dark:text-blue-400 rounded-xl group-hover:bg-blue-100 dark:group-hover:bg-blue-900/40 transition-colors">
                                    <FileText className="w-6 h-6" />
                                </div>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                    report.status === 'Ready' ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400' : 'bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400'
                                }`}>
                                    { generating === report.id ? 'Processing...' : report.status }
                                </span>
                            </div>
                            
                            <div className="flex-1">
                                <h3 className="font-bold text-slate-800 dark:text-slate-200 text-lg mb-2 leading-tight">{report.title}</h3>
                                <div className="flex items-center gap-4 text-xs text-slate-400">
                                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {report.date}</span>
                                    <span className="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-[10px] uppercase font-bold text-slate-500 dark:text-slate-400 tracking-wider">
                                        { report.type }
                                    </span>
                                </div>
                            </div>

                            <button
                                onClick={ ( e ) =>
                                {
                                    e.stopPropagation();
                                    handleGenerate( report.id === 'performance_summary' ? 'performance' : 'risk' );
                                } }
                                disabled={ generating !== null }
                                className="w-full mt-4 flex items-center justify-center gap-2 py-2 text-sm text-blue-600 dark:text-blue-400 font-medium hover:bg-blue-50 dark:hover:bg-blue-900/20 disabled:hover:bg-transparent disabled:opacity-50 rounded-lg transition-colors border border-transparent hover:border-blue-100 dark:hover:border-blue-900/30"
                            >
                                <Download className={ `w-4 h-4 ${ generating === report.id ? 'animate-bounce' : '' }` } />
                                { generating === report.id ? 'Generating...' : 'Regenerate & Download' }
                            </button>
                        </motion.div>
                    ))}
                </div>
            ) : (
                 <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                     <FileText className="w-12 h-12 mb-4 opacity-20" />
                     <p>No reports found matching "{searchQuery}".</p>
                 </div>
            )}
        </div>
    );
};

export default Reports;
