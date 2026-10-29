'use client';

import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Calculator,
  CheckCircle2,
  Cpu,
  Database,
  FileText,
  Info,
  Layers,
  Percent,
  RefreshCw,
  Scale,
  ShieldAlert,
  Zap,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { LoadingState } from '@/components/ui/LoadingSpinner';
import { gridGuardApi } from '@/lib/api';
import type {
  AccountingBoundaryData,
  AccountingDossierData,
} from '@/types/api';

export function DiscrepancyExplorer() {
  const [boundaries, setBoundaries] = useState<AccountingBoundaryData[]>([]);
  const [selectedBoundary, setSelectedBoundary] = useState<string>('DT-11KV-415V-101');
  const [dossier, setDossier] = useState<AccountingDossierData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isReconciling, setIsReconciling] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadBoundaries() {
      setIsLoading(true);
      try {
        const res = await gridGuardApi.getAccountingBoundaries();
        setBoundaries(res.data);
        if (res.data.length > 0 && !selectedBoundary) {
          setSelectedBoundary(res.data[0].asset_code);
        }
      } catch (err: any) {
        setError(err.message || 'Unable to load network accounting boundaries.');
      } finally {
        setIsLoading(false);
      }
    }
    loadBoundaries();
  }, []);

  const runReconciliation = async (assetCode: string) => {
    setIsReconciling(true);
    setError(null);
    try {
      const res = await gridGuardApi.reconcileBoundary(assetCode);
      setDossier(res.data);
    } catch (err: any) {
      setError(err.message || 'Energy accounting calculation failed.');
      setDossier(null);
    } finally {
      setIsReconciling(false);
    }
  };

  useEffect(() => {
    if (selectedBoundary) {
      runReconciliation(selectedBoundary);
    }
  }, [selectedBoundary]);

  const getClassificationBadge = (cls: string) => {
    switch (cls) {
      case 'NORMAL_TECHNICAL_LOSS':
        return <Badge variant="emerald">NORMAL TECHNICAL LOSS</Badge>;
      case 'DATA_QUALITY_OR_LATENCY_UNCERTAINTY':
        return <Badge variant="amber">DATA QUALITY / LATENCY</Badge>;
      case 'TOPOLOGICAL_MAPPING_MISMATCH':
        return <Badge variant="cyan">TOPOLOGY MISMATCH (GIS)</Badge>;
      case 'UNRECONCILED_RESIDUAL_REQUIRING_INVESTIGATION':
        return <Badge variant="rose">RESIDUAL REQUIRING INVESTIGATION</Badge>;
      default:
        return <Badge variant="slate">{cls}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Strict Non-Prejudgment Principle Banner */}
      <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-400 shrink-0">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-mono text-xs font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
              Forensic Non-Prejudgment Mandate
              <Badge variant="cyan" className="text-[9px]">Enforced</Badge>
            </h4>
            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
              In strict accordance with GridGuard intelligence architecture, an energy discrepancy is <strong>never automatically classified as physical theft, fraud, or meter tampering</strong>.
              The accounting engine deterministically isolates sensor uncertainty (Class 0.5 utility tolerance), telemetry latency, and GIS topological mapping mismatches prior to escalating an investigative docket.
            </p>
          </div>
        </div>
      </div>

      {/* Boundary Selector Bar */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <label className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold block">
            Select Physical Distribution Boundary:
          </label>
          <div className="flex items-center gap-2">
            <select
              value={selectedBoundary}
              onChange={(e) => setSelectedBoundary(e.target.value)}
              className="px-3.5 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 font-mono text-xs focus:outline-none focus:border-cyan-500 transition-colors"
            >
              {boundaries.map((b) => (
                <option key={b.asset_code} value={b.asset_code}>
                  {b.asset_code} — {b.name} ({b.voltage_class})
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => runReconciliation(selectedBoundary)}
              disabled={isReconciling}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all cursor-pointer"
              title="Refresh Reconciliation"
            >
              <RefreshCw className={`w-4 h-4 ${isReconciling ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* Selected Boundary Quick Spec */}
        {dossier && (
          <div className="flex items-center gap-3 text-xs font-mono self-stretch md:self-auto justify-between md:justify-end border-t md:border-t-0 pt-3 md:pt-0 border-slate-800">
            <div className="text-right">
              <span className="text-slate-400 block text-[10px] uppercase">Hierarchy Level</span>
              <span className="font-bold text-slate-200">{dossier.boundary_asset_type}</span>
            </div>
            <div className="h-7 w-px bg-slate-800" />
            <div className="text-right">
              <span className="text-slate-400 block text-[10px] uppercase">Voltage Rating</span>
              <span className="font-bold text-cyan-400">{dossier.voltage_class}</span>
            </div>
            <div className="h-7 w-px bg-slate-800" />
            <div className="text-right">
              <span className="text-slate-400 block text-[10px] uppercase">Analysis Window</span>
              <span className="font-bold text-slate-200">{dossier.total_actual_intervals} Intervals (60m)</span>
            </div>
          </div>
        )}
      </div>

      {/* Loading Skeleton */}
      {isReconciling && (
        <LoadingState message={`Computing deterministic energy balance for boundary '${selectedBoundary}'...`} />
      )}

      {/* Error State */}
      {error && !isReconciling && (
        <ErrorAlert
          title="Accounting Reconciliation Error"
          message={error}
          code="ERR_ACCOUNTING_FAILED"
          onRetry={() => runReconciliation(selectedBoundary)}
        />
      )}

      {/* Dossier Report */}
      {dossier && !isReconciling && (
        <div className="space-y-6">
          {/* Top KPI Cards: Energy Flow Equation Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                1. Energy Entering (E_in)
              </span>
              <div className="mt-1 font-mono font-bold text-xl text-cyan-400">
                {dossier.energy_entering_boundary_kwh.toFixed(1)} <span className="text-xs text-slate-400">kWh</span>
              </div>
              <span className="text-[11px] text-slate-400 mt-0.5 block">Boundary Check Meter</span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                2. Downstream Recorded (E_downstream)
              </span>
              <div className="mt-1 font-mono font-bold text-xl text-emerald-400">
                {dossier.recorded_downstream_energy_kwh.toFixed(1)} <span className="text-xs text-slate-400">kWh</span>
              </div>
              <span className="text-[11px] text-slate-400 mt-0.5 block">
                {dossier.source_measurements.length} Child Entities (Anti-Double-Count)
              </span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                3. Technical Losses (E_technical)
              </span>
              <div className="mt-1 font-mono font-bold text-xl text-purple-400">
                {dossier.other_accounted_flows_kwh.toFixed(1)} <span className="text-xs text-slate-400">kWh</span>
              </div>
              <span className="text-[11px] text-slate-400 mt-0.5 block">Accounted Physics Flow (~2.8%)</span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                4. Net Unaccounted (E_unaccounted)
              </span>
              <div className={`mt-1 font-mono font-bold text-xl ${dossier.unaccounted_energy_kwh > 50 ? 'text-rose-400' : 'text-slate-200'}`}>
                {dossier.unaccounted_energy_kwh.toFixed(1)} <span className="text-xs text-slate-400">kWh</span>
              </div>
              <span className="text-[11px] text-slate-400 mt-0.5 block">Net Discrepancy: {dossier.discrepancy_percentage.toFixed(2)}%</span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                5. Diagnostic Assessment
              </span>
              <div className="mt-1.5">{getClassificationBadge(dossier.neutral_classification)}</div>
              <span className="text-[11px] text-slate-400 mt-1 block truncate">
                Tolerance: ±{dossier.remaining_uncertainty_percent}%
              </span>
            </div>
          </div>

          {/* Diagnostic Reason Detail Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-slate-800 text-cyan-400 shrink-0">
                <Info className="w-4 h-4" />
              </div>
              <div className="space-y-1">
                <h4 className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider">
                  Diagnostic Classification & Reason
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  {dossier.classification_reason}
                </p>
                <div className="text-[11px] font-mono text-slate-400 pt-1 flex items-center gap-4">
                  <span>Reproducibility Docket: <code className="text-cyan-400">{dossier.reproducibility_hash}</code></span>
                  <span>Sensor Class 0.5 Uncertainty: <code className="text-slate-300">±{dossier.sensor_uncertainty_kwh.toFixed(2)} kWh</code></span>
                </div>
              </div>
            </div>
          </div>

          {/* Mathematical Calculation Steps (Transparent & Inspectable) */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-mono text-sm font-bold text-slate-100 flex items-center gap-2">
                  <Calculator className="w-4 h-4 text-cyan-400" />
                  Deterministic Calculation Steps (Inspectable Mathematical Proof)
                </h3>
                <span className="text-xs text-slate-400">
                  Fully reproducible accounting pipeline implementing: Unaccounted = Entering − Downstream − Other Flows.
                </span>
              </div>
              <Badge variant="cyan" className="text-[10px]">{dossier.calculation_steps.length} Steps Logged</Badge>
            </div>

            <div className="space-y-3">
              {dossier.calculation_steps.map((step) => (
                <div
                  key={step.step_number}
                  className="rounded-lg border border-slate-800/80 bg-slate-950/60 p-4 font-mono text-xs space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-cyan-300">
                      Step {step.step_number}: {step.title}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800/60 text-cyan-300 font-bold">
                      {step.output_name} = {step.output_value.toFixed(3)} {step.unit}
                    </span>
                  </div>

                  <div className="p-2 rounded bg-slate-900/90 border border-slate-800 text-[11px] text-slate-300">
                    <code className="text-amber-300">{step.formula}</code>
                  </div>

                  <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
                    {step.explanation}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Source Measurements Traceability Table */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-mono text-sm font-bold text-slate-100 flex items-center gap-2">
                  <Database className="w-4 h-4 text-emerald-400" />
                  Source Measurements Traceability (Audit Evidence)
                </h3>
                <span className="text-xs text-slate-400">
                  Verification of individual meters and boundary inputs contributing to downstream recorded energy.
                </span>
              </div>
              <Badge variant="emerald" className="text-[10px]">{dossier.source_measurements.length} Child Sources</Badge>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                    <th className="py-2.5 px-3">Entity Identifier</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Readings Count</th>
                    <th className="py-2.5 px-3">Interval</th>
                    <th className="py-2.5 px-3">Total Energy</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Provenance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {dossier.source_measurements.map((src, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/50 transition-colors">
                      <td className="py-2 px-3 font-bold text-cyan-400">{src.entity_code}</td>
                      <td className="py-2 px-3 text-slate-400 text-[11px]">{src.entity_type}</td>
                      <td className="py-2 px-3">{src.readings_count}</td>
                      <td className="py-2 px-3">{src.interval_minutes}m</td>
                      <td className="py-2 px-3 font-bold text-emerald-400">
                        {src.total_energy_kwh.toFixed(2)} {src.unit}
                      </td>
                      <td className="py-2 px-3">
                        <Badge
                          variant={src.validation_status === 'VALID' ? 'emerald' : 'amber'}
                          className="text-[9px]"
                        >
                          {src.validation_status}
                        </Badge>
                      </td>
                      <td className="py-2 px-3 text-[11px] text-slate-400">
                        {src.is_simulated ? 'Simulated' : 'Live'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
