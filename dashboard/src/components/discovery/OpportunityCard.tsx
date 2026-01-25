import React from 'react';
import { cn } from "@/lib/utils";
import { Zap, Hammer, TrendingUp, MessageSquare, Twitter, Youtube, Package } from 'lucide-react';

interface OpportunityCardProps {
    rank: number;
    appIdea: string;
    problem: string;
    demandScore: number;
    viralityScore: number;
    buildabilityScore: number;
    opportunityScore: number;
    sources: string[];
    sourceBreakdown?: Record<string, number>;  // {"reddit": 120, "twitter": 45}
    similarProducts?: string[];
}

// Source icon mapping
const SourceIcon: React.FC<{ source: string; className?: string }> = ({ source, className }) => {
    const iconClass = cn("h-3 w-3", className);
    switch (source.toLowerCase()) {
        case 'reddit':
            return <MessageSquare className={iconClass} />;
        case 'twitter':
            return <Twitter className={iconClass} />;
        case 'youtube':
            return <Youtube className={iconClass} />;
        case 'producthunt':
            return <Package className={iconClass} />;
        default:
            return <Zap className={iconClass} />;
    }
};

export const OpportunityCard: React.FC<OpportunityCardProps> = ({
    rank,
    appIdea,
    problem,
    demandScore,
    viralityScore,
    buildabilityScore,
    opportunityScore,
    sources,
    sourceBreakdown,
    similarProducts,
}) => {
    // Score color based on value
    const getScoreColor = (score: number) => {
        if (score >= 80) return "text-green-400";
        if (score >= 60) return "text-accent";
        if (score >= 40) return "text-yellow-400";
        return "text-muted-foreground";
    };

    // Count unique sources
    const sourceCount = sourceBreakdown ? Object.keys(sourceBreakdown).length : new Set(sources).size;

    return (
        <div className="trend-card group relative">
            {/* Rank Badge */}
            <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-accent flex items-center justify-center text-sm font-bold text-white shadow-lg">
                {rank}
            </div>

            {/* Multi-source indicator */}
            {sourceCount > 1 && (
                <div className="absolute -top-2 -right-2 px-2 py-0.5 rounded-full bg-green-500/20 border border-green-500/30 text-[10px] font-medium text-green-400">
                    {sourceCount} sources
                </div>
            )}

            {/* Header Row */}
            <div className="flex justify-between items-start mb-4 pt-2">
                <div className="flex-1 pr-4">
                    <h3 className="card-title-sm text-white/90 group-hover:text-white transition-colors leading-tight">
                        {appIdea}
                    </h3>
                </div>

                {/* Opportunity Score */}
                <div className="text-right shrink-0">
                    <div className={cn("trend-score-value", getScoreColor(opportunityScore))}>
                        {opportunityScore}
                    </div>
                    <div className="trend-label mt-1">
                        Score
                    </div>
                </div>
            </div>

            {/* Problem Description - Full text with scroll */}
            <p className="text-sm text-muted-foreground mb-4 max-h-[100px] overflow-y-auto">
                {problem}
            </p>

            {/* Score Breakdown */}
            <div className="grid grid-cols-3 gap-2 mb-4 border-t border-white/5 pt-4">
                <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                        <TrendingUp className="h-3 w-3 text-muted-foreground" />
                    </div>
                    <div className={cn("font-medium", getScoreColor(demandScore))}>
                        {demandScore}
                    </div>
                    <div className="text-xs text-muted-foreground">Validation</div>
                </div>
                <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                        <Zap className="h-3 w-3 text-muted-foreground" />
                    </div>
                    <div className={cn("font-medium", getScoreColor(viralityScore))}>
                        {viralityScore}
                    </div>
                    <div className="text-xs text-muted-foreground">Engagement</div>
                </div>
                <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                        <Hammer className="h-3 w-3 text-muted-foreground" />
                    </div>
                    <div className={cn("font-medium", getScoreColor(buildabilityScore))}>
                        {buildabilityScore}
                    </div>
                    <div className="text-xs text-muted-foreground">Build</div>
                </div>
            </div>

            {/* Source Breakdown with Engagement */}
            <div className="border-t border-white/5 pt-3">
                <div className="flex flex-wrap gap-2">
                    {sourceBreakdown ? (
                        Object.entries(sourceBreakdown).map(([source, engagement]) => (
                            <span
                                key={source}
                                className="flex items-center gap-1 text-xs text-muted-foreground bg-white/5 px-2 py-1 rounded"
                            >
                                <SourceIcon source={source} />
                                <span className="capitalize">{source}</span>
                                <span className="text-white/70">{engagement}</span>
                            </span>
                        ))
                    ) : (
                        [...new Set(sources)].map(source => (
                            <span
                                key={source}
                                className="flex items-center gap-1 text-xs text-muted-foreground bg-white/5 px-2 py-1 rounded capitalize"
                            >
                                <SourceIcon source={source} />
                                {source}
                            </span>
                        ))
                    )}
                </div>
            </div>

            {/* Similar Products from Product Hunt */}
            {similarProducts && similarProducts.length > 0 && (
                <div className="border-t border-white/5 pt-3 mt-3">
                    <div className="text-xs text-muted-foreground mb-1">Similar on PH:</div>
                    <div className="text-xs text-white/60 line-clamp-2">
                        {similarProducts.join(', ')}
                    </div>
                </div>
            )}
        </div>
    );
};

