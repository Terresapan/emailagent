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
            return <Youtube className={cn(iconClass, "text-primary")} />;
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
    // Score color based on value using semantic classes
    const getScoreColor = (score: number) => {
        if (score >= 80) return "text-accent";
        if (score >= 60) return "text-primary";
        if (score >= 40) return "text-muted-foreground";
        return "text-destructive";
    };

    // Count unique sources
    const sourceCount = sourceBreakdown ? Object.keys(sourceBreakdown).length : new Set(sources).size;

    return (
        <div className="trend-card group relative transition-all duration-300 hover:shadow-[0_0_20px_hsl(var(--primary)/0.25)] hover:border-primary/30">
            {/* Rank Badge */}
            <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-primary flex items-center justify-center text-xs font-bold text-primary-foreground shadow-lg">
                {rank}
            </div>

            {/* Multi-source indicator */}
            {sourceCount > 1 && (
                <div className="absolute -top-2 -right-2 item-tag">
                    {sourceCount} sources
                </div>
            )}

            {/* Header Row with Score */}
            <div className="flex justify-between items-start mb-4 pt-2 pb-4 border-b border-border">
                {/* Opportunity Score - Top-right for prominence */}
                <div className="order-2 text-right shrink-0 ml-3">
                    <div className={cn("trend-score-value", getScoreColor(opportunityScore))}>
                        {opportunityScore}
                    </div>
                    <div className="trend-label mt-1">
                        Score
                    </div>
                </div>

                {/* App Name + Tagline - Split on em-dash */}
                <div className="order-1 flex-1 min-w-0">
                    {(() => {
                        const parts = appIdea.split(/\s*[—–-]\s*/);
                        const appName = parts[0] || appIdea;
                        // Capitalize first letter and join with shorter en-dash
                        const rawTagline = parts.slice(1).join(' – ');
                        const tagline = rawTagline.charAt(0).toUpperCase() + rawTagline.slice(1);
                        return (
                            <>
                                <h3 className="section-header group-hover:text-foreground transition-colors">
                                    {appName}
                                </h3>
                                {tagline && (
                                    <p className="text-sm text-muted-foreground mt-1 leading-snug">
                                        {tagline}
                                    </p>
                                )}
                            </>
                        );
                    })()}
                </div>
            </div>

            {/* Problem Section - Separated with its own header */}
            <div className="mb-4">
                <div className="item-description font-semibold mb-2">Problem:</div>
                <p className="item-description max-h-[100px] overflow-y-auto leading-relaxed">
                    {problem}
                </p>
            </div>

            {/* Score Breakdown */}
            <div className="grid grid-cols-3 gap-2 mb-4 border-t border-border pt-4">
                <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                        <TrendingUp className="h-3 w-3 text-muted-foreground" />
                    </div>
                    <div className={cn("font-medium text-lg", getScoreColor(demandScore))}>
                        {demandScore}
                    </div>
                    <div className="trend-label">Validation</div>
                </div>
                <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                        <Zap className="h-3 w-3 text-muted-foreground" />
                    </div>
                    <div className={cn("font-medium text-lg", getScoreColor(viralityScore))}>
                        {viralityScore}
                    </div>
                    <div className="trend-label">Engagement</div>
                </div>
                <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                        <Hammer className="h-3 w-3 text-muted-foreground" />
                    </div>
                    <div className={cn("font-medium text-lg", getScoreColor(buildabilityScore))}>
                        {buildabilityScore}
                    </div>
                    <div className="trend-label">Build</div>
                </div>
            </div>

            {/* Source Breakdown with Engagement */}
            <div className="border-t border-border pt-3">
                <div className="flex flex-wrap gap-2">
                    {sourceBreakdown ? (
                        Object.entries(sourceBreakdown).map(([source, engagement]) => (
                            <span
                                key={source}
                                className="item-tag-neutral flex items-center gap-1.5"
                            >
                                <SourceIcon source={source} />
                                <span className="capitalize">{source}</span>
                                <span className="text-foreground/70 font-semibold">{engagement}</span>
                            </span>
                        ))
                    ) : (
                        [...new Set(sources)].map(source => (
                            <span
                                key={source}
                                className="item-tag-neutral flex items-center gap-1.5 capitalize"
                            >
                                <SourceIcon source={source} />
                                {source}
                            </span>
                        ))
                    )}
                </div>
            </div>

            {/* Similar Products from Google Search */}
            {similarProducts && similarProducts.length > 0 && (
                <div className="border-t border-border pt-3 mt-3">
                    <div className="item-description font-semibold mb-1.5">Similar Products:</div>
                    <div className="item-description hover:text-foreground transition-colors cursor-default">
                        {similarProducts.join(', ')}
                    </div>
                </div>
            )}
        </div>
    );
};
