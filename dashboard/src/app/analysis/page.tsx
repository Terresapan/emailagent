'use client';

import React, { useState, useEffect } from 'react';
import { TopicCard } from '@/components/analysis/TopicCard';

// Using fetch for client-side data fetching for simplicity in this iteration
// Ideally would use TanStack Query or SWR in production

interface TrendValidation {
    keyword: string;
    interest_score: number;
    momentum: number;
    trend_direction: string;
    related_queries: string[];
    audience_tags: string[];
    trend_score: number;
    api_source: string;
}

interface TopicAnalysis {
    id: number;
    source: string;
    source_date: string;
    topics: TrendValidation[];
    summary: string;
    created_at: string;
}

const SOURCES = [
    { id: 'newsletter', label: 'Newsletter' },
    { id: 'producthunt', label: 'Product Hunt' },
    { id: 'hackernews', label: 'Hacker News' },
    { id: 'youtube', label: 'YouTube' },
    { id: 'manual', label: 'Manual/Ad-hoc' }
];

export default function AnalysisPage() {
    const [activeSource, setActiveSource] = useState('newsletter');
    const [analysis, setAnalysis] = useState<TopicAnalysis | null>(null);
    const [loading, setLoading] = useState(true);
    const [validating, setValidating] = useState(false);
    const [validationMsg, setValidationMsg] = useState<string | null>(null);

    const handleRunAnalysis = async () => {
        setValidating(true);
        setValidationMsg("Running global validation (~30s)...");
        try {
            const res = await fetch('http://localhost:8000/api/analysis/validate?source=all', {
                method: 'POST'
            });
            if (res.ok) {
                setValidationMsg("✅ Analysis complete! Check your inbox.");
                const data = await res.json();
                if (data.source === activeSource) {
                    setAnalysis(data);
                } else {
                    setActiveSource(prev => prev); // Trigger re-fetch
                }
                setTimeout(() => setValidationMsg(null), 5000);
            } else {
                setValidationMsg("❌ Validation failed.");
            }
        } catch (e) {
            setValidationMsg("❌ Error connecting to server.");
        } finally {
            setValidating(false);
        }
    };

    useEffect(() => {
        async function fetchAnalysis() {
            setLoading(true);
            try {
                const res = await fetch(`http://localhost:8000/api/analysis/latest?source=${activeSource}`);
                if (res.ok) {
                    const data = await res.json();
                    setAnalysis(data);
                } else {
                    setAnalysis(null);
                }
            } catch (error) {
                console.error("Failed to fetch analysis", error);
                setAnalysis(null);
            } finally {
                setLoading(false);
            }
        }

        fetchAnalysis();
    }, [activeSource]);

    return (
        <div className="min-h-screen bg-background text-foreground p-8 pl-24">
            {/* Header Section */}
            <header className="mb-12 flex justify-between items-end">
                <div>
                    <div className="section-label text-accent mb-2">Market Validation</div>
                    <h1 className="text-giant font-serif text-white tracking-tight leading-none">
                        Trend<br />Intelligence
                    </h1>
                    <p className="font-sans text-xl text-muted-foreground mt-6 max-w-2xl leading-relaxed">
                        Validation of high-signal topics against global search behavior.
                        Cross-referenced with builder and founder intent.
                    </p>
                </div>

                {/* Global Run Button */}
                <div className="mb-4 flex flex-col items-end gap-2">
                    <button
                        onClick={handleRunAnalysis}
                        disabled={validating}
                        className={`
                            flex items-center gap-2 px-6 py-3 rounded-full font-medium tracking-wide transition-all
                            ${validating
                                ? 'bg-accent/20 text-accent cursor-not-allowed'
                                : 'bg-accent text-white hover:bg-accent/90 hover:shadow-lg hover:shadow-accent/20'}
                        `}
                    >
                        {validating ? (
                            <>
                                <span className="animate-spin">⟳</span> Validating...
                            </>
                        ) : (
                            <>
                                <span>▶</span> Run Global Analysis
                            </>
                        )}
                    </button>
                    {validationMsg && (
                        <span className="text-xs font-medium text-accent animate-pulse">
                            {validationMsg}
                        </span>
                    )}
                </div>
            </header>

            {/* Source Tabs */}
            <div className="flex gap-1 mb-10 border-b border-white/10 pb-4">
                {SOURCES.map(source => (
                    <button
                        key={source.id}
                        onClick={() => setActiveSource(source.id)}
                        className={`
              px-6 py-2 rounded-full text-sm font-medium transition-all duration-300
              ${activeSource === source.id
                                ? 'bg-accent/10 text-accent border border-accent/20'
                                : 'text-muted-foreground hover:text-white hover:bg-white/5 border border-transparent'}
            `}
                    >
                        {source.label}
                    </button>
                ))}
            </div>

            {/* Content Area */}
            {loading ? (
                <div className="animate-pulse space-y-4">
                    <div className="h-40 bg-white/5 rounded-xl w-full" />
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <div className="h-64 bg-white/5 rounded-xl" />
                        <div className="h-64 bg-white/5 rounded-xl" />
                        <div className="h-64 bg-white/5 rounded-xl" />
                    </div>
                </div>
            ) : analysis ? (
                <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">

                    {/* Summary Card */}
                    {analysis.summary && (
                        <div className="glass-card p-8 rounded-2xl border-l-4 border-l-accent">
                            <h2 className="section-header mb-4 text-accent">Validation Summary</h2>
                            <p className="text-lg text-white/90 font-sans leading-relaxed">
                                {analysis.summary}
                            </p>
                        </div>
                    )}

                    {/* Topics Grid */}
                    <div>
                        <div className="flex justify-between items-end mb-6">
                            <h2 className="section-header">Validated Topics ({analysis.topics.length})</h2>
                            <span className="text-xs text-muted-foreground">
                                Last updated: {new Date(analysis.created_at).toLocaleDateString()}
                            </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                            {analysis.topics.map((topic) => (
                                <TopicCard
                                    key={topic.keyword}
                                    keyword={topic.keyword}
                                    interestScore={topic.interest_score}
                                    momentum={topic.momentum}
                                    trendDirection={topic.trend_direction}
                                    relatedQueries={topic.related_queries}
                                    audienceTags={topic.audience_tags}
                                    trendScore={topic.trend_score}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            ) : (
                /* Empty State */
                <div className="flex flex-col items-center justify-center py-20 opacity-50 border border-dashed border-white/10 rounded-2xl">
                    <div className="card-title text-muted-foreground mb-2">No Data Available</div>
                    <p className="text-sm text-gray-500">
                        No trend analysis found for {SOURCES.find(s => s.id === activeSource)?.label}.
                    </p>
                </div>
            )}
        </div>
    );
}
