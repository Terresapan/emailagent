"use client";

import { useState } from "react";
import { Linkedin, Copy, Check, ChevronDown, ChevronUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface LinkedInCardProps {
  content: string | null;
  className?: string;
}

export default function LinkedInCard({ content, className }: LinkedInCardProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  if (!content) {
    return (
      <Card className={cn("bg-card/50 backdrop-blur-sm border-white/5", className)}>
        <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
          <Linkedin className="h-4 w-4 text-accent" />
          <CardTitle className="card-title">LinkedIn Drafts</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="card-empty-text text-sm">No drafts generated.</p>
        </CardContent>
      </Card>
    );
  }

  const posts = parseLinkedInPosts(content);

  const handleCopy = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <Card className={cn("bg-card/50 backdrop-blur-sm border-white/5 overflow-hidden transition-all duration-300", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 border-b border-white/5 pb-4">
        <div className="flex items-center gap-2">
          <Linkedin className="h-4 w-4 text-accent" />
          {/* Increased tracking as requested */}
          <CardTitle className="card-title">LinkedIn Drafts</CardTitle>
        </div>
        <span className="font-mono text-xs text-accent font-medium bg-accent/10 px-2 py-1 rounded">
          {posts.length > 0 ? posts.length - 1 : 0} DRAFTS
        </span>
      </CardHeader>

      <CardContent className="space-y-4 pt-6">
        {posts.map((post, index) => {
          // Logic: First item is "Topics", rest are "Drafts"
          const isTopics = index === 0;
          const label = isTopics ? "LinkedIn Topics" : `Draft #${index}`;
          
          return (
          <div
            key={index}
            className={cn(
              "group rounded-lg border transition-all duration-300",
              expandedIndex === index 
               ? "border-accent/30 bg-accent/5" 
               : "border-white/5 bg-white/5 hover:border-white/10"
            )}
          >
            {/* Post Header */}
            <div
              onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
              className="flex w-full cursor-pointer items-center justify-between px-4 py-3 text-left"
              role="button"
              tabIndex={0}
            >
              <span className={cn(
                "text-sm font-medium transition-colors uppercase tracking-wider", // Added uppercase and tracking
                expandedIndex === index ? "text-white" : "text-muted-foreground group-hover:text-foreground",
                isTopics && "text-accent" // Highlight Topics
              )}>
                {label}
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-white hover:bg-white/10"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCopy(post, index);
                  }}
                  title="Copy to clipboard"
                >
                  {copiedIndex === index ? (
                    <Check className="h-4 w-4 text-green-400" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
                {expandedIndex === index ? (
                  <ChevronUp className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
            </div>

            {/* Post Content */}
            {expandedIndex === index && (
              <div className="border-t border-accent/10 px-4 py-4 animate-in slide-in-from-top-2 duration-200">
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground font-sans">
                  {post}
                </p>
              </div>
            )}
          </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

function parseLinkedInPosts(content: string): string[] {
  let posts: string[] = [];
  if (content.includes("---")) {
    posts = content.split(/---+/).map((p) => p.trim()).filter((p) => p.length > 50);
  } else if (/POST\s*\d/i.test(content)) {
    posts = content.split(/POST\s*\d+[:\.]?\s*/i).map((p) => p.trim()).filter((p) => p.length > 50);
  } else if (/^\d+\./m.test(content)) {
    const sections = content.split(/(?=^\d+\.)/m);
    posts = sections.map((p) => p.replace(/^\d+\.\s*/, "").trim()).filter((p) => p.length > 50);
  }
  if (posts.length === 0) {
    posts = [content.trim()];
  }
  const introPatterns = [
    /here are the.*posts/i,
    /here's the.*content/i,
    /reviewed and.*tightened/i,
    /optimized for/i,
    /each post has/i,
    /content pack/i,
    /linkedin posts.*below/i,
  ];
  posts = posts.filter((post) => {
    const isIntro = introPatterns.some((pattern) => pattern.test(post));
    const isTooShort = post.length < 100;
    return !isIntro && !isTooShort;
  });
  return posts.slice(0, 5);
}