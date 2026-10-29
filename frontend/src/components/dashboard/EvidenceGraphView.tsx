'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Compass,
  FileCheck2,
  FileText,
  Filter,
  HelpCircle,
  Layers,
  Network,
  RefreshCw,
  Scale,
  Search,
  Shield,
  ShieldAlert,
  Sparkles,
  Zap,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { LoadingState } from '@/components/ui/LoadingSpinner';
import { gridGuardApi } from '@/lib/api';
import type {
  AccountingBoundaryData,
  GraphNodeData,
  GraphVisualState,
  InvestigationGraphData,
} from '@/types/api';

const VISUAL_STATE_CONFIG: Record<
  GraphVisualState,
  { label: string; bg: string; border: string; text: string; badgeVariant: 'cyan' | 'amber' | 'violet' | 'emerald' | 'rose' | 'slate' }
> = {
  OBSERVED_EVIDENCE: {
    label: 'Observed Evidence',
    bg: 'bg-cyan-950/30',
    border: 'border-cyan-500/40',
    text: 'text-cyan-400',
    badgeVariant: 'cyan',
  },
  CALCULATED_FINDING: {
    label: 'Calculated Finding',
    bg: 'bg-amber-950/30',
    border: 'border-amber-500/40',
    text: 'text-amber-400',
    badgeVariant: 'amber',
  },
  HYPOTHESIS: {
    label: 'Hypothesis',
    bg: 'bg-violet-950/30',
    border: 'border-violet-500/40',
    text: 'text-violet-400',
    badgeVariant: 'violet',
  },
  RECOMMENDATION: {
    label: 'Recommendation',
    bg: 'bg-emerald-950/30',
    border: 'border-emerald-500/40',
    text: 'text-emerald-400',
    badgeVariant: 'emerald',
  },
  CONFIRMED_OUTCOME: {
    label: 'Confirmed Outcome',
    bg: 'bg-rose-950/30',
    border: 'border-rose-500/40',
    text: 'text-rose-400',
    badgeVariant: 'rose',
  },
};

