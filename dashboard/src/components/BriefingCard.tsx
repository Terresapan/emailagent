"use client";

import { Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface BriefingCardProps {
  briefing: string | null;
}

export default function BriefingCard({ briefing }: BriefingCardProps) {
  if (!briefing) {
    return (
      <div className="glass-card flex h-full min-h-[400px] flex-col rounded-xl p-6">
        <div className="mb-4 flex items-center gap-2">
          <div className="rounded-lg bg-gradient-to-br from-fuchsia-500 to-purple-500 p-2">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <h3 className="text-lg font-semibold text-white">AI Briefing</h3>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <p className="text-gray-500">No briefing available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card flex h-full min-h-[400px] flex-col rounded-xl p-6 transition-all duration-300 animate-slide-up">
      {/* Header */}
      <div className="mb-4 flex items-center gap-2">
        <div className="rounded-lg bg-gradient-to-br from-fuchsia-500 to-purple-500 p-2">
          <Sparkles className="h-5 w-5 text-white" />
        </div>
        <h3 className="text-lg font-semibold text-white">AI Briefing</h3>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="prose-dark">
          <ReactMarkdown
            components={{
              h2: ({ children }) => (
                <h2 className="mt-6 first:mt-0 mb-3 text-lg font-semibold text-white border-b border-white/10 pb-2">
                  {children}
                </h2>
              ),
              ul: ({ children }) => (
                <ul className="list-disc pl-5 space-y-1 text-gray-300">
                  {children}
                </ul>
              ),
              li: ({ children }) => (
                <li className="text-gray-300 leading-relaxed">{children}</li>
              ),
              strong: ({ children }) => (
                <strong className="text-white font-semibold">{children}</strong>
              ),
              p: ({ children }) => (
                <p className="text-gray-300 leading-relaxed my-2">{children}</p>
              ),
            }}
          >
            {briefing}
          </ReactMarkdown>
        </div>
      </div>

      {/* Footer gradient fade */}
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-12 rounded-b-xl bg-gradient-to-t from-gray-950/80 to-transparent" />
    </div>
  );
}
