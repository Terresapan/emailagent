"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Newspaper,
  Archive,
  Settings,
  Rocket,
  Zap,
  Menu
} from "lucide-react";
import { useState, useEffect } from "react";

const navItems = [
  { href: "/", label: "Briefing", icon: Newspaper },
  { href: "/archives", label: "Archives", icon: Archive },
  { href: "/discovery", label: "Discovery", icon: Rocket },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function IntelligenceRail() {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setIsCollapsed(true);
      } else {
        setIsCollapsed(false);
      }
    };

    // Initial check
    handleResize();

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <aside className={cn(
      "fixed left-0 top-0 z-40 h-screen border-r border-white/5 bg-card/50 backdrop-blur-xl transition-all duration-500 ease-[cubic-bezier(0.32,0.725,0,1)]",
      isCollapsed ? "w-20" : "w-80"
    )}>
      <div className="flex h-full flex-col">
        {/* Header / Brand */}
        <div className="flex h-32 flex-col justify-between p-6">
          <div className="flex items-center justify-between">
            <div className={cn("h-8 w-1 bg-accent transition-all", isCollapsed ? "h-4" : "")} />
            <Button
              variant="ghost"
              size="icon"
              className="text-muted-foreground hover:text-white"
              onClick={() => setIsCollapsed(!isCollapsed)}
            >
              <Menu className="h-4 w-4" />
            </Button>
          </div>

          <div className={cn("transition-opacity duration-300", isCollapsed ? "opacity-0 hidden" : "opacity-100")}>
            <h1 className="font-serif text-2xl font-bold leading-none tracking-tighter text-muted-foreground">
              The <br />
              <span className="text-white text-3xl">Intelligent Content</span> <br />
              Agent
            </h1>
          </div>
        </div>

        <Separator className="bg-white/5" />

        {/* Navigation */}
        <ScrollArea className="flex-1 py-6">
          <nav className="space-y-2 px-4">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link key={item.href} href={item.href} onClick={() => setIsCollapsed(true)}>
                  <Button
                    variant="ghost"
                    className={cn(
                      "group w-full justify-start gap-4 overflow-hidden rounded-none py-6 text-sm font-medium tracking-widest uppercase transition-all hover:bg-white/5",
                      isActive
                        ? "text-accent hover:text-accent"
                        : "text-muted-foreground hover:text-white",
                      isCollapsed && "justify-center px-0"
                    )}
                  >
                    <Icon className={cn("h-5 w-5 transition-transform group-hover:scale-110", isActive && "text-accent")} />
                    <span className={cn(
                      "transition-all duration-300",
                      isCollapsed ? "w-0 opacity-0 translate-x-10 absolute" : "w-auto opacity-100 translate-x-0"
                    )}>
                      {item.label}
                    </span>
                  </Button>
                </Link>
              );
            })}
          </nav>
        </ScrollArea>

        {/* Footer / Status */}
        <div className="p-6">
          <div className={cn(
            "rounded-lg border border-white/5 bg-white/5 p-4 backdrop-blur-md transition-all",
            isCollapsed ? "hidden" : "block"
          )}>
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/10">
                <Zap className="h-4 w-4 text-accent animate-pulse" />
              </div>
              <div>
                <p className="status-label">System Status</p>
                <p className="text-[10px] text-green-400">All Agents Online</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