export function EvidenceGraphView() {
  const [boundaries, setBoundaries] = useState<AccountingBoundaryData[]>([]);
  const [selectedBoundary, setSelectedBoundary] = useState<string>('DT-11KV-415V-101');
  const [graphData, setGraphData] = useState<InvestigationGraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNodeData | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isGraphLoading, setIsGraphLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

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

  const loadGraph = useCallback(async (assetCode: string) => {
    setIsGraphLoading(true);
    setError(null);
    try {
      const res = await gridGuardApi.getEvidenceGraph(assetCode);
      setGraphData(res.data);
      if (res.data.nodes.length > 0) {
        setSelectedNode(res.data.nodes[0]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to generate evidence investigation graph.';
      setError(msg);
      setGraphData(null);
    } finally {
      setIsGraphLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBoundaries();
  }, [loadBoundaries]);

  useEffect(() => {
    if (selectedBoundary) {
      loadGraph(selectedBoundary);
    }
  }, [selectedBoundary, loadGraph]);

  const filteredNodes = graphData
    ? activeFilter === 'ALL'
      ? graphData.nodes
      : graphData.nodes.filter((n) => n.visual_state === activeFilter)
    : [];

  return (
    <div className="space-y-6">
      {/* Top Controls & Boundary Selector */}
      <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5 shadow-sm lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Network className="h-5 w-5 text-indigo-400" />
            <h2 className="text-xl font-bold tracking-tight text-foreground">
              Level 5: Interactive Evidence Investigation Graph
            </h2>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            End-to-end evidence lineage connecting Detected Discrepancy → Source Measurements → Data-Quality Findings → Hypotheses → Actions → Outcome.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label htmlFor="graph-boundary-select" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Boundary:
            </label>
            <select
              id="graph-boundary-select"
              value={selectedBoundary}
              onChange={(e) => setSelectedBoundary(e.target.value)}
              disabled={isLoading || isGraphLoading}
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
            onClick={() => loadGraph(selectedBoundary)}
            disabled={isGraphLoading}
            className="flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-1.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isGraphLoading ? 'animate-spin' : ''}`} />
            {isGraphLoading ? 'Rebuilding...' : 'Refresh Graph'}
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={() => loadGraph(selectedBoundary)} />}

      {isGraphLoading && !graphData && (
        <LoadingState message="Constructing full evidence investigation graph & linking forensic provenance..." />
      )}

      {graphData && (
        <>
          {/* Visual State Legend & Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-3.5 shadow-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mr-1 flex items-center gap-1">
                <Filter className="h-3.5 w-3.5" />
                <span>Filter States:</span>
              </span>

              <button
                onClick={() => setActiveFilter('ALL')}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                  activeFilter === 'ALL'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary/40 text-muted-foreground hover:bg-secondary hover:text-foreground'
                }`}
              >
                All Nodes ({graphData.nodes.length})
              </button>

              {(Object.keys(VISUAL_STATE_CONFIG) as GraphVisualState[]).map((stateKey) => {
                const cfg = VISUAL_STATE_CONFIG[stateKey];
                const count = graphData.summary?.nodes_by_visual_state?.[stateKey] || 0;
                const isSelected = activeFilter === stateKey;
                return (
                  <button
                    key={stateKey}
                    onClick={() => setActiveFilter(stateKey)}
                    className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium border transition-all ${
                      isSelected
                        ? `${cfg.bg} ${cfg.border} ${cfg.text} font-bold shadow-sm`
                        : 'border-border/60 bg-background/50 text-muted-foreground hover:bg-secondary/40'
                    }`}
                  >
                    <span>{cfg.label}</span>
                    <span className="rounded bg-background/80 px-1 py-0.2 text-[10px] font-mono">
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="flex items-center gap-2 font-mono text-xs text-muted-foreground">
              <span>Nodes: {graphData.nodes.length}</span>
              <span>•</span>
              <span>Edges: {graphData.edges.length}</span>
            </div>
          </div>

          {/* Main Workspace: Graph Flow Canvas + Inspector Docket Drawer */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            {/* Left 8 Cols: Interactive Node-Link Canvas */}
            <div className="lg:col-span-8 rounded-xl border border-border bg-card p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-bold text-foreground">
                    Evidence Lineage Flow for {graphData.boundary_asset_code}
                  </h3>
                </div>
                <Badge variant="cyan" className="text-[11px]">
                  Click Any Node to Inspect Evidence
                </Badge>
              </div>

              {/* Node Cards Stream */}
              <div className="space-y-3 max-h-[640px] overflow-y-auto pr-2">
                {filteredNodes.map((node) => {
                  const cfg = VISUAL_STATE_CONFIG[node.visual_state] || VISUAL_STATE_CONFIG.OBSERVED_EVIDENCE;
                  const isSelected = selectedNode?.node_id === node.node_id;

                  return (
                    <div
                      key={node.node_id}
                      onClick={() => setSelectedNode(node)}
                      className={`cursor-pointer rounded-xl border p-4 transition-all ${
                        isSelected
                          ? `ring-2 ring-primary ${cfg.bg} ${cfg.border} shadow-md`
                          : `border-border/70 bg-background/60 hover:border-primary/50 hover:bg-secondary/20`
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                        <div className="flex items-center gap-2.5">
                          <span
                            className={`h-2.5 w-2.5 rounded-full ${
                              node.visual_state === 'OBSERVED_EVIDENCE'
                                ? 'bg-cyan-400'
                                : node.visual_state === 'CALCULATED_FINDING'
                                ? 'bg-amber-400'
                                : node.visual_state === 'HYPOTHESIS'
                                ? 'bg-violet-400'
                                : node.visual_state === 'RECOMMENDATION'
                                ? 'bg-emerald-400'
                                : 'bg-rose-400'
                            }`}
                          />
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="text-sm font-semibold text-foreground">
                                {node.label}
                              </h4>
                              {node.entity_code && (
                                <span className="font-mono text-xs text-muted-foreground">
                                  [{node.entity_code}]
                                </span>
                              )}
                            </div>
                            {node.subtitle && (
                              <p className="text-xs text-muted-foreground mt-0.5">
                                {node.subtitle}
                              </p>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 self-start sm:self-auto">
                          {node.metric_value !== null && node.metric_value !== undefined && (
                            <div className="rounded bg-secondary/50 px-2 py-0.5 text-xs font-mono font-bold text-foreground">
                              {String(node.metric_value)} {node.unit || ''}
                            </div>
                          )}

                          <Badge variant={cfg.badgeVariant} className="text-[10px]">
                            {cfg.label}
                          </Badge>
                        </div>
                      </div>

                      {/* Micro Metadata preview */}
                      <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-border/40 pt-2 text-[11px] text-muted-foreground font-mono">
                        <span>Status: <strong className="text-foreground">{node.data_status}</strong></span>
                        <span>•</span>
                        <span>Verification: <strong className="text-foreground">{node.verification_status}</strong></span>
                        {node.calculation_formula && (
                          <>
                            <span>•</span>
                            <span className="truncate max-w-[280px]">Formula: {node.calculation_formula}</span>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right 4 Cols: Detailed Node Inspection Docket Drawer */}
            <div className="lg:col-span-4 rounded-xl border border-border bg-card p-5 shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-border pb-3">
                <FileText className="h-4 w-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-foreground">
                  Node Forensic Docket Inspector
                </h3>
              </div>

              {selectedNode ? (
                <div className="space-y-4 text-xs">
                  {/* Node Identity & Visual State */}
                  <div>
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Inspected Node ID:
                    </span>
                    <div className="font-mono text-sm font-bold text-primary mt-0.5">
                      {selectedNode.node_id}
                    </div>
                    <Badge
                      variant={VISUAL_STATE_CONFIG[selectedNode.visual_state]?.badgeVariant || 'slate'}
                      className="mt-1 text-[10px]"
                    >
                      {VISUAL_STATE_CONFIG[selectedNode.visual_state]?.label}
                    </Badge>
                  </div>

                  {/* Node Title & Subtitle */}
                  <div className="rounded-lg bg-secondary/30 p-3 space-y-1">
                    <div className="font-semibold text-foreground text-sm">{selectedNode.label}</div>
                    {selectedNode.subtitle && (
                      <p className="text-muted-foreground text-xs">{selectedNode.subtitle}</p>
                    )}
                  </div>

                  {/* Core Inspection Attributes */}
                  <div className="space-y-2 border-y border-border py-3">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Source Identifier:</span>
                      <span className="font-mono font-semibold text-foreground">
                        {selectedNode.entity_code || 'BOUNDARY_ROOT'}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Timestamp / Window:</span>
                      <span className="font-mono text-[11px] text-foreground truncate max-w-[180px]">
                        {selectedNode.timestamp_or_period || 'N/A'}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Measurement / Metric:</span>
                      <span className="font-mono font-bold text-foreground">
                        {selectedNode.metric_value !== null && selectedNode.metric_value !== undefined
                          ? `${String(selectedNode.metric_value)} ${selectedNode.unit || ''}`
                          : 'N/A'}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Data Status:</span>
                      <span className="font-semibold text-emerald-400">{selectedNode.data_status}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Verification Status:</span>
                      <span className="font-semibold text-foreground">{selectedNode.verification_status}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Data Provenance:</span>
                      <span className="text-muted-foreground">
                        {selectedNode.is_simulated ? 'SYNTHETIC_SIMULATION' : 'REAL_UTILITY_INGEST'}
                      </span>
                    </div>
                  </div>

                  {/* Calculation Formula */}
                  {selectedNode.calculation_formula && (
                    <div className="space-y-1">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                        Calculation Formula:
                      </span>
                      <div className="rounded bg-secondary/40 p-2 font-mono text-[11px] text-foreground break-all">
                        {selectedNode.calculation_formula}
                      </div>
                    </div>
                  )}

                  {/* Governing Reasoning Rule */}
                  {selectedNode.reasoning_rule && (
                    <div className="space-y-1">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                        Reasoning Rule:
                      </span>
                      <div className="rounded bg-secondary/40 p-2 font-mono text-[11px] text-primary">
                        {selectedNode.reasoning_rule}
                      </div>
                    </div>
                  )}

                  {/* Supporting Evidence Items */}
                  {selectedNode.supporting_evidence_ids.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                        Supporting Evidence ({selectedNode.supporting_evidence_ids.length}):
                      </span>
                      <div className="flex flex-wrap gap-1.5 pt-0.5">
                        {selectedNode.supporting_evidence_ids.map((evId, idx) => (
                          <span
                            key={idx}
                            className="rounded border border-border bg-background px-2 py-0.5 font-mono text-[10px] text-foreground"
                          >
                            {evId}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Missing Evidence Items */}
                  {selectedNode.missing_evidence_list.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                        Missing Telemetry Elements:
                      </span>
                      <ul className="space-y-1 text-[11px] text-muted-foreground">
                        {selectedNode.missing_evidence_list.map((m, idx) => (
                          <li key={idx} className="flex items-start gap-1">
                            <span className="text-amber-400 font-bold">•</span>
                            <span>{m}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-muted-foreground">
                  Select any node in the graph lineage flow to inspect its forensic docket attributes.
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

