import { fetchArchiveById, ArchivedItem } from "@/lib/api";
import { MotionOrchestrator, MotionItem } from "@/components/MotionOrchestrator";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Calendar } from "lucide-react";
import Link from "next/link";
import BriefingCard from "@/components/briefing/BriefingCard";
import DeepDiveCard from "@/components/briefing/DeepDiveCard";
import ToolsCard from "@/components/briefing/ToolsCard";
import HackerNewsCard from "@/components/briefing/HackerNewsCard";
import YouTubeCard from "@/components/briefing/YouTubeCard";
import LinkedInCard from "@/components/briefing/LinkedInCard";
import NewsletterItem from "@/components/briefing/NewsletterItem";
import { OpportunityCard } from "@/components/discovery/OpportunityCard";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import MarkdownView from "@/components/MarkdownView";

// Badge Component (Server Component compatible if no state)
function Badge({ type }: { type: string }) {
    const styles: Record<string, string> = {
        daily: "bg-blue-500/10 text-blue-400 border-blue-500/20",
        weekly: "bg-purple-500/10 text-purple-400 border-purple-500/20",
        discovery: "bg-green-500/10 text-green-400 border-green-500/20",
        producthunt: "bg-orange-500/10 text-orange-400 border-orange-500/20",
        hackernews: "bg-orange-600/10 text-orange-500 border-orange-600/20",
        youtube: "bg-red-500/10 text-red-400 border-red-500/20",
    };

    const labels: Record<string, string> = {
        daily: "Newsletter",
        weekly: "Strategy",
        discovery: "Discovery",
        producthunt: "Product Hunt",
        hackernews: "Hacker News",
        youtube: "YouTube",
    };

    return (
        <span className={`text-xs uppercase tracking-widest px-3 py-1.5 rounded border font-medium ${styles[type] || "bg-gray-500/10 text-gray-400 border-gray-500/20"}`}>
            {labels[type] || type}
        </span>
    );
}

export const revalidate = 60;

