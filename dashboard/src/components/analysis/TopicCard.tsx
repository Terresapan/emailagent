import React from 'react';
import { cn } from "@/lib/utils";
import { TrendSparkline } from './TrendSparkline';

/* Using tokens from globals.css:
 * .trend-score-value
 * .trend-label
 * .audience-badge
 * .trend-card
 */

interface TopicCardProps {
    keyword: string;
    interestScore: number;
    momentum: number;
    trendDirection: string;
    relatedQueries: string[];
    audienceTags: string[];
    trendScore: number; // Composite score (0-100)
}

export const TopicCard: React.FC<TopicCardProps> = ({
    keyword,
    interestScore,
    momentum,
    trendDirection,
    relatedQueries,
    audienceTags,
    trendScore,
}) => {
    const isRising = momentum > 0;

    return (
        <div className="trend-card group">
            {/* Header Row */}
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="card-title-sm text-white/90 group-hover:text-white transition-colors">
                        {keyword}
                    </h3>
                    <div className="flex gap-2 mt-2">
                        {audienceTags.map(tag => (
                            <span
                                key={tag}
                                className={cn(
                                    "audience-badge",
                                    tag === 'builder' ? "audience-badge-builder" : "audience-badge-founder"
                                )}
                            >
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Score Visual */}
                <div className="text-right">
                    <div className="trend-score-value text-accent">
                        {trendScore}
                    </div>
                    <div className="trend-label mt-1">
                        Trend Score
                    </div>
                </div>
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-2 gap-4 mb-4 border-t border-white/5 pt-4">
                <div>
                    <div className="trend-label mb-1">Interest</div>
                    <div className="text-white font-medium text-lg">
                        {interestScore}/100
                    </div>
                </div>

                <div className="relative">
                    <div className="trend-label mb-1">Momentum</div>
                    <div className="flex items-center gap-2">
                        <span className={cn(
                            "font-medium text-lg",
                            isRising ? "text-accent" : "text-white/60"
                        )}>
                            {momentum > 0 ? '+' : ''}{momentum}%
                        </span>
                    </div>
                    {/* Sparkline Visual Overlay */}
                    <div className="absolute top-0 right-0 -mt-2 opacity-50">
                        <TrendSparkline momentum={momentum} trendDirection={trendDirection} className="h-10 w-16" />
                    </div>
                </div>
            </div>

            {/* Related Queries */}
            <div className="border-t border-white/5 pt-3">
                <div className="trend-label mb-2 opacity-70">Rising Context</div>
                <div className="flex flex-wrap gap-2">
                    {relatedQueries.slice(0, 3).map(query => (
                        <span
                            key={query}
                            className="text-xs text-muted-foreground bg-white/5 px-2 py-1 rounded hover:bg-white/10 transition-colors cursor-default"
                        >
                            {query}
                        </span>
                    ))}
                    {relatedQueries.length > 3 && (
                        <span className="text-xs text-muted-foreground/50 px-2 py-1">
                            +{relatedQueries.length - 3}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
};
