'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Bot,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Compass,
  FileCheck2,
  HelpCircle,
  Layers,
  ListChecks,
  RefreshCw,
  Scale,
  Send,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { LoadingState } from '@/components/ui/LoadingSpinner';
import { gridGuardApi } from '@/lib/api';
import type {
  AccountingBoundaryData,
  AssistantQueryResponseData,
  HypothesisAnalysisData,
  InvestigationDossierData,
} from '@/types/api';

const QUICK_PROMPTS = [
  'Why did this discrepancy occur?',
  'Which evidence supports this explanation?',
  'What information is missing?',
  'What should be investigated next?',
  'How would a delayed reading affect the result?',
  'Which hypotheses remain plausible?',
];

export function AiInvestigationView() {
  const [boundaries, setBoundaries] = useState<AccountingBoundaryData[]>([]);
  const [selectedBoundary, setSelectedBoundary] = useState<string>('DT-11KV-415V-101');
  const [dossier, setDossier] = useState<InvestigationDossierData | null>(null);
  const [selectedHypothesisCode, setSelectedHypothesisCode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Assistant states
  const [queryInput, setQueryInput] = useState<string>('');
  const [isQuerying, setIsQuerying] = useState<boolean>(false);
  const [assistantResponse, setAssistantResponse] = useState<AssistantQueryResponseData | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    prioritization: true,
    hypotheses: true,
    assistant: true,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const loadBoundaries = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await gridGuardApi.getAccountingBoundaries();
      setBoundaries(res.data);
      if (res.data.length > 0 && !selectedBoundary) {
        setSelectedBoundary(res.data[0].asset_code);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to load network boundaries.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [selectedBoundary]);

  const runInvestigation = useCallback(async (assetCode: string) => {
    setIsAnalyzing(true);
    setError(null);
    try {
      const res = await gridGuardApi.analyzeInvestigation(assetCode);
      setDossier(res.data);
      if (res.data.hypotheses.length > 0) {
        setSelectedHypothesisCode(res.data.hypotheses[0].code);
      }
      // Reset assistant response when boundary changes
      setAssistantResponse(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Investigation analysis failed.';
      setError(msg);
      setDossier(null);
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const handleAskAssistant = async (queryText: string) => {
    if (!queryText.trim() || !selectedBoundary) return;
    setIsQuerying(true);
    setError(null);
    try {
      const res = await gridGuardApi.queryAiAssistant(selectedBoundary, queryText.trim());
      setAssistantResponse(res.data);
      setQueryInput('');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'AI Assistant query failed.';
      setError(msg);
    } finally {
      setIsQuerying(false);
    }
  };

  useEffect(() => {
    loadBoundaries();
  }, [loadBoundaries]);

  useEffect(() => {
    if (selectedBoundary) {
      runInvestigation(selectedBoundary);
    }
  }, [selectedBoundary, runInvestigation]);

  const selectedHypothesis: HypothesisAnalysisData | undefined =
    dossier?.hypotheses.find((h) => h.code === selectedHypothesisCode) ||
    dossier?.hypotheses[0];

  return (
    <div className="space-y-6">
      {/* Top Controls & Boundary Selector */}
      <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5 shadow-sm lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <BrainCircuit className="h-5 w-5 text-indigo-400" />
            <h2 className="text-xl font-bold tracking-tight text-foreground">
              Level 4: AI-Assisted Forensic Investigation
            </h2>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Multi-hypothesis forensic matrix, 6-factor explainable prioritization, and evidence-grounded AI assistant with automated deterministic fallback.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label htmlFor="boundary-select" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Boundary:
            </label>
            <select
              id="boundary-select"
              value={selectedBoundary}
              onChange={(e) => setSelectedBoundary(e.target.value)}
              disabled={isLoading || isAnalyzing}
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
            onClick={() => runInvestigation(selectedBoundary)}
            disabled={isAnalyzing}
            className="flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-1.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
            {isAnalyzing ? 'Analyzing...' : 'Re-Analyze'}
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={() => runInvestigation(selectedBoundary)} />}

      {isAnalyzing && !dossier && (
        <LoadingState message="Conducting multi-hypothesis forensic analysis & computing explainable priority ranking..." />
      )}

      {dossier && (
        <>
          {/* Summary Metric Ribbon */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <div className="rounded-xl border border-border bg-card p-3.5 shadow-sm">
              <span className="text-xs font-medium text-muted-foreground">Entering Energy (E_in)</span>
              <div className="mt-1 text-lg font-bold text-foreground">
                {dossier.accounting.energy_entering_boundary_kwh.toLocaleString(undefined, { maximumFractionDigits: 1 })} <span className="text-xs font-normal text-muted-foreground">kWh</span>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-3.5 shadow-sm">
              <span className="text-xs font-medium text-muted-foreground">Downstream Recorded</span>
              <div className="mt-1 text-lg font-bold text-foreground">
                {dossier.accounting.recorded_downstream_energy_kwh.toLocaleString(undefined, { maximumFractionDigits: 1 })} <span className="text-xs font-normal text-muted-foreground">kWh</span>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-3.5 shadow-sm">
              <span className="text-xs font-medium text-muted-foreground">Technical Losses</span>
              <div className="mt-1 text-lg font-bold text-sky-400">
                {dossier.accounting.other_accounted_flows_kwh.toLocaleString(undefined, { maximumFractionDigits: 1 })} <span className="text-xs font-normal text-muted-foreground">kWh</span>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-3.5 shadow-sm">
              <span className="text-xs font-medium text-muted-foreground">Unaccounted Energy</span>
              <div className={`mt-1 text-lg font-bold ${dossier.accounting.unaccounted_energy_kwh > 5 ? 'text-amber-400' : 'text-emerald-400'}`}>
                {dossier.accounting.unaccounted_energy_kwh.toLocaleString(undefined, { maximumFractionDigits: 1 })} <span className="text-xs font-normal text-muted-foreground">kWh</span>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-3.5 shadow-sm">
              <span className="text-xs font-medium text-muted-foreground">Gross Discrepancy</span>
              <div className={`mt-1 text-lg font-bold ${dossier.accounting.discrepancy_percentage > 3.5 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {dossier.accounting.discrepancy_percentage.toFixed(2)}%
              </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-3.5 shadow-sm">
              <span className="text-xs font-medium text-muted-foreground">Priority Score</span>
              <div className="mt-1 flex items-center gap-1.5 text-lg font-bold text-indigo-400">
                <span>{dossier.prioritization.total_priority_score.toFixed(1)}</span>
                <span className="text-xs font-normal text-muted-foreground">/ 100</span>
                <Badge
                  variant={
                    dossier.prioritization.priority_level === 'CRITICAL'
                      ? 'rose'
                      : dossier.prioritization.priority_level === 'HIGH'
                      ? 'amber'
                      : 'cyan'
                  }
                  className="ml-auto text-[10px] uppercase"
                >
                  {dossier.prioritization.priority_level}
                </Badge>
              </div>
            </div>
          </div>

          {/* Forensic Protocol Banner */}
          <div className="flex items-start gap-3 rounded-xl border border-border/70 bg-secondary/30 p-4">
            <Scale className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" />
            <div className="space-y-1 text-xs leading-relaxed text-muted-foreground">
              <div className="font-semibold text-foreground">
                Standard Grid Forensic Classification: <span className="font-mono text-primary">{dossier.accounting.neutral_classification}</span>
              </div>
              <p>
                {dossier.accounting.classification_reason}
              </p>
              <div className="flex flex-wrap items-center gap-2 pt-1 font-mono text-[11px] text-muted-foreground">
                <span>Boundary: {dossier.boundary_asset_code}</span>
                <span>•</span>
                <span>Window: {dossier.analysis_period_start.slice(0, 16)} to {dossier.analysis_period_end.slice(0, 16)} UTC</span>
                <span>•</span>
                <span>Zero-Prejudgment Protocol Active</span>
              </div>
            </div>
          </div>

          {/* Section 1: Explainable 6-Factor Prioritization Breakdown */}
          <div className="rounded-xl border border-border bg-card shadow-sm">
            <button
              onClick={() => toggleSection('prioritization')}
              className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-secondary/20"
            >
              <div className="flex items-center gap-2.5">
                <Compass className="h-5 w-5 text-indigo-400" />
                <h3 className="font-semibold text-foreground">
                  Explainable 6-Factor Prioritization Ranking (Score: {dossier.prioritization.total_priority_score.toFixed(1)} / 100)
                </h3>
                <Badge variant="slate" className="text-xs text-muted-foreground">
                  Zero-Unexplained Scores
                </Badge>
              </div>
              {expandedSections.prioritization ? (
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              )}
            </button>

            {expandedSections.prioritization && (
              <div className="border-t border-border p-5 space-y-4">
                <div className="rounded-lg bg-secondary/20 p-3 text-xs text-muted-foreground">
                  <div className="font-medium text-foreground">Primary Triage Recommendation:</div>
                  <div className="mt-0.5 text-primary font-semibold">{dossier.prioritization.top_recommended_hypothesis}</div>
                  <p className="mt-1">{dossier.prioritization.operational_action_summary}</p>
                </div>

                <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
                  {dossier.prioritization.factors.map((factor) => (
                    <div key={factor.factor_id} className="rounded-lg border border-border/60 bg-background/50 p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-foreground">{factor.name}</span>
                        <span className="text-[11px] font-mono font-medium text-indigo-400">
                          +{factor.weighted_contribution.toFixed(1)} pts
                        </span>
                      </div>

                      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                        <div
                          className="h-full bg-indigo-500 transition-all duration-300"
                          style={{ width: `${Math.min(100, factor.normalized_score)}%` }}
                        />
                      </div>

                      <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
                        <span>Weight: {factor.weight_percent.toFixed(0)}%</span>
                        <span>Score: {factor.normalized_score.toFixed(1)}/100</span>
                      </div>

                      <p className="mt-1 text-[11px] text-muted-foreground line-clamp-2">
                        {factor.explanation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Section 2: Multi-Hypothesis Forensic Matrix */}
          <div className="rounded-xl border border-border bg-card shadow-sm">
            <button
              onClick={() => toggleSection('hypotheses')}
              className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-secondary/20"
            >
              <div className="flex items-center gap-2.5">
                <Layers className="h-5 w-5 text-indigo-400" />
                <h3 className="font-semibold text-foreground">
                  Multi-Hypothesis Forensic Matrix ({dossier.hypotheses.length} Competing Causes Evaluated)
                </h3>
                <Badge variant="slate" className="text-xs text-muted-foreground">
                  Never Auto-Selects One Cause
                </Badge>
              </div>
              {expandedSections.hypotheses ? (
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              )}
            </button>

            {expandedSections.hypotheses && (
              <div className="border-t border-border p-5">
                {/* Hypothesis Selection Chips */}
                <div className="flex flex-wrap gap-2 pb-4">
                  {dossier.hypotheses.map((h) => {
                    const isSelected = selectedHypothesisCode === h.code;
                    return (
                      <button
                        key={h.code}
                        onClick={() => setSelectedHypothesisCode(h.code)}
                        className={`flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium transition-all ${
                          isSelected
                            ? 'bg-primary text-primary-foreground shadow-sm'
                            : 'border border-border bg-background hover:bg-secondary/40 text-foreground'
                        }`}
                      >
                        <span className="truncate max-w-[200px]">{h.title}</span>
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                            h.plausibility === 'HIGH'
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : h.plausibility === 'MEDIUM'
                              ? 'bg-amber-500/20 text-amber-300'
                              : 'bg-zinc-500/20 text-zinc-300'
                          }`}
                        >
                          {h.plausibility}
                        </span>
                      </button>
                    );
                  })}
                </div>

                {/* Selected Hypothesis Full Forensic Docket */}
                {selectedHypothesis && (
                  <div className="rounded-xl border border-border/80 bg-background/60 p-5 space-y-5">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-base font-bold text-foreground">
                            {selectedHypothesis.title}
                          </h4>
                          <span className="font-mono text-xs text-muted-foreground">
                            [{selectedHypothesis.code}]
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          Category: <span className="font-medium text-foreground">{selectedHypothesis.category}</span>
                        </p>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div className="text-xs text-muted-foreground">Confidence Rationale</div>
                          <div className="text-sm font-bold text-foreground">
                            {(selectedHypothesis.confidence_score * 100).toFixed(0)}%
                          </div>
                        </div>
                        <Badge
                          variant={
                            selectedHypothesis.plausibility === 'HIGH'
                              ? 'emerald'
                              : selectedHypothesis.plausibility === 'MEDIUM'
                              ? 'amber'
                              : 'slate'
                          }
                        >
                          {selectedHypothesis.plausibility} PLAUSIBILITY
                        </Badge>
                      </div>
                    </div>

                    {/* Explanation */}
                    <div className="space-y-1">
                      <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Detailed Engineering Explanation
                      </div>
                      <p className="text-sm leading-relaxed text-foreground bg-secondary/10 p-3 rounded-lg border border-border/40">
                        {selectedHypothesis.explanation}
                      </p>
                    </div>

                    {/* Evidence Grids: Supporting vs Contradicting */}
                    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                      {/* Supporting Evidence */}
                      <div className="rounded-lg border border-emerald-500/30 bg-emerald-950/10 p-4 space-y-2">
                        <div className="flex items-center gap-2 font-semibold text-xs text-emerald-400">
                          <CheckCircle2 className="h-4 w-4" />
                          <span>Supporting Evidence Items ({selectedHypothesis.supporting_evidence.length})</span>
                        </div>

                        {selectedHypothesis.supporting_evidence.length === 0 ? (
                          <p className="text-xs text-muted-foreground italic">No direct supporting measurements recorded.</p>
                        ) : (
                          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                            {selectedHypothesis.supporting_evidence.map((ev) => (
                              <div key={ev.evidence_id} className="rounded border border-emerald-500/20 bg-background/60 p-2 text-xs">
                                <div className="flex items-center justify-between text-[11px] font-mono text-emerald-400">
                                  <span>{ev.evidence_id} • {ev.entity_code}</span>
                                  <span>{String(ev.metric_value)} {ev.unit || ''}</span>
                                </div>
                                <p className="mt-1 text-muted-foreground text-[11px]">{ev.description}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Contradicting Evidence */}
                      <div className="rounded-lg border border-amber-500/30 bg-amber-950/10 p-4 space-y-2">
                        <div className="flex items-center gap-2 font-semibold text-xs text-amber-400">
                          <AlertTriangle className="h-4 w-4" />
                          <span>Contradicting Evidence Items ({selectedHypothesis.contradicting_evidence.length})</span>
                        </div>

                        {selectedHypothesis.contradicting_evidence.length === 0 ? (
                          <p className="text-xs text-muted-foreground italic">No contradictory evidence recorded.</p>
                        ) : (
                          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                            {selectedHypothesis.contradicting_evidence.map((ev) => (
                              <div key={ev.evidence_id} className="rounded border border-amber-500/20 bg-background/60 p-2 text-xs">
                                <div className="flex items-center justify-between text-[11px] font-mono text-amber-400">
                                  <span>{ev.evidence_id} • {ev.entity_code}</span>
                                  <span>{String(ev.metric_value)} {ev.unit || ''}</span>
                                </div>
                                <p className="mt-1 text-muted-foreground text-[11px]">{ev.description}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Missing Evidence & Action Steps */}
                    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                      <div className="rounded-lg border border-border p-3.5 space-y-2">
                        <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
                          <FileCheck2 className="h-4 w-4 text-indigo-400" />
                          <span>Missing Telemetry & Data Required</span>
                        </div>
                        <ul className="space-y-1 text-xs text-muted-foreground">
                          {selectedHypothesis.missing_evidence.map((item, idx) => (
                            <li key={idx} className="flex items-start gap-1.5">
                              <span className="text-indigo-400 font-bold">•</span>
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="rounded-lg border border-border p-3.5 space-y-2">
                        <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
                          <ListChecks className="h-4 w-4 text-emerald-400" />
                          <span>Recommended Verification Procedures</span>
                        </div>
                        <ul className="space-y-1 text-xs text-muted-foreground">
                          {selectedHypothesis.recommended_verification_steps.map((step, idx) => (
                            <li key={idx} className="flex items-start gap-1.5">
                              <ArrowRight className="h-3.5 w-3.5 text-emerald-400 mt-0.5 shrink-0" />
                              <span>{step}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Section 3: AI Investigation Assistant Console */}
          <div className="rounded-xl border border-border bg-card shadow-sm">
            <button
              onClick={() => toggleSection('assistant')}
              className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-secondary/20"
            >
              <div className="flex items-center gap-2.5">
                <Bot className="h-5 w-5 text-indigo-400" />
                <h3 className="font-semibold text-foreground">
                  AI Investigation Assistant & Guardrail Verification Console
                </h3>
                <Badge variant="slate" className="text-xs text-muted-foreground">
                  Strict Evidence Grounding
                </Badge>
              </div>
              {expandedSections.assistant ? (
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              )}
            </button>

            {expandedSections.assistant && (
              <div className="border-t border-border p-5 space-y-4">
                {/* Fast Prompt Chips */}
                <div>
                  <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                    <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                    <span>Quick Forensic Inquiries:</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {QUICK_PROMPTS.map((prompt) => (
                      <button
                        key={prompt}
                        onClick={() => handleAskAssistant(prompt)}
                        disabled={isQuerying}
                        className="rounded-lg border border-border/70 bg-secondary/30 px-3 py-1.5 text-xs font-medium text-foreground transition-all hover:bg-secondary hover:text-primary disabled:opacity-50"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Free Text Input */}
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={queryInput}
                    onChange={(e) => setQueryInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleAskAssistant(queryInput);
                    }}
                    placeholder={`Ask the AI Assistant about boundary ${dossier.boundary_asset_code}...`}
                    disabled={isQuerying}
                    className="flex-1 rounded-lg border border-border bg-background px-4 py-2.5 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  <button
                    onClick={() => handleAskAssistant(queryInput)}
                    disabled={isQuerying || !queryInput.trim()}
                    className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
                  >
                    <Send className="h-4 w-4" />
                    <span>{isQuerying ? 'Analyzing...' : 'Ask'}</span>
                  </button>
                </div>

                {/* Real-time Assistant Response Card */}
                {isQuerying && (
                  <LoadingState message="Synthesizing verified evidence records and executing forensic guardrails..." />
                )}

                {assistantResponse && !isQuerying && (
                  <div className="rounded-xl border border-border bg-background p-5 space-y-4">
                    {/* Header with Mode & Model */}
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-3">
                      <div className="flex items-center gap-2">
                        <Bot className="h-5 w-5 text-indigo-400" />
                        <span className="text-sm font-bold text-foreground">
                          Assistant Response: &ldquo;{assistantResponse.query}&rdquo;
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold ${
                            assistantResponse.mode === 'EXTERNAL_AI'
                              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                              : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          }`}
                        >
                          {assistantResponse.mode === 'EXTERNAL_AI'
                            ? `EXTERNAL AI (${assistantResponse.model_name})`
                            : 'RULE-BASED FALLBACK CORE'}
                        </span>
                        <span className="text-xs text-muted-foreground font-mono">
                          {assistantResponse.timestamp.slice(11, 19)} UTC
                        </span>
                      </div>
                    </div>

                    {/* Answer Text (Markdown formatted preview) */}
                    <div className="prose prose-sm dark:prose-invert max-w-none text-sm text-foreground leading-relaxed whitespace-pre-line font-sans">
                      {assistantResponse.answer}
                    </div>

                    {/* Evidence Citations Drawer */}
                    {assistantResponse.evidence_citations.length > 0 && (
                      <div className="rounded-lg border border-border/60 bg-secondary/20 p-3 space-y-2">
                        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                          <span>Direct Evidence Citations ({assistantResponse.evidence_citations.length}):</span>
                        </div>
                        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                          {assistantResponse.evidence_citations.map((ev) => (
                            <div key={ev.evidence_id} className="rounded border border-border/80 bg-background/70 p-2 text-xs">
                              <div className="flex items-center justify-between font-mono text-[11px] text-primary">
                                <span>{ev.evidence_id}</span>
                                <span>{String(ev.metric_value)} {ev.unit || ''}</span>
                              </div>
                              <p className="mt-0.5 text-muted-foreground text-[11px] truncate">{ev.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Guardrail Safety Verification Badges */}
                    <div className="rounded-lg border border-emerald-500/30 bg-emerald-950/10 p-3">
                      <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 mb-2">
                        <ShieldCheck className="h-4 w-4" />
                        <span>Forensic Safety Guardrail Verification Status</span>
                      </div>
                      <div className="grid grid-cols-1 gap-2 text-xs text-muted-foreground sm:grid-cols-2 lg:grid-cols-3">
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                          <span>Accounting Invariance Verified</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                          <span>Unsupported Allegations Blocked</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                          <span>Citations Traceable to DB</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                          <span>Utility Privacy Safeguarded</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                          <span>Simulations Clearly Labeled</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
