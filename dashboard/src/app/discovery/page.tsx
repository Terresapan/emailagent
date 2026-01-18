'use client';

import React, { useState, useEffect } from 'react';
import { Play, RefreshCw, Rocket, Zap, Hammer, TrendingUp, Youtube, ExternalLink } from 'lucide-react';
import { OpportunityCard } from '@/components/discovery/OpportunityCard';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MotionOrchestrator, MotionItem } from "@/components/MotionOrchestrator";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Types matching the API response
interface PainPoint {
    text: string;
    problem: string;
    source: string;
    engagement: number;
}

interface AppOpportunity {
    problem: string;
    app_idea: string;
    demand_score: number;
    virality_score: number;
    buildability_score: number;
    opportunity_score: number;
    category?: string;
    target_audience?: string;
    pain_points: PainPoint[];
}

interface DiscoveryBriefing {
    date: string;
    top_opportunities: AppOpportunity[];
    total_data_points: number;
    total_pain_points_extracted: number;
    total_candidates_filtered: number;
    arcade_calls: number;
    serpapi_calls: number;
    youtube_quota: number;
    llm_calls: number;
    estimated_cost: number;
}

// New types for trends and videos
interface TrendData {
    keyword: string;
    app_idea: string;
    interest_score: number;
    trend_score: number;
    momentum: number;
    trend_direction: string;
    related_queries: string[];
}

interface VideoData {
    id: string;
    title: string;
    views: number;
    channel: string;
    url: string;
}

const TABS = [
    { id: 'discovery', label: 'Top Ideas', icon: Rocket },
    { id: 'trends', label: 'Trends', icon: TrendingUp },
    { id: 'videos', label: 'Videos', icon: Youtube },
    { id: 'stats', label: 'API Stats', icon: Zap },
];

