"use client";

import React, { useState, useEffect } from 'react';
import { RefreshCw, Rocket, Zap, Youtube, ExternalLink, Archive as ArchiveIcon } from 'lucide-react';
import { OpportunityCard } from '@/components/discovery/OpportunityCard';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MotionOrchestrator, MotionItem } from "@/components/MotionOrchestrator";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { archiveItem, runDiscovery, DiscoveryBriefing, VideoData } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { useRouter } from "next/navigation";

interface DiscoveryClientProps {
    initialBriefing: DiscoveryBriefing | null;
    initialVideos: VideoData[];
}

const TABS = [
    { id: 'discovery', label: 'Top Ideas', icon: Rocket },
    { id: 'videos', label: 'Videos', icon: Youtube },
    { id: 'stats', label: 'API Stats', icon: Zap },
];

export default function DiscoveryClient({ initialBriefing, initialVideos }: DiscoveryClientProps) {
    const router = useRouter();
    const [activeTab, setActiveTab] = useState('discovery');
    
    // We use the initial props, but allowing re-fetching/refreshing via router
    const [briefing, setBriefing] = useState<DiscoveryBriefing | null>(initialBriefing);
    const [videos, setVideos] = useState<VideoData[]>(initialVideos);
    
    const [running, setRunning] = useState(false);
    const [statusMsg, setStatusMsg] = useState<string | null>(null);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(new Date());

    const [archiving, setArchiving] = useState(false);
    const { toast } = useToast();

    // Sync with server props if they change (e.g. after navigation/refresh)
    useEffect(() => {
        setBriefing(initialBriefing);
        setVideos(initialVideos);
        setLastRefresh(new Date());
    }, [initialBriefing, initialVideos]);

    const handleArchiveDiscovery = async () => {
        if (!briefing) return;
        setArchiving(true);
        try {
            await archiveItem(
                "discovery",
                0, // No ID on briefing object, using 0 as placeholder
                `Discovery - ${new Date(briefing.date).toLocaleDateString()}`,
                `${briefing.top_opportunities.length} opportunities, ${briefing.total_data_points} data points`,
                briefing
            );
            toast({
                title: "Saved to Archives",
                description: "Discovery briefing saved.",
            });
        } catch (error) {
            toast({
                title: "Failed to Archive",
                description: "Could not save.",
                variant: "destructive",
            });
        } finally {
            setArchiving(false);
        }
    };

    const handleRunDiscovery = async () => {
        setRunning(true);
        setStatusMsg("Running discovery (~5-10 min)...");
        try {
            const data = await runDiscovery();
            setStatusMsg("✅ Discovery complete!");
            setBriefing(data);
            setLastRefresh(new Date());
            router.refresh(); // Refresh server data for consistency
            setTimeout(() => setStatusMsg(null), 5000);
        } catch (e: any) {
            setStatusMsg(`❌ ${e.message || 'Discovery failed'}`);
        } finally {
            setRunning(false);
        }
    };

    const handleRefresh = () => {
        router.refresh();
    };

    return (
        <div className="min-h-screen pb-20">
            {/* Giant Typography Header */}
            <MotionOrchestrator className="mb-20">
                <MotionItem className="relative z-10 -ml-2 lg:-ml-4">
                    <h1 className="utitle select-none">
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
                            className="gap-2 bg-primary hover:opacity-90 text-primary-foreground border-0 shadow-lg shadow-primary/20"
                        >
                            <Rocket className={cn("h-3 w-3", running && "animate-bounce")} />
                            {running ? "Running..." : "Run Discovery"}
                        </Button>

                        <div className="flex items-center gap-3 text-muted-foreground text-xs tracking-widest uppercase">
                            {lastRefresh && (
                                <span>
                                    {lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            )}
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={handleRefresh}
                                className="hover:text-white hover:bg-white/5"
                            >
                                <RefreshCw className="h-4 w-4" />
                            </Button>
                        </div>

                        {/* Archive Button */}
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={handleArchiveDiscovery}
                            disabled={archiving || !briefing}
                            className="hover:text-accent hover:bg-accent/10 transition-colors ml-2"
                            title="Save to Archives"
                        >
                            <ArchiveIcon className={cn("h-4 w-4", archiving && "animate-pulse")} />
                        </Button>
                    </div>

                </MotionItem>
            </MotionOrchestrator>

            {/* Content Area */}
            <MotionOrchestrator>
                {activeTab === 'discovery' && briefing ? (
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
                                        sourceBreakdown={opp.source_breakdown}
                                        similarProducts={opp.similar_products}
                                    />
                                ))}
                            </div>
                        </MotionItem>
                    </div>
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
                                            <Card className="bg-card/50 backdrop-blur-sm border-white/5 hover:border-primary/50 transition-colors">
                                                <CardContent className="pt-6">
                                                    <div className="flex gap-3">
                                                        <Youtube className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                                                        <div className="flex-1 min-w-0">
                                                            <h3 className="font-medium text-white line-clamp-2 text-sm">{video.title}</h3>
                                                            <p className="text-xs text-muted-foreground mt-1">{video.channel}</p>
                                                            <div className="flex items-center gap-2 mt-2">
                                                                <span className="text-xs text-primary">{video.views?.toLocaleString()} views</span>
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
            </MotionOrchestrator >
        </div >
    );
}