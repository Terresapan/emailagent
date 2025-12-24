"use client";

import { BookOpen } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface DeepDiveCardProps {
  briefing: string | null;
}

export default function DeepDiveCard({ briefing }: DeepDiveCardProps) {
  if (!briefing) {
    return (
      <div className="journal-card flex h-full min-h-[400px] flex-col p-8">
        <div className="mb-6 flex items-center gap-3">
          <BookOpen className="h-5 w-5 text-brand-indigo" />
          <h3 className="font-serif text-xl font-bold text-white tracking-wide">Deep Dive Analysis</h3>
        </div>
        <div className="flex flex-1 items-center justify-center border-t border-dashed border-white/10">
          <p className="font-serif italic text-gray-500">No analysis available.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="journal-card flex h-full min-h-[400px] flex-col p-8 transition-all duration-300 animate-slide-up">
      {/* Header */}
      <div className="mb-8 flex items-center gap-3 border-b border-white/10 pb-4">
        <BookOpen className="h-5 w-5 text-brand-indigo" />
        <h3 className="font-serif text-xl font-bold text-white tracking-wide">Deep Dive Analysis</h3>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="prose-dark max-w-none">
          <ReactMarkdown
            components={{
              h2: ({ children }) => (
                <h2 className="mt-10 first:mt-0 mb-6 text-2xl font-serif font-bold text-white">
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3 className="mt-8 mb-3 text-lg font-bold text-brand-indigo font-sans tracking-wide uppercase">
                  {children}
                </h3>
              ),
              ul: ({ children }) => (
                <ul className="space-y-2 my-4">
                  {children}
                </ul>
              ),
              li: ({ children }) => (
                <li className="text-gray-300 leading-relaxed pl-4 border-l-2 border-brand-indigo/30">
                  {children}
                </li>
              ),
              strong: ({ children }) => (
                <strong className="text-white font-bold">{children}</strong>
              ),
              p: ({ children }) => (
                <p className="text-gray-300 leading-7 my-4 font-sans text-lg">{children}</p>
              ),
              hr: () => (
                <hr className="my-8 border-white/10" />
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