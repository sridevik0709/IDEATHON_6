'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Database,
  ExternalLink,
  Flame,
  Info,
  Layers,
  Radio,
  Server,
  Shield,
  Zap,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { LoadingState } from '@/components/ui/LoadingSpinner';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { ReadinessGrid } from '@/components/dashboard/ReadinessGrid';
import { SystemHealthCard } from '@/components/dashboard/SystemHealthCard';
import { ValidationConsole } from '@/components/dashboard/ValidationConsole';
import { envConfig } from '@/lib/config';
import { gridGuardApi } from '@/lib/api';
import type { HealthStatusData, VersionInfoData } from '@/types/api';

export function OverviewDashboard() {
  const [health, setHealth] = useState<HealthStatusData | null>(null);
  const [version, setVersion] = useState<VersionInfoData | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>('overview');

  const fetchStatus = useCallback(async (silent = false) => {
    if (!silent) setIsRefreshing(true);
    setError(null);

    try {
      const [healthRes, versionRes] = await Promise.all([
        gridGuardApi.getHealth(),
        gridGuardApi.getVersion(),
      ]);

      setHealth(healthRes.data);
      setVersion(versionRes.data);
      setLatencyMs(healthRes.latencyMs);
      setLastChecked(new Date());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown communication error';
      setError(msg);
      setLatencyMs(null);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(() => {
      fetchStatus(true);
    }, envConfig.pollIntervalMs);

    return () => clearInterval(interval);
  }, [fetchStatus]);

  const isConnected = !!health && !error;
  const storageDialect = health?.database?.details?.includes('Dialect: sqlite')
    ? 'SQLite (Dev Fallback)'
    : health?.database?.details?.includes('Dialect: postgresql')
    ? 'PostgreSQL'
    : 'Configured Storage';

  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activeTab={activeTab}
        onSelectTab={(tabId) => setActiveTab(tabId)}
        dbDialect={storageDialect}
      />

      {/* Main Content Pane */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header */}
        <Header
          isConnected={isConnected}
          isChecking={isRefreshing}
          latencyMs={latencyMs}
          lastChecked={lastChecked}
          onRefresh={() => fetchStatus()}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />

        {/* Scrollable Dashboard Body */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
          {/* Top Banner: Stage Identifier */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-cyan-500/20 bg-cyan-950/10 text-cyan-200">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-400 shrink-0">
                <Zap className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold uppercase tracking-wider text-cyan-400">
                    National Ideathon Milestone:
                  </span>
                  <Badge variant="cyan" className="text-[10px]">
                    LEVEL 1 ONLY
                  </Badge>
                </div>
                <p className="text-xs text-slate-300 font-sans mt-0.5">
                  Full-stack software foundation with decoupled domain boundaries, FastAPI ASGI gateway, and Pydantic validation.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto font-mono text-xs">
              <span className="text-slate-400">Gateway:</span>
              <code className="px-2 py-0.5 rounded bg-black/40 text-cyan-300 border border-cyan-900/40">
                {envConfig.apiBaseUrl}
              </code>
            </div>
          </div>

          {/* Error Alert if Disconnected */}
          {error && (
            <ErrorAlert
              title="FastAPI Backend Disconnected"
              message={error}
              code="ERR_BACKEND_UNREACHABLE"
              onRetry={() => fetchStatus()}
            />
          )}

          {/* Initial Loading Skeleton */}
          {isLoading ? (
            <LoadingState message="Establishing Handshake with GridGuard Nexus Core..." />
          ) : (
            <>
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  {/* System Health Card */}
                  <SystemHealthCard
                    health={health}
                    latencyMs={latencyMs}
                    error={error}
                  />

                  {/* High-Integrity Ideathon Notice (Zero Fabricated Statistics) */}
                  <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-5 backdrop-blur-sm">
                    <div className="flex items-start gap-3.5">
                      <div className="p-2 rounded-lg bg-slate-800 text-cyan-400 shrink-0">
                        <Info className="w-5 h-5" />
                      </div>
                      <div className="text-xs text-slate-300 leading-relaxed space-y-1">
                        <h4 className="font-mono font-bold text-sm text-slate-100 flex items-center gap-2">
                          Engineering Integrity Notice: Zero Fabricated Statistics
                          <Badge variant="emerald" className="text-[9px]">
                            Verified
                          </Badge>
                        </h4>
                        <p className="text-slate-400">
                          In accordance with Level 1 constraints, this dashboard shell deliberately does not render fake energy savings, mocked theft percentages, or synthetic anomaly dials.
                          Energy accounting algorithms, loss calculation engines, and live smart-meter stream processing are scheduled for progressive deployment in <strong>Level 2</strong> and <strong>Level 3</strong>.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Readiness Subsystems Grid */}
                  {health?.subsystems && (
                    <ReadinessGrid subsystems={health.subsystems} />
                  )}
                </div>
              )}

              {activeTab === 'diagnostics' && (
                <ValidationConsole />
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
