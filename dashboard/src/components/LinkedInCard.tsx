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
      <div className="glass-card flex h-full min-h-[400px] flex-col rounded-xl p-6">
        <div className="mb-4 flex items-center gap-2">
          <div className="rounded-lg bg-gradient-to-br from-purple-500 to-indigo-500 p-2">
            <Linkedin className="h-5 w-5 text-white" />
          </div>
          <h3 className="text-lg font-semibold text-white">LinkedIn Posts</h3>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <p className="text-gray-500">No LinkedIn content available</p>
        </div>
      </div>
    );
  }

  // Split content into individual posts (assuming posts are separated by "---" or numbered)
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
    <div className="glass-card flex h-full min-h-[400px] flex-col rounded-xl p-6 transition-all duration-300 animate-slide-up">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-gradient-to-br from-purple-500 to-indigo-500 p-2">
            <Linkedin className="h-5 w-5 text-white" />
          </div>
          <h3 className="text-lg font-semibold text-white">LinkedIn Posts</h3>
        </div>
        <span className="rounded-full bg-indigo-500/20 px-2 py-1 text-xs font-medium text-indigo-400">
          {posts.length} posts
        </span>
      </div>

      {/* Posts */}
      <div className="flex-1 space-y-3 overflow-y-auto">
        {posts.map((post, index) => (
          <div
            key={index}
            className="rounded-lg bg-white/5 transition-all duration-200 hover:bg-white/10"
          >
            {/* Post Header */}
            <button
              onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
              className="flex w-full items-center justify-between px-4 py-3 text-left"
            >
              <span className="text-sm font-medium text-white">
                Post {index + 1}
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
            </button>

            {/* Post Content */}
            {expandedIndex === index && (
              <div className="border-t border-white/5 px-4 py-3">
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-300">
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

/**
 * Parse LinkedIn content into individual posts.
 * Handles various formats: numbered lists, "---" separators, or "POST" headers.
 */
function parseLinkedInPosts(content: string): string[] {
  // Try splitting by common separators
  let posts: string[] = [];

  // Check for "---" separator
  if (content.includes("---")) {
    posts = content
      .split(/---+/)
      .map((p) => p.trim())
      .filter((p) => p.length > 50);
  }
  // Check for "POST 1:", "POST 2:" pattern
  else if (/POST\s*\d/i.test(content)) {
    posts = content
      .split(/POST\s*\d+[:\.]?\s*/i)
      .map((p) => p.trim())
      .filter((p) => p.length > 50);
  }
  // Check for numbered pattern "1.", "2.", etc. at start of lines
  else if (/^\d+\./m.test(content)) {
    const sections = content.split(/(?=^\d+\.)/m);
    posts = sections
      .map((p) => p.replace(/^\d+\.\s*/, "").trim())
      .filter((p) => p.length > 50);
  }

  // If no patterns found, treat the whole content as one post
  if (posts.length === 0) {
    posts = [content.trim()];
  }

  // Limit to 5 posts max
  return posts.slice(0, 5);
}
