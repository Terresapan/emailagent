"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, Mail, Linkedin, Calendar, Clock, Bell } from "lucide-react";
import BriefingCard from "@/components/BriefingCard";
import LinkedInCard from "@/components/LinkedInCard";
import { fetchLatestDigest, Digest } from "@/lib/api";

export default function Home() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [newContentAvailable, setNewContentAvailable] = useState(false);
  const [lastKnownDigestId, setLastKnownDigestId] = useState<number | null>(null);
  const [mounted, setMounted] = useState(false);

  const loadDigest = async () => {
    setLoading(true);
    setError(null);
    setNewContentAvailable(false);
    try {
      const data = await fetchLatestDigest();
      setDigest(data);
      if (data) {
        setLastKnownDigestId(data.id);
      }
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
      const data = await fetchLatestDigest();
      if (data && lastKnownDigestId !== null && data.id !== lastKnownDigestId) {
        setNewContentAvailable(true);
      }
    } catch {
      // Silently fail on background check
    }
  }, [lastKnownDigestId]);

  useEffect(() => {
    setMounted(true);
    loadDigest();
  }, []);

  // Poll for new content every 5 minutes
  useEffect(() => {
    if (lastKnownDigestId === null) return;
    
    const interval = setInterval(checkForNewContent, 5 * 60 * 1000); // 5 minutes
    return () => clearInterval(interval);
  }, [lastKnownDigestId, checkForNewContent]);

  return (
    <div className="animate-fade-in space-y-8">
      {/* New Content Banner */}
      {newContentAvailable && (
        <div className="animate-slide-down">
          <button
            onClick={loadDigest}
            className="flex w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-fuchsia-500/20 via-purple-500/20 to-indigo-500/20 border border-purple-500/30 px-4 py-3 text-sm font-medium text-white transition-all hover:from-fuchsia-500/30 hover:via-purple-500/30 hover:to-indigo-500/30"
          >
            <Bell className="h-4 w-4 text-purple-400 animate-bounce" />
            <span>New content available!</span>
            <span className="text-purple-400">Click to refresh</span>
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Today's Briefing & LinkedIn</h2>
          <p className="mt-1 text-gray-400">
            AI-curated insights from your newsletters
          </p>
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
            onClick={loadDigest}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-fuchsia-500 via-purple-500 to-indigo-500 px-4 py-2 text-sm font-medium text-white transition-all hover:opacity-90 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="glass-card rounded-xl p-4 text-center">
          <p className="text-red-400">{error}</p>
          <button
            onClick={loadDigest}
            className="mt-2 text-sm text-purple-400 hover:text-purple-300"
          >
            Try again
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && !digest && (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="glass-card h-96 animate-pulse rounded-xl" />
          <div className="glass-card h-96 animate-pulse rounded-xl" />
        </div>
      )}

      {/* Empty State */}
      {!loading && !digest && !error && (
        <div className="glass-card rounded-xl p-12 text-center">
          <Mail className="mx-auto h-12 w-12 text-gray-600" />
          <h3 className="mt-4 text-lg font-medium text-white">No digests yet</h3>
          <p className="mt-2 text-gray-400">
            Your AI briefings will appear here after the next email processing run.
          </p>
        </div>
      )}

      {/* Content Cards */}
      {digest && (
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
                  <p className="font-medium text-white">{digest.date}</p>
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
                    {digest.emails_processed?.length || 0}
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
            <BriefingCard briefing={digest.briefing} />
            <LinkedInCard content={digest.linkedin_content} />
          </div>

          {/* Processed Emails List */}
          {digest.emails_processed && digest.emails_processed.length > 0 && (
            <div className="glass-card rounded-xl p-6">
              <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
                <Mail className="h-5 w-5 text-purple-400" />
                Processed Newsletters
              </h3>
              <ul className="space-y-2">
                {digest.emails_processed.map((email, index) => (
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
