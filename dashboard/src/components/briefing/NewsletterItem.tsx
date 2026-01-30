"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Mail, Newspaper, Lightbulb, GraduationCap } from "lucide-react";
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
          ? "border-primary/50 bg-editorial-card ring-1 ring-primary/20" 
          : "border-white/5 bg-editorial-card/50 hover:border-white/10 hover:bg-editorial-card"
      }`}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between p-6 text-left"
      >
        <div className="flex items-center gap-4">
          <div className={`rounded-lg p-2 transition-colors ${
            isExpanded ? "bg-primary/20 text-primary" : "bg-white/5 text-gray-400 group-hover:text-gray-300"
          }`}>
            <Newspaper className="h-5 w-5" />
          </div>
          <div>
            <h4 className="font-serif text-lg font-semibold text-white line-clamp-1 group-hover:text-primary transition-colors">
              {digest.subject}
            </h4>
            <div className="mt-1 flex items-center gap-2 text-xs uppercase tracking-wider text-gray-500">
              <span className="font-medium text-gray-400">{digest.sender}</span>
            </div>
          </div>
        </div>
        {hasDetails && (
          <div className="text-gray-500 transition-transform duration-300">
            {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
          </div>
        )}
      </button>

      {isExpanded && hasDetails && (
        <div className="animate-slide-down border-t border-white/5 p-6 pt-4">
          <div className="space-y-6">
            
            {/* Core Thesis (Weekly Only usually) */}
            {summary.core_thesis && (
              <div className="rounded-lg bg-primary/10 border-l-2 border-primary p-4 italic text-white text-lg tracking-wide font-serif">
                "{summary.core_thesis}"
              </div>
            )}

            {/* Industry News */}
            {summary.industry_news && summary.industry_news.length > 0 && (
              <section>
                <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-primary">
                  <Newspaper className="h-3 w-3" />
                  Industry News
                </div>
                <ul className="space-y-2">
                  {summary.industry_news.map((item, i) => (
                    <li key={i} className="text-base text-gray-300 leading-relaxed pl-4 relative border-l border-white/10 hover:border-primary/50 transition-colors">
                      {item}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* New Tools */}
            {summary.new_tools && summary.new_tools.length > 0 && (
              <section>
                <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-primary">
                  <Lightbulb className="h-3 w-3" />
                  New Tools
                </div>
                <ul className="space-y-2">
                  {summary.new_tools.map((item, i) => (
                    <li key={i} className="text-base text-gray-300 leading-relaxed pl-4 relative border-l border-white/10 hover:border-primary/50 transition-colors">
                      {item}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* Insights */}
            {summary.insights && summary.insights.length > 0 && (
              <section>
                <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-primary">
                  <GraduationCap className="h-3 w-3" />
                  Strategic Insights
                </div>
                <ul className="space-y-2">
                  {summary.insights.map((item, i) => (
                    <li key={i} className="text-base text-gray-300 leading-relaxed pl-4 relative border-l border-white/10 hover:border-primary/50 transition-colors">
                      {item}
                    </li>
                  ))}
                </ul>
              </section>
            )}
            
            {/* Key Concepts Tags */}
            {summary.key_concepts && summary.key_concepts.length > 0 && (
              <section className="pt-2">
                <div className="flex flex-wrap gap-2">
                  {summary.key_concepts.map((concept, i) => (
                    <span key={i} className="item-tag-neutral">
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