export default function DiscoveryPage() {
    const [activeTab, setActiveTab] = useState('discovery');
    const [briefing, setBriefing] = useState<DiscoveryBriefing | null>(null);
    const [trends, setTrends] = useState<TrendData[]>([]);
    const [videos, setVideos] = useState<VideoData[]>([]);
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const [statusMsg, setStatusMsg] = useState<string | null>(null);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
    const [mounted, setMounted] = useState(false);

    const handleRunDiscovery = async () => {
        setRunning(true);
        setStatusMsg("Running discovery (~5-10 min)...");
        try {
            const res = await fetch('http://localhost:8000/api/discovery/run', {
                method: 'POST'
            });
            if (res.ok) {
                setStatusMsg("✅ Discovery complete!");
                const data = await res.json();
                setBriefing(data);
                setLastRefresh(new Date());
                // Refresh tabs data
                fetchTrends();
                fetchVideos();
                setTimeout(() => setStatusMsg(null), 5000);
            } else {
                const error = await res.json();
                setStatusMsg(`❌ ${error.detail || 'Discovery failed'}`);
            }
        } catch (e) {
            setStatusMsg("❌ Error connecting to server.");
        } finally {
            setRunning(false);
        }
    };

    const fetchBriefing = async () => {
        setLoading(true);
        try {
            const res = await fetch('http://localhost:8000/api/discovery/briefing');
            if (res.ok) {
                const data = await res.json();
                setBriefing(data);
                setLastRefresh(new Date());
            } else {
                setBriefing(null);
            }
        } catch (error) {
            console.error("Failed to fetch briefing", error);
            setBriefing(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        setMounted(true);
        fetchBriefing();
        fetchTrends();
        fetchVideos();
    }, []);

    const fetchTrends = async () => {
        try {
            console.log("Fetching trends...");
            const res = await fetch('http://localhost:8000/api/discovery/trends', { cache: 'no-store' });
            if (res.ok) {
                const data = await res.json();
                console.log("Trends data:", data);
                setTrends(data.trends || []);
            } else {
                console.error("Trends fetch failed:", res.status);
            }
        } catch (error) {
            console.error("Failed to fetch trends", error);
        }
    };

    const fetchVideos = async () => {
        try {
            console.log("Fetching videos...");
            const res = await fetch('http://localhost:8000/api/discovery/videos', { cache: 'no-store' });
            if (res.ok) {
                const data = await res.json();
                console.log("Videos data:", data);
                setVideos(data.videos || []);
            } else {
                console.error("Videos fetch failed:", res.status);
            }
        } catch (error) {
            console.error("Failed to fetch videos", error);
        }
    };

    return (
        <div className="min-h-screen pb-20">
            {/* Giant Typography Header */}
            <MotionOrchestrator className="mb-20">
                <MotionItem className="relative z-10 -ml-2 lg:-ml-4">
                    <h1 className="font-serif text-giant font-bold tracking-tighter leading-[0.8] select-none text-transparent bg-clip-text bg-gradient-to-b from-foreground to-muted-foreground">
                        VIRAL APP<br />DISCOVERY
                    </h1>
                </MotionItem>

                {/* Navigation */}
                <MotionItem className="relative z-20 flex items-center justify-between border-b border-white/10 pb-6 mt-4">
                    <div className="flex gap-8">
                        {TABS.map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={cn(
                                    "flex items-center gap-2 text-sm font-medium tracking-[0.2em] uppercase transition-all duration-300",
                                    activeTab === tab.id
                                        ? "text-accent"
                                        : "text-muted-foreground hover:text-white"
                                )}
                            >
                                <tab.icon className="h-4 w-4" />
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    <div className="flex items-center gap-6">
                        {statusMsg && (
                            <span className={cn(
                                "text-xs font-medium px-3 py-1 rounded-full",
                                statusMsg.includes("✅") ? "bg-green-500/20 text-green-400" :
                                    statusMsg.includes("❌") ? "bg-red-500/20 text-red-400" :
                                        "bg-accent/20 text-accent animate-pulse"
                            )}>
                                {statusMsg}
                            </span>
                        )}

                        <Button
                            variant="default"
                            size="sm"
                            disabled={running}
                            onClick={handleRunDiscovery}
                            className="gap-2 bg-accent hover:opacity-90 text-white border-0 shadow-lg shadow-accent/20"
                        >
                            <Rocket className={cn("h-3 w-3", running && "animate-bounce")} />
                            {running ? "Running..." : "Run Discovery"}
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
                                onClick={fetchBriefing}
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
                ) : activeTab === 'discovery' && briefing ? (
                    <div className="space-y-8">
                        {/* Stats Summary */}
                        <MotionItem>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <Card className="bg-card/50 backdrop-blur-sm border-white/5">
                                    <CardContent className="pt-6">
                                        <div className="text-3xl font-bold text-accent">{briefing.top_opportunities.length}</div>
                                        <div className="text-sm text-muted-foreground">Top Opportunities</div>
                                    </CardContent>
                                </Card>
                                <Card className="bg-card/50 backdrop-blur-sm border-white/5">
                                    <CardContent className="pt-6">
                                        <div className="text-3xl font-bold text-white">{briefing.total_data_points}</div>
                                        <div className="text-sm text-muted-foreground">Data Points</div>
                                    </CardContent>
                                </Card>
                                <Card className="bg-card/50 backdrop-blur-sm border-white/5">
                                    <CardContent className="pt-6">
                                        <div className="text-3xl font-bold text-white">{briefing.total_pain_points_extracted}</div>
                                        <div className="text-sm text-muted-foreground">Pain Points Found</div>
                                    </CardContent>
                                </Card>
                                <Card className="bg-card/50 backdrop-blur-sm border-white/5">
                                    <CardContent className="pt-6">
                                        <div className="text-3xl font-bold text-green-400">${briefing.estimated_cost.toFixed(2)}</div>
                                        <div className="text-sm text-muted-foreground">API Cost</div>
                                    </CardContent>
                                </Card>
                            </div>
                        </MotionItem>

                        {/* Opportunities Grid */}
                        <MotionItem>
                            <div className="flex justify-between items-end mb-6">
                                <h2 className="section-header">App Ideas ({briefing.top_opportunities.length})</h2>
                                <span className="item-meta">
                                    Generated: {new Date(briefing.date).toLocaleDateString()}
                                </span>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                                {briefing.top_opportunities.map((opp, index) => (
                                    <OpportunityCard
                                        key={index}
                                        rank={index + 1}
                                        appIdea={opp.app_idea}
                                        problem={opp.problem}
                                        demandScore={opp.demand_score}
                                        viralityScore={opp.virality_score}
                                        buildabilityScore={opp.buildability_score}
                                        opportunityScore={opp.opportunity_score}
                                        sources={opp.pain_points.map(p => p.source)}
                                    />
                                ))}
                            </div>
                        </MotionItem>
                    </div>
                ) : activeTab === 'trends' ? (
                    <MotionItem>
                        <div className="space-y-6">
                            <h2 className="section-header">Google Trends Validation ({trends.length})</h2>
                            {trends.length > 0 ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {trends.map((trend, index) => (
                                        <Card key={index} className="bg-card/50 backdrop-blur-sm border-white/5">
                                            <CardContent className="pt-6">
                                                <div className="flex justify-between items-start mb-4">
                                                    <div>
                                                        <h3 className="font-semibold text-white">{trend.keyword}</h3>
                                                        <p className="text-sm text-muted-foreground line-clamp-1">{trend.app_idea}</p>
                                                    </div>
                                                    <div className="text-right shrink-0">
                                                        <div className={cn(
                                                            "text-2xl font-bold",
                                                            trend.trend_score >= 60 ? "text-green-400" :
                                                                trend.trend_score >= 40 ? "text-yellow-400" : "text-muted-foreground"
                                                        )}>
                                                            {trend.trend_score}
                                                        </div>
                                                        <div className="text-xs text-muted-foreground">Trend Score</div>
                                                    </div>
                                                </div>
                                                <div className="flex gap-4 text-sm mb-4">
                                                    <span className="text-muted-foreground">Interest: <span className="text-white">{trend.interest_score}</span></span>
                                                    <span className="text-muted-foreground">Direction: <span className={cn(
                                                        trend.trend_direction === 'rising' ? 'text-green-400' :
                                                            trend.trend_direction === 'falling' ? 'text-red-400' : 'text-white'
                                                    )}>{trend.trend_direction}</span></span>
                                                </div>
                                                {trend.related_queries.length > 0 && (
                                                    <div>
                                                        <div className="text-xs text-muted-foreground mb-2">Related Queries:</div>
                                                        <div className="flex flex-wrap gap-2">
                                                            {trend.related_queries.map((q, i) => (
                                                                <span key={i} className="text-xs px-2 py-1 bg-white/5 rounded">{q}</span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            ) : (
                                <div className="py-16 text-center border border-dashed border-white/10 rounded-lg">
                                    <TrendingUp className="h-12 w-12 mx-auto text-muted-foreground/30 mb-4" />
                                    <p className="text-muted-foreground">No trends data available. Run discovery to fetch Google Trends.</p>
                                </div>
                            )}
                        </div>
                    </MotionItem>
                ) : activeTab === 'videos' ? (
                    <MotionItem>
                        <div className="space-y-6">
                            <h2 className="section-header">YouTube Viral Videos ({videos.length})</h2>
                            {videos.length > 0 ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {videos.map((video, index) => (
                                        <a
                                            key={index}
                                            href={video.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="block"
                                        >
                                            <Card className="bg-card/50 backdrop-blur-sm border-white/5 hover:border-accent/50 transition-colors">
                                                <CardContent className="pt-6">
                                                    <div className="flex gap-3">
                                                        <Youtube className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
                                                        <div className="flex-1 min-w-0">
                                                            <h3 className="font-medium text-white line-clamp-2 text-sm">{video.title}</h3>
                                                            <p className="text-xs text-muted-foreground mt-1">{video.channel}</p>
                                                            <div className="flex items-center gap-2 mt-2">
                                                                <span className="text-xs text-accent">{video.views?.toLocaleString()} views</span>
                                                                <ExternalLink className="h-3 w-3 text-muted-foreground" />
                                                            </div>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        </a>
                                    ))}
                                </div>
                            ) : (
                                <div className="py-16 text-center border border-dashed border-white/10 rounded-lg">
                                    <Youtube className="h-12 w-12 mx-auto text-muted-foreground/30 mb-4" />
                                    <p className="text-muted-foreground">No video data available. Run discovery to fetch YouTube videos.</p>
                                </div>
                            )}
                        </div>
                    </MotionItem>
                ) : activeTab === 'stats' && briefing ? (
                    <MotionItem>
                        <Card className="bg-card/50 backdrop-blur-sm border-white/5">
                            <CardHeader>
                                <CardTitle className="card-title">API Usage This Run</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                                    <div>
                                        <div className="text-2xl font-bold text-white">{briefing.arcade_calls}</div>
                                        <div className="text-sm text-muted-foreground">Arcade Calls</div>
                                    </div>
                                    <div>
                                        <div className="text-2xl font-bold text-white">{briefing.serpapi_calls}</div>
                                        <div className="text-sm text-muted-foreground">SerpAPI Calls</div>
                                    </div>
                                    <div>
                                        <div className="text-2xl font-bold text-white">{briefing.youtube_quota}</div>
                                        <div className="text-sm text-muted-foreground">YouTube Quota</div>
                                    </div>
                                    <div>
                                        <div className="text-2xl font-bold text-white">{briefing.llm_calls}</div>
                                        <div className="text-sm text-muted-foreground">LLM Calls</div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </MotionItem>
                ) : (
                    /* Empty State */
                    <MotionItem>
                        <div className="py-32 text-center border border-dashed border-white/10 rounded-lg">
                            <Rocket className="h-16 w-16 mx-auto text-muted-foreground/30 mb-6" />
                            <p className="font-serif text-3xl text-muted-foreground italic">
                                "No discovery data yet."
                            </p>
                            <p className="item-meta mt-4">
                                Click "Run Discovery" to find viral app ideas.
                            </p>
                        </div>
                    </MotionItem>
                )}
            </MotionOrchestrator>
        </div>
    );
}
