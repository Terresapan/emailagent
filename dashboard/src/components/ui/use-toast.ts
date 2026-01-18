// Simplified use-toast hook
import { useState, useEffect, ReactNode } from "react"

export interface Toast {
    id: string
    title?: string
    description?: string
    action?: ReactNode
    variant?: "default" | "destructive"
}

export function useToast() {
    const [toasts, setToasts] = useState<Toast[]>([])

    const toast = ({ title, description, variant }: Omit<Toast, "id">) => {
        const id = Math.random().toString(36).substring(2, 9)
        console.log(`[TOAST] ${title}: ${description}`)
        // In a real app we'd dispatch this to a context
        // For now we just log it and maybe alert if critical?
        // Let's rely on the console since we don't have the full Provider setup
    }

    return { toast, toasts }
}