export default async function ArchiveDetailPage({ 
    params 
}: { 
    params: Promise<{ type: string; id: string }> 
}) {
    const { id } = await params;
    let item: ArchivedItem | null = null;
    try {
        item = await fetchArchiveById(id);
    } catch (err) {
        console.error("Failed to load archive item", err);
    }

    if (!item) {
        return (
            <div className="min-h-screen pt-20 px-8">
                <div className="max-w-4xl mx-auto text-center">
                    <h1 className="text-2xl font-bold mb-4">Content Not Found</h1>
                    <p className="text-muted-foreground mb-8">This archived item could not be found or has been deleted.</p>
                    <Link href="/archives">
                        <Button variant="outline">
                            <ArrowLeft className="mr-2 h-4 w-4" />
                            Back to Archives
                        </Button>
                    </Link>
                </div>
            </div>
        );
    }

    const renderContent = () => {
        // 1. Rich Content (if data exists)
        if (item.data) {
            switch (item.item_type) {
                case "daily":
                case "weekly":
                    // item.data is the full Digest object
                    const digest = item.data;
                    return (
                        <div className="grid grid-cols-1 gap-8">
                            {/* Main Briefing Card */}
                            {item.item_type === "daily" ? (
                                <BriefingCard briefing={digest.briefing} className="min-h-[600px]" />
                            ) : (
                                <DeepDiveCard briefing={digest.briefing} className="min-h-[600px]" />
                            )}

                            {/* Source Intercepts (Emails) */}
                            {digest.structured_digests && digest.structured_digests.length > 0 && (
                                <div className="pt-8">
                                    <div className="flex items-center gap-4 mb-8">
                                        <Separator className="flex-1 bg-white/10" />
                                        <h3 className="font-serif text-2xl text-white italic">Source Intercepts</h3>
                                        <Separator className="flex-1 bg-white/10" />
                                    </div>
                                    <div className="grid gap-6">
                                        {digest.structured_digests.map((emailDigest: any, index: number) => (
                                            <NewsletterItem key={index} digest={emailDigest} />
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* LinkedIn Content (Daily only) */}
                            {item.item_type === "daily" && digest.linkedin_content && (
                                <div className="mt-8 relative group">
                                    <div className="absolute -inset-0.5 bg-gradient-to-r from-accent to-primary opacity-20 blur transition group-hover:opacity-30 rounded-lg" />
                                    <div className="relative">
                                        <LinkedInCard content={digest.linkedin_content} />
                                    </div>
                                </div>
                            )}
                        </div>
                    );

                case "producthunt":
                    return <ToolsCard insight={item.data} className="min-h-[600px]" />;

                case "hackernews":
                    return <HackerNewsCard insight={item.data} className="min-h-[600px]" />;

                case "youtube":
                    return <YouTubeCard insight={item.data} className="min-h-[600px]" />;

                case "discovery":
                    // Discovery needs a custom grid layout akin to DiscoveryPage
                    const opportunities = item.data.top_opportunities || [];
                    return (
                        <div className="space-y-8">
                            {/* Summary Stats Card */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <Card className="bg-card/50 backdrop-blur-sm border-white/5">
                                    <CardContent className="pt-6">
                                        <div className="text-3xl font-bold text-accent">{opportunities.length}</div>
                                        <div className="text-sm text-muted-foreground">Opportunities</div>
                                    </CardContent>
                                </Card>
                                <Card className="bg-card/50 backdrop-blur-sm border-white/5">
                                    <CardContent className="pt-6">
                                        <div className="text-3xl font-bold text-white">{item.data.total_data_points || 0}</div>
                                        <div className="text-sm text-muted-foreground">Data Points</div>
                                    </CardContent>
                                </Card>
                                <Card className="bg-card/50 backdrop-blur-sm border-white/5">
                                    <CardContent className="pt-6">
                                        <div className="text-3xl font-bold text-white">{item.data.total_pain_points_extracted || 0}</div>
                                        <div className="text-sm text-muted-foreground">Pain Points</div>
                                    </CardContent>
                                </Card>
                                <Card className="bg-card/50 backdrop-blur-sm border-white/5">
                                    <CardContent className="pt-6">
                                        <div className="text-3xl font-bold text-green-400">${item.data.estimated_cost?.toFixed(2) || "0.00"}</div>
                                        <div className="text-sm text-muted-foreground">API Cost</div>
                                    </CardContent>
                                </Card>
                            </div>

                            <div className="flex justify-between items-end border-b border-white/10 pb-4">
                                <h2 className="section-header">App Ideas ({opportunities.length})</h2>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {opportunities.map((opp: any, index: number) => (
                                    <OpportunityCard
                                        key={index}
                                        rank={index + 1}
                                        appIdea={opp.app_idea}
                                        problem={opp.problem}
                                        demandScore={opp.demand_score}
                                        viralityScore={opp.virality_score}
                                        buildabilityScore={opp.buildability_score}
                                        opportunityScore={opp.opportunity_score}
                                        sources={opp.pain_points?.map((p: any) => p.source) || []}
                                    />
                                ))}
                            </div>
                        </div>
                    );

                default:
                    return (
                        <div className="bg-card/50 border border-white/5 rounded-lg p-8">
                            <h3 className="text-lg font-bold text-white mb-2">Raw Data View</h3>
                            <pre className="text-xs text-muted-foreground overflow-auto max-h-96">
                                {JSON.stringify(item.data, null, 2)}
                            </pre>
                        </div>
                    );
            }
        }

        // 2. Legacy / Fallback Content (Markdown Summary)
        return (
            <div className="bg-card/50 border border-white/5 rounded-lg p-6 md:p-10">
                <div className="prose prose-invert prose-lg max-w-none">
                    <MarkdownView content={item.summary || "*No content available.*"} />
                </div>
            </div>
        );
    };

    return (
        <div className="min-h-screen pb-20">
            <MotionOrchestrator className="max-w-7xl mx-auto px-4 md:px-8 pt-8">
                {/* Header Section */}
                <MotionItem className="mb-8">
                    <Link href="/archives" className="inline-block mb-6 -ml-4">
                        <Button
                            variant="ghost"
                            className="hover:bg-white/5 text-muted-foreground hover:text-white"
                        >
                            <ArrowLeft className="mr-2 h-4 w-4" />
                            Back to Archives
                        </Button>
                    </Link>

                    <div className="flex flex-col gap-4">
                        <div className="flex flex-wrap items-center gap-4">
                            <Badge type={item.item_type} />
                            <div className="flex items-center text-sm text-muted-foreground">
                                <Calendar className="mr-2 h-4 w-4" />
                                {new Date(item.created_at).toLocaleDateString()}
                            </div>
                        </div>
                        <h1 className="font-serif text-3xl md:text-5xl font-bold leading-tight text-white">
                            {item.title}
                        </h1>
                    </div>
                </MotionItem>

                {/* Main Content Render */}
                <MotionItem>
                    {renderContent()}
                </MotionItem>
            </MotionOrchestrator>
        </div>
    );
}