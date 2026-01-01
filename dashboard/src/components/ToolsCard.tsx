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
            <Rocket className="h-5 w-5 text-brand-orange" />
            <CardTitle className="font-serif text-2xl tracking-wide text-white">AI Tools</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="flex flex-1 items-center justify-center">
          <p className="font-serif italic text-muted-foreground">Waiting for discoveries...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn(
      "flex h-full min-h-[500px] flex-col bg-card/50 backdrop-blur-sm overflow-hidden transition-colors duration-500",
      isWeekly ? "border-brand-purple/30" : "border-white/5",
      className
    )}>
      <CardHeader className="border-b border-white/5 pb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Rocket className={cn("h-5 w-5", isWeekly ? "text-brand-purple" : "text-brand-orange")} />
            <CardTitle className="font-serif text-2xl tracking-wide text-white">
              {isWeekly ? "Weekly AI Tool Best" : "AI Tools Discovery"}
            </CardTitle>
          </div>
        </div>
      </CardHeader>
      
      <ScrollArea className="flex-1">
        <CardContent className="pt-6 space-y-8">
          {/* Top Launches */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className={cn("h-4 w-4", isWeekly ? "text-brand-indigo" : "text-brand-fuchsia")} />
              <h3 className={cn("font-serif text-lg tracking-wide", isWeekly ? "text-brand-purple" : "text-white")}>
                {isWeekly ? "Best of the Week" : "Top AI Launches"}
              </h3>
            </div>
            <div className="space-y-3">
              {insight.launches.slice(0, 5).map((launch, i) => (
                <div 
                  key={launch.id} 
                  className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-white/5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold text-brand-fuchsia">#{i + 1}</span>
                        {launch.website ? (
                          <a 
                            href={launch.website} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="font-semibold text-white hover:text-brand-orange hover:underline transition-colors"
                          >
                            {launch.name}
                          </a>
                        ) : (
                          <h4 className="font-semibold text-white">{launch.name}</h4>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{launch.tagline}</p>
                    </div>
                    <Badge variant="secondary" className="shrink-0 bg-white/10 text-white hover:bg-white/20">
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
                <TrendingUp className="h-4 w-4 text-brand-purple" />
                <h3 className="font-serif text-lg text-white tracking-wide">Trend Analysis</h3>
              </div>
              <div className="text-muted-foreground leading-relaxed">
                <ReactMarkdown
                  components={{
                    strong: ({ children }) => (
                      <strong className="text-white font-semibold font-serif">{children}</strong>
                    ),
                    p: ({ children }) => (
                      <p className="mb-2 last:mb-0 hover:text-gray-200 transition-colors duration-300">{children}</p>
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
                <Lightbulb className="h-4 w-4 text-yellow-500" />
                <h3 className="font-serif text-lg text-white tracking-wide">Content Ideas</h3>
              </div>
              <ul className="space-y-3">
                {insight.content_angles.map((angle, i) => (
                  <li 
                    key={i} 
                    className="text-muted-foreground leading-relaxed pl-4 border-l-2 border-white/10 hover:border-brand-fuchsia/50 transition-colors duration-300 hover:text-gray-200 text-base"
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
