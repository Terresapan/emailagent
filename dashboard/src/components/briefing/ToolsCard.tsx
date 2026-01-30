import { Rocket, TrendingUp, Lightbulb } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ProductLaunch {
  id: string;
  name: string;
  tagline: string;
  votes: number;
  website?: string;
  topics: string[];
}

interface ToolsInsight {
  id: number;
  date: string;
  launches: ProductLaunch[];
  trend_summary?: string;
  content_angles: string[];
  period: "daily" | "weekly";
  created_at: string;
}

interface ToolsCardProps {
  insight: ToolsInsight | null;
  className?: string;
}

export default function ToolsCard({ insight, className }: ToolsCardProps) {
  const isWeekly = insight?.period === "weekly";

  if (!insight) {
    return (
      <Card className={cn("flex h-full min-h-[500px] flex-col bg-card/50 backdrop-blur-sm border-white/5", className)}>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Rocket className="h-5 w-5 text-primary" />
            <CardTitle className="card-title">Product Hunt</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="flex flex-1 items-center justify-center">
          <p className="card-empty-text">Waiting for discoveries...</p>
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
            <Rocket className={cn("h-5 w-5", isWeekly ? "text-primary" : "text-primary")} />
            <CardTitle className="card-title">
              {isWeekly ? "Weekly Product Hunt Best" : "Today's Top Launches"}
            </CardTitle>
          </div>
        </div>
      </CardHeader>

      <ScrollArea className="flex-1">
        <CardContent className="pt-6 space-y-8">
          {/* Top Launches */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className={cn("h-4 w-4", isWeekly ? "text-primary" : "text-primary")} />
              <h3 className={cn("font-serif text-lg tracking-wide", isWeekly ? "text-primary" : "text-white")}>
                {isWeekly ? "Best of the Week" : "Top Launches"}
              </h3>
            </div>
            <div className="space-y-3">
              {insight.launches.slice(0, 10).map((launch, i) => (
                <div
                  key={launch.id}
                  className="item-card"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold text-primary">#{i + 1}</span>
                        {launch.website ? (
                          <a
                            href={launch.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="item-title hover:text-primary hover:underline transition-colors"
                          >
                            {launch.name}
                          </a>
                        ) : (
                          <h4 className="item-title">{launch.name}</h4>
                        )}
                      </div>
                      <p className="item-description mt-1">{launch.tagline}</p>
                      {launch.topics && launch.topics.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {launch.topics.slice(0, 5).map((topic, j) => (
                            <span
                              key={j}
                              className="item-tag"
                            >
                              {topic}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <Badge variant="secondary" className="badge-votes">
                      🔺 {launch.votes}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Trend Summary */}
          {insight.trend_summary && (
            <div className="border-t border-white/5 pt-6">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="h-4 w-4 text-primary" />
                <h3 className="font-serif text-lg text-white tracking-wide">Trend Analysis</h3>
              </div>
              <div className="text-muted-foreground leading-relaxed">
                <ReactMarkdown
                  components={{
                    strong: ({ children }) => (
                      <strong className="text-white font-semibold font-serif">{children}</strong>
                    ),
                    p: ({ children }) => (
                      <p className="mb-2 last:mb-0 hover:text-foreground transition-colors duration-300">{children}</p>
                    ),
                  }}
                >
                  {insight.trend_summary}
                </ReactMarkdown>
              </div>
            </div>
          )}

          {/* Content Angles */}
          {insight.content_angles.length > 0 && (
            <div className="border-t border-white/5 pt-6">
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="h-4 w-4 text-primary" />
                <h3 className="font-serif text-lg text-white tracking-wide">Content Ideas</h3>
              </div>
              <ul className="space-y-3">
                {insight.content_angles.map((angle, i) => (
                  <li
                    key={i}
                    className="text-muted-foreground leading-relaxed pl-4 border-l-2 border-white/10 hover:border-primary/50 transition-colors duration-300 hover:text-foreground text-base"
                  >
                    {angle}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </ScrollArea>
    </Card>
  );
}
