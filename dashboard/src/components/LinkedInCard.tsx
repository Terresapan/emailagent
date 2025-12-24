"use client";

import { useState } from "react";
import { Linkedin, Copy, Check, ChevronDown, ChevronUp } from "lucide-react";

interface LinkedInCardProps {
  content: string | null;
}

export default function LinkedInCard({ content }: LinkedInCardProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  if (!content) {
    return (
      <div className="journal-card flex flex-col p-6 rounded-none border-l-4 border-l-brand-indigo/20">
        <div className="mb-4 flex items-center gap-2">
          <Linkedin className="h-4 w-4 text-brand-indigo" />
          <h3 className="font-serif font-bold text-white">LinkedIn Drafts</h3>
        </div>
        <p className="text-sm text-gray-500 italic">No drafts generated.</p>
      </div>
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
    <div className="journal-card flex flex-col p-6 transition-all duration-300 animate-slide-up">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between border-b border-white/5 pb-4">
        <div className="flex items-center gap-2">
          <Linkedin className="h-4 w-4 text-brand-indigo" />
          <h3 className="font-serif font-bold text-white">LinkedIn Drafts</h3>
        </div>
        <span className="font-mono text-xs text-brand-indigo">
          {posts.length} READY
        </span>
      </div>

      {/* Posts */}
      <div className="space-y-4">
        {posts.map((post, index) => (
          <div
            key={index}
            className={`group rounded-lg border transition-all duration-200 ${
               expandedIndex === index 
               ? "border-brand-indigo/30 bg-brand-indigo/5" 
               : "border-white/5 bg-white/5 hover:border-white/10"
            }`}
          >
            {/* Post Header */}
            <div
              onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
              className="flex w-full cursor-pointer items-center justify-between px-4 py-3 text-left"
              role="button"
              tabIndex={0}
            >
              <span className={`text-sm font-medium ${expandedIndex === index ? "text-white" : "text-gray-400 group-hover:text-gray-300"}`}>
                Draft #{index + 1}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCopy(post, index);
                  }}
                  className="rounded-md p-1.5 text-gray-400 transition-colors hover:bg-white/10 hover:text-white"
                  title="Copy to clipboard"
                >
                  {copiedIndex === index ? (
                    <Check className="h-4 w-4 text-green-400" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </button>
                {expandedIndex === index ? (
                  <ChevronUp className="h-4 w-4 text-gray-400" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-400" />
                )}
              </div>
            </div>

            {/* Post Content */}
            {expandedIndex === index && (
              <div className="border-t border-brand-indigo/10 px-4 py-4">
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-300 font-sans">
                  {post}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
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