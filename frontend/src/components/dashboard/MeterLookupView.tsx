'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Search,
  Shield,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { LoadingState } from '@/components/ui/LoadingSpinner';
import { gridGuardApi } from '@/lib/api';
import type {
  MeterConsumptionData,
  MeterLookupData,
} from '@/types/api';

const DEMO_METERS = [
  { code: 'AGG-MTR-DT101-A', label: 'DT-101 Cluster A (18 Homes)', tag: 'Normal' },
  { code: 'AGG-MTR-DT101-B', label: 'DT-101 Cluster B (22 Homes)', tag: 'Normal' },
  { code: 'AGG-MTR-DT102-A', label: 'DT-102 Cluster A (15 Homes)', tag: 'GIS Target' },
  { code: 'AGG-MTR-DT103-A', label: 'DT-103 Cluster A (25 Homes)', tag: 'Lag Injected' },
  { code: 'MTR-UNKNOWN-999', label: 'Unknown Test Meter', tag: '404 Diagnostic' },
];

export function MeterLookupView() {
  const [selectedMeterCode, setSelectedMeterCode] = useState<string>('AGG-MTR-DT101-A');
  const [inputCode, setInputCode] = useState<string>('AGG-MTR-DT101-A');
  const [meterInfo, setMeterInfo] = useState<MeterLookupData | null>(null);
  const [consumption, setConsumption] = useState<MeterConsumptionData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<{ code: string; message: string } | null>(null);

  const fetchMeterData = useCallback(async (code: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const [lookupRes, consumptionRes] = await Promise.all([
        gridGuardApi.lookupMeter(code),
        gridGuardApi.getMeterConsumption(code),
      ]);
      setMeterInfo(lookupRes.data);
      setConsumption(consumptionRes.data);
    } catch (err: unknown) {
      const anyErr = err as { code?: string; message?: string };
      setError({
        code: anyErr?.code || 'ERR_METER_LOOKUP_FAILED',
        message: anyErr?.message || 'Unable to retrieve meter information.',
      });
      setMeterInfo(null);
      setConsumption(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedMeterCode) {
      fetchMeterData(selectedMeterCode);
    }
  }, [selectedMeterCode, fetchMeterData]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputCode.trim()) {
      setSelectedMeterCode(inputCode.trim().toUpperCase());
    }
  };

  return (
    <div className="space-y-6">
      {/* Privacy & Anti-Surveillance Banner */}
      <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400 shrink-0">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-mono text-xs font-bold text-emerald-300 uppercase tracking-wider flex items-center gap-2">
              National Ideathon Privacy Safeguard: Aggregate Metering Only
              <Badge variant="emerald" className="text-[9px]">Verified</Badge>
            </h4>
            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
              In accordance with engineering guidelines, GridGuard Nexus X strictly monitors household cluster aggregate meters (10–25 premises per meter node).
              Appliance-level surveillance or individual household monitoring is unsupported and strictly prohibited.
            </p>
          </div>
        </div>
      </div>

      {/* Search Bar & Quick Demo Chips */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm space-y-4">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={inputCode}
              onChange={(e) => setInputCode(e.target.value)}
              placeholder="Enter meter identifier (e.g., AGG-MTR-DT101-A)..."
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 font-mono text-sm focus:outline-none focus:border-cyan-500 transition-colors"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !inputCode.trim()}
            className="px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-mono text-xs font-bold flex items-center justify-center gap-2 transition-all shrink-0 cursor-pointer"
          >
            {isLoading ? 'Querying...' : 'Inspect Meter'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Quick Demo Meter Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-800/80">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
            Demonstration Meters:
          </span>
          {DEMO_METERS.map((dm) => (
            <button
              key={dm.code}
              type="button"
              onClick={() => {
                setInputCode(dm.code);
                setSelectedMeterCode(dm.code);
              }}
              className={`px-2.5 py-1 rounded-md text-xs font-mono transition-all flex items-center gap-1.5 border ${
                selectedMeterCode === dm.code
                  ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300 font-semibold'
                  : 'bg-slate-800/60 hover:bg-slate-800 border-slate-700/60 text-slate-300'
              }`}
            >
              <span>{dm.code}</span>
              <span className="text-[10px] text-slate-400 opacity-70">({dm.tag})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <LoadingState message={`Interrogating telemetry register for '${selectedMeterCode}'...`} />
      )}

      {/* Error State */}
      {error && !isLoading && (
        <ErrorAlert
          title="Meter Lookup Diagnostic"
          message={error.message}
          code={error.code}
          onRetry={() => fetchMeterData(selectedMeterCode)}
        />
      )}

      {/* Meter Details & Consumption Profile */}
      {meterInfo && consumption && !isLoading && (
        <div className="space-y-6">
          {/* Metadata Card */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Meter Identifier</span>
              <div className="mt-1 font-mono font-bold text-lg text-cyan-400">{meterInfo.meter_code}</div>
              <span className="text-xs text-slate-400 mt-0.5 block">{meterInfo.installation_type}</span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Consumer Aggregate</span>
              <div className="mt-1 font-mono font-bold text-lg text-emerald-400">{meterInfo.household_count} Premises</div>
              <span className="text-xs text-slate-400 mt-0.5 block">Cluster Aggregate Node</span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Parent Distribution Asset</span>
              <div className="mt-1 font-mono font-bold text-base text-slate-200 truncate">
                {meterInfo.associated_asset_code || 'Unassigned'}
              </div>
              <span className="text-xs text-slate-400 mt-0.5 block">{meterInfo.associated_asset_name || 'GIS Asset'}</span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Source Provenance</span>
              <div className="mt-1 font-mono font-bold text-sm text-amber-400 truncate">
                {meterInfo.data_source_code}
              </div>
              <div className="flex items-center gap-1.5 mt-1">
                <Badge variant={meterInfo.is_simulated ? 'amber' : 'emerald'} className="text-[9px]">
                  {meterInfo.is_simulated ? 'SIMULATED' : 'LIVE UTILITY'}
                </Badge>
                <span className="text-[10px] text-slate-400">Phase: {meterInfo.phase_configuration}</span>
              </div>
            </div>
          </div>

          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-3">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Total Energy</span>
              <div className="mt-1 text-lg font-mono font-bold text-cyan-400">
                {consumption.total_consumption_kwh.toFixed(1)} <span className="text-xs text-slate-400">kWh</span>
              </div>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-3">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Hourly Average</span>
              <div className="mt-1 text-lg font-mono font-bold text-slate-200">
                {consumption.average_hourly_kwh.toFixed(2)} <span className="text-xs text-slate-400">kWh</span>
              </div>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-3">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Peak Power</span>
              <div className="mt-1 text-lg font-mono font-bold text-purple-400">
                {consumption.peak_power_kw.toFixed(1)} <span className="text-xs text-slate-400">kW</span>
              </div>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-3">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Interval Range</span>
              <div className="mt-1 text-sm font-mono font-bold text-slate-300">
                {consumption.minimum_interval_kwh.toFixed(1)} – {consumption.maximum_interval_kwh.toFixed(1)} <span className="text-xs text-slate-400">kWh</span>
              </div>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-3">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Missing Intervals</span>
              <div className={`mt-1 text-lg font-mono font-bold ${consumption.missing_intervals_count > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                {consumption.missing_intervals_count} / {consumption.expected_readings_count}
              </div>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-3">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Unusual Variations</span>
              <div className={`mt-1 text-lg font-mono font-bold ${consumption.unusual_changes_count > 0 ? 'text-rose-400' : 'text-slate-400'}`}>
                {consumption.unusual_changes_count}
              </div>
            </div>
          </div>

          {/* Consumption Interval Profile & Trends */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-mono text-sm font-bold text-slate-100 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-cyan-400" />
                  24-Hour Interval Consumption Profile (Hourly Aggregate)
                </h3>
                <span className="text-xs text-slate-400">
                  Window: {new Date(consumption.analysis_period_start).toLocaleTimeString()} – {new Date(consumption.analysis_period_end).toLocaleTimeString()}
                </span>
              </div>
              <Badge variant="cyan" className="text-[10px]">{consumption.readings_count} Readings Captured</Badge>
            </div>

            {/* Visual Bar Chart */}
            <div className="h-44 flex items-end gap-1.5 pt-4 pb-2 px-2 bg-slate-950/60 rounded-lg border border-slate-800/80 overflow-x-auto">
              {consumption.trend_series.map((pt, idx) => {
                const maxVal = Math.max(...consumption.trend_series.map((p) => p.energy_kwh), 1.0);
                const heightPct = Math.max(8, (pt.energy_kwh / maxVal) * 100);
                return (
                  <div
                    key={idx}
                    className="flex-1 min-w-[28px] flex flex-col items-center gap-1 group relative"
                  >
                    {/* Tooltip */}
                    <div className="absolute -top-10 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-900 border border-slate-700 text-slate-100 text-[10px] font-mono rounded px-2 py-1 pointer-events-none z-20 whitespace-nowrap shadow-lg">
                      {new Date(pt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}: {pt.energy_kwh} kWh
                      {pt.is_unusual && ` (${pt.unusual_reason})`}
                    </div>

                    <div
                      style={{ height: `${heightPct}%` }}
                      className={`w-full rounded-t transition-all ${
                        pt.is_unusual
                          ? 'bg-rose-500 hover:bg-rose-400'
                          : 'bg-cyan-500/70 hover:bg-cyan-400'
                      }`}
                    />
                    <span className="text-[9px] font-mono text-slate-500">
                      {idx % 4 === 0 ? `${idx}h` : ''}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Data-Quality Findings & Diagnostic Reasons */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-mono text-sm font-bold text-slate-100 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-400" />
                  10-Point Data-Quality Audit Findings & Diagnostic Explanations
                </h3>
                <span className="text-xs text-slate-400">
                  Comprehensive audit across completeness, timestamps, units, intervals, and plausibility.
                </span>
              </div>
              <Badge variant={consumption.data_quality_warnings.length === 0 ? 'emerald' : 'amber'} className="text-[10px]">
                {consumption.data_quality_warnings.length === 0 ? '100% Passed' : `${consumption.data_quality_warnings.length} Warnings`}
              </Badge>
            </div>

            {consumption.data_quality_warnings.length === 0 ? (
              <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2 font-mono">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                All 10 quality checks passed: Zero missing packets, uniform 60m intervals, verified KWH units, valid timestamps.
              </div>
            ) : (
              <div className="space-y-3">
                {consumption.data_quality_warnings.map((finding, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/50 space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-xs">
                        <Badge
                          variant={finding.severity === 'CRITICAL' ? 'rose' : 'amber'}
                          className="text-[9px]"
                        >
                          {finding.severity}
                        </Badge>
                        <span className="font-bold text-slate-200">{finding.rule_code}</span>
                        <span className="text-slate-500">[{finding.dimension}]</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">Target: {finding.target_entity}</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {finding.diagnostic_message}
                    </p>
                    {finding.recommended_action && (
                      <div className="text-[11px] text-cyan-400 font-mono pt-1">
                        → Recommended Action: {finding.recommended_action}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
