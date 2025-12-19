import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Content Agent Dashboard",
  description: "AI-powered email briefings and LinkedIn content",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} antialiased`}>
        {/* Gradient Header */}
        <header className="sticky top-0 z-50 border-b border-white/10 bg-gray-950/80 backdrop-blur-xl">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-fuchsia-500 via-purple-500 to-indigo-500" />
                <h1 className="bg-gradient-to-r from-fuchsia-500 via-purple-500 to-indigo-500 bg-clip-text text-xl font-bold text-transparent">
                  Content Agent
                </h1>
              </div>
              <nav className="flex items-center gap-6">
                <span className="text-sm text-gray-400">Dashboard</span>
              </nav>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-white/5 py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <p className="text-center text-sm text-gray-500">
              Content Agent • AI-powered newsletter insights
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
