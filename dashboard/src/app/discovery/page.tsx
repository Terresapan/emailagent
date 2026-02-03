import { Suspense } from "react";
import DiscoveryClient from "./discovery-client";
import { fetchDiscoveryBriefing, fetchDiscoveryVideos } from "@/lib/api";

export const revalidate = 60; // Revalidate every minute

async function getData() {
    try {
        const [briefing, videosData] = await Promise.all([
            fetchDiscoveryBriefing().catch(() => null),
            fetchDiscoveryVideos().catch(() => ({ videos: [] })),
        ]);
        return { briefing, videos: videosData?.videos || [] };
    } catch (e) {
        console.error("Failed to load discovery data", e);
        return { briefing: null, videos: [] };
    }
}

export default async function DiscoveryPage() {
    const { briefing, videos } = await getData();

    return (
        <Suspense fallback={<div className="min-h-screen pt-20 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div></div>}>
            <DiscoveryClient initialBriefing={briefing} initialVideos={videos} />
        </Suspense>
    );
}