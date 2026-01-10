"use client";

import { Youtube, TrendingUp, Eye, ExternalLink, Play } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { YouTubeInsight } from "@/lib/api";

interface YouTubeCardProps {
    insight: YouTubeInsight | null;
    className?: string;
}

export default function YouTubeCard({ insight, className }: YouTubeCardProps) {
    const isWeekly = insight?.period === "weekly";

    if (!insight) {
        return (
            <Card className={cn("flex h-full min-h-[500px] flex-col bg-card/50 backdrop-blur-sm border-white/5", className)}>
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <Youtube className="h-5 w-5 text-red-500" />
                        <CardTitle className="card-title">YouTube Influencers</CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="flex flex-1 items-center justify-center">
                    <p className="card-empty-text">Waiting for insights...</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className={cn(
            "flex h-full min-h-[500px] flex-col bg-card/50 backdrop-blur-sm overflow-hidden transition-colors duration-500",
            isWeekly ? "border-accent/30" : "border-white/5",
            className
        )}>
            <CardHeader className="border-b border-white/5 pb-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Youtube className={cn("h-5 w-5", isWeekly ? "text-red-400" : "text-red-500")} />
                        <CardTitle className="card-title">
                            {isWeekly ? "Weekly YouTube Rewind" : "YouTube Influencers"}
                        </CardTitle>
                    </div>
                    <Badge variant="outline" className="border-white/10 text-muted-foreground">
                        {new Date(insight.date).toLocaleDateString()}
                    </Badge>
                </div>
            </CardHeader>

            <ScrollArea className="flex-1">
                <CardContent className="pt-6 space-y-8">
                    {/* Trend Summary */}
                    {insight.trend_summary && (
                        <div>
                            <h3 className={cn("font-serif text-lg tracking-wide mb-3", isWeekly ? "text-accent" : "text-white")}>
                                {isWeekly ? "Week in Review" : "What Influencers Are Discussing"}
                            </h3>
                            <p className="text-muted-foreground leading-relaxed hover:text-white transition-colors">
                                {insight.trend_summary}
                            </p>
                        </div>
                    )}

                    {/* Key Topics */}
                    {insight.key_topics.length > 0 && (
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <TrendingUp className={cn("h-4 w-4", isWeekly ? "text-accent" : "text-accent")} />
                                <h3 className={cn("font-serif text-lg tracking-wide", isWeekly ? "text-accent" : "text-white")}>
                                    Trending Topics
                                </h3>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {insight.key_topics.map((topic, i) => (
                                    <span
                                        key={i}
                                        className="item-tag"
                                    >
                                        {topic}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Video List */}
                    {insight.videos.length > 0 && (
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <Play className={cn("h-4 w-4", isWeekly ? "text-accent" : "text-accent")} />
                                <h3 className={cn("font-serif text-lg tracking-wide", isWeekly ? "text-accent" : "text-white")}>
                                    {isWeekly ? "Top Videos This Week" : "Recent Videos"}
                                </h3>
                            </div>
                            <div className="space-y-3">
                                {insight.videos.slice(0, 10).map((video) => (
                                    <div
                                        key={video.id}
                                        className="item-card"
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="flex-1 min-w-0">
                                                <p className="item-title truncate">
                                                    {video.title}
                                                </p>
                                                <div className="flex items-center gap-3 mt-1 item-meta">
                                                    <span className="text-red-400/80">{video.channel_name}</span>
                                                    <span className="flex items-center gap-1">
                                                        <Eye className="h-3 w-3" />
                                                        {video.view_count >= 1000
                                                            ? `${(video.view_count / 1000).toFixed(1)}k`
                                                            : video.view_count}
                                                    </span>
                                                </div>

                                                {/* Video Summary */}
                                                {video.summary && (
                                                    <div className="mt-2 bg-white/5 rounded p-2 border border-white/5">
                                                        <p className="text-xs text-muted-foreground leading-snug hover:text-white transition-colors">
                                                            {video.summary}
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                            <a
                                                href={`https://youtube.com/watch?v=${video.id}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="shrink-0 p-1 text-muted-foreground hover:text-red-400 transition-colors"
                                            >
                                                <ExternalLink className="h-4 w-4" />
                                            </a>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </CardContent>
            </ScrollArea>
        </Card>
    );
}
