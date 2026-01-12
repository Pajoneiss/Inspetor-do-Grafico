"use client";

import React, { useState, useEffect } from 'react';
import { Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CalendarEvent {
    event: string;
    date: string;
    time?: string;
    importance?: string;
    estimate?: string;
    previous?: string;
}

export default function EconomicCalendarWidget() {
    const [events, setEvents] = useState<CalendarEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

    useEffect(() => {
        const fetchCalendar = async () => {
            if (!API_URL) {
                setLoading(false);
                return;
            }
            try {
                const res = await fetch(`${API_URL}/api/economic-calendar?days=7`);
                const data = await res.json();
                if (data.events) {
                    setEvents(data.events);
                }
            } catch (err) {
                console.error("Calendar fetch error:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchCalendar();
    }, [API_URL]);

    if (loading) {
        return (
            <div className="flex items-center justify-center w-full h-full text-white/30">
                <div className="w-6 h-6 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    if (events.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center w-full h-full text-white/30 text-xs">
                <Calendar className="w-8 h-8 mb-2 opacity-50" />
                <span>No upcoming events</span>
            </div>
        );
    }

    return (
        <div className="w-full h-full overflow-y-auto pr-2 custom-scrollbar">
            <div className="space-y-2">
                {events.map((event, i) => (
                    <div
                        key={i}
                        className={cn(
                            "p-3 rounded-lg bg-white/5 border-l-2",
                            event.importance === "HIGH" ? "border-red-500" : "border-yellow-500"
                        )}
                    >
                        <div className="flex justify-between items-start gap-4">
                            <span className="font-medium text-xs text-white/90">{event.event || "Unknown"}</span>
                            <span className="text-[10px] text-white/50 whitespace-nowrap bg-white/5 px-1.5 py-0.5 rounded">
                                {event.date !== "TBD" ? new Date(event.date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "TBD"} {event.time || ""}
                            </span>
                        </div>
                        {(event.estimate || event.previous) && (
                            <div className="flex gap-3 mt-1.5 text-[10px] text-white/40">
                                {event.estimate && <span>Est: <span className="text-white/60">{event.estimate}</span></span>}
                                {event.previous && <span>Prev: <span className="text-white/60">{event.previous}</span></span>}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
