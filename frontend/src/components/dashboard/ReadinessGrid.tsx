'use client';

import React from 'react';
import { AlertCircle, CheckCircle2, Clock4, Layers, Server } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import type { SubsystemHealth } from '@/types/api';

interface ReadinessGridProps {
  subsystems: SubsystemHealth[];
}

export function ReadinessGrid({ subsystems }: ReadinessGridProps) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-md">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h3 className="font-mono text-base font-bold text-slate-100 flex items-center gap-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            Subsystem Architecture & Readiness Matrix
          </h3>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Registered operational services and progressive milestone allocation
          </p>
        </div>
        <Badge variant="cyan" className="font-mono text-xs">
          {subsystems.filter((s) => s.ready).length} of {subsystems.length} Ready
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        {subsystems.map((subsystem, index) => {
          const isOperational = subsystem.status === 'operational';
          const isStandby = subsystem.status === 'standby';

          return (
            <div
              key={index}
              className={`rounded-xl border p-4.5 transition-all ${
                isOperational
                  ? 'border-emerald-500/30 bg-emerald-950/10'
                  : isStandby
                  ? 'border-slate-800 bg-slate-950/60'
                  : 'border-amber-500/30 bg-amber-950/10'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div
                    className={`p-2 rounded-lg ${
                      isOperational
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : isStandby
                        ? 'bg-slate-800 text-slate-400'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}
                  >
                    {isOperational ? (
                      <CheckCircle2 className="w-4 h-4" />
                    ) : isStandby ? (
                      <Clock4 className="w-4 h-4" />
                    ) : (
                      <AlertCircle className="w-4 h-4" />
                    )}
                  </div>
                  <div>
                    <h4 className="font-mono text-sm font-semibold text-slate-200">
                      {subsystem.name}
                    </h4>
                    <span className="text-[11px] font-mono text-slate-400">
                      {isOperational ? 'Ready for Execution' : 'Reserved for Level 2/3'}
                    </span>
                  </div>
                </div>

                <Badge
                  variant={isOperational ? 'emerald' : isStandby ? 'slate' : 'amber'}
                  dot={isOperational}
                  pulse={isOperational}
                  className="capitalize"
                >
                  {subsystem.status}
                </Badge>
              </div>

              {subsystem.details && (
                <div className="mt-3 text-xs font-mono text-slate-400/90 bg-slate-950/80 rounded-lg p-2.5 border border-slate-800/80">
                  {subsystem.details}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
