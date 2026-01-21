
import React, { useState, useEffect } from 'react';
import { Sparkles, Brain, TrendingUp, TrendingDown, Info, ChevronDown, ChevronUp, AlertTriangle, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * MLInsightsPanel Component
 * 
 * Displays ML prediction details including:
 * - Confidence score with visual indicator
 * - Probability distribution across risk levels
 * - Top risk factors with SHAP-based explanations
 * - Feature importance visualization
 */
const MLInsightsPanel = ( { siteId, isOpen, onClose } ) =>
{
    const [ prediction, setPrediction ] = useState( null );
    const [ loading, setLoading ] = useState( false );
    const [ error, setError ] = useState( null );
    const [ expanded, setExpanded ] = useState( false );

    useEffect( () =>
    {
        if ( siteId && isOpen )
        {
            fetchPrediction();
        }
    }, [ siteId, isOpen ] );

    const fetchPrediction = async () =>
    {
        setLoading( true );
        setError( null );

        try
        {
            const response = await fetch( `http://127.0.0.1:8000/analytics/ml-predict/${ encodeURIComponent( siteId ) }` );

            if ( !response.ok )
            {
                throw new Error( 'Failed to fetch prediction' );
            }

            const data = await response.json();
            setPrediction( data );
        } catch ( err )
        {
            console.error( 'ML Prediction fetch error:', err );
            setError( err.message );
        } finally
        {
            setLoading( false );
        }
    };

    if ( !isOpen ) return null;

    const getConfidenceColor = ( confidence ) =>
    {
        if ( confidence >= 0.8 ) return 'text-emerald-500';
        if ( confidence >= 0.6 ) return 'text-amber-500';
        return 'text-rose-500';
    };

    const getRiskLevelColor = ( level ) =>
    {
        switch ( level )
        {
            case 'High': return 'from-rose-500 to-pink-600';
            case 'Medium': return 'from-amber-500 to-orange-600';
            case 'Low': return 'from-emerald-500 to-teal-600';
            default: return 'from-slate-500 to-slate-600';
        }
    };

    return (
        <motion.div
            initial={ { opacity: 0, y: 20 } }
            animate={ { opacity: 1, y: 0 } }
            exit={ { opacity: 0, y: 20 } }
            className="fixed bottom-4 right-4 w-96 bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden z-50"
        >
            {/* Header */ }
            <div className="p-4 bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-white/20 rounded-lg">
                        <Brain className="w-4 h-4 text-white" />
                    </div>
                    <div>
                        <h3 className="text-white font-bold text-sm">ML Risk Prediction</h3>
                        <p className="text-white/70 text-xs">{ siteId?.startsWith( 'Site' ) ? siteId : `Site ${ siteId }` }</p>
                    </div>
                </div>
                <button
                    onClick={ onClose }
                    className="text-white/70 hover:text-white transition-colors"
                >
                    ×
                </button>
            </div>

            {/* Content */ }
            <div className="p-4">
                { loading ? (
                    <div className="flex items-center justify-center py-8">
                        <div className="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full"></div>
                        <span className="ml-2 text-sm text-slate-500">Analyzing site data...</span>
                    </div>
                ) : error ? (
                    <div className="text-center py-8">
                        <AlertTriangle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
                        <p className="text-sm text-slate-500">{ error }</p>
                        <button
                            onClick={ fetchPrediction }
                            className="mt-2 text-xs text-indigo-600 hover:underline"
                        >
                            Retry
                        </button>
                    </div>
                ) : prediction ? (
                    <div className="space-y-4">
                        {/* Risk Level & Confidence */ }
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className={ `px-3 py-1.5 rounded-lg bg-gradient-to-r ${ getRiskLevelColor( prediction.risk_level ) } text-white font-bold text-sm` }>
                                    { prediction.risk_level } Risk
                                </div>
                                <div className="flex items-center gap-1">
                                    <span className={ `text-lg font-bold ${ getConfidenceColor( prediction.confidence ) }` }>
                                        { ( prediction.confidence * 100 ).toFixed( 0 ) }%
                                    </span>
                                    <span className="text-xs text-slate-400">confidence</span>
                                </div>
                            </div>
                            <div className="text-xs text-slate-400">
                                v{ prediction.model_version || '2.0' }
                            </div>
                        </div>

                        {/* Probability Distribution */ }
                        { prediction.probability_distribution && (
                            <div className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-3">
                                <p className="text-xs font-medium text-slate-500 mb-2">Probability Distribution</p>
                                <div className="space-y-2">
                                    { Object.entries( prediction.probability_distribution ).map( ( [ level, prob ] ) => (
                                        <div key={ level } className="flex items-center gap-2">
                                            <span className="text-xs text-slate-500 w-14">{ level }</span>
                                            <div className="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                                                <motion.div
                                                    initial={ { width: 0 } }
                                                    animate={ { width: `${ prob * 100 }%` } }
                                                    transition={ { duration: 0.5, delay: 0.2 } }
                                                    className={ `h-full rounded-full ${ level === 'High' ? 'bg-rose-500' :
                                                            level === 'Medium' ? 'bg-amber-500' : 'bg-emerald-500'
                                                        }` }
                                                />
                                            </div>
                                            <span className="text-xs font-medium text-slate-600 dark:text-slate-300 w-12 text-right">
                                                { ( prob * 100 ).toFixed( 1 ) }%
                                            </span>
                                        </div>
                                    ) ) }
                                </div>
                            </div>
                        ) }

                        {/* DQI Percentile */ }
                        { prediction.dqi_percentile !== undefined && (
                            <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-900/50 rounded-lg p-3">
                                <span className="text-xs text-slate-500">DQI Percentile</span>
                                <span className={ `text-sm font-bold ${ prediction.dqi_percentile > 70 ? 'text-emerald-500' :
                                        prediction.dqi_percentile > 30 ? 'text-amber-500' : 'text-rose-500'
                                    }` }>
                                    { prediction.dqi_percentile.toFixed( 0 ) }th percentile
                                </span>
                            </div>
                        ) }

                        {/* Top Risk Factors */ }
                        { prediction.top_risk_factors && prediction.top_risk_factors.length > 0 && (
                            <div>
                                <button
                                    onClick={ () => setExpanded( !expanded ) }
                                    className="w-full flex items-center justify-between text-xs font-medium text-slate-500 mb-2"
                                >
                                    <span className="flex items-center gap-1">
                                        <Sparkles className="w-3 h-3" />
                                        Top Risk Factors ({ prediction.top_risk_factors.length })
                                    </span>
                                    { expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" /> }
                                </button>

                                <AnimatePresence>
                                    { expanded && (
                                        <motion.div
                                            initial={ { height: 0, opacity: 0 } }
                                            animate={ { height: 'auto', opacity: 1 } }
                                            exit={ { height: 0, opacity: 0 } }
                                            className="space-y-2 overflow-hidden"
                                        >
                                            { prediction.top_risk_factors.map( ( factor, idx ) => (
                                                <motion.div
                                                    key={ idx }
                                                    initial={ { x: -10, opacity: 0 } }
                                                    animate={ { x: 0, opacity: 1 } }
                                                    transition={ { delay: idx * 0.1 } }
                                                    className="flex items-start gap-2 p-2 bg-slate-50 dark:bg-slate-900/50 rounded-lg"
                                                >
                                                    <div className={ `p-1 rounded ${ factor.direction === 'increases_risk'
                                                            ? 'bg-rose-100 text-rose-500'
                                                            : 'bg-emerald-100 text-emerald-500'
                                                        }` }>
                                                        { factor.direction === 'increases_risk'
                                                            ? <TrendingUp className="w-3 h-3" />
                                                            : <TrendingDown className="w-3 h-3" />
                                                        }
                                                    </div>
                                                    <div className="flex-1">
                                                        <p className="text-xs text-slate-600 dark:text-slate-300">
                                                            { factor.explanation || factor.feature }
                                                        </p>
                                                        <div className="flex items-center gap-2 mt-1">
                                                            <span className="text-[10px] text-slate-400">
                                                                Impact: { ( factor.impact * 100 ).toFixed( 0 ) }%
                                                            </span>
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            ) ) }
                                        </motion.div>
                                    ) }
                                </AnimatePresence>
                            </div>
                        ) }

                        {/* Prediction Source */ }
                        <div className="flex items-center justify-center gap-2 pt-2 border-t border-slate-100 dark:border-slate-700">
                            <CheckCircle className="w-3 h-3 text-emerald-500" />
                            <span className="text-[10px] text-slate-400">
                                { prediction.prediction_source === 'advanced_ml'
                                    ? 'Ensemble Model (XGBoost + RF + NN)'
                                    : 'Heuristic Fallback'
                                }
                            </span>
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-8 text-slate-400">
                        No prediction data available
                    </div>
                ) }
            </div>
        </motion.div>
    );
};

/**
 * MLConfidenceBadge Component
 * 
 * Compact badge showing ML prediction confidence
 */
export const MLConfidenceBadge = ( { confidence, riskLevel, onClick } ) =>
{
    const getColor = () =>
    {
        if ( !confidence ) return 'bg-slate-100 text-slate-400';
        if ( confidence >= 0.8 ) return 'bg-emerald-50 text-emerald-600 border-emerald-200';
        if ( confidence >= 0.6 ) return 'bg-amber-50 text-amber-600 border-amber-200';
        return 'bg-rose-50 text-rose-600 border-rose-200';
    };

    return (
        <button
            onClick={ onClick }
            className={ `inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${ getColor() } hover:opacity-80 transition-opacity` }
            title="Click for ML details"
        >
            <Sparkles className="w-3 h-3" />
            { riskLevel }
            { confidence && (
                <span className="opacity-70">
                    ({ ( confidence * 100 ).toFixed( 0 ) }%)
                </span>
            ) }
        </button>
    );
};

export default MLInsightsPanel;
