import { Newspaper, TrendingUp, MessageSquare, ExternalLink } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { HackerNewsInsight } from "@/lib/api";

interface HackerNewsCardProps {
  insight: HackerNewsInsight | null;
  className?: string;
}

export default function HackerNewsCard({ insight, className }: HackerNewsCardProps) {
  const isWeekly = insight?.period === "weekly";

  if (!insight) {
    return (
      <Card className={cn("flex h-full min-h-[500px] flex-col bg-card/50 backdrop-blur-sm border-white/5", className)}>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Newspaper className="h-5 w-5 text-primary" />
            <h2 className="card-title">HackerNews</h2>
          </div>
        </CardHeader>
        <CardContent className="flex flex-1 items-center justify-center">
          <p className="card-empty-text">Waiting for trends...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn(
      "flex h-full min-h-[500px] flex-col bg-card/50 backdrop-blur-sm overflow-hidden transition-colors duration-500",
      isWeekly ? "border-primary/30" : "border-white/5",
      className
    )}>
      <CardHeader className="border-b border-white/5 pb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Newspaper className={cn("h-5 w-5", isWeekly ? "text-primary" : "text-primary")} />
            <h2 className="card-title">
              {isWeekly ? "Weekly HN Rewind" : "HackerNews"}
            </h2>
          </div>
          <Badge variant="outline" className="border-white/10 text-muted-foreground">
            {new Date(insight.date).toLocaleDateString()}
          </Badge>
        </div>
      </CardHeader>

      <ScrollArea className="flex-1">
        <CardContent className="pt-6 space-y-8">
          {/* Developer Zeitgeist Summary */}
          {insight.summary && (
            <div>
              <h3 className={cn("font-serif text-lg tracking-wide mb-3", isWeekly ? "text-primary" : "text-white")}>
                {isWeekly ? "Meta-Trend Synthesis" : "Developer Zeitgeist"}
              </h3>
              <p className="text-muted-foreground leading-relaxed hover:text-white transition-colors">
                {insight.summary}
              </p>
            </div>
          )}

          {/* Top Themes */}
          {insight.top_themes.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className={cn("h-4 w-4", isWeekly ? "text-primary" : "text-primary")} />
                <h3 className={cn("font-serif text-lg tracking-wide", isWeekly ? "text-primary" : "text-white")}>
                  Top Themes
                </h3>
              </div>
              <div className="space-y-2">
                {insight.top_themes.map((theme, i) => (
                  <div
                    key={i}
                    className="item-card"
                  >
                    <p className="list-item-text tracking-wide">{theme}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top Stories */}
          {insight.stories.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <MessageSquare className={cn("h-4 w-4", isWeekly ? "text-primary" : "text-primary")} />
                <h3 className={cn("font-serif text-lg tracking-wide", isWeekly ? "text-primary" : "text-white")}>
                  {isWeekly ? "Most Discussed this Week" : "Top Stories"}
                </h3>
              </div>
              <div className="space-y-3">
                {insight.stories.slice(0, 10).map((story, i) => (
                  <div
                    key={story.id}
                    className="item-card"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="item-title truncate">
                          {story.title}
                        </p>
                        <div className="flex items-center gap-3 mt-1 item-meta">
                          <span>{story.score} pts</span>
                          <span>{story.comments_count} comments</span>
                          {story.github_stars && (
                            <span className="flex items-center gap-1 text-primary">
                              ⭐ {story.github_stars >= 1000 ? `${(story.github_stars / 1000).toFixed(1)}k` : story.github_stars}
                            </span>
                          )}
                          {story.by && <span>by {story.by}</span>}
                        </div>

                        {/* Community Verdict */}
                        {(story.verdict || story.sentiment) && (
                          <div className="mt-2 flex items-start gap-2 bg-white/5 rounded p-2 border border-white/5">
                            {story.sentiment && <span className="text-sm shrink-0 mt-0.5" aria-label="Sentiment">{story.sentiment}</span>}
                            {story.verdict && (
                              <p className="text-sm text-muted-foreground leading-snug hover:text-white transition-colors">
                                <span className={cn("font-semibold", isWeekly ? "text-primary/80" : "text-primary/80")}>Verdict: </span>
                                {story.verdict}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                      {story.url && (
                        <a
                          href={story.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="shrink-0 p-1 text-muted-foreground hover:text-white transition-colors"
                          aria-label={`Open ${story.title} in new tab`}
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      )}
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
