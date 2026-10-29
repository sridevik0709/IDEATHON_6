'use client';

import React, { useState } from 'react';
import {
  AlertTriangle,
  Bug,
  CheckCircle2,
  Code2,
  FlaskConical,
  Play,
  RefreshCw,
  Send,
  Terminal,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ApiClientError, gridGuardApi } from '@/lib/api';
import type { ValidationProbeRequest, ValidationProbeResponse } from '@/types/api';

export function ValidationConsole() {
  const [stationId, setStationId] = useState('SUB-NORTH-01');
  const [frequency, setFrequency] = useState('50.02');
  const [voltage, setVoltage] = useState('11000');
  const [feederCount, setFeederCount] = useState('8');

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{
    success: boolean;
    data?: ValidationProbeResponse;
    error?: { code: string; message: string; field?: string | null; details?: unknown };
    latencyMs?: number;
  } | null>(null);

  const [simulatedError, setSimulatedError] = useState<{
    scenario: string;
    status: number;
    response: unknown;
  } | null>(null);
  const [simulatingScenario, setSimulatingScenario] = useState<string | null>(null);

  const handleValidate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setResult(null);

    const payload: ValidationProbeRequest = {
      station_id: stationId,
      grid_frequency_hz: parseFloat(frequency) || 0,
      voltage_rms: parseFloat(voltage) || 0,
      feeder_count: parseInt(feederCount, 10) || 0,
    };

    try {
      const res = await gridGuardApi.validateTelemetry(payload);
      setResult({
        success: true,
        data: res.data,
        latencyMs: res.latencyMs,
      });
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        setResult({
          success: false,
          error: {
            code: err.code,
            message: err.message,
            field: err.field,
            details: err.details,
          },
        });
      } else {
        setResult({
          success: false,
          error: {
            code: 'ERR_UNEXPECTED',
            message: String(err),
          },
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSimulate = async (scenario: string) => {
    setSimulatingScenario(scenario);
    setSimulatedError(null);
    try {
      await gridGuardApi.simulateError(scenario);
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        setSimulatedError({
          scenario,
          status: err.status,
          response: {
            status: 'error',
            error: {
              code: err.code,
              message: err.message,
              details: err.details,
            },
          },
        });
      }
    } finally {
      setSimulatingScenario(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Telemetry Envelope Validation Card */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
          <div>
            <h3 className="font-mono text-base font-bold text-slate-100 flex items-center gap-2">
              <FlaskConical className="w-5 h-5 text-cyan-400" />
              Pydantic Request Validation Test Bench
            </h3>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Dispatches live envelopes to FastAPI endpoint <code>/api/v1/validate/telemetry-envelope</code>
            </p>
          </div>
          <Badge variant="cyan" className="font-mono text-xs self-start sm:self-auto">
            POST /api/v1/validate
          </Badge>
        </div>

        {/* Quick Presets */}
        <div className="mt-4 flex flex-wrap items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">Quick Test Vectors:</span>
          <button
            type="button"
            onClick={() => {
              setStationId('SUB-EAST-11KV');
              setFrequency('50.01');
              setVoltage('11000');
              setFeederCount('6');
            }}
            className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
          >
            ✓ Standard 50Hz 11kV Substation
          </button>
          <button
            type="button"
            onClick={() => {
              setStationId('SUB-WEST-400V');
              setFrequency('60.00');
              setVoltage('415');
              setFeederCount('4');
            }}
            className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
          >
            ✓ Standard 60Hz 415V Feeder
          </button>
          <button
            type="button"
            onClick={() => {
              setStationId('bad@id#special');
              setFrequency('15.5');
              setVoltage('-100');
              setFeederCount('0');
            }}
            className="px-2.5 py-1 rounded-md bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border border-rose-800/50 transition-colors"
          >
            ✕ Out-of-Bounds Vector (Triggers 422)
          </button>
        </div>

        {/* Form Inputs */}
        <form onSubmit={handleValidate} className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">
              Station ID (pattern: [A-Z0-9_\-]+)
            </label>
            <input
              type="text"
              value={stationId}
              onChange={(e) => setStationId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 font-mono text-xs focus:outline-none focus:border-cyan-500"
              placeholder="e.g. SUB-NORTH-01"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">
              Grid Frequency (45.0 - 65.0 Hz)
            </label>
            <input
              type="number"
              step="0.01"
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 font-mono text-xs focus:outline-none focus:border-cyan-500"
              placeholder="e.g. 50.0"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">
              RMS Voltage (0 - 500,000 V)
            </label>
            <input
              type="number"
              step="1"
              value={voltage}
              onChange={(e) => setVoltage(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 font-mono text-xs focus:outline-none focus:border-cyan-500"
              placeholder="e.g. 11000"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">
              Feeder Count (1 - 128 circuits)
            </label>
            <input
              type="number"
              value={feederCount}
              onChange={(e) => setFeederCount(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 font-mono text-xs focus:outline-none focus:border-cyan-500"
              placeholder="e.g. 8"
              required
            />
          </div>

          <div className="sm:col-span-2 lg:col-span-4 mt-2 flex items-center justify-end gap-3">
            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-mono font-bold text-xs shadow-lg shadow-cyan-500/20 disabled:opacity-50 transition-colors"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Validating with Backend...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Dispatch Probe to FastAPI
                </>
              )}
            </button>
          </div>
        </form>

        {/* Validation Result Box */}
        {result && (
          <div
            className={`mt-6 rounded-xl border p-4.5 font-mono text-xs transition-all ${
              result.success
                ? 'border-emerald-500/30 bg-emerald-950/20 text-emerald-200'
                : 'border-rose-500/30 bg-rose-950/20 text-rose-200'
            }`}
          >
            <div className="flex items-center gap-2 font-bold mb-2">
              {result.success ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Validation Passed (HTTP 200 OK)</span>
                  {result.latencyMs !== undefined && (
                    <span className="text-[11px] font-normal text-slate-400 ml-auto">
                      Roundtrip: {result.latencyMs}ms
                    </span>
                  )}
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  <span>Validation Error Rejected (HTTP 422 Unprocessable Entity)</span>
                </>
              )}
            </div>

            {result.success && result.data && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3 bg-black/40 rounded-lg p-3 border border-emerald-500/20">
                <div>
                  <span className="text-slate-400 text-[11px] block">Normalized Station:</span>
                  <span className="text-emerald-300 font-bold">{result.data.received_station}</span>
                </div>
                <div>
                  <span className="text-slate-400 text-[11px] block">Frequency Tier:</span>
                  <span className="text-emerald-300 font-bold">{result.data.nominal_band}</span>
                </div>
                <div>
                  <span className="text-slate-400 text-[11px] block">Voltage Classification:</span>
                  <span className="text-emerald-300 font-bold">{result.data.voltage_class}</span>
                </div>
              </div>
            )}

            {!result.success && result.error && (
              <div className="mt-2 space-y-1.5 bg-black/40 rounded-lg p-3 border border-rose-500/20">
                <div className="flex items-center gap-2">
                  <span className="text-rose-400 font-bold">Code:</span>
                  <code className="text-rose-300">{result.error.code}</code>
                </div>
                <div>
                  <span className="text-rose-400 font-bold">Message:</span>{' '}
                  <span className="text-rose-200">{result.error.message}</span>
                </div>
                {result.error.field && (
                  <div>
                    <span className="text-rose-400 font-bold">Target Field:</span>{' '}
                    <code className="text-rose-300">{result.error.field}</code>
                  </div>
                )}
                {Boolean(result.error.details) && (
                  <div className="mt-2 text-[11px] text-slate-400">
                    <pre className="p-2 bg-slate-950 rounded overflow-x-auto text-rose-300">
                      {JSON.stringify(result.error.details, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Error Consistency Demonstrator */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
          <div>
            <h3 className="font-mono text-base font-bold text-slate-100 flex items-center gap-2">
              <Bug className="w-5 h-5 text-amber-400" />
              Standardized Error Response Envelope Inspector
            </h3>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Verify that 404, 503, and 500 scenarios strictly follow the standard JSON schema
            </p>
          </div>
          <Badge variant="amber" className="font-mono text-xs self-start sm:self-auto">
            Consistent Error Contracts
          </Badge>
        </div>

        <div className="mt-4 flex flex-wrap gap-2.5">
          <button
            type="button"
            disabled={simulatingScenario !== null}
            onClick={() => handleSimulate('not_found')}
            className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs border border-slate-700 transition-colors"
          >
            Trigger 404 Not Found
          </button>
          <button
            type="button"
            disabled={simulatingScenario !== null}
            onClick={() => handleSimulate('database')}
            className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs border border-slate-700 transition-colors"
          >
            Trigger 503 Storage Unavailable
          </button>
          <button
            type="button"
            disabled={simulatingScenario !== null}
            onClick={() => handleSimulate('config')}
            className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs border border-slate-700 transition-colors"
          >
            Trigger 500 Configuration Fault
          </button>
        </div>

        {simulatedError && (
          <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span>Scenario: {simulatedError.scenario} (HTTP {simulatedError.status})</span>
              <span className="text-emerald-400">✓ Schema Compliant</span>
            </div>
            <pre className="p-3 bg-black/60 rounded-lg text-amber-300 overflow-x-auto text-[11px]">
              {JSON.stringify(simulatedError.response, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
