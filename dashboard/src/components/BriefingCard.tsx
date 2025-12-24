"use client";

import { Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface BriefingCardProps {
  briefing: string | null;
}

export default function BriefingCard({ briefing }: BriefingCardProps) {
  if (!briefing) {
    return (
      <div className="journal-card flex h-full min-h-[400px] flex-col p-8">
        <div className="mb-6 flex items-center gap-3">
          <Sparkles className="h-5 w-5 text-brand-fuchsia" />
          <h3 className="font-serif text-xl font-bold text-white tracking-wide">Daily Briefing</h3>
        </div>
        <div className="flex flex-1 items-center justify-center border-t border-dashed border-white/10">
          <p className="font-serif italic text-gray-500">Waiting for intelligence...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="journal-card flex h-full min-h-[400px] flex-col p-8 transition-all duration-300 animate-slide-up">
      {/* Header */}
      <div className="mb-8 flex items-center gap-3 border-b border-white/10 pb-4">
        <Sparkles className="h-5 w-5 text-brand-fuchsia" />
        <h3 className="font-serif text-xl font-bold text-white tracking-wide">Daily Briefing</h3>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="prose-dark max-w-none">
          <ReactMarkdown
            components={{
              h2: ({ children }) => (
                <h2 className="mt-8 first:mt-0 mb-4 text-lg font-serif font-bold text-white border-b border-brand-purple/20 pb-2">
                  {children}
                </h2>
              ),
              ul: ({ children }) => (
                <ul className="space-y-2 my-4">
                  {children}
                </ul>
              ),
              li: ({ children }) => (
                <li className="text-gray-300 leading-relaxed pl-0 before:hidden relative pl-4 border-l-2 border-white/10 hover:border-brand-fuchsia/50 transition-colors">
                  {children}
                </li>
              ),
              strong: ({ children }) => (
                <strong className="text-white font-semibold font-serif">{children}</strong>
              ),
              p: ({ children }) => (
                <p className="text-gray-300 leading-relaxed my-3 font-sans">{children}</p>
              ),
            }}
          >
            {briefing}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}