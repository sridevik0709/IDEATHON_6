'use client';

import React from 'react';
import {
  Activity,
  BarChart3,
  Cpu,
  Database,
  Layers,
  Radio,
  Server,
  ShieldAlert,
  Sparkles,
  Workflow,
  X,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { envConfig } from '@/lib/config';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  activeTab?: string;
  onSelectTab?: (tabId: string) => void;
  dbDialect?: string;
}

export function Sidebar({
  isOpen = false,
  onClose,
  activeTab = 'overview',
  onSelectTab,
  dbDialect = 'PostgreSQL',
}: SidebarProps) {
  const navItems = [
    {
      id: 'overview',
      label: 'Mission Dashboard',
      description: 'System health & foundation shell',
      icon: Activity,
      badge: 'Level 1 Active',
      badgeVariant: 'emerald' as const,
      disabled: false,
    },
    {
      id: 'diagnostics',
      label: 'API & Validation Console',
      description: 'Live payload verification',
      icon: Radio,
      badge: 'Interactive',
      badgeVariant: 'cyan' as const,
      disabled: false,
    },
    {
      id: 'telemetry',
      label: 'Telemetry Stream Ingest',
      description: 'Feeder voltage & current ingest',
      icon: Layers,
      badge: 'Level 2 Milestone',
      badgeVariant: 'slate' as const,
      disabled: true,
    },
    {
      id: 'accounting',
      label: 'Energy Accounting & Loss',
      description: 'Reconciliation & balancing',
      icon: BarChart3,
      badge: 'Level 2 Milestone',
      badgeVariant: 'slate' as const,
      disabled: true,
    },
    {
      id: 'forensics',
      label: 'AI Forensic Investigation',
      description: 'Theft anomaly classification',
      icon: Cpu,
      badge: 'Level 3 Milestone',
      badgeVariant: 'slate' as const,
      disabled: true,
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm md:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-800 bg-slate-950 transition-transform duration-200 ease-in-out md:static md:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Mobile Header Close */}
        <div className="flex h-16 items-center justify-between border-b border-slate-800 px-4 md:hidden">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-cyan-400" />
            <span className="font-mono text-sm font-bold text-slate-100">NAVIGATION</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Section Title */}
        <div className="px-5 pt-6 pb-2">
          <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-semibold">
            Operational Modules
          </div>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 space-y-1.5 px-3 py-2 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                disabled={item.disabled}
                onClick={() => {
                  if (onSelectTab && !item.disabled) {
                    onSelectTab(item.id);
                    if (onClose) onClose();
                  }
                }}
                className={`group flex w-full flex-col rounded-xl px-3.5 py-3 text-left transition-all ${
                  isActive
                    ? 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.1)]'
                    : item.disabled
                    ? 'opacity-40 cursor-not-allowed hover:bg-transparent border border-transparent'
                    : 'text-slate-300 hover:bg-slate-900 border border-transparent hover:border-slate-800'
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                    <span className="font-mono text-xs font-semibold tracking-wide">
                      {item.label}
                    </span>
                  </div>
                  <Badge variant={item.badgeVariant} className="text-[9px] py-0 px-1.5">
                    {item.badge}
                  </Badge>
                </div>
                <span className="mt-1 text-[11px] text-slate-500 pl-6 leading-tight">
                  {item.description}
                </span>
              </button>
            );
          })}
        </nav>

        {/* Architecture & Storage Environment Box */}
        <div className="border-t border-slate-800/80 p-4 bg-slate-900/40">
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3 text-[11px] font-mono space-y-2">
            <div className="flex items-center justify-between text-slate-400">
              <span className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-cyan-400" />
                Storage Engine:
              </span>
              <span className="text-slate-200 font-semibold">{dbDialect.toUpperCase()}</span>
            </div>

            <div className="flex items-center justify-between text-slate-400">
              <span className="flex items-center gap-1.5">
                <Workflow className="w-3.5 h-3.5 text-cyan-400" />
                Gateway Target:
              </span>
              <span className="text-slate-200 truncate max-w-[110px]" title={envConfig.apiBaseUrl}>
                {envConfig.apiBaseUrl}
              </span>
            </div>

            <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex items-center justify-between">
              <span>GridGuard Core</span>
              <span>v1.0.0-L1</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
