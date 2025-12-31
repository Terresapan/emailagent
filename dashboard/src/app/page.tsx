"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, Bell, Play } from "lucide-react";
import BriefingCard from "@/components/BriefingCard";
import LinkedInCard from "@/components/LinkedInCard";
import DeepDiveCard from "@/components/DeepDiveCard";
import NewsletterItem from "@/components/NewsletterItem";
import { fetchLatestDigest, triggerProcess, Digest } from "@/lib/api";
import { MotionOrchestrator, MotionItem } from "@/components/MotionOrchestrator";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

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
  const [processing, setProcessing] = useState(false);
  const [processMessage, setProcessMessage] = useState<string | null>(null);

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
  },[]);

  useEffect(() => {
    if (lastKnownDailyId === null && lastKnownWeeklyId === null) return;
    const interval = setInterval(checkForNewContent, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [lastKnownDailyId, lastKnownWeeklyId, checkForNewContent]);

  const currentDigest = activeView === "daily" ? dailyDigest : weeklyDigest;

  return (
    <div className="min-h-screen pb-20">
      
      {/* Giant Typography Header */}
      <MotionOrchestrator className="mb-20">
        <MotionItem className="relative z-10 -ml-2 lg:-ml-4">
          <h1 className="font-serif text-giant font-bold tracking-tighter leading-[0.8] select-none text-transparent bg-clip-text bg-gradient-to-b from-foreground to-muted-foreground break-words">
            {activeView === "daily" ? "DAILY INSIGHTS" : "WEEKLY INTELLIGENCE"}
          </h1>
        </MotionItem>
        {/* Navigation - Added z-index to ensure clickability over giant type */}
        <MotionItem className="relative z-20 flex items-center justify-between border-b border-white/10 pb-6 mt-4">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveView("daily")}
              className={`text-sm font-medium tracking-[0.2em] uppercase transition-all duration-300 ${
                activeView === "daily"
                  ? "text-brand-fuchsia"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              Intelligence
            </button>
            <button
              onClick={() => setActiveView("weekly")}
              className={`text-sm font-medium tracking-[0.2em] uppercase transition-all duration-300 ${
                activeView === "weekly"
                  ? "text-brand-indigo"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              Strategy
            </button>
          </div>

          <div className="flex items-center gap-6">
             {newContentAvailable && (
               <Button
               variant="ghost"
               onClick={loadDigests}
               className="text-brand-fuchsia animate-pulse gap-2"
             >
               <Bell className="h-4 w-4" />
               New Reports
             </Button>
             )}

             {/* Run Now Button - Enhanced UX */}
             <Button
               variant="default"
               size="sm"
               disabled={processing}
               onClick={async () => {
                 setProcessing(true);
                 setProcessMessage("⏳ Processing started... (~2-3 min)");
                 try {
                   const digestType = activeView === "daily" ? "dailydigest" : "weeklydeepdives";
                   const currentId = activeView === "daily" ? lastKnownDailyId : lastKnownWeeklyId;
                   await triggerProcess(digestType);
                   
                   // Poll for new content every 15 seconds for up to 5 minutes
                   // Check created_at timestamp (not ID) because upsert updates same ID
                   let attempts = 0;
                   const maxAttempts = 20;
                   const startTime = new Date().toISOString();
                   const pollInterval = setInterval(async () => {
                     attempts++;
                     setProcessMessage(`⏳ Processing... (${attempts * 15}s)`);
                     
                     try {
                       const latest = await fetchLatestDigest(activeView);
                       // Check if created_at is newer than when we started
                       if (latest && latest.created_at > startTime) {
                         // New/updated content found!
                         clearInterval(pollInterval);
                         setProcessMessage("✅ Complete! Refreshing...");
                         await loadDigests();
                         setTimeout(() => setProcessMessage(null), 2000);
                         setProcessing(false);
                       } else if (attempts >= maxAttempts) {
                         // Timeout
                         clearInterval(pollInterval);
                         setProcessMessage("⏰ Timed out. Click refresh to check manually.");
                         setProcessing(false);
                       }
                     } catch {
                       // Silently continue polling on error
                     }
                   }, 15000);
                   
                 } catch (err) {
                   setProcessMessage(err instanceof Error ? err.message : "Failed to start");
                   setProcessing(false);
                 }
               }}
               className="gap-2 bg-gradient-to-r from-brand-fuchsia to-brand-purple hover:opacity-90 text-white border-0 shadow-lg shadow-brand-fuchsia/20"
             >
               <Play className={`h-3 w-3 ${processing ? "animate-spin" : ""}`} />
               {processing ? "Processing..." : "Run Now"}
             </Button>

             {processMessage && (
               <span className={`text-xs font-medium px-3 py-1 rounded-full ${
                 processMessage.includes("✅") ? "bg-green-500/20 text-green-400" :
                 processMessage.includes("Failed") || processMessage.includes("Timed") ? "bg-red-500/20 text-red-400" :
                 "bg-brand-fuchsia/20 text-brand-fuchsia"
               }`}>
                 {processMessage}
               </span>
             )}
             
             <div className="flex items-center gap-3 text-muted-foreground text-xs tracking-widest uppercase">
                {mounted && lastRefresh && (
                   <span>
                     {lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                   </span>
                )}
                <Button variant="ghost" size="icon" onClick={loadDigests} disabled={loading} className="hover:text-white hover:bg-white/5">
                   <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                </Button>
             </div>
          </div>
        </MotionItem>
      </MotionOrchestrator>
      
      {/* Main Content Grid */}
      <MotionOrchestrator className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">
        
        {/* Left Column (Main Story) */}
        <div className="lg:col-span-8 flex flex-col gap-8">
          
          {error && (
            <div className="p-4 border border-red-900/50 bg-red-900/10 text-red-200 text-sm font-serif">
              Error: {error}
            </div>
          )}

          {loading && !currentDigest && (
             <div className="space-y-4 animate-pulse">
                <div className="h-96 bg-white/5 rounded-lg border border-white/5" />
             </div>
          )}

          {!loading && !currentDigest && !error && (
            <div className="py-32 text-center border border-dashed border-white/10 rounded-lg">
              <p className="font-serif text-3xl text-muted-foreground italic">
                "Silence is also information."
              </p>
            </div>
          )}

          {currentDigest && (
            <>
              {/* Primary Article */}
              <MotionItem className="h-full">
                 {activeView === "daily" ? (
                    <BriefingCard briefing={currentDigest.briefing} />
                 ) : (
                    <DeepDiveCard briefing={currentDigest.briefing} />
                 )}
              </MotionItem>

              {/* Source Material (Digests) */}
              {currentDigest.structured_digests && currentDigest.structured_digests.length > 0 && (
                <MotionItem className="pt-12">
                  <div className="flex items-center gap-4 mb-8">
                    <Separator className="flex-1 bg-white/10" />
                    <h3 className="font-serif text-2xl text-white italic">Source Intercepts</h3>
                    <Separator className="flex-1 bg-white/10" />
                  </div>
                  <div className="grid gap-6">
                    {currentDigest.structured_digests.map((emailDigest, index) => (
                      <NewsletterItem key={index} digest={emailDigest} />
                    ))}
                  </div>
                </MotionItem>
              )}
            </>
          )}
        </div>

        {/* Right Column (Sidebar) */}
        <div className="lg:col-span-4 flex flex-col gap-8 h-fit lg:sticky lg:top-8">
           
           {/* Metadata / Stats */}
           {currentDigest && (
             <MotionItem>
               <div className="p-6 bg-card/30 backdrop-blur-md border border-white/5 rounded-lg">
                  <h4 className="font-sans text-xs font-bold uppercase tracking-widest text-muted-foreground mb-6">
                    Metadata
                  </h4>
                  
                  <div className="space-y-6">
                    <div className="flex items-start justify-between pb-4 border-b border-white/5">
                       <span className="text-sm text-gray-400">Date</span>
                       <span className="font-serif text-white">{currentDigest.date}</span>
                    </div>

                    <div className="flex items-start justify-between pb-4 border-b border-white/5">
                       <span className="text-sm text-gray-400">Sources</span>
                       <span className="font-serif text-white">{currentDigest.emails_processed?.length || 0}</span>
                    </div>

                    <div className="flex items-start justify-between">
                       <span className="text-sm text-gray-400">Est. Read</span>
                       <span className="font-serif text-white">~5 min</span>
                    </div>
                  </div>
               </div>
             </MotionItem>
           )}

           {/* LinkedIn (Only on Daily) */}
           {currentDigest && activeView === "daily" && (
             <MotionItem>
                <div className="relative group">
                   <div className="absolute -inset-0.5 bg-gradient-to-r from-brand-fuchsia to-brand-purple opacity-20 blur transition group-hover:opacity-30 rounded-lg" />
                   <div className="relative">
                     <LinkedInCard content={currentDigest.linkedin_content} />
                   </div>
                </div>
             </MotionItem>
           )}

           {/* Quote */}
           <MotionItem>
             <div className="p-6 border-l-2 border-brand-purple/50 pl-6 italic font-serif text-muted-foreground text-lg">
                "The goal is not to read more, but to understand better."
             </div>
           </MotionItem>

        </div>
      </MotionOrchestrator>
    </div>
  );
}
