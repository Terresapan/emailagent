"use client";

import { useEffect, useState } from "react";
import { MotionOrchestrator, MotionItem } from "@/components/MotionOrchestrator";
import { fetchArchives, deleteArchive, ArchivedItem } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Archive, Trash2, ExternalLink, Calendar, FileText, X } from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";

const TABS = [
    { id: 'all', label: 'All' },
    { id: 'daily', label: 'Newsletter' },
    { id: 'weekly', label: 'Strategy' },
    { id: 'discovery', label: 'Discovery' },
    { id: 'producthunt', label: 'Product Hunt' },
    { id: 'hackernews', label: 'Hacker News' },
    { id: 'youtube', label: 'YouTube' },
];

export default function ArchivesPage() {
    const [archives, setArchives] = useState<ArchivedItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('all');
    const [deletingId, setDeletingId] = useState<number | null>(null);

    useEffect(() => {
        loadArchives();
    }, []);

    const loadArchives = async () => {
        try {
            const data = await fetchArchives();
            setArchives(data);
        } catch (error) {
            console.error("Failed to load archives", error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (e: React.MouseEvent, id: number) => {
        e.preventDefault();
        e.stopPropagation();
        if (!confirm("Are you sure you want to remove this item from archives?")) return;

        setDeletingId(id);
        try {
            await deleteArchive(id);
            setArchives(prev => prev.filter(item => item.id !== id));
        } catch (error) {
            console.error("Failed to delete archive", error);
        } finally {
            setDeletingId(null);
        }
    };

    const filteredArchives = activeTab === 'all'
        ? archives
        : archives.filter(item => item.item_type === activeTab);

    return (
        <div className="min-h-screen pb-20">
            {/* Header */}
            <MotionOrchestrator className="mb-12">
                <MotionItem className="relative z-10 -ml-2 lg:-ml-4 mb-8">
                    <h1 className="utitle select-none">
                        INTELLIGENCE<br />ARCHIVES
                    </h1>
                </MotionItem>

                {/* Filter Tabs */}
                <MotionItem>
                    <div className="flex flex-wrap gap-4 border-b border-white/10 pb-6">
                        {TABS.map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={cn(
                                    "text-sm font-medium tracking-[0.2em] uppercase transition-all duration-300",
                                    activeTab === tab.id
                                        ? "text-accent"
                                        : "text-muted-foreground hover:text-white"
                                )}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </MotionItem>
            </MotionOrchestrator>

            {/* Content Grid */}
            <MotionOrchestrator>
                {loading ? (
                    <MotionItem className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-48 bg-white/5 rounded-lg border border-white/5" />
                        ))}
                    </MotionItem>
                ) : filteredArchives.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredArchives.map((item, index) => (
                            <MotionItem key={item.id}>
                                {/* Link to dynamic detail page */}
                                <Link href={`/archives/${item.item_type}/${item.id}`} className="group relative block h-full">
                                    <Card className="h-full bg-card/50 backdrop-blur-sm border-white/5 hover:border-accent/50 transition-all duration-300 group-hover:bg-white/5">
                                        <CardContent className="pt-6 flex flex-col h-full">

                                            {/* Type Badge */}
                                            <div className="flex justify-between items-start mb-4">
                                                <Badge type={item.item_type} />
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-8 w-8 text-muted-foreground hover:text-red-400 -mr-2 -mt-2 opacity-0 group-hover:opacity-100 transition-opacity"
                                                    onClick={(e) => handleDelete(e, item.id)}
                                                    disabled={deletingId === item.id}
                                                >
                                                    {deletingId === item.id ? (
                                                        <span className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                                                    ) : (
                                                        <Trash2 className="h-4 w-4" />
                                                    )}
                                                </Button>
                                            </div>

                                            {/* Content */}
                                            <h3 className="font-serif text-xl font-bold text-white mb-2 line-clamp-2">
                                                {item.title}
                                            </h3>

                                            {item.summary && (
                                                <p className="text-sm text-muted-foreground line-clamp-3 mb-4 flex-1">
                                                    {item.summary}
                                                </p>
                                            )}

                                            {/* Footer */}
                                            <div className="flex items-center gap-4 text-xs text-muted-foreground mt-auto pt-4 border-t border-white/5">
                                                <div className="flex items-center gap-1.5">
                                                    <Calendar className="h-3 w-3" />
                                                    {new Date(item.created_at).toLocaleDateString()}
                                                </div>
                                                {/* Placeholder for View Action */}
                                                <div className="flex items-center gap-1.5 ml-auto text-accent opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <span>View</span>
                                                    <ExternalLink className="h-3 w-3" />
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                </Link>
                            </MotionItem>
                        ))}
                    </div>
                ) : (
                    <MotionItem>
                        <div className="py-32 text-center border border-dashed border-white/10 rounded-lg">
                            <Archive className="h-16 w-16 mx-auto text-muted-foreground/30 mb-6" />
                            <p className="font-serif text-3xl text-muted-foreground italic">
                                "The archives are empty."
                            </p>
                            <p className="item-meta mt-4">
                                Save briefings and discoveries to build your library.
                            </p>
                        </div>
                    </MotionItem>
                )}
            </MotionOrchestrator>
        </div>
    );
}

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
        <span className={cn(
            "text-[10px] uppercase tracking-widest px-2 py-1 rounded border font-medium",
            styles[type] || "bg-gray-500/10 text-gray-400 border-gray-500/20"
        )}>
            {labels[type] || type}
        </span>
    );
}
