import { Suspense } from "react";
import HomeClient from "./home-client";
import { fetchLatestDigest, fetchToolsInsight, fetchHackerNewsInsight, fetchYouTubeInsight } from "@/lib/api";

// Revalidate data every minute to keep it relatively fresh without constant fetching
// or set to 0 if we want instant updates. Given the dashboard nature, 60s is good.
export const revalidate = 60;

async function getDashboardData() {
  try {
    const [daily, weekly, tools, hn, yt] = await Promise.all([
      fetchLatestDigest("daily").catch(() => null),
      fetchLatestDigest("weekly").catch(() => null),
      fetchToolsInsight().catch(() => null),
      fetchHackerNewsInsight().catch(() => null),
      fetchYouTubeInsight().catch(() => null),
    ]);
    return { daily, weekly, tools, hn, yt };
  } catch (error) {
    console.error("Failed to fetch dashboard data", error);
    return { daily: null, weekly: null, tools: null, hn: null, yt: null };
  }
}

export default async function Home() {
  const { daily, weekly, tools, hn, yt } = await getDashboardData();

  return (
    <Suspense fallback={<div className="min-h-screen pt-20 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div></div>}>
      <HomeClient
        initialDailyDigest={daily}
        initialWeeklyDigest={weekly}
        initialToolsInsight={tools}
        initialHackerNewsInsight={hn}
        initialYoutubeInsight={yt}
      />
    </Suspense>
  );
}