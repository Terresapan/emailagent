import type { Metadata } from "next";
import { Playfair_Display, DM_Sans } from "next/font/google";
import "./globals.css";
import { IntelligenceRail } from "@/components/IntelligenceRail";

const playfair = Playfair_Display({ 
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
});

const dmSans = DM_Sans({ 
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "The Daily Briefing",
  description: "Curated intelligence and strategic insights.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${playfair.variable} ${dmSans.variable}`}>
      <body className="flex min-h-screen bg-background font-sans text-foreground antialiased selection:bg-brand-purple/30">
        
        {/* Fixed Intelligence Rail */}
        <IntelligenceRail />

        {/* Main Content Area */}
        {/* We add left padding to account for the rail. 
            By default the rail is w-80 (20rem). 
            We can make this dynamic or just set a safe margin for the expanded state as default 
            since the user has plenty of screen space usually. 
            Or we can use a wrapper that isn't connected to the internal rail state easily without context.
            For now, let's assume standard desktop view with padding-left-80. 
        */}
        <main className="flex-1 pl-20 lg:pl-80 transition-all duration-500 will-change-[padding]">
          <div className="mx-auto max-w-[1600px] px-6 py-12 lg:px-12">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
