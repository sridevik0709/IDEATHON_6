'use client';

import React, { useEffect, useState } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Database,
  FileCheck2,
  FileText,
  Flame,
  Layers,
  Lock,
  Play,
  RefreshCw,
  Search,
  Server,
  ShieldAlert,
  Sparkles,
  Terminal,
  Workflow,
  Zap,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { gridGuardApi } from '@/lib/api';
import type {
  DataSourceItem,
  InvestigationCaseItem,
  ScenarioDescriptor,
  ScenarioExecutionResponse,
} from '@/types/api';

export function ScenariosExplorer() {
  const [scenarios, setScenarios] = useState<ScenarioDescriptor[]>([]);
  const [selectedCode, setSelectedCode] = useState<string>('SCENARIO_D');
  const [seed, setSeed] = useState<number>(42);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [lastExecution, setLastExecution] = useState<ScenarioExecutionResponse | null>(null);
  const [cases, setCases] = useState<InvestigationCaseItem[]>([]);
  const [dataSources, setDataSources] = useState<DataSourceItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const loadMetadata = async () => {
    try {
      const [scenariosRes, sourcesRes, casesRes] = await Promise.allSettled([
        gridGuardApi.getScenarios(),
        gridGuardApi.getDataSources(),
        gridGuardApi.getInvestigationCases(),
      ]);

      if (scenariosRes.status === 'fulfilled') {
        setScenarios(scenariosRes.value.data);
      }
      if (sourcesRes.status === 'fulfilled') {
        setDataSources(sourcesRes.value.data);
      }
      if (casesRes.status === 'fulfilled') {
        setCases(casesRes.value.data);
      }
    } catch (err: unknown) {
      console.warn('Metadata load error:', err);
    }
  };

  useEffect(() => {
    loadMetadata();
  }, []);

  const handleRunScenario = async () => {
    setIsRunning(true);
    setError(null);

    try {
      const res = await gridGuardApi.runScenario({
        scenario_code: selectedCode,
        seed: Number(seed) || 42,
        persist_to_database: true,
      });

      setLastExecution(res.data);
      // Reload cases after run
      const casesRes = await gridGuardApi.getInvestigationCases();
      setCases(casesRes.data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Scenario execution failed';
      setError(msg);
    } finally {
      setIsRunning(false);
    }
  };

  const selectedScenario = scenarios.find((s) => s.scenario_code === selectedCode);

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-slate-950 p-6 shadow-xl backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                <Workflow className="w-5 h-5 text-cyan-400" />
              </div>
              <h2 className="text-lg font-mono font-bold tracking-wide text-slate-100">
                Data Foundation & Five Repeatable Demonstration Scenarios
              </h2>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Deterministic generator, PostgreSQL persistent models, and multi-tier grid telemetry scenarios.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="cyan" dot pulse className="font-mono text-xs">
              LEVEL 2 ACTIVE
            </Badge>
          </div>
        </div>

        {/* 5 Scenario Selector Tabs */}
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-2.5 mt-5">
          {[
            { code: 'SCENARIO_A', label: 'A: Normal', badge: 'Balanced' },
            { code: 'SCENARIO_B', label: 'B: Delayed', badge: 'Lag' },
            { code: 'SCENARIO_C', label: 'C: Mismap', badge: 'GIS Fault' },
            { code: 'SCENARIO_D', label: 'D: Theft Gap', badge: 'Theft Case' },
            { code: 'SCENARIO_E', label: 'E: Quality', badge: 'Corrupt' },
          ].map((tab) => {
            const isSelected = selectedCode === tab.code;
            return (
              <button
                key={tab.code}
                type="button"
                onClick={() => setSelectedCode(tab.code)}
                className={`flex flex-col items-start rounded-xl p-3 text-left transition-all font-mono text-xs border ${
                  isSelected
                    ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300 shadow-[0_0_15px_rgba(6,182,212,0.15)]'
                    : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                }`}
              >
                <span className="font-bold text-[13px]">{tab.label}</span>
                <span className="text-[10px] text-slate-500 mt-0.5">{tab.badge}</span>
              </button>
            );
          })}
        </div>

        {/* Selected Scenario Details & Run Trigger */}
        {selectedScenario && (
          <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/70 p-5 font-mono text-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
              <div>
                <h3 className="font-bold text-sm text-cyan-300">{selectedScenario.scenario_name}</h3>
                <p className="text-slate-400 mt-1 font-sans text-xs">{selectedScenario.description}</p>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-300">
                  <span className="text-[10px] text-slate-500">Seed:</span>
                  <input
                    type="number"
                    value={seed}
                    onChange={(e) => setSeed(parseInt(e.target.value, 10) || 42)}
                    className="w-14 bg-transparent text-cyan-300 focus:outline-none text-xs font-bold"
                  />
                </div>

                <button
                  type="button"
                  onClick={handleRunScenario}
                  disabled={isRunning}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 disabled:opacity-50 transition-all"
                >
                  {isRunning ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Executing...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-current" />
                      Execute Scenario
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Documented Inputs & Expected Outcomes Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 text-[11px]">
              <div className="bg-black/30 rounded-lg p-3 border border-slate-800/80">
                <span className="text-slate-400 font-bold uppercase text-[10px] block mb-2 text-cyan-400">
                  Documented Inputs:
                </span>
                <pre className="text-slate-300 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(selectedScenario.documented_inputs, null, 2)}
                </pre>
              </div>

              <div className="bg-black/30 rounded-lg p-3 border border-slate-800/80">
                <span className="text-slate-400 font-bold uppercase text-[10px] block mb-2 text-emerald-400">
                  Expected Outcomes:
                </span>
                <pre className="text-slate-300 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(selectedScenario.expected_outcomes, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4">
            <ErrorAlert message={error} code="ERR_SCENARIO_RUN_FAILED" onRetry={handleRunScenario} />
          </div>
        )}
      </div>

      {/* Execution Results View */}
      {lastExecution && (
        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/10 p-6 backdrop-blur-md font-mono text-xs">
          <div className="flex items-center justify-between pb-4 border-b border-emerald-500/20">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <span>Scenario Execution Completed & Persisted</span>
            </div>
            <Badge variant="emerald" dot>
              {lastExecution.status}
            </Badge>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
            <div className="p-3 bg-black/40 rounded-lg border border-slate-800">
              <span className="text-slate-400 text-[10px] block">Generated Records</span>
              <span className="text-lg font-bold text-slate-100">{lastExecution.records_generated_count}</span>
            </div>

            <div className="p-3 bg-black/40 rounded-lg border border-slate-800">
              <span className="text-slate-400 text-[10px] block">Anomalies Detected</span>
              <span className="text-lg font-bold text-amber-400">{lastExecution.anomaly_count}</span>
            </div>

            <div className="p-3 bg-black/40 rounded-lg border border-slate-800">
              <span className="text-slate-400 text-[10px] block">Cases Generated</span>
              <span className="text-lg font-bold text-cyan-400">{lastExecution.cases_generated_count}</span>
            </div>

            <div className="p-3 bg-black/40 rounded-lg border border-slate-800">
              <span className="text-slate-400 text-[10px] block">Execution Seed</span>
              <span className="text-lg font-bold text-slate-300">{lastExecution.seed}</span>
            </div>
          </div>

          {lastExecution.summary_metrics && (
            <div className="mt-4 p-3 bg-black/50 rounded-lg border border-slate-800 text-[11px]">
              <span className="text-slate-400 font-bold block mb-1">Physics & Accounting Summary Metrics:</span>
              <pre className="text-emerald-300 overflow-x-auto">
                {JSON.stringify(lastExecution.summary_metrics, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Forensic Investigation Case Dockets & Evidence Records */}
      {cases.length > 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-md">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h3 className="font-mono text-base font-bold text-slate-100 flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-400" />
                Active Investigation Cases & Evidence Records
              </h3>
              <p className="text-xs text-slate-400 font-mono mt-1">
                Forensic dockets with cryptographic SHA-256 evidence digests and financial recovery valuations.
              </p>
            </div>
            <Badge variant="amber">{cases.length} Dockets Registered</Badge>
          </div>

          <div className="mt-5 space-y-4">
            {cases.map((c) => (
              <div
                key={c.id}
                className="rounded-xl border border-slate-800 bg-slate-950/80 p-5 font-mono text-xs space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800/80">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-cyan-400 text-sm">{c.case_number}</span>
                    <span className="text-slate-200">— {c.title}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={c.priority === 'CRITICAL' ? 'rose' : 'amber'}>
                      {c.priority}
                    </Badge>
                    <Badge variant="cyan">{c.status}</Badge>
                  </div>
                </div>

                <p className="text-slate-400 font-sans text-xs">{c.summary}</p>

                {/* Evidence Records */}
                {c.evidence && c.evidence.length > 0 && (
                  <div className="mt-3 bg-black/40 rounded-lg p-3 border border-slate-800/80 space-y-2">
                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span className="font-bold flex items-center gap-1.5 text-slate-300">
                        <Lock className="w-3.5 h-3.5 text-cyan-400" />
                        Cryptographic Evidence Record (Non-Repudiation)
                      </span>
                      <span className="text-[10px] text-slate-500">Collected: {c.evidence[0].collected_at}</span>
                    </div>

                    <div className="text-[11px] text-slate-300">
                      <strong>Title:</strong> {c.evidence[0].title}
                    </div>

                    <div className="flex items-center gap-2 text-[10px] text-slate-400 bg-slate-950 p-2 rounded border border-slate-800">
                      <span className="text-cyan-400 font-bold shrink-0">SHA-256 Digest:</span>
                      <code className="text-slate-300 truncate font-mono">{c.evidence[0].hash_sha256}</code>
                    </div>
                  </div>
                )}

                {/* Outcome & Recovery */}
                {c.outcome && (
                  <div className="mt-2 bg-emerald-950/20 rounded-lg p-3 border border-emerald-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <span className="text-emerald-400 font-bold block text-[11px]">
                        Resolution: {c.outcome.outcome_type}
                      </span>
                      <span className="text-slate-400 text-[11px]">{c.outcome.action_taken}</span>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-[10px] text-slate-500 block">Estimated Recovery</span>
                      <span className="text-base font-bold text-emerald-400">
                        ₹{c.outcome.estimated_financial_loss_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Source Architecture Cards */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-md">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h3 className="font-mono text-base font-bold text-slate-100 flex items-center gap-2">
              <Server className="w-5 h-5 text-cyan-400" />
              Common Data-Source Architecture Adapters
            </h3>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Uniform interfaces across synthetic generators, local datasets, and real utility integrations.
            </p>
          </div>
          <Badge variant="cyan">{dataSources.length} Adapters Registered</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
          {dataSources.map((ds, idx) => (
            <div
              key={idx}
              className={`rounded-xl border p-4 font-mono text-xs space-y-2.5 ${
                ds.is_authorized
                  ? 'border-emerald-500/30 bg-emerald-950/10'
                  : 'border-slate-800 bg-slate-950/60'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-200">{ds.name}</span>
                <Badge variant={ds.is_authorized ? 'emerald' : 'slate'}>
                  {ds.is_authorized ? 'Authorized' : 'Unconfigured'}
                </Badge>
              </div>

              <div className="text-[11px] text-slate-400 space-y-1">
                <div>
                  <span className="text-slate-500">Code:</span> <code>{ds.code}</code>
                </div>
                <div>
                  <span className="text-slate-500">Type:</span> <code>{ds.source_type}</code>
                </div>
              </div>

              <div className="text-[10px] text-slate-500 pt-2 border-t border-slate-800/80">
                {ds.is_authorized
                  ? '✓ Built-in authorized adapter'
                  : '⚠ Awaiting authorized utility API token'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

