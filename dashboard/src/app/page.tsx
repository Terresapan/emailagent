"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, Bell, Play } from "lucide-react";
import BriefingCard from "@/components/briefing/BriefingCard";
import LinkedInCard from "@/components/briefing/LinkedInCard";
import DeepDiveCard from "@/components/briefing/DeepDiveCard";
import ToolsCard from "@/components/briefing/ToolsCard";
import HackerNewsCard from "@/components/briefing/HackerNewsCard";
import YouTubeCard from "@/components/briefing/YouTubeCard";
import NewsletterItem from "@/components/briefing/NewsletterItem";
import { fetchLatestDigest, triggerProcess, getProcessStatus, fetchToolsInsight, fetchHackerNewsInsight, fetchYouTubeInsight, Digest, ToolsInsight, HackerNewsInsight, YouTubeInsight } from "@/lib/api";
import { MotionOrchestrator, MotionItem } from "@/components/MotionOrchestrator";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { archiveItem } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { Archive as ArchiveIcon } from "lucide-react";

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
  const { toast } = useToast();
  const [archiving, setArchiving] = useState(false);

  const handleArchive = async () => {
    if (!currentDigest && activeView !== "producthunt" && activeView !== "hackernews" && activeView !== "youtube") return;

    setArchiving(true);
    try {
      if (activeView === "producthunt" && toolsInsight) {
        await archiveItem("producthunt", toolsInsight.id, `Product Hunt - ${toolsInsight.date}`, toolsInsight.trend_summary, toolsInsight);
      } else if (activeView === "hackernews" && hackerNewsInsight) {
        await archiveItem("hackernews", hackerNewsInsight.id, `Hacker News - ${hackerNewsInsight.date}`, hackerNewsInsight.summary, hackerNewsInsight);
      } else if (activeView === "youtube" && youtubeInsight) {
        await archiveItem("youtube", youtubeInsight.id, `YouTube - ${youtubeInsight.date}`, youtubeInsight.trend_summary, youtubeInsight);
      } else if (currentDigest) {
        await archiveItem(
          activeView === "daily" ? "daily" : "weekly",
          currentDigest.id,
          `${activeView === "daily" ? "Daily Briefing" : "Weekly Strategy"} - ${currentDigest.date}`,
          currentDigest.briefing?.substring(0, 200) + "...",
          currentDigest
        );
      }

      toast({
        title: "Saved to Archives",
        description: "This item has been saved for future reference.",
      });
    } catch (error) {
      toast({
        title: "Failed to Archive",
        description: "Could not save this item. it may already be archived.",
        variant: "destructive",
      });
    } finally {
      setArchiving(false);
    }
  };

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

  const [showStickyHeader, setShowStickyHeader] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      // Show sticky header after scrolling past the main specific title area (~200px)
      if (window.scrollY > 200) {
        setShowStickyHeader(true);
      } else {
        setShowStickyHeader(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const currentDigest = activeView === "daily" ? dailyDigest : weeklyDigest;

  return (
    <div className="min-h-screen pb-20 relative">
      {/* Scroll-Aware Sticky Header */}
      <div
        className={`sticky-header ${showStickyHeader ? "translate-y-0" : "-translate-y-full"
          }`}
      >
        <div className="flex items-center gap-4">
          {/* Sidebar Spacer (Desktop only) to align with content */}
          <div className="w-0 lg:w-80 shrink-0" />
          <h2 className="text-xl font-serif text-white tracking-wide">
            {activeView === "daily" ? "Daily Insights" :
              activeView === "producthunt" ? "Product Hunt" :
                activeView === "hackernews" ? "HackerNews" :
                  activeView === "youtube" ? "YouTube Channels" :
                    "Weekly Intelligence"}
          </h2>
        </div>

        {/* Action Button (Moved from Navigation for easy access) */}
        <Button
          variant="default"
          size="sm"
          disabled={processing}
          onClick={async () => {
            setProcessing(true);
            setProcessingType(activeView);
            // Reuse logic from main button (simplified here for brevity, ideally refactor trigger logic)
            const processTypeMap = {
              daily: "dailydigest",
              producthunt: "productlaunch",
              hackernews: "hackernews",
              youtube: "youtube",
              weekly: "weeklydeepdives",
            };
            // ... trigger/poll logic duplicating main button click ...
            // For this implementation, I will just replicate the simpler trigger call
            // In a full refactor, specific trigger logic should be a shared function.
            try {
              const digestType = processTypeMap[activeView as ViewType];
              await triggerProcess(digestType as any);
              setProcessMessage("Processing started...");
              // Simple polling or reload
              setTimeout(loadDigests, 5000);
            } catch (e) {
              console.error(e);
            } finally {
              setProcessing(false);
              setProcessingType(null);
            }
          }}
          className="mr-6 bg-primary hover:opacity-90 text-primary-foreground border-0 shadow-lg shadow-primary/20 gap-2"
        >
          <Play className={`h-3 w-3 ${processing ? "animate-spin" : ""}`} />
          Run Process
        </Button>
      </div>

      {/* Giant Typography Header */}
      <MotionOrchestrator className="mb-20">
        <MotionItem className="relative z-10 -ml-2 lg:-ml-4">
          <h1 className="utitle select-none break-words">
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
              className="gap-2 bg-primary hover:opacity-90 text-primary-foreground border-0 shadow-lg shadow-primary/20"
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

              {/* Archive Button - Always visible, disabled if no content */}
              <Button
                variant="ghost"
                size="icon"
                onClick={handleArchive}
                disabled={archiving || (!currentDigest && activeView !== "producthunt" && activeView !== "hackernews" && activeView !== "youtube") || (activeView === "producthunt" && !toolsInsight) || (activeView === "hackernews" && !hackerNewsInsight) || (activeView === "youtube" && !youtubeInsight)}
                className="hover:text-accent hover:bg-accent/10 transition-colors"
                title="Save to Archives"
                aria-label="Save to Archives"
              >
                <ArchiveIcon className={`h-4 w-4 ${archiving ? "animate-pulse" : ""}`} />
              </Button>

              <Button variant="ghost" size="icon" onClick={loadDigests} disabled={loading} className="hover:text-white hover:bg-white/5" aria-label="Refresh content">
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
              <div className="relative group rounded-lg transition-all duration-300 hover:shadow-[0_0_20px_rgba(216,180,254,0.25)] hover:border-primary/30 border border-transparent">
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
