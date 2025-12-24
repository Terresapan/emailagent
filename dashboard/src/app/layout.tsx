import type { Metadata } from "next";
import { Playfair_Display, DM_Sans } from "next/font/google";
import "./globals.css";

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
      <body className="font-sans antialiased bg-editorial-bg text-editorial-text selection:bg-brand-purple/30">
        {/* Editorial Header */}
        <header className="sticky top-0 z-50 border-b border-white/5 bg-editorial-bg/60 backdrop-blur-md">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-20 items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-10 w-1 bg-gradient-brand rounded-full" />
                <div>
                  <h1 className="font-serif text-2xl font-bold tracking-tight text-white">
                    The Content Agent
                  </h1>
                  <p className="text-xs uppercase tracking-widest text-brand-purple/80 font-medium">
                    Daily Intelligence
                  </p>
                </div>
              </div>
              <nav className="hidden sm:flex items-center gap-8">
                <span className="text-xs font-medium uppercase tracking-widest text-gray-500 hover:text-brand-fuchsia transition-colors cursor-pointer">
                  Briefings
                </span>
                <span className="text-xs font-medium uppercase tracking-widest text-gray-500 hover:text-brand-fuchsia transition-colors cursor-pointer">
                  Archives
                </span>
                <div className="h-4 w-px bg-white/10" />
                <span className="text-sm font-serif italic text-gray-400" suppressHydrationWarning>
                  {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
                </span>
              </nav>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          {children}
        </main>

        {/* Footer */}
        <footer className="mt-12 border-t border-white/5 py-12">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
            <p className="font-serif italic text-gray-600">
              "Knowledge is power."
            </p>
            <p className="mt-4 text-xs uppercase tracking-widest text-gray-700">
              Powered by AI • Curated for You
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
