import React from 'react';
import { cn } from "@/lib/utils";

interface TrendSparklineProps {
    momentum: number;
    trendDirection: string;
    className?: string;
}

export const TrendSparkline: React.FC<TrendSparklineProps> = ({
    momentum,
    trendDirection,
    className
}) => {
    const isRising = momentum > 0;
    const isStable = Math.abs(momentum) < 5;

    // Color based on trend
    const strokeColor = isStable
        ? "stroke-muted-foreground"
        : isRising
            ? "stroke-accent"
            : "stroke-orange-400"; // Muted warning color for declining

    // Simple SVG path generation based on momentum
    // If rising: curve goes up. If declining: curve goes down.
    // We'll use a cubic bezier for a smooth "organic" feel

    const getPath = () => {
        if (isStable) {
            return "M0,25 C20,25 40,25 60,25";
        }
        if (isRising) {
            // Curve up
            return "M0,40 C20,40 30,10 60,5";
        }
        // Curve down
        return "M0,10 C20,10 30,40 60,45";
    };

    return (
        <div className={cn("relative h-12 w-24 overflow-hidden", className)}>
            {/* Background Glow */}
            <div className={cn(
                "absolute inset-0 opacity-20 blur-xl",
                isStable ? "bg-gray-500" : isRising ? "bg-accent" : "bg-orange-500"
            )} />

            <svg
                viewBox="0 0 60 50"
                className="h-full w-full overflow-visible"
                preserveAspectRatio="none"
            >
                {/* Shadow Line */}
                <path
                    d={getPath()}
                    fill="none"
                    stroke="black"
                    strokeWidth="4"
                    strokeLinecap="round"
                    className="opacity-50 blur-[1px]"
                />

                {/* Main Line */}
                <path
                    d={getPath()}
                    fill="none"
                    className={cn("stroke-[3px]", strokeColor)}
                    strokeLinecap="round"
                    vectorEffect="non-scaling-stroke"
                />

                {/* End Dot */}
                {/* <circle 
          cx="60" 
          cy={isStable ? 25 : isRising ? 5 : 45} 
          r="3" 
          className={cn("fill-white", strokeColor)} 
        /> */}
            </svg>
        </div>
    );
};
