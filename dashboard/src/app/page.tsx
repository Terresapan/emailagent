"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, Mail, Linkedin, Calendar, Clock, Bell, BookOpen, Sparkles } from "lucide-react";
import BriefingCard from "@/components/BriefingCard";
import LinkedInCard from "@/components/LinkedInCard";
import DeepDiveCard from "@/components/DeepDiveCard";
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
      // Load both daily and weekly digests in parallel
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

  // Check for new content in the background
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

  // Poll for new content every 5 minutes
  useEffect(() => {
    if (lastKnownDailyId === null && lastKnownWeeklyId === null) return;
    
    const interval = setInterval(checkForNewContent, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [lastKnownDailyId, lastKnownWeeklyId, checkForNewContent]);

  // Get current digest based on active view
  const currentDigest = activeView === "daily" ? dailyDigest : weeklyDigest;

  return (
    <div className="animate-fade-in space-y-8">
      {/* New Content Banner */}
      {newContentAvailable && (
        <div className="animate-slide-down">
          <button
            onClick={loadDigests}
            className="flex w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-fuchsia-500/20 via-purple-500/20 to-indigo-500/20 border border-purple-500/30 px-4 py-3 text-sm font-medium text-white transition-all hover:from-fuchsia-500/30 hover:via-purple-500/30 hover:to-indigo-500/30"
          >
            <Bell className="h-4 w-4 text-purple-400 animate-bounce" />
            <span>New content available!</span>
            <span className="text-purple-400">Click to refresh</span>
          </button>
        </div>
      )}

      {/* View Toggle Tabs */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex rounded-lg bg-white/5 p-1">
            <button
              onClick={() => setActiveView("daily")}
              className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-all ${
                activeView === "daily"
                  ? "bg-gradient-to-r from-fuchsia-500 to-fuchsia-600 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              <Sparkles className="h-4 w-4" />
              Daily Briefing
            </button>
            <button
              onClick={() => setActiveView("weekly")}
              className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-all ${
                activeView === "weekly"
                  ? "bg-gradient-to-r from-indigo-500 to-indigo-600 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              <BookOpen className="h-4 w-4" />
              Weekly Deep Dive
            </button>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {mounted && lastRefresh && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Clock className="h-4 w-4" />
              <span>
                Updated {lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          )}
          <button
            onClick={loadDigests}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-fuchsia-500 via-purple-500 to-indigo-500 px-4 py-2 text-sm font-medium text-white transition-all hover:opacity-90 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">
          {activeView === "daily" ? "Today's Briefing & LinkedIn" : "Weekly Deep Dive"}
        </h2>
        <p className="mt-1 text-gray-400">
          {activeView === "daily"
            ? "AI-curated insights from your daily newsletters"
            : "Strategic analysis from expert essays"}
        </p>
      </div>

      {/* Error State */}
      {error && (
        <div className="glass-card rounded-xl p-4 text-center">
          <p className="text-red-400">{error}</p>
          <button
            onClick={loadDigests}
            className="mt-2 text-sm text-purple-400 hover:text-purple-300"
          >
            Try again
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && !currentDigest && (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="glass-card h-96 animate-pulse rounded-xl" />
          {activeView === "daily" && (
            <div className="glass-card h-96 animate-pulse rounded-xl" />
          )}
        </div>
      )}

      {/* Empty State */}
      {!loading && !currentDigest && !error && (
        <div className="glass-card rounded-xl p-12 text-center">
          {activeView === "daily" ? (
            <>
              <Mail className="mx-auto h-12 w-12 text-gray-600" />
              <h3 className="mt-4 text-lg font-medium text-white">No daily digests yet</h3>
              <p className="mt-2 text-gray-400">
                Your daily briefings will appear here after the next email processing run.
              </p>
            </>
          ) : (
            <>
              <BookOpen className="mx-auto h-12 w-12 text-gray-600" />
              <h3 className="mt-4 text-lg font-medium text-white">No weekly deep dives yet</h3>
              <p className="mt-2 text-gray-400">
                Your weekly strategic briefings will appear here after Sunday's processing run.
              </p>
            </>
          )}
        </div>
      )}

      {/* Content Cards - Daily View */}
      {currentDigest && activeView === "daily" && (
        <>
          {/* Stats Bar */}
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="glass-card rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-fuchsia-500/20 p-2">
                  <Calendar className="h-5 w-5 text-fuchsia-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Date</p>
                  <p className="font-medium text-white">{currentDigest.date}</p>
                </div>
              </div>
            </div>
            <div className="glass-card rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-purple-500/20 p-2">
                  <Mail className="h-5 w-5 text-purple-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Emails Processed</p>
                  <p className="font-medium text-white">
                    {currentDigest.emails_processed?.length || 0}
                  </p>
                </div>
              </div>
            </div>
            <div className="glass-card rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-indigo-500/20 p-2">
                  <Linkedin className="h-5 w-5 text-indigo-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">LinkedIn Posts</p>
                  <p className="font-medium text-white">3 ready</p>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content Grid */}
          <div className="grid gap-6 lg:grid-cols-2">
            <BriefingCard briefing={currentDigest.briefing} />
            <LinkedInCard content={currentDigest.linkedin_content} />
          </div>

          {/* Processed Emails List */}
          {currentDigest.emails_processed && currentDigest.emails_processed.length > 0 && (
            <div className="glass-card rounded-xl p-6">
              <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
                <Mail className="h-5 w-5 text-purple-400" />
                Processed Newsletters
              </h3>
              <ul className="space-y-2">
                {currentDigest.emails_processed.map((email, index) => (
                  <li
                    key={index}
                    className="rounded-lg bg-white/5 px-4 py-2 text-sm text-gray-300"
                  >
                    {email}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {/* Content Cards - Weekly View */}
      {currentDigest && activeView === "weekly" && (
        <>
          {/* Stats Bar */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="glass-card rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-indigo-500/20 p-2">
                  <Calendar className="h-5 w-5 text-indigo-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Week of</p>
                  <p className="font-medium text-white">{currentDigest.date}</p>
                </div>
              </div>
            </div>
            <div className="glass-card rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-purple-500/20 p-2">
                  <BookOpen className="h-5 w-5 text-purple-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Essays Analyzed</p>
                  <p className="font-medium text-white">
                    {currentDigest.emails_processed?.length || 0}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Deep Dive Content - Full Width */}
          <DeepDiveCard briefing={currentDigest.briefing} />

          {/* Processed Essays List */}
          {currentDigest.emails_processed && currentDigest.emails_processed.length > 0 && (
            <div className="glass-card rounded-xl p-6">
              <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
                <BookOpen className="h-5 w-5 text-indigo-400" />
                Analyzed Essays
              </h3>
              <ul className="space-y-2">
                {currentDigest.emails_processed.map((email, index) => (
                  <li
                    key={index}
                    className="rounded-lg bg-white/5 px-4 py-2 text-sm text-gray-300"
                  >
                    {email}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
