
import React, { useState, useEffect } from 'react';
import { FileText, Download, Clock, Sparkles, Building2, Users, BarChart3, Loader2, ChevronDown, AlertTriangle, CheckCircle2, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Reports Page Component
 * 
 * Provides AI-powered report generation with:
 * - Report type selection (Site Risk, CRA Performance, Executive)
 * - Real-time generation with progress indicators
 * - AI-generated narrative display with markdown rendering
 * - Report history and PDF download
 */
const Reports = ({ searchQuery, reports, setReports }) => {
    const [ generating, setGenerating ] = useState( false );
    const [ selectedReportType, setSelectedReportType ] = useState( 'executive_summary' );
    const [ generatedReport, setGeneratedReport ] = useState( null );
    const [ savedReports, setSavedReports ] = useState( [] );
    const [ showReportModal, setShowReportModal ] = useState( false );
    const [ siteId, setSiteId ] = useState( '' );
    const [ craId, setCraId ] = useState( '' );
    const [ error, setError ] = useState( null );

    // Fetch saved reports on mount
    useEffect( () =>
    {
        fetchSavedReports();
    }, [] );

    const fetchSavedReports = async () =>
    {
        try
        {
            const response = await fetch( 'http://127.0.0.1:8000/reports/saved' );
            if ( response.ok )
            {
                const data = await response.json();
                setSavedReports( data );
            }
        } catch ( error )
        {
            console.error( "Failed to fetch saved reports", error );
        }
    };

    const reportTypes = [
        {
            id: 'site_risk',
            name: 'Site Risk Assessment',
            icon: Building2,
            description: 'Comprehensive risk analysis for a specific site',
            color: 'from-rose-500 to-pink-600',
            requiresInput: true,
            inputLabel: 'Site ID',
            inputPlaceholder: 'Enter site ID (e.g., 01, Site 01)'
        },
        {
            id: 'cra_performance',
            name: 'CRA Performance',
            icon: Users,
            description: 'Performance summary for a Clinical Research Associate',
            color: 'from-blue-500 to-indigo-600',
            requiresInput: true,
            inputLabel: 'CRA Name',
            inputPlaceholder: 'Enter CRA name or ID'
        },
        {
            id: 'executive_summary',
            name: 'Executive Summary',
            icon: BarChart3,
            description: 'High-level study overview for leadership',
            color: 'from-emerald-500 to-teal-600',
            requiresInput: false
        }
    ];

    const handleGenerateReport = async () =>
    {
        setGenerating( true );
        setError( null );
        setGeneratedReport( null );

        try
        {
            let endpoint = '';

            switch ( selectedReportType )
            {
                case 'site_risk':
                    if ( !siteId.trim() )
                    {
                        throw new Error( 'Please enter a Site ID' );
                    }
                    endpoint = `http://127.0.0.1:8000/reports/generate/site/${ encodeURIComponent( siteId.trim() ) }`;
                    break;
                case 'cra_performance':
                    if ( !craId.trim() )
                    {
                        throw new Error( 'Please enter a CRA name or ID' );
                    }
                    endpoint = `http://127.0.0.1:8000/reports/generate/cra/${ encodeURIComponent( craId.trim() ) }`;
                    break;
                case 'executive_summary':
                    endpoint = 'http://127.0.0.1:8000/reports/generate/executive';
                    break;
                default:
                    throw new Error( 'Invalid report type' );
            }

            const response = await fetch( endpoint, { method: 'POST' } );

            if ( !response.ok )
            {
                const errorData = await response.json();
                throw new Error( errorData.detail || 'Report generation failed' );
            }

            const report = await response.json();
            setGeneratedReport( report );
            setShowReportModal( true );

            // Refresh saved reports list
            fetchSavedReports();

        } catch ( error )
        {
            console.error( "Report generation failed", error );
            setError( error.message || 'Failed to generate report' );
        } finally
        {
            setGenerating( false );
        }
    };

    const handleLegacyGenerate = async () =>
    {
        try {
            const response = await fetch( 'http://127.0.0.1:8000/reports/generate', {
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
            alert( "Error generating report" );
        }
    };

    const selectedType = reportTypes.find( t => t.id === selectedReportType );

    const filteredReports = reports.filter(r => 
        r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.type.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Combine static and saved reports
    const allReports = [
        ...filteredReports,
        ...savedReports.map( r => ( {
            id: r.report_id,
            title: r.title,
            date: r.generated_at?.split( 'T' )[ 0 ] || 'N/A',
            type: r.report_type?.replace( '_', ' ' ).replace( /\b\w/g, l => l.toUpperCase() ) || 'AI Generated',
            status: r.status === 'complete' ? 'Ready' : 'Processing',
            isAIGenerated: true,
            generationSource: r.generation_source
        } ) )
    ];

    return (
        <div className="max-w-7xl mx-auto">
            {/* Header */ }
            <div className="flex justify-between items-center mb-10">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">AI Report Generation</h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-2">Generate comprehensive reports powered by AI and ML insights.</p>
                </div>
                <button
                    onClick={ handleLegacyGenerate }
                    className="bg-slate-600 hover:bg-slate-700 text-white px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 transition-all"
                >
                    <Download className="w-4 h-4" /> Quick PDF
                </button>
            </div>

            {/* Report Type Selector */ }
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-100 dark:border-slate-700 shadow-sm mb-8">
                <h2 className="text-lg font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-indigo-500" />
                    Generate New AI Report
                </h2>

                {/* Type Selection */ }
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    { reportTypes.map( ( type ) => (
                        <motion.button
                            key={ type.id }
                            whileHover={ { scale: 1.02 } }
                            whileTap={ { scale: 0.98 } }
                            onClick={ () => setSelectedReportType( type.id ) }
                            className={ `p-4 rounded-xl border-2 text-left transition-all ${ selectedReportType === type.id
                                    ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                                    : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500'
                                }` }
                        >
                            <div className={ `w-10 h-10 rounded-lg bg-gradient-to-br ${ type.color } flex items-center justify-center mb-3` }>
                                <type.icon className="w-5 h-5 text-white" />
                            </div>
                            <h3 className="font-semibold text-slate-800 dark:text-white text-sm">{ type.name }</h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{ type.description }</p>
                        </motion.button>
                    ) ) }
                </div>

                {/* Input Field (if required) */ }
                { selectedType?.requiresInput && (
                    <div className="mb-6">
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                            { selectedType.inputLabel }
                        </label>
                        <input
                            type="text"
                            value={ selectedReportType === 'site_risk' ? siteId : craId }
                            onChange={ ( e ) => selectedReportType === 'site_risk' ? setSiteId( e.target.value ) : setCraId( e.target.value ) }
                            placeholder={ selectedType.inputPlaceholder }
                            className="w-full max-w-md px-4 py-2.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-700 dark:text-white placeholder-slate-400"
                        />
                    </div>
                ) }

                {/* Error Message */ }
                { error && (
                    <div className="mb-4 p-3 bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-lg flex items-center gap-2 text-rose-700 dark:text-rose-400 text-sm">
                        <AlertTriangle className="w-4 h-4" />
                        { error }
                    </div>
                ) }

                {/* Generate Button */ }
                <button 
                    onClick={ handleGenerateReport }
                    disabled={ generating }
                    className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-indigo-500/30 flex items-center gap-2 transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                >
                    { generating ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            Generating with AI...
                        </>
                    ) : (
                        <>
                            <Sparkles className="w-5 h-5" />
                            Generate { selectedType?.name }
                        </>
                    ) }
                </button>
            </div>

            {/* Reports Grid */ }
            { allReports.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    { allReports.map( ( report ) => (
                        <motion.div 
                            whileHover={{ y: -5 }}
                            key={report.id} 
                            className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col h-56 group cursor-pointer relative transition-colors"
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div className={ `p-3 rounded-xl transition-colors ${ report.isAIGenerated
                                        ? 'bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-900/30 dark:to-purple-900/30'
                                        : 'bg-blue-50 dark:bg-blue-900/20 group-hover:bg-blue-100 dark:group-hover:bg-blue-900/40'
                                    }` }>
                                    { report.isAIGenerated ? (
                                        <Sparkles className="w-6 h-6 text-indigo-500" />
                                    ) : (
                                        <FileText className="w-6 h-6 text-blue-500 dark:text-blue-400" />
                                    ) }
                                </div>
                                <div className="flex items-center gap-2">
                                    { report.isAIGenerated && (
                                        <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
                                            AI
                                        </span>
                                    ) }
                                    <span className={ `px-2 py-1 rounded-full text-xs font-medium ${ report.status === 'Ready' ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400' : 'bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400'
                                        }` }>
                                        { report.status }
                                    </span>
                                </div>
                            </div>
                            
                            <div className="flex-1">
                                <h3 className="font-bold text-slate-800 dark:text-slate-200 text-lg mb-2 leading-tight">{report.title}</h3>
                                <div className="flex items-center gap-4 text-xs text-slate-400">
                                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {report.date}</span>
                                    <span>{ report.type }</span>
                                </div>
                            </div>

                            { report.status === 'Ready' && (
                                <button
                                    onClick={ ( e ) =>
                                    {
                                        e.stopPropagation();
                                        if ( report.isAIGenerated )
                                        {
                                            // Fetch and show AI report
                                            fetch( `http://127.0.0.1:8000/reports/${ report.id }` )
                                                .then( res => res.json() )
                                                .then( data =>
                                                {
                                                    setGeneratedReport( data );
                                                    setShowReportModal( true );
                                                } );
                                        } else
                                        {
                                            alert( `Downloading ${ report.title }...` );
                                        }
                                    } }
                                    className="w-full mt-4 flex items-center justify-center gap-2 py-2 text-sm text-blue-600 dark:text-blue-400 font-medium hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                                >
                                    { report.isAIGenerated ? (
                                        <><FileText className="w-4 h-4" /> View Report</>
                                    ) : (
                                        <><Download className="w-4 h-4" /> Download PDF</>
                                    ) }
                                </button>
                            ) }
                        </motion.div>
                    ))}
                </div>
            ) : (
                    <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                        <FileText className="w-12 h-12 mb-4 opacity-20" />
                        <p>No reports found matching "{ searchQuery }".</p>
                    </div>
            )}

            {/* AI Report Modal */ }
            <AnimatePresence>
                { showReportModal && generatedReport && (
                    <motion.div
                        initial={ { opacity: 0 } }
                        animate={ { opacity: 1 } }
                        exit={ { opacity: 0 } }
                        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                        onClick={ () => setShowReportModal( false ) }
                    >
                        <motion.div
                            initial={ { scale: 0.95, opacity: 0 } }
                            animate={ { scale: 1, opacity: 1 } }
                            exit={ { scale: 0.95, opacity: 0 } }
                            className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
                            onClick={ ( e ) => e.stopPropagation() }
                        >
                            {/* Modal Header */ }
                            <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex justify-between items-start">
                                <div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg">
                                            <Sparkles className="w-4 h-4 text-white" />
                                        </div>
                                        <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400 uppercase tracking-wide">
                                            AI Generated Report
                                        </span>
                                    </div>
                                    <h2 className="text-xl font-bold text-slate-800 dark:text-white">{ generatedReport.title }</h2>
                                    <p className="text-sm text-slate-500 mt-1">
                                        Generated: { new Date( generatedReport.generated_at ).toLocaleString() } •
                                        Source: { generatedReport.generation_source === 'gemini' ? 'Gemini AI' : 'Template' }
                                    </p>
                                </div>
                                <button
                                    onClick={ () => setShowReportModal( false ) }
                                    className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                                >
                                    <X className="w-5 h-5 text-slate-500" />
                                </button>
                            </div>

                            {/* Modal Body */ }
                            <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
                                {/* Executive Summary */ }
                                <div className="mb-8">
                                    <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                                        <div className="w-1 h-6 bg-indigo-500 rounded-full"></div>
                                        Executive Summary
                                    </h3>
                                    <p className="text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl">
                                        { generatedReport.executive_summary }
                                    </p>
                                </div>

                                {/* Sections */ }
                                { generatedReport.sections?.map( ( section, idx ) => (
                                    <div key={ idx } className="mb-6">
                                        <h4 className="font-semibold text-slate-800 dark:text-white mb-2">{ section.title }</h4>
                                        <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                                            { section.content }
                                        </p>

                                        {/* Metrics if available */ }
                                        { section.metrics && (
                                            <div className="flex flex-wrap gap-3 mt-3">
                                                { Object.entries( section.metrics ).map( ( [ key, value ] ) => (
                                                    <div key={ key } className="px-3 py-1.5 bg-slate-100 dark:bg-slate-700 rounded-lg text-xs">
                                                        <span className="text-slate-500 dark:text-slate-400">{ key.replace( /_/g, ' ' ) }: </span>
                                                        <span className="font-semibold text-slate-700 dark:text-white">{ value }</span>
                                                    </div>
                                                ) ) }
                                            </div>
                                        ) }

                                        {/* Risk Factors if available */ }
                                        { section.factors && section.factors.length > 0 && (
                                            <div className="mt-3 space-y-2">
                                                { section.factors.map( ( factor, i ) => (
                                                    <div key={ i } className="flex items-center gap-2 text-sm">
                                                        <span className={ `w-2 h-2 rounded-full ${ factor.direction === 'increases_risk' ? 'bg-rose-500' : 'bg-emerald-500'
                                                            }` }></span>
                                                        <span className="text-slate-600 dark:text-slate-300">{ factor.explanation }</span>
                                                    </div>
                                                ) ) }
                                            </div>
                                        ) }
                                    </div>
                                ) ) }

                                {/* Recommendations */ }
                                { generatedReport.recommendations && generatedReport.recommendations.length > 0 && (
                                    <div className="mt-8 p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl border border-emerald-200 dark:border-emerald-800">
                                        <h4 className="font-semibold text-emerald-800 dark:text-emerald-300 mb-3 flex items-center gap-2">
                                            <CheckCircle2 className="w-5 h-5" />
                                            Recommendations
                                        </h4>
                                        <ul className="space-y-2">
                                            { generatedReport.recommendations.map( ( rec, idx ) => (
                                                <li key={ idx } className="flex items-start gap-2 text-sm text-emerald-700 dark:text-emerald-300">
                                                    <span className="font-bold text-emerald-500">{ idx + 1 }.</span>
                                                    { rec }
                                                </li>
                                            ) ) }
                                        </ul>
                                    </div>
                                ) }
                            </div>

                            {/* Modal Footer */ }
                            <div className="p-4 border-t border-slate-200 dark:border-slate-700 flex justify-end gap-3">
                                <button
                                    onClick={ () => setShowReportModal( false ) }
                                    className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                                >
                                    Close
                                </button>
                                <button
                                    onClick={ handleLegacyGenerate }
                                    className="px-4 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors flex items-center gap-2"
                                >
                                    <Download className="w-4 h-4" />
                                    Export as PDF
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                ) }
            </AnimatePresence>
        </div>
    );
};

export default Reports;
