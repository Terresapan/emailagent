"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Mail, Newspaper, Wrench, Lightbulb, GraduationCap } from "lucide-react";
import { EmailDigest } from "@/lib/api";

interface NewsletterItemProps {
  digest: EmailDigest;
}

export default function NewsletterItem({ digest }: NewsletterItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const { summary } = digest;
  const hasDetails = 
    (summary.industry_news && summary.industry_news.length > 0) ||
    (summary.new_tools && summary.new_tools.length > 0) ||
    (summary.insights && summary.insights.length > 0) ||
    summary.core_thesis;

  return (
    <div 
      className={`group rounded-xl border transition-all duration-300 ${
        isExpanded 
          ? "border-purple-500/50 bg-white/10 ring-1 ring-purple-500/20" 
          : "border-white/5 bg-white/5 hover:border-white/10 hover:bg-white/8"
      }`}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between p-4 text-left"
      >
        <div className="flex items-center gap-4">
          <div className={`rounded-lg p-2 transition-colors ${
            isExpanded ? "bg-purple-500/20 text-purple-400" : "bg-white/5 text-gray-400 group-hover:text-gray-300"
          }`}>
            <Newspaper className="h-5 w-5" />
          </div>
          <div>
            <h4 className="font-medium text-white line-clamp-1">{digest.subject}</h4>
            <p className="text-xs text-gray-400">{digest.sender}</p>
          </div>
        </div>
        {hasDetails && (
          <div className="text-gray-500">
            {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
          </div>
        )}
      </button>

      {isExpanded && hasDetails && (
        <div className="animate-slide-down border-t border-white/5 p-4 pt-2">
          <div className="space-y-4">
            {/* Industry News */}
            {summary.industry_news && summary.industry_news.length > 0 && (
              <section>
                <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-fuchsia-400/80">
                  <Newspaper className="h-3 w-3" />
                  Industry News
                </div>
                <ul className="space-y-1.5">
                  {summary.industry_news.map((item, i) => (
                    <li key={i} className="text-sm text-gray-300 leading-relaxed pl-4 relative before:content-['•'] before:absolute before:left-0 before:text-fuchsia-500/50">
                      {item}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* New Tools */}
            {summary.new_tools && summary.new_tools.length > 0 && (
              <section>
                <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-purple-400/80">
                  <Lightbulb className="h-3 w-3" />
                  New Tools
                </div>
                <ul className="space-y-1.5">
                  {summary.new_tools.map((item, i) => (
                    <li key={i} className="text-sm text-gray-300 leading-relaxed pl-4 relative before:content-['•'] before:absolute before:left-0 before:text-purple-500/50">
                      {item}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* Insights */}
            {summary.insights && summary.insights.length > 0 && (
              <section>
                <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-400/80">
                  <GraduationCap className="h-3 w-3" />
                  Strategic Insights
                </div>
                <ul className="space-y-1.5">
                  {summary.insights.map((item, i) => (
                    <li key={i} className="text-sm text-gray-300 leading-relaxed pl-4 relative before:content-['•'] before:absolute before:left-0 before:text-indigo-500/50">
                      {item}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* Weekly Deep Dive Specifics */}
            {summary.core_thesis && (
              <div className="rounded-lg bg-indigo-500/10 p-3 italic text-indigo-200 text-sm">
                "{summary.core_thesis}"
              </div>
            )}
            
            {summary.key_concepts && summary.key_concepts.length > 0 && (
              <section>
                <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-indigo-300/80">Key Concepts</div>
                <div className="flex flex-wrap gap-2">
                  {summary.key_concepts.map((concept, i) => (
                    <span key={i} className="rounded-full bg-indigo-500/20 px-2 py-1 text-[10px] text-indigo-300">
                      {concept}
                    </span>
                  ))}
                </div>
              </section>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
