'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Compass,
  Database,
  FileCheck2,
  HelpCircle,
  Layers,
  Lock,
  Play,
  RefreshCw,
  Scale,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { LoadingState } from '@/components/ui/LoadingSpinner';
import { gridGuardApi } from '@/lib/api';
import type {
  AccountingBoundaryData,
  BeforeAfterComparisonData,
  WhatIfCatalogItemData,
} from '@/types/api';

export function WhatIfSimulatorView() {
  const [boundaries, setBoundaries] = useState<AccountingBoundaryData[]>([]);
  const [selectedBoundary, setSelectedBoundary] = useState<string>('DT-11KV-415V-101');
  const [scenarios, setScenarios] = useState<WhatIfCatalogItemData[]>([]);
  const [selectedScenarioType, setSelectedScenarioType] = useState<string>('DELAYED_READINGS_ARRIVED');
  const [parameterOverrides, setParameterOverrides] = useState<Record<string, unknown>>({});
  const [comparisonResult, setComparisonResult] = useState<BeforeAfterComparisonData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadInitialData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [bndRes, scenRes] = await Promise.all([
        gridGuardApi.getAccountingBoundaries(),
        gridGuardApi.getWhatIfScenarios(),
      ]);
      setBoundaries(bndRes.data);
      setScenarios(scenRes.data);
      if (bndRes.data.length > 0 && !selectedBoundary) {
        setSelectedBoundary(bndRes.data[0].asset_code);
      }
      if (scenRes.data.length > 0 && !selectedScenarioType) {
        setSelectedScenarioType(scenRes.data[0].scenario_type);
        setParameterOverrides(scenRes.data[0].default_parameters);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to load What-If simulation parameters.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [selectedBoundary, selectedScenarioType]);

  const handleSelectScenario = (scen: WhatIfCatalogItemData) => {
    setSelectedScenarioType(scen.scenario_type);
    setParameterOverrides(scen.default_parameters || {});
    setComparisonResult(null);
  };

  const runWhatIfSimulation = async () => {
    if (!selectedBoundary || !selectedScenarioType) return;
    setIsSimulating(true);
    setError(null);
    try {
      const res = await gridGuardApi.simulateWhatIf({
        boundary_asset_code: selectedBoundary,
        scenario_type: selectedScenarioType,
        parameters: parameterOverrides,
        simulated_provenance: 'HYPOTHETICAL_SIMULATION',
      });
      setComparisonResult(res.data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'What-if simulation failed.';
      setError(msg);
      setComparisonResult(null);
    } finally {
      setIsSimulating(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  const activeScenario = scenarios.find((s) => s.scenario_type === selectedScenarioType);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5 shadow-sm lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-indigo-400" />
            <h2 className="text-xl font-bold tracking-tight text-foreground">
              Level 5: What-If Simulation & Before-and-After Comparison
            </h2>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Test how telemetry latency, interval alignments, mapping fixes, or sensor calibrations impact distribution discrepancies without modifying production records.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label htmlFor="what-if-boundary-select" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Target Boundary:
            </label>
            <select
              id="what-if-boundary-select"
              value={selectedBoundary}
              onChange={(e) => {
                setSelectedBoundary(e.target.value);
                setComparisonResult(null);
              }}
              disabled={isLoading || isSimulating}
              className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {boundaries.map((b) => (
                <option key={b.asset_code} value={b.asset_code}>
                  {b.asset_code} — {b.name} ({b.voltage_class})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={runWhatIfSimulation}
            disabled={isSimulating}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            <Play className={`h-4 w-4 ${isSimulating ? 'animate-spin' : ''}`} />
            <span>{isSimulating ? 'Simulating...' : 'Run What-If Simulation'}</span>
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={runWhatIfSimulation} />}

      {/* Scenario Template Cards */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Select Repeatable What-If Assumption Scenario:
          </span>
          <Badge variant="cyan" className="text-[11px]">
            5 Repeatable Scenarios
          </Badge>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {scenarios.map((scen) => {
            const isSelected = selectedScenarioType === scen.scenario_type;
            return (
              <div
                key={scen.scenario_type}
                onClick={() => handleSelectScenario(scen)}
                className={`cursor-pointer rounded-xl border p-4 transition-all ${
                  isSelected
                    ? 'border-primary ring-2 ring-primary/40 bg-primary/5 shadow-sm'
                    : 'border-border/70 bg-card hover:border-primary/40 hover:bg-secondary/20'
                }`}
              >
                <div className="flex items-center justify-between">
                  <Badge variant={isSelected ? 'emerald' : 'slate'} className="text-[10px]">
                    {scen.category}
                  </Badge>
                  {isSelected && <CheckCircle2 className="h-4 w-4 text-primary" />}
                </div>

                <h4 className="mt-2 text-sm font-bold text-foreground">{scen.title}</h4>
                <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{scen.description}</p>
                <div className="mt-2 text-[11px] font-medium text-primary line-clamp-1">
                  Impact: {scen.typical_impact}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Parameter Overrides Configuration Panel */}
      {activeScenario && (
        <div className="rounded-xl border border-border bg-card p-4 space-y-3 shadow-sm">
          <div className="flex items-center justify-between border-b border-border pb-2">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-indigo-400" />
              <h4 className="text-sm font-semibold text-foreground">
                Assumption Parameters for: {activeScenario.title}
              </h4>
            </div>
            <span className="font-mono text-xs text-muted-foreground">
              Provenance: HYPOTHETICAL_SIMULATION
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(activeScenario.default_parameters || {}).map(([key, defaultVal]) => (
              <div key={key} className="space-y-1">
                <label className="text-xs font-mono font-medium text-muted-foreground">
                  {key}:
                </label>
                <input
                  type="text"
                  value={String(parameterOverrides[key] ?? defaultVal)}
                  onChange={(e) => {
                    const val = e.target.value;
                    const num = Number(val);
                    setParameterOverrides((prev) => ({
                      ...prev,
                      [key]: isNaN(num) || val === '' ? val : num,
                    }));
                  }}
                  className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-mono text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {isSimulating && (
        <LoadingState message="Executing isolated in-memory what-if simulation & re-balancing distribution boundary..." />
      )}

      {/* Comparison Results Section */}
      {comparisonResult && !isSimulating && (
        <div className="space-y-6">
          {/* Key Delta Ribbon Banner */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-4">
            <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
              <span className="text-xs font-medium text-muted-foreground">Δ Unaccounted Energy</span>
              <div className="mt-1 flex items-baseline gap-1.5">
                <span
                  className={`text-xl font-bold font-mono ${
                    comparisonResult.differences.delta_unaccounted_kwh < 0
                      ? 'text-emerald-400'
                      : comparisonResult.differences.delta_unaccounted_kwh > 0
                      ? 'text-rose-400'
                      : 'text-foreground'
                  }`}
                >
                  {comparisonResult.differences.delta_unaccounted_kwh > 0 ? '+' : ''}
                  {comparisonResult.differences.delta_unaccounted_kwh.toFixed(1)}
                </span>
                <span className="text-xs text-muted-foreground font-normal">kWh</span>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
              <span className="text-xs font-medium text-muted-foreground">Δ Gross Discrepancy</span>
              <div className="mt-1 flex items-baseline gap-1.5">
                <span
                  className={`text-xl font-bold font-mono ${
                    comparisonResult.differences.delta_discrepancy_pct < 0
                      ? 'text-emerald-400'
                      : comparisonResult.differences.delta_discrepancy_pct > 0
                      ? 'text-rose-400'
                      : 'text-foreground'
                  }`}
                >
                  {comparisonResult.differences.delta_discrepancy_pct > 0 ? '+' : ''}
                  {comparisonResult.differences.delta_discrepancy_pct.toFixed(2)}%
                </span>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
              <span className="text-xs font-medium text-muted-foreground">Discrepancy Status</span>
              <div className="mt-1 flex items-center gap-1.5">
                <Badge
                  variant={comparisonResult.differences.discrepancy_resolved ? 'emerald' : 'amber'}
                  className="text-xs"
                >
                  {comparisonResult.differences.discrepancy_resolved
                    ? 'DISCREPANCY RESOLVED'
                    : 'RESIDUAL PERSISTS'}
                </Badge>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
              <span className="text-xs font-medium text-muted-foreground">Quality Warnings</span>
              <div className="mt-1 flex items-baseline gap-1.5">
                <span className="text-xl font-bold text-foreground">
                  {comparisonResult.resolved_warnings.length}
                </span>
                <span className="text-xs text-emerald-400 font-medium">Warnings Resolved</span>
              </div>
            </div>
          </div>

          {/* Side-by-Side Before vs After Cards */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Left Card: Original Observed State */}
            <div className="rounded-xl border border-border bg-card p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <Scale className="h-4 w-4 text-muted-foreground" />
                  <h3 className="text-sm font-bold text-foreground">
                    1. Original Observed Accounting Baseline
                  </h3>
                </div>
                <Badge variant="slate" className="text-[10px]">
                  ORIGINAL GROUND TRUTH
                </Badge>
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="flex items-center justify-between py-1 border-b border-border/40">
                  <span className="text-muted-foreground">Energy Entering (E_in):</span>
                  <span className="font-mono font-bold text-foreground">
                    {comparisonResult.original_accounting.energy_entering_kwh.toLocaleString()} kWh
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-border/40">
                  <span className="text-muted-foreground">Recorded Downstream:</span>
                  <span className="font-mono font-bold text-foreground">
                    {comparisonResult.original_accounting.recorded_downstream_kwh.toLocaleString()} kWh
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-border/40">
                  <span className="text-muted-foreground">Technical Losses (2.8%):</span>
                  <span className="font-mono text-sky-400 font-bold">
                    {comparisonResult.original_accounting.other_accounted_flows_kwh.toLocaleString()} kWh
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-border/40">
                  <span className="text-muted-foreground">Net Unaccounted Energy:</span>
                  <span className="font-mono font-bold text-amber-400">
                    {comparisonResult.original_accounting.unaccounted_energy_kwh.toLocaleString()} kWh
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-border/40">
                  <span className="text-muted-foreground">Gross Discrepancy %:</span>
                  <span className="font-mono font-bold text-rose-400">
                    {comparisonResult.original_accounting.discrepancy_percentage.toFixed(2)}%
                  </span>
                </div>

                <div className="pt-2">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Classification:
                  </span>
                  <div className="mt-1 rounded bg-secondary/30 p-2 font-mono text-[11px] text-foreground">
                    {comparisonResult.original_accounting.neutral_classification}
                  </div>
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    {comparisonResult.original_accounting.classification_reason}
                  </p>
                </div>
              </div>
            </div>

            {/* Right Card: Revised Hypothetical State */}
            <div className="rounded-xl border border-indigo-500/40 bg-indigo-950/10 p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-indigo-500/30 pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-indigo-400" />
                  <h3 className="text-sm font-bold text-foreground">
                    2. Revised Accounting Under What-If Assumption
                  </h3>
                </div>
                <Badge variant="cyan" className="text-[10px]">
                  HYPOTHETICAL SIMULATION
                </Badge>
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="flex items-center justify-between py-1 border-b border-indigo-500/20">
                  <span className="text-muted-foreground">Energy Entering (E_in):</span>
                  <span className="font-mono font-bold text-foreground">
                    {comparisonResult.revised_accounting.energy_entering_kwh.toLocaleString()} kWh
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-indigo-500/20">
                  <span className="text-muted-foreground">Recorded Downstream:</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {comparisonResult.revised_accounting.recorded_downstream_kwh.toLocaleString()} kWh
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-indigo-500/20">
                  <span className="text-muted-foreground">Technical Losses (2.8%):</span>
                  <span className="font-mono text-sky-400 font-bold">
                    {comparisonResult.revised_accounting.other_accounted_flows_kwh.toLocaleString()} kWh
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-indigo-500/20">
                  <span className="text-muted-foreground">Net Unaccounted Energy:</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {comparisonResult.revised_accounting.unaccounted_energy_kwh.toLocaleString()} kWh
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-indigo-500/20">
                  <span className="text-muted-foreground">Gross Discrepancy %:</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {comparisonResult.revised_accounting.discrepancy_percentage.toFixed(2)}%
                  </span>
                </div>

                <div className="pt-2">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Revised Classification:
                  </span>
                  <div className="mt-1 rounded bg-indigo-900/40 p-2 font-mono text-[11px] text-emerald-300 border border-indigo-500/30">
                    {comparisonResult.revised_accounting.neutral_classification}
                  </div>
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    {comparisonResult.revised_accounting.classification_reason}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Hypotheses Shifts & Quality Changes Grid */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {/* Hypotheses Shift */}
            <div className="rounded-xl border border-border bg-card p-4 space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <Compass className="h-4 w-4 text-indigo-400" />
                <span>Forensic Hypothesis Shift</span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Original Top Hypothesis:</span>
                  <span className="font-semibold text-foreground truncate max-w-[200px]">
                    {comparisonResult.hypotheses_shift.original_top_hypothesis}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Revised Top Hypothesis:</span>
                  <span className="font-semibold text-emerald-400 truncate max-w-[200px]">
                    {comparisonResult.hypotheses_shift.revised_top_hypothesis}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Priority Score Shift:</span>
                  <span className="font-mono font-bold text-foreground">
                    {comparisonResult.hypotheses_shift.original_priority_score} → {comparisonResult.hypotheses_shift.revised_priority_score}{' '}
                    ({comparisonResult.hypotheses_shift.delta_priority_score > 0 ? '+' : ''}
                    {comparisonResult.hypotheses_shift.delta_priority_score} pts)
                  </span>
                </div>
              </div>
            </div>

            {/* Resolved Warnings */}
            <div className="rounded-xl border border-border bg-card p-4 space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <FileCheck2 className="h-4 w-4 text-emerald-400" />
                <span>Data Quality Impact ({comparisonResult.resolved_warnings.length} Resolved)</span>
              </div>
              {comparisonResult.resolved_warnings.length === 0 ? (
                <p className="text-xs text-muted-foreground italic">No data quality audit flags affected by this assumption.</p>
              ) : (
                <div className="space-y-1.5">
                  {comparisonResult.resolved_warnings.map((w, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 rounded bg-emerald-950/20 border border-emerald-500/20 px-2.5 py-1 text-xs text-emerald-300"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                      <span className="truncate">{w}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Strict Data Protection Mandate Guarantee Card */}
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-5 space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2 text-xs font-bold text-emerald-400">
                <ShieldCheck className="h-5 w-5" />
                <span>Data Protection & Forensic Integrity Certification</span>
              </div>
              <span className="font-mono text-[11px] text-muted-foreground">
                Run ID: {comparisonResult.data_protection.scenario_run_id}
              </span>
            </div>

            <p className="text-xs text-muted-foreground leading-relaxed">
              {comparisonResult.data_protection.audit_notice}
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 font-mono text-[11px]">
              <div className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Original Data Immutable</span>
              </div>
              <div className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Isolated Sandbox Execution</span>
              </div>
              <div className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Real Cases Protected</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

