"use client";

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
  if (!insight) {
    return (
      <Card className={cn("flex h-full min-h-[500px] flex-col bg-card/50 backdrop-blur-sm border-white/5", className)}>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Newspaper className="h-5 w-5 text-brand-fuchsia" />
            <CardTitle className="font-serif text-2xl tracking-wide text-white">HackerNews</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="flex flex-1 items-center justify-center">
          <p className="font-serif italic text-muted-foreground">Waiting for trends...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn(
      "flex h-full min-h-[500px] flex-col bg-card/50 backdrop-blur-sm overflow-hidden border-white/5",
      className
    )}>
      <CardHeader className="border-b border-white/5 pb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Newspaper className="h-5 w-5 text-brand-fuchsia" />
            <CardTitle className="font-serif text-2xl tracking-wide text-white">
              HackerNews
            </CardTitle>
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
              <h3 className="font-serif text-lg tracking-wide text-white mb-3">
                Developer Zeitgeist
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
                <TrendingUp className="h-4 w-4 text-brand-fuchsia" />
                <h3 className="font-serif text-lg tracking-wide text-white">
                  Top Themes
                </h3>
              </div>
              <div className="space-y-2">
                {insight.top_themes.map((theme, i) => (
                  <div 
                    key={i}
                    className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-white/5"
                  >
                    <p className="text-muted-foreground tracking-wide hover:text-white transition-colors">{theme}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top Stories */}
          {insight.stories.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <MessageSquare className="h-4 w-4 text-brand-purple" />
                <h3 className="font-serif text-lg tracking-wide text-white">
                  Top Stories
                </h3>
              </div>
              <div className="space-y-3">
                {insight.stories.slice(0, 7).map((story, i) => (
                  <div 
                    key={story.id}
                    className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-white/5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-white truncate">
                          {story.title}
                        </p>
                        <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                          <span>{story.score} pts</span>
                          <span>{story.comments_count} comments</span>
                          {story.by && <span>by {story.by}</span>}
                        </div>
                      </div>
                      {story.url && (
                        <a 
                          href={story.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="shrink-0 p-1 text-muted-foreground hover:text-white transition-colors"
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
