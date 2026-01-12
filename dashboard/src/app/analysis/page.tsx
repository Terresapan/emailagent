'use client';

import React, { useState, useEffect } from 'react';
import { Play, RefreshCw } from 'lucide-react';
import { TopicCard } from '@/components/analysis/TopicCard';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MotionOrchestrator, MotionItem } from "@/components/MotionOrchestrator";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface TrendValidation {
    keyword: string;
    interest_score: number;
    momentum: number;
    trend_direction: string;
    related_queries: string[];
    audience_tags: string[];
    trend_score: number;
    api_source: string;
    content_source?: string; // Source where keyword was extracted from (newsletter, youtube, producthunt)
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
    { id: 'global', label: 'Global (All)' },
    { id: 'newsletter', label: 'Newsletter' },
    { id: 'producthunt', label: 'Product Hunt' },
    { id: 'hackernews', label: 'Hacker News' },
    { id: 'youtube', label: 'YouTube' },
    { id: 'manual', label: 'Manual/Ad-hoc' }
];

export default function AnalysisPage() {
    const [activeSource, setActiveSource] = useState('global');
    const [analysis, setAnalysis] = useState<TopicAnalysis | null>(null);
    const [loading, setLoading] = useState(true);
    const [validating, setValidating] = useState(false);
    const [validationMsg, setValidationMsg] = useState<string | null>(null);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
    const [mounted, setMounted] = useState(false);

    const handleRunAnalysis = async () => {
        setValidating(true);
        setValidationMsg("Running global validation (~30s)...");
        try {
            // On Saturday, add force=true to bypass auto-skip
            const isSaturday = new Date().getDay() === 6;
            const url = `http://localhost:8000/api/analysis/validate?source=all${isSaturday ? '&force=true' : ''}`;
            const res = await fetch(url, {
                method: 'POST'
            });
            if (res.ok) {
                setValidationMsg("✅ Analysis complete! Check your inbox.");
                const data = await res.json();
                setAnalysis(data);
                setActiveSource(data.source);
                setLastRefresh(new Date());
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

    const fetchAnalysis = async () => {
        setLoading(true);
        try {
            const res = await fetch(`http://localhost:8000/api/analysis/latest?source=${activeSource}`);
            if (res.ok) {
                const data = await res.json();
                setAnalysis(data);
                setLastRefresh(new Date());
            } else {
                setAnalysis(null);
            }
        } catch (error) {
            console.error("Failed to fetch analysis", error);
            setAnalysis(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        setMounted(true);
        fetchAnalysis();
    }, [activeSource]);

    return (
        <div className="min-h-screen pb-20">
            {/* Giant Typography Header */}
            <MotionOrchestrator className="mb-20">
                <MotionItem className="relative z-10 -ml-2 lg:-ml-4">
                    <h1 className="font-serif text-giant font-bold tracking-tighter leading-[0.8] select-none text-transparent bg-clip-text bg-gradient-to-b from-foreground to-muted-foreground">
                        TREND<br />INTELLIGENCE
                    </h1>
                </MotionItem>

                {/* Navigation */}
                <MotionItem className="relative z-20 flex items-center justify-between border-b border-white/10 pb-6 mt-4">
                    <div className="flex gap-8">
                        {SOURCES.map(source => (
                            <button
                                key={source.id}
                                onClick={() => setActiveSource(source.id)}
                                className={cn(
                                    "text-sm font-medium tracking-[0.2em] uppercase transition-all duration-300",
                                    activeSource === source.id
                                        ? "text-accent"
                                        : "text-muted-foreground hover:text-white"
                                )}
                            >
                                {source.label}
                            </button>
                        ))}
                    </div>

                    <div className="flex items-center gap-6">
                        {validationMsg && (
                            <span className={cn(
                                "text-xs font-medium px-3 py-1 rounded-full",
                                validationMsg.includes("✅") ? "bg-green-500/20 text-green-400" :
                                    validationMsg.includes("❌") ? "bg-red-500/20 text-red-400" :
                                        "bg-accent/20 text-accent animate-pulse"
                            )}>
                                {validationMsg}
                            </span>
                        )}

                        <Button
                            variant="default"
                            size="sm"
                            disabled={validating}
                            onClick={handleRunAnalysis}
                            className="gap-2 bg-accent hover:opacity-90 text-white border-0 shadow-lg shadow-accent/20"
                        >
                            <Play className={cn("h-3 w-3", validating && "animate-spin")} />
                            {validating ? "Validating..." : "Run Global Analysis"}
                        </Button>

                        <div className="flex items-center gap-3 text-muted-foreground text-xs tracking-widest uppercase">
                            {mounted && lastRefresh && (
                                <span>
                                    {lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            )}
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={fetchAnalysis}
                                disabled={loading}
                                className="hover:text-white hover:bg-white/5"
                            >
                                <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                            </Button>
                        </div>
                    </div>
                </MotionItem>
            </MotionOrchestrator>

            {/* Content Area */}
            <MotionOrchestrator>
                {loading ? (
                    <MotionItem className="space-y-4 animate-pulse">
                        <div className="h-40 bg-white/5 rounded-lg border border-white/5" />
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                            <div className="h-64 bg-white/5 rounded-lg border border-white/5" />
                            <div className="h-64 bg-white/5 rounded-lg border border-white/5" />
                            <div className="h-64 bg-white/5 rounded-lg border border-white/5" />
                            <div className="h-64 bg-white/5 rounded-lg border border-white/5" />
                        </div>
                    </MotionItem>
                ) : analysis ? (
                    <div className="space-y-8">
                        {/* Summary Card */}
                        {analysis.summary && (
                            <MotionItem>
                                <Card className="bg-card/50 backdrop-blur-sm border-white/5 border-l-4 border-l-accent overflow-hidden">
                                    <CardHeader className="border-b border-white/5 pb-6">
                                        <CardTitle className="card-title">Validation Summary</CardTitle>
                                    </CardHeader>
                                    <CardContent className="pt-6">
                                        <div className="text-lg text-muted-foreground leading-relaxed font-sans space-y-2">
                                            {analysis.summary.split('\n').map((line, i) => (
                                                <p key={i}>
                                                    {line.split('**').map((part, j) => (
                                                        j % 2 === 1 ? <strong key={j} className="text-white font-medium">{part}</strong> : part
                                                    ))}
                                                </p>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            </MotionItem>
                        )}

                        {/* Topics Grid */}
                        <MotionItem>
                            <div className="flex justify-between items-end mb-6">
                                <h2 className="section-header">Validated Topics ({analysis.topics.length})</h2>
                                <span className="item-meta">
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
                                        contentSource={topic.content_source}
                                    />
                                ))}
                            </div>
                        </MotionItem>
                    </div>
                ) : (
                    /* Empty State */
                    <MotionItem>
                        <div className="py-32 text-center border border-dashed border-white/10 rounded-lg">
                            <p className="font-serif text-3xl text-muted-foreground italic">
                                "No trend data available."
                            </p>
                            <p className="item-meta mt-4">
                                No analysis found for {SOURCES.find(s => s.id === activeSource)?.label}.
                            </p>
                        </div>
                    </MotionItem>
                )}
            </MotionOrchestrator>
        </div>
    );
}
