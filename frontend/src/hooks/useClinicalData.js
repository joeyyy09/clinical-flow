
import { useState, useEffect, useCallback } from 'react';

const BASE_URL = 'http://127.0.0.1:8000';

/**
 * Custom hook for centralizing clinical data fetching and state management.
 */
export const useClinicalData = () =>
{
    const [ stats, setStats ] = useState( null );
    const [ riskData, setRiskData ] = useState( [] );
    const [ score, setScore ] = useState( 0 );
    const [ trends, setTrends ] = useState( [] );
    const [ mlStatus, setMlStatus ] = useState( null );
    const [ loading, setLoading ] = useState( true );
    const [ error, setError ] = useState( null );

    // Chat State
    const [ messages, setMessages ] = useState( [
        { role: 'agent', content: 'Hello! I am your Clinical AI Copilot. I can help you analyze risks, draft reports, or query data.' }
    ] );
    const [ chatLoading, setChatLoading ] = useState( false );
    const [ chartData, setChartData ] = useState( null );

    // Ingestion State
    const [ ingestionStatus, setIngestionStatus ] = useState( 'idle' );
    const [ ingestionProgress, setIngestionProgress ] = useState( 0 );
    const [ ingestionLogs, setIngestionLogs ] = useState( [] );
    const [ lastSync, setLastSync ] = useState( localStorage.getItem( 'last_ingestion_sync' ) || null );

    const fetchOverviewData = useCallback( async () =>
    {
        try
        {
            const [ statsRes, riskRes, scoreRes, trendRes ] = await Promise.all( [
                fetch( `${ BASE_URL }/stats` ),
                fetch( `${ BASE_URL }/analytics/risk` ),
                fetch( `${ BASE_URL }/analytics/score` ),
                fetch( `${ BASE_URL }/analytics/trend` )
            ] );

            const [ statsJson, riskJson, scoreJson, trendJson ] = await Promise.all( [
                statsRes.json(),
                riskRes.json(),
                scoreRes.json(),
                trendRes.json()
            ] );

            setStats( statsJson.data );
            setRiskData( riskJson );
            setScore( scoreJson.score );
            setTrends( trendJson );
        } catch ( err )
        {
            console.error( "Overview Fetch Error", err );
            setError( err );
        }
    }, [] );

    const fetchRiskMonitorData = useCallback( async () =>
    {
        setLoading( true );
        try
        {
            const res = await fetch( `${ BASE_URL }/analytics/risk-monitor` );
            const data = await res.json();
            setRiskData( data );
        } catch ( err )
        {
            console.error( "Risk Monitor Fetch Error", err );
            setError( err );
        } finally
        {
            setLoading( false );
        }
    }, [] );

    const fetchMLStatus = useCallback( async () =>
    {
        try
        {
            const res = await fetch( `${ BASE_URL }/analytics/ml-status` );
            const data = await res.json();
            setMlStatus( data );
        } catch ( err )
        {
            console.error( "ML Status Fetch Error", err );
        }
    }, [] );

    const generateReport = async () =>
    {
        try
        {
            const response = await fetch( `${ BASE_URL }/reports/generate`, { method: 'POST' } );
            if ( response.ok )
            {
                const blob = await response.blob();
                const url = window.URL.createObjectURL( blob );
                const a = document.createElement( 'a' );
                a.href = url;
                a.download = "risk_assessment_report.pdf";
                document.body.appendChild( a );
                a.click();
                a.remove();
                return true;
            }
            return false;
        } catch ( error )
        {
            console.error( "Report generation failed", error );
            return false;
        }
    };

    const sendMessage = async ( query ) =>
    {
        if ( !query.trim() ) return;

        const userMsg = { role: 'user', content: query };
        setMessages( prev => [ ...prev, userMsg ] );
        setChatLoading( true );
        setChartData( null );

        try
        {
            // Note: Backend router for chat is /chat (POST)
            const response = await fetch( `${ BASE_URL }/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify( { query: userMsg.content } ),
            } );
            const data = await response.json();

            setMessages( prev => [ ...prev, { role: 'agent', content: data.answer } ] );
            if ( data.chart_type ) setChartData( data );
        } catch ( error )
        {
            setMessages( prev => [ ...prev, { role: 'agent', content: 'Connection error. Please try again.' } ] );
        } finally
        {
            setChatLoading( false );
        }
    };

    const startIngestionPipeline = async ( file ) =>
    {
        if ( !file ) return;
        setIngestionStatus( 'uploading' );
        setIngestionProgress( 0 );
        setIngestionLogs( [] );

        const addLog = ( msg ) =>
        {
            const timestamp = new Date().toLocaleTimeString();
            setIngestionLogs( prev => [ `[${ timestamp }] ${ msg }`, ...prev ] );
        };

        addLog( `Started ingestion pipeline for ${ file.name }...` );
        const formData = new FormData();
        formData.append( 'file', file );

        try
        {
            setIngestionProgress( 30 );
            addLog( "Uploading file to secure storage..." );

            const response = await fetch( `${ BASE_URL }/ingest/file`, {
                method: 'POST',
                body: formData,
            } );

            if ( response.ok )
            {
                setIngestionProgress( 60 );
                setIngestionStatus( 'processing' );
                addLog( "Upload complete. Triggering ingestion engine..." );

                setTimeout( () =>
                {
                    setIngestionProgress( 85 );
                    addLog( "Parsing entities and updating vector index..." );

                    setTimeout( () =>
                    {
                        setIngestionProgress( 100 );
                        setIngestionStatus( 'complete' );
                        addLog( "Ingestion complete. Knowledge base updated." );

                        const now = new Date().toLocaleString();
                        setLastSync( now );
                        localStorage.setItem( 'last_ingestion_sync', now );
                    }, 1500 );
                }, 1500 );
            } else
            {
                setIngestionStatus( 'error' );
                addLog( "Error: Upload failed." );
            }
        } catch ( error )
        {
            setIngestionStatus( 'error' );
            addLog( "Error: Connection failed." );
        }
    };

    return {
        stats,
        riskData,
        score,
        trends,
        mlStatus,
        loading,
        error,
        // Chat
        messages,
        chatLoading,
        chartData,
        sendMessage,
        // Ingestion
        ingestionStatus,
        ingestionProgress,
        ingestionLogs,
        lastSync,
        startIngestionPipeline,
        // Methods
        fetchOverviewData,
        fetchRiskMonitorData,
        fetchMLStatus,
        generateReport
    };
};
