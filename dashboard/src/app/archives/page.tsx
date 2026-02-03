import { Suspense } from "react";
import ArchivesClient from "./archives-client";
import { fetchArchives, ArchivedItem } from "@/lib/api";

// Revalidate every minute
export const revalidate = 60;

export default async function ArchivesPage() {
    let archives: ArchivedItem[] = [];
    try {
        archives = await fetchArchives();
    } catch (error) {
        console.error("Failed to load archives", error);
    }

    return (
        <Suspense fallback={<div className="min-h-screen pt-20 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div></div>}>
            <ArchivesClient initialArchives={archives} />
        </Suspense>
    );
}