"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, Mail, Linkedin, Calendar, Clock, Bell, BookOpen, ArrowRight } from "lucide-react";
import BriefingCard from "@/components/BriefingCard";
import LinkedInCard from "@/components/LinkedInCard";
import DeepDiveCard from "@/components/DeepDiveCard";
import NewsletterItem from "@/components/NewsletterItem";
import { fetchLatestDigest, Digest } from "@/lib/api";

type ViewType = "daily" | "weekly";

export default function Home() {
  const [activeView, setActiveView] = useState<ViewType>("daily");
  const [dailyDigest, setDailyDigest] = useState<Digest | null>(null);
  const [weeklyDigest, setWeeklyDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [newContentAvailable, setNewContentAvailable] = useState(false);
  const [lastKnownDailyId, setLastKnownDailyId] = useState<number | null>(null);
  const [lastKnownWeeklyId, setLastKnownWeeklyId] = useState<number | null>(null);
  const [mounted, setMounted] = useState(false);

  const loadDigests = async () => {
    setLoading(true);
    setError(null);
    setNewContentAvailable(false);
    try {
      const [daily, weekly] = await Promise.all([
        fetchLatestDigest("daily"),
        fetchLatestDigest("weekly"),
      ]);
      setDailyDigest(daily);
      setWeeklyDigest(weekly);
      if (daily) setLastKnownDailyId(daily.id);
      if (weekly) setLastKnownWeeklyId(weekly.id);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load digest");
    } finally {
      setLoading(false);
    }
  };

  const checkForNewContent = useCallback(async () => {
    try {
      const [daily, weekly] = await Promise.all([
        fetchLatestDigest("daily"),
        fetchLatestDigest("weekly"),
      ]);
      if (
        (daily && lastKnownDailyId !== null && daily.id !== lastKnownDailyId) ||
        (weekly && lastKnownWeeklyId !== null && weekly.id !== lastKnownWeeklyId)
      ) {
        setNewContentAvailable(true);
      }
    } catch {
      // Silently fail on background check
    }
  }, [lastKnownDailyId, lastKnownWeeklyId]);

  useEffect(() => {
    setMounted(true);
    loadDigests();
  }, []);

  useEffect(() => {
    if (lastKnownDailyId === null && lastKnownWeeklyId === null) return;
    const interval = setInterval(checkForNewContent, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [lastKnownDailyId, lastKnownWeeklyId, checkForNewContent]);

  const currentDigest = activeView === "daily" ? dailyDigest : weeklyDigest;

  return (
    <div className="animate-fade-in min-h-screen">
      
      {/* Editorial Navigation / View Toggle */}
      <div className="flex flex-col md:flex-row md:items-end justify-between border-b border-white/5 pb-6 mb-12">
        <div className="space-y-4">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveView("daily")}
              className={`pb-1 text-sm font-medium tracking-widest uppercase transition-all ${
                activeView === "daily"
                  ? "text-brand-fuchsia border-b border-brand-fuchsia"
                  : "text-gray-500 hover:text-white"
              }`}
            >
              The Daily Briefing
            </button>
            <button
              onClick={() => setActiveView("weekly")}
              className={`pb-1 text-sm font-medium tracking-widest uppercase transition-all ${
                activeView === "weekly"
                  ? "text-brand-indigo border-b border-brand-indigo"
                  : "text-gray-500 hover:text-white"
              }`}
            >
              Weekly Deep Dive
            </button>
          </div>
          <h2 className="font-serif text-4xl md:text-5xl font-bold text-white tracking-tight">
            {activeView === "daily" ? "Today's Insights" : "Strategic Analysis"}
          </h2>
        </div>

        <div className="flex items-center gap-6 mt-6 md:mt-0">
          {newContentAvailable && (
             <button
             onClick={loadDigests}
             className="flex items-center gap-2 text-brand-purple text-sm font-medium animate-pulse"
           >
             <Bell className="h-4 w-4" />
             <span>New Intelligence Ready</span>
           </button>
          )}
          
          <div className="flex items-center gap-3 text-gray-500 text-xs tracking-wider uppercase">
             {mounted && lastRefresh && (
                <span>
                  Last Sync: {lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
             )}
             <button onClick={loadDigests} disabled={loading} className="hover:text-white transition-colors">
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
             </button>
          </div>
        </div>
      </div>

      {/* Main Content Grid - Newspaper Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        
        {/* Left Column (Main Story) - Spans 8 cols */}
        <div className="lg:col-span-8 space-y-12">
          
          {error && (
            <div className="p-4 border border-red-900/50 bg-red-900/10 text-red-200 text-sm font-serif">
              Error: {error}
            </div>
          )}

          {loading && !currentDigest && (
             <div className="space-y-4 animate-pulse">
                <div className="h-8 w-3/4 bg-white/5 rounded" />
                <div className="h-96 bg-white/5 rounded" />
             </div>
          )}

          {!loading && !currentDigest && !error && (
            <div className="py-20 text-center border-y border-white/5">
              <p className="font-serif text-xl text-gray-400 italic">
                "Silence is also information."
              </p>
              <p className="mt-2 text-sm text-gray-600 uppercase tracking-widest">
                No digests available for this period.
              </p>
            </div>
          )}

          {currentDigest && (
            <>
              {/* Primary Article */}
              <section>
                 {activeView === "daily" ? (
                    <BriefingCard briefing={currentDigest.briefing} />
                 ) : (
                    <DeepDiveCard briefing={currentDigest.briefing} />
                 )}
              </section>

              {/* Secondary Articles (Digests) */}
              {currentDigest.structured_digests && currentDigest.structured_digests.length > 0 && (
                <section className="border-t border-white/5 pt-12">
                  <h3 className="font-serif text-2xl text-white mb-8">Source Material</h3>
                  <div className="grid gap-6">
                    {currentDigest.structured_digests.map((emailDigest, index) => (
                      <NewsletterItem key={index} digest={emailDigest} />
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
        </div>

        {/* Right Column (Sidebar) - Spans 4 cols */}
        <div className="lg:col-span-4 space-y-8">
           
           {/* Sidebar: Metadata / Stats */}
           {currentDigest && (
             <div className="p-6 bg-editorial-card border border-white/5">
                <h4 className="font-sans text-xs font-bold uppercase tracking-widest text-gray-500 mb-6">
                  At a Glance
                </h4>
                
                <div className="space-y-6">
                  <div className="flex items-start justify-between pb-4 border-b border-white/5">
                     <div className="flex items-center gap-3">
                        <Calendar className="h-4 w-4 text-brand-fuchsia" />
                        <span className="text-sm text-gray-300">Edition Date</span>
                     </div>
                     <span className="font-serif text-white">{currentDigest.date}</span>
                  </div>

                  <div className="flex items-start justify-between pb-4 border-b border-white/5">
                     <div className="flex items-center gap-3">
                        <Mail className="h-4 w-4 text-brand-purple" />
                        <span className="text-sm text-gray-300">Sources Analyzed</span>
                     </div>
                     <span className="font-serif text-white">{currentDigest.emails_processed?.length || 0}</span>
                  </div>

                  <div className="flex items-start justify-between">
                     <div className="flex items-center gap-3">
                        <Clock className="h-4 w-4 text-brand-indigo" />
                        <span className="text-sm text-gray-300">Reading Time</span>
                     </div>
                     <span className="font-serif text-white">~5 min</span>
                  </div>
                </div>
             </div>
           )}

           {/* Sidebar: LinkedIn (Only on Daily) */}
           {currentDigest && activeView === "daily" && (
             <div className="group relative">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-brand-fuchsia to-brand-purple opacity-20 blur transition group-hover:opacity-40" />
                <div className="relative">
                  <LinkedInCard content={currentDigest.linkedin_content} />
                </div>
             </div>
           )}

           {/* Sidebar: Quote or Filler */}
           <div className="p-6 border-l-2 border-brand-purple/50 pl-6 italic font-serif text-gray-400">
              "The goal is not to read more, but to understand better."
           </div>

        </div>
      </div>
    </div>
  );
}
