"use client";

import { Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

interface BriefingCardProps {
  briefing: string | null;
  className?: string; // Allow parent to pass classNames (e.g. for layout/motion)
}

export default function BriefingCard({ briefing, className }: BriefingCardProps) {
  if (!briefing) {
    return (
      <Card className={cn("flex h-full min-h-[500px] flex-col bg-card/50 backdrop-blur-sm border-white/5", className)}>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Sparkles className="h-5 w-5 text-primary" />
            <CardTitle className="card-title">Daily Briefing</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="flex flex-1 items-center justify-center">
          <p className="card-empty-text">Waiting for intelligence...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("flex h-full min-h-[500px] flex-col bg-card/50 backdrop-blur-sm border-white/5 overflow-hidden", className)}>
      <CardHeader className="border-b border-white/5 pb-6">
        <div className="flex items-center gap-3">
          <Sparkles className="h-5 w-5 text-primary" />
          <CardTitle className="card-title">Daily Briefing</CardTitle>
        </div>
      </CardHeader>

      <ScrollArea className="flex-1">
        <CardContent className="pt-6 pr-6">
          <div className="prose prose-invert prose-p:font-sans prose-headings:font-serif max-w-none break-words [overflow-wrap:anywhere]">
            <ReactMarkdown
              components={{
                h2: ({ children }) => (
                  <h2 className="mt-8 first:mt-0 mb-4 text-2xl font-serif font-bold text-white border-b border-primary/20 pb-2">
                    {children}
                  </h2>
                ),
                ul: ({ children }) => (
                  <ul className="space-y-3 my-4">
                    {children}
                  </ul>
                ),
                li: ({ children }) => (
                  <li className="list-item list-item-text text-base hover:border-primary/50">
                    {children}
                  </li>
                ),
                strong: ({ children }) => (
                  <strong className="text-primary font-bold font-serif text-lg block mt-6 mb-2 first:mt-0">{children}</strong>
                ),
                p: ({ children }) => (
                  <p className="text-muted-foreground leading-relaxed my-3 font-sans transition-colors duration-300 hover:text-foreground text-lg">{children}</p>
                ),
              }}
            >
              {briefing}
            </ReactMarkdown>
          </div>
        </CardContent>
      </ScrollArea>
    </Card>
  );
}