'use client';

import React, { useEffect, useState } from 'react';
import { Activity, Clock, Menu, RefreshCw, Shield, Wifi, WifiOff } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { envConfig } from '@/lib/config';

interface HeaderProps {
  isConnected: boolean;
  isChecking: boolean;
  latencyMs: number | null;
  lastChecked: Date | null;
  onRefresh: () => void;
  onToggleSidebar?: () => void;
}

export function Header({
  isConnected,
  isChecking,
  latencyMs,
  lastChecked,
  onRefresh,
  onToggleSidebar,
}: HeaderProps) {
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setCurrentTime(now.toUTCString().replace('GMT', 'UTC'));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-800 bg-slate-950/80 px-4 md:px-6 backdrop-blur-md">
      {/* Left: Mobile trigger & Project branding */}
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button
            type="button"
            onClick={onToggleSidebar}
            className="md:hidden p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
            aria-label="Toggle navigation"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-500/40 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.15)]">
            <Shield className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-mono text-sm md:text-base font-bold tracking-wider text-slate-100">
                GRIDGUARD <span className="text-cyan-400">NEXUS X</span>
              </h1>
              <Badge variant="cyan" className="hidden sm:inline-flex text-[10px]">
                LEVEL 1
              </Badge>
            </div>
            <p className="text-[10px] font-mono text-slate-400 hidden sm:block">
              Electricity Intelligence & Forensic Investigation Platform
            </p>
          </div>
        </div>
      </div>

      {/* Right: Live Telemetry Status, Clock & Actions */}
      <div className="flex items-center gap-2.5 md:gap-4">
        {/* Real-time UTC Clock */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span>{currentTime || 'Synchronizing Clock...'}</span>
        </div>

        {/* Backend Connection Live Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 font-mono text-xs">
          {isConnected ? (
            <>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
              </span>
              <span className="text-emerald-400 font-medium hidden sm:inline">LIVE LINK</span>
              {latencyMs !== null && (
                <span className="text-slate-400 text-[11px] pl-1 border-l border-slate-700">
                  {latencyMs}ms
                </span>
              )}
            </>
          ) : isChecking ? (
            <>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-400" />
              </span>
              <span className="text-amber-400 font-medium">CONNECTING</span>
            </>
          ) : (
            <>
              <span className="relative flex h-2 w-2">
                <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500" />
              </span>
              <span className="text-rose-400 font-medium">OFFLINE</span>
            </>
          )}
        </div>

        {/* Refresh Handshake Button */}
        <button
          type="button"
          onClick={onRefresh}
          disabled={isChecking}
          title="Refresh backend telemetry handshake"
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 hover:text-cyan-400 hover:border-cyan-500/40 disabled:opacity-50 transition-colors"
          aria-label="Refresh telemetry status"
        >
          <RefreshCw className={`w-4 h-4 ${isChecking ? 'animate-spin text-cyan-400' : ''}`} />
        </button>
      </div>
    </header>
  );
}
