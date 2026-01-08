"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, Bell, Play } from "lucide-react";
import BriefingCard from "@/components/BriefingCard";
import LinkedInCard from "@/components/LinkedInCard";
import DeepDiveCard from "@/components/DeepDiveCard";
import ToolsCard from "@/components/ToolsCard";
import HackerNewsCard from "@/components/HackerNewsCard";
import YouTubeCard from "@/components/YouTubeCard";
import NewsletterItem from "@/components/NewsletterItem";
import { fetchLatestDigest, triggerProcess, getProcessStatus, fetchToolsInsight, fetchHackerNewsInsight, fetchYouTubeInsight, Digest, ToolsInsight, HackerNewsInsight, YouTubeInsight } from "@/lib/api";
import { MotionOrchestrator, MotionItem } from "@/components/MotionOrchestrator";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

type ViewType = "daily" | "producthunt" | "hackernews" | "youtube" | "weekly";

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
  const [toolsInsight, setToolsInsight] = useState<ToolsInsight | null>(null);
  const [hackerNewsInsight, setHackerNewsInsight] = useState<HackerNewsInsight | null>(null);
  const [youtubeInsight, setYoutubeInsight] = useState<YouTubeInsight | null>(null);
  const [mounted, setMounted] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [processingType, setProcessingType] = useState<ViewType | null>(null);
  const [processMessage, setProcessMessage] = useState<string | null>(null);

  const loadDigests = async () => {
    setLoading(true);
    setError(null);
    setNewContentAvailable(false);
    try {
      const [daily, weekly, tools, hn, yt] = await Promise.all([
        fetchLatestDigest("daily"),
        fetchLatestDigest("weekly"),
        fetchToolsInsight(),
        fetchHackerNewsInsight(),
        fetchYouTubeInsight(),
      ]);
      setDailyDigest(daily);
      setWeeklyDigest(weekly);
      setToolsInsight(tools);
      setHackerNewsInsight(hn);
      setYoutubeInsight(yt);
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
    <div className="min-h-screen pb-20">

      {/* Giant Typography Header */}
      <MotionOrchestrator className="mb-20">
        <MotionItem className="relative z-10 -ml-2 lg:-ml-4">
          <h1 className="font-serif text-giant font-bold tracking-tighter leading-[0.8] select-none text-transparent bg-clip-text bg-gradient-to-b from-foreground to-muted-foreground break-words">
            {activeView === "daily" ? "DAILY INSIGHTS" :
              activeView === "producthunt" ? "PRODUCT HUNT" :
                activeView === "hackernews" ? (<>HACKER<br className="sm:hidden" /> NEWS</>) :
                  activeView === "youtube" ? (<>YOUTUBE<br className="sm:hidden" /> CHANNELS</>) :
                    "WEEKLY INTELLIGENCE"}
          </h1>
        </MotionItem>
        {/* Navigation - Added z-index to ensure clickability over giant type */}
        <MotionItem className="relative z-20 flex items-center justify-between border-b border-white/10 pb-6 mt-4">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveView("daily")}
              className={`text-sm font-medium tracking-[0.2em] uppercase transition-all duration-300 ${activeView === "daily"
                ? "text-accent"
                : "text-muted-foreground hover:text-white"
                }`}
            >
              Intelligence
            </button>
            <button
              onClick={() => setActiveView("producthunt")}
              className={`text-sm font-medium tracking-[0.2em] uppercase transition-all duration-300 ${activeView === "producthunt"
                ? "text-accent"
                : "text-muted-foreground hover:text-white"
                }`}
            >
              Product Hunt
            </button>
            <button
              onClick={() => setActiveView("hackernews")}
              className={`text-sm font-medium tracking-[0.2em] uppercase transition-all duration-300 ${activeView === "hackernews"
                ? "text-accent"
                : "text-muted-foreground hover:text-white"
                }`}
            >
              HackerNews
            </button>
            <button
              onClick={() => setActiveView("youtube")}
              className={`text-sm font-medium tracking-[0.2em] uppercase transition-all duration-300 ${activeView === "youtube"
                ? "text-accent"
                : "text-muted-foreground hover:text-white"
                }`}
            >
              YouTube
            </button>
            <button
              onClick={() => setActiveView("weekly")}
              className={`text-sm font-medium tracking-[0.2em] uppercase transition-all duration-300 ${activeView === "weekly"
                ? "text-accent"
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
                className="text-accent animate-pulse gap-2"
              >
                <Bell className="h-4 w-4" />
                New Reports
              </Button>
            )}

            {/* Run Now Button - Context-Aware */}
            <Button
              variant="default"
              size="sm"
              disabled={processing}
              onClick={async () => {
                setProcessing(true);
                setProcessingType(activeView);
                const processTypeMap: Record<ViewType, "dailydigest" | "weeklydeepdives" | "productlaunch" | "hackernews" | "youtube"> = {
                  daily: "dailydigest",
                  producthunt: "productlaunch",
                  hackernews: "hackernews",
                  youtube: "youtube",
                  weekly: "weeklydeepdives",
                };
                const labelMap: Record<ViewType, string> = {
                  daily: "Newsletter",
                  producthunt: "Product Hunt",
                  hackernews: "HackerNews",
                  youtube: "YouTube",
                  weekly: "Strategy",
                };
                const digestType = processTypeMap[activeView];
                setProcessMessage(`⏳ Running ${labelMap[activeView]}... (~30s-2min)`);
                try {
                  await triggerProcess(digestType);

                  // Poll process status every 5 seconds
                  let attempts = 0;
                  const maxAttempts = 60; // 5 minutes at 5s intervals
                  const pollInterval = setInterval(async () => {
                    attempts++;
                    setProcessMessage(`⏳ Running ${labelMap[activeView]}... (${attempts * 5}s)`);

                    try {
                      const status = await getProcessStatus();

                      if (status.status === "completed") {
                        clearInterval(pollInterval);
                        setProcessMessage(`✅ Complete!`);
                        await loadDigests();
                        setTimeout(() => {
                          setProcessMessage(null);
                          setProcessingType(null);
                        }, 3000);
                        setProcessing(false);
                      } else if (status.status === "no_emails") {
                        clearInterval(pollInterval);
                        setProcessMessage("📭 No new content to process");
                        setTimeout(() => {
                          setProcessMessage(null);
                          setProcessingType(null);
                        }, 5000);
                        setProcessing(false);
                      } else if (status.status === "error") {
                        clearInterval(pollInterval);
                        setProcessMessage(`❌ Error: ${status.message}`);
                        setProcessing(false);
                        setProcessingType(null);
                      } else if (attempts >= maxAttempts) {
                        clearInterval(pollInterval);
                        setProcessMessage("⏰ Timed out. Click refresh to check manually.");
                        setProcessing(false);
                        setProcessingType(null);
                      }
                    } catch {
                      // Silently continue polling on error
                    }
                  }, 5000);

                } catch (err) {
                  setProcessMessage(err instanceof Error ? err.message : "Failed to start");
                  setProcessing(false);
                  setProcessingType(null);
                }
              }}
              className="gap-2 bg-accent hover:opacity-90 text-white border-0 shadow-lg shadow-accent/20"
            >
              <Play className={`h-3 w-3 ${processing ? "animate-spin" : ""}`} />
              {processing ? (
                processingType === "daily" ? "Running Newsletter..." :
                  processingType === "producthunt" ? "Running Product Hunt..." :
                    processingType === "hackernews" ? "Running HackerNews..." :
                      processingType === "youtube" ? "Running YouTube..." :
                        processingType === "weekly" ? "Running Strategy..." :
                          "Processing..."
              ) : (
                activeView === "daily" ? "Run Newsletter" :
                  activeView === "producthunt" ? "Run Product Hunt" :
                    activeView === "hackernews" ? "Run HackerNews" :
                      activeView === "youtube" ? "Run YouTube" :
                        "Run Strategy"
              )}
            </Button>

            {processMessage && (
              <span className={`text-xs font-medium px-3 py-1 rounded-full ${processMessage.includes("✅") ? "bg-green-500/20 text-green-400" :
                processMessage.includes("Failed") || processMessage.includes("Timed") ? "bg-red-500/20 text-red-400" :
                  "bg-accent/20 text-accent"
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

          {loading && !currentDigest && activeView !== "producthunt" && activeView !== "hackernews" && (
            <div className="space-y-4 animate-pulse">
              <div className="h-96 bg-white/5 rounded-lg border border-white/5" />
            </div>
          )}

          {/* Product Hunt View */}
          {activeView === "producthunt" && (
            <MotionItem className="h-full">
              <ToolsCard insight={toolsInsight} />
            </MotionItem>
          )}

          {/* HackerNews View */}
          {activeView === "hackernews" && (
            <MotionItem className="h-full">
              <HackerNewsCard insight={hackerNewsInsight} />
            </MotionItem>
          )}

          {/* YouTube View */}
          {activeView === "youtube" && (
            <MotionItem className="h-full">
              <YouTubeCard insight={youtubeInsight} />
            </MotionItem>
          )}

          {/* Daily/Weekly Digest Views */}
          {activeView !== "producthunt" && activeView !== "hackernews" && activeView !== "youtube" && !loading && !currentDigest && !error && (
            <div className="py-32 text-center border border-dashed border-white/10 rounded-lg">
              <p className="font-serif text-3xl text-muted-foreground italic">
                "Silence is also information."
              </p>
            </div>
          )}

          {activeView !== "producthunt" && activeView !== "hackernews" && activeView !== "youtube" && currentDigest && (
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
          {/* Metadata / Stats */}
          {(currentDigest || (activeView === "producthunt" && toolsInsight) || (activeView === "hackernews" && hackerNewsInsight) || (activeView === "youtube" && youtubeInsight)) && (
            <MotionItem>
              <div className="p-6 bg-card/30 backdrop-blur-md border border-white/5 rounded-lg">
                <h4 className="font-sans text-xs font-bold uppercase tracking-widest text-muted-foreground mb-6">
                  Metadata
                </h4>

                {activeView === "producthunt" && toolsInsight ? (
                  <div className="space-y-6">
                    <div className="flex items-start justify-between pb-4 border-b border-white/5">
                      <span className="text-sm text-gray-400">Date</span>
                      <span className="font-serif text-white">{toolsInsight.date}</span>
                    </div>

                    <div className="flex items-start justify-between pb-4 border-b border-white/5">
                      <span className="text-sm text-gray-400">Tools Found</span>
                      <span className="font-serif text-white">{toolsInsight.launches.length}</span>
                    </div>

                    <div className="flex items-start justify-between">
                      <span className="text-sm text-gray-400">Top Trend</span>
                      <span className="font-serif text-white line-clamp-1 max-w-[150px]" title={toolsInsight.trend_summary?.split('\n')[0].replace(/\*\*/g, '')}>
                        {toolsInsight.trend_summary?.split('\n')[2]?.replace(/\*\*/g, '').replace('Top Trends: ', '').split(',')[0] || "AI Agents"}
                      </span>
                    </div>
                  </div>
                ) : activeView === "hackernews" && hackerNewsInsight ? (
                  <div className="space-y-6">
                    <div className="flex items-start justify-between pb-4 border-b border-white/5">
                      <span className="text-sm text-gray-400">Date</span>
                      <span className="font-serif text-white">{hackerNewsInsight.date}</span>
                    </div>

                    <div className="flex items-start justify-between pb-4 border-b border-white/5">
                      <span className="text-sm text-gray-400">Stories</span>
                      <span className="font-serif text-white">{hackerNewsInsight.stories.length}</span>
                    </div>

                    <div className="flex items-start justify-between pb-4 border-b border-white/5">
                      <span className="text-sm text-gray-400">Themes</span>
                      <span className="font-serif text-white">{hackerNewsInsight.top_themes.length}</span>
                    </div>

                    <div className="flex items-start justify-between">
                      <span className="text-sm text-gray-400">Top Theme</span>
                      <span className="font-serif text-white line-clamp-2 max-w-[180px] text-right" title={hackerNewsInsight.top_themes[0]}>
                        {hackerNewsInsight.top_themes[0]?.split('(')[0]?.trim() || "Developer Trends"}
                      </span>
                    </div>
                  </div>
                ) : activeView === "youtube" && youtubeInsight ? (
                  <div className="space-y-6">
                    <div className="flex items-start justify-between pb-4 border-b border-white/5">
                      <span className="text-sm text-gray-400">Date</span>
                      <span className="font-serif text-white">{youtubeInsight.date}</span>
                    </div>

                    <div className="flex items-start justify-between pb-4 border-b border-white/5">
                      <span className="text-sm text-gray-400">Videos</span>
                      <span className="font-serif text-white">{youtubeInsight.videos.length}</span>
                    </div>

                    <div className="flex items-start justify-between pb-4 border-b border-white/5">
                      <span className="text-sm text-gray-400">Topics</span>
                      <span className="font-serif text-white">{youtubeInsight.key_topics.length}</span>
                    </div>

                    <div className="flex items-start justify-between">
                      <span className="text-sm text-gray-400">Top Topic</span>
                      <span className="font-serif text-white line-clamp-2 max-w-[180px] text-right" title={youtubeInsight.key_topics[0]}>
                        {youtubeInsight.key_topics[0]?.split('/')[0]?.trim() || "AI Trends"}
                      </span>
                    </div>
                  </div>
                ) : currentDigest && (
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
                )}
              </div>
            </MotionItem>
          )}

          {/* LinkedIn (Only on Daily) */}
          {currentDigest && activeView === "daily" && (
            <MotionItem>
              <div className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-accent to-primary opacity-20 blur transition group-hover:opacity-30 rounded-lg" />
                <div className="relative">
                  <LinkedInCard content={currentDigest.linkedin_content} />
                </div>
              </div>
            </MotionItem>
          )}

          {/* Quote */}
          <MotionItem>
            <div className="p-6 border-l-2 border-accent/50 pl-6 italic font-serif text-muted-foreground text-lg">
              "The goal is not to read more, but to understand better."
            </div>
          </MotionItem>

        </div>
      </MotionOrchestrator>
    </div>
  );
}
