
import { useState, useEffect, useCallback } from 'react';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * Custom hook for centralizing clinical data fetching and state management.
 */
export const useClinicalData = () => {
    const [stats, setStats] = useState(null);
    const [riskData, setRiskData] = useState([]);
    const [score, setScore] = useState(0);
    const [trends, setTrends] = useState([]);
    const [mlStatus, setMlStatus] = useState(null);
    const [readiness, setReadiness] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Chat State
    const [messages, setMessages] = useState([
        { role: 'agent', content: 'Hello! I am your Clinical AI Copilot. I can help you analyze risks, draft reports, or query data.' }
    ]);
    const [chatLoading, setChatLoading] = useState(false);
    const [chartData, setChartData] = useState(null);

    // Ingestion State
    const [ingestionStatus, setIngestionStatus] = useState('idle');
    const [ingestionProgress, setIngestionProgress] = useState(0);
    const [ingestionLogs, setIngestionLogs] = useState([]);
    const [lastSync, setLastSync] = useState(localStorage.getItem('last_ingestion_sync') || null);

    const fetchOverviewData = useCallback(async () => {
        // Fire all requests in parallel but update state individually as each resolves,
        // so DQI / trend / heatmap appear without waiting for the slower /chat/stats.
        const safe = (promise) => promise.catch(err => { console.warn('Overview fetch error', err); return null; });

        safe(fetch(`${BASE_URL}/chat/stats`).then(r => r.json())).then(json => {
            if (json) setStats(json.data);
        });
        safe(fetch(`${BASE_URL}/analytics/risk`).then(r => r.json())).then(json => {
            if (json) setRiskData(json);
        });
        safe(fetch(`${BASE_URL}/analytics/score`).then(r => r.json())).then(json => {
            if (json) setScore(json.score);
        });
        safe(fetch(`${BASE_URL}/analytics/trend`).then(r => r.json())).then(json => {
            if (json) setTrends(json);
        });
        safe(fetch(`${BASE_URL}/analytics/readiness`).then(r => r.json())).then(json => {
            if (json) setReadiness(json);
        });
    }, []);

    const fetchRiskMonitorData = useCallback(async () => {
        // Only show loading spinner on first load — avoids flash when navigating back.
        setRiskData(current => {
            if (current.length === 0) setLoading(true);
            return current;
        });

        // Fire both fetches in parallel but update state independently as each resolves.
        // This way the risk grid appears even if /readiness is slow, and vice versa.
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000); // 30s hard timeout

        const safe = (promise) => promise.catch(err => {
            console.warn('Risk Monitor fetch error:', err.message);
            return null;
        });

        safe(
            fetch(`${BASE_URL}/analytics/risk-monitor`, { signal: controller.signal })
                .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
        ).then(json => {
            if (json) setRiskData(json);
            setLoading(false);
        });

        safe(
            fetch(`${BASE_URL}/analytics/readiness`, { signal: controller.signal })
                .then(r => r.json())
        ).then(json => {
            if (json) setReadiness(json);
        });

        // Clear timeout once both are done (approximate — clears after 30s max)
        Promise.allSettled([
            fetch(`${BASE_URL}/analytics/risk-monitor`).catch(() => {}),
            fetch(`${BASE_URL}/analytics/readiness`).catch(() => {})
        ]).finally(() => clearTimeout(timeout));
    }, []);

    const fetchMLStatus = useCallback(async () => {
        try {
            const res = await fetch(`${BASE_URL}/analytics/ml-status?t=${new Date().getTime()}`);
            const data = await res.json();
            setMlStatus(data);
        } catch (err) {
            console.error("ML Status Fetch Error", err);
        }
    }, []);

    const generateReport = async () => {
        try {
            const response = await fetch(`${BASE_URL}/reports/generate`, { method: 'POST' });
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = "risk_assessment_report.pdf";
                document.body.appendChild(a);
                a.click();
                a.remove();
                return true;
            }
            return false;
        } catch (error) {
            console.error("Report generation failed", error);
            return false;
        }
    };

    const sendMessage = async (query) => {
        if (!query.trim()) return;

        const userMsg = { role: 'user', content: query };
        setMessages(prev => [...prev, userMsg]);
        setChatLoading(true);
        setChartData(null);

        try {
            // Note: Backend router for chat is /chat (POST)
            const response = await fetch(`${BASE_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: userMsg.content }),
            });
            const data = await response.json();

            setMessages(prev => [...prev, { role: 'agent', content: data.answer }]);
            if (data.chart_type) setChartData(data);
        } catch (error) {
            setMessages(prev => [...prev, { role: 'agent', content: 'Connection error. Please try again.' }]);
        } finally {
            setChatLoading(false);
        }
    };

    const startIngestionPipeline = async (file) => {
        if (!file) return;
        setIngestionStatus('uploading');
        setIngestionProgress(0);
        setIngestionLogs([]);

        const addLog = (msg) => {
            const timestamp = new Date().toLocaleTimeString();
            setIngestionLogs(prev => [`[${timestamp}] ${msg}`, ...prev]);
        };

        addLog(`Started ingestion pipeline for ${file.name}...`);
        const formData = new FormData();
        formData.append('file', file);

        try {
            setIngestionProgress(30);
            addLog("Uploading file to secure storage...");

            const response = await fetch(`${BASE_URL}/ingest/file`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                setIngestionProgress(60);
                setIngestionStatus('processing');
                addLog("Upload complete. Triggering ingestion engine...");

                setTimeout(() => {
                    setIngestionProgress(85);
                    addLog("Parsing entities and updating vector index...");

                    setTimeout(() => {
                        setIngestionProgress(100);
                        setIngestionStatus('complete');
                        addLog("Ingestion complete. Knowledge base updated.");

                        const now = new Date().toLocaleString();
                        setLastSync(now);
                        localStorage.setItem('last_ingestion_sync', now);
                    }, 1500);
                }, 1500);
            } else {
                setIngestionStatus('error');
                addLog("Error: Upload failed.");
            }
        } catch (error) {
            setIngestionStatus('error');
            addLog("Error: Connection failed.");
        }
    };

    return {
        stats,
        riskData,
        score,
        trends,
        mlStatus,
        readiness,
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
