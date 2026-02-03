import { BookOpen } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

interface DeepDiveCardProps {
  briefing: string | null;
  className?: string;
}

export default function DeepDiveCard({ briefing, className }: DeepDiveCardProps) {
  if (!briefing) {
    return (
      <Card className={cn("flex h-full min-h-[500px] flex-col bg-card/50 backdrop-blur-sm border-white/5", className)}>
        <CardHeader>
          <div className="flex items-center gap-3">
            <BookOpen className="h-5 w-5 text-primary" />
            <CardTitle className="card-title">Deep Dive Analysis</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="flex flex-1 items-center justify-center">
          <p className="card-empty-text">No analysis available.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("flex h-full min-h-[500px] flex-col bg-card/50 backdrop-blur-sm border-white/5 overflow-hidden", className)}>
      <CardHeader className="border-b border-white/5 pb-6">
        <div className="flex items-center gap-3">
          <BookOpen className="h-5 w-5 text-primary" />
          <CardTitle className="card-title">Deep Dive Analysis</CardTitle>
        </div>
      </CardHeader>

      <ScrollArea className="flex-1">
        <CardContent className="pt-6 pr-6">
          <div className="prose prose-invert prose-p:font-sans prose-headings:font-serif max-w-none break-words [overflow-wrap:anywhere]">
            <ReactMarkdown
              components={{
                h2: ({ children }) => (
                  <h2 className="mt-10 first:mt-0 mb-6 text-2xl font-serif font-bold text-white">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="mt-8 mb-3 text-lg font-bold text-primary font-sans tracking-wide uppercase">
                    {children}
                  </h3>
                ),
                ul: ({ children }) => (
                  <ul className="space-y-3 my-4">
                    {children}
                  </ul>
                ),
                li: ({ children }) => (
                  <li className="text-muted-foreground leading-relaxed pl-4 border-l-2 border-white/10 transition-colors duration-300 hover:text-foreground hover:border-primary text-base">
                    {children}
                  </li>
                ),
                strong: ({ children }) => (
                  <strong className="text-primary font-bold font-serif text-lg block mt-6 mb-2 first:mt-0">{children}</strong>
                ),
                p: ({ children }) => (
                  <p className="text-muted-foreground leading-7 my-4 font-sans text-lg transition-colors duration-300 hover:text-foreground">{children}</p>
                ),
                hr: () => (
                  <hr className="my-8 border-white/10" />
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