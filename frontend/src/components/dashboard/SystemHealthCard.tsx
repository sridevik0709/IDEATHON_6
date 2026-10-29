'use client';

import React from 'react';
import { CheckCircle2, Clock, Cpu, Database, Server, ShieldCheck, Zap } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import type { HealthStatusData } from '@/types/api';

interface SystemHealthCardProps {
  health: HealthStatusData | null;
  latencyMs: number | null;
  error?: string | null;
}

export function SystemHealthCard({ health, latencyMs, error }: SystemHealthCardProps) {
  const isHealthy = health?.status === 'healthy';
  const isFallback = health?.status === 'operational_fallback';

  return (
    <div className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900/90 via-slate-900/50 to-slate-950 p-6 shadow-xl backdrop-blur-md">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div className="flex items-center gap-3.5">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.15)]">
            <ShieldCheck className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-lg font-mono font-bold tracking-wide text-slate-100">
                {health?.project || 'GRIDGUARD NEXUS X'}
              </h2>
              {isHealthy ? (
                <Badge variant="emerald" dot pulse>
                  SYSTEM OPERATIONAL
                </Badge>
              ) : isFallback ? (
                <Badge variant="amber" dot>
                  DEV FALLBACK ACTIVE
                </Badge>
              ) : error ? (
                <Badge variant="rose" dot>
                  COMMUNICATION FAULT
                </Badge>
              ) : (
                <Badge variant="cyan" dot pulse>
                  INITIALIZING
                </Badge>
              )}
            </div>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              {health?.stage || 'LEVEL 1: PROJECT FOUNDATION'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Badge variant="slate" className="text-xs">
            Core Version: {health?.version || '1.0.0-level1'}
          </Badge>
          <Badge variant="cyan" className="text-xs">
            Env: {health?.environment || 'development'}
          </Badge>
        </div>
      </div>

      {/* Grid of Key Telemetry Indicators */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6">
        {/* Gateway Uptime */}
        <div className="rounded-xl border border-slate-800/90 bg-slate-950/60 p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-1.5">
            <span>Gateway Uptime</span>
            <Clock className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-mono font-bold text-slate-100">
            {health ? `${health.uptime_seconds.toFixed(1)}s` : '—'}
          </div>
          <span className="text-[10px] font-mono text-slate-500">Continuous ASGI cycle</span>
        </div>

        {/* Handshake Latency */}
        <div className="rounded-xl border border-slate-800/90 bg-slate-950/60 p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-1.5">
            <span>Network Latency</span>
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-mono font-bold text-slate-100">
            {latencyMs !== null ? `${latencyMs} ms` : '—'}
          </div>
          <span className="text-[10px] font-mono text-emerald-500/80">Round-trip HTTP probe</span>
        </div>

        {/* Persistent Storage */}
        <div className="rounded-xl border border-slate-800/90 bg-slate-950/60 p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-1.5">
            <span>Storage Health</span>
            <Database className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-mono font-bold text-slate-100 capitalize">
            {health?.database.status || 'Checking...'}
          </div>
          <span className="text-[10px] font-mono text-slate-500 truncate block" title={health?.database.details || ''}>
            {health?.database.details || 'PostgreSQL Engine'}
          </span>
        </div>

        {/* Protocol Gateway */}
        <div className="rounded-xl border border-slate-800/90 bg-slate-950/60 p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-1.5">
            <span>Validation Core</span>
            <Cpu className="w-4 h-4 text-violet-400" />
          </div>
          <div className="text-xl font-mono font-bold text-slate-100">
            Pydantic v2
          </div>
          <span className="text-[10px] font-mono text-violet-400/80">Schema enforcement active</span>
        </div>
      </div>
    </div>
  );
}
