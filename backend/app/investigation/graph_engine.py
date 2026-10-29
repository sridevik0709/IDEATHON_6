"""
Evidence Investigation Graph Engine.
Level 5: Evidence Traceability and What-If Analysis.

Constructs an interactive, inspectable directed graph connecting:
Detected Discrepancy
  -> Source Measurements
  -> Data-Quality Findings
  -> Possible Explanations (Hypotheses)
  -> Verification Actions
  -> Investigation Outcome

Visual State Conventions:
- OBSERVED_EVIDENCE: Concrete physical sensor reads, raw telemetry records, meter readings.
- CALCULATED_FINDING: Deterministic math outputs (discrepancy, unaccounted kWh, audit flags).
- HYPOTHESIS: Plausible root-cause explanations evaluated by the multi-hypothesis engine.
- RECOMMENDATION: Actionable physical/digital triage steps for utility engineers.
- CONFIRMED_OUTCOME: Standard forensic case classification and closure state.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.accounting.data_quality import QualityFinding
from app.accounting.engine import AccountingDossier, EnergyAccountingEngine
from app.ai_services.hypothesis_engine import HypothesisAnalysis, HypothesisGenerationEngine
from app.ai_services.prioritizer import InvestigationPrioritizer, PrioritizationReport
from app.schemas.what_if import (
    GraphEdgeSchema,
    GraphNodeSchema,
    InvestigationGraphResponse,
)


class EvidenceGraphBuilder:
    """
    Constructs an interactive Node-Link forensic graph tracing detected discrepancies
    back to raw sensor measurements, audit rules, competing hypotheses, and triage actions.
    """

    @classmethod
    def build_graph(
        cls,
        dossier: AccountingDossier,
        hypotheses: List[HypothesisAnalysis],
        prioritization: PrioritizationReport,
    ) -> InvestigationGraphResponse:
        nodes: List[GraphNodeSchema] = []
        edges: List[GraphEdgeSchema] = []

        # ----------------------------------------------------------------------
        # 1. Root Node: Detected Discrepancy (CALCULATED_FINDING)
        # ----------------------------------------------------------------------
        root_node_id = f"NODE_DISC_{dossier.boundary_asset_code}"
        nodes.append(GraphNodeSchema(
            node_id=root_node_id,
            node_type="DISCREPANCY_ROOT",
            visual_state="CALCULATED_FINDING",
            label=f"Boundary Discrepancy: {dossier.boundary_asset_code}",
            subtitle=f"{dossier.boundary_asset_name} ({dossier.voltage_class})",
            entity_code=dossier.boundary_asset_code,
            timestamp_or_period=f"{dossier.time_window_start} to {dossier.time_window_end}",
            metric_value=round(dossier.unaccounted_energy_kwh, 2),
            unit="KWH",
            data_status="VALID",
            calculation_formula="E_unaccounted = E_in - E_downstream - E_technical",
            supporting_evidence_ids=[s.entity_code for s in dossier.source_measurements],
            missing_evidence_list=[],
            reasoning_rule="RULE_DETERMINISTIC_ACCOUNTING_CONSERVATION_OF_ENERGY",
            verification_status="VERIFIED",
            is_simulated=True,
            metadata={
                "energy_entering_kwh": dossier.energy_entering_boundary_kwh,
                "recorded_downstream_kwh": dossier.recorded_downstream_energy_kwh,
                "technical_losses_kwh": dossier.other_accounted_flows_kwh,
                "gross_discrepancy_kwh": dossier.gross_discrepancy_kwh,
                "discrepancy_pct": dossier.discrepancy_percentage,
                "sensor_uncertainty_kwh": dossier.sensor_uncertainty_kwh,
            },
        ))

        # ----------------------------------------------------------------------
        # 2. Source Measurement Nodes (OBSERVED_EVIDENCE)
        # ----------------------------------------------------------------------
        # A. Boundary Input Feeder Meter
        input_node_id = f"NODE_SRC_IN_{dossier.boundary_asset_code}"
        nodes.append(GraphNodeSchema(
            node_id=input_node_id,
            node_type="SOURCE_MEASUREMENT",
            visual_state="OBSERVED_EVIDENCE",
            label=f"Primary Input Telemetry: {dossier.boundary_asset_code}",
            subtitle=f"Boundary Feeder Sensor ({dossier.total_actual_intervals} intervals)",
            entity_code=dossier.boundary_asset_code,
            timestamp_or_period=f"{dossier.time_window_start} to {dossier.time_window_end}",
            metric_value=round(dossier.energy_entering_boundary_kwh, 2),
            unit="KWH",
            data_status="VALID",
            calculation_formula="E_in = SUM(boundary_readings.energy_kwh)",
            supporting_evidence_ids=[f"EV-BND-{dossier.boundary_asset_code}"],
            missing_evidence_list=[],
            reasoning_rule="RULE_PHYSICAL_CT_PT_INTEGRATION",
            verification_status="VERIFIED",
            is_simulated=True,
            metadata={
                "readings_count": dossier.total_actual_intervals,
                "expected_intervals": dossier.total_expected_intervals,
                "missing_intervals": dossier.missing_intervals_count,
            },
        ))
        edges.append(GraphEdgeSchema(
            edge_id=f"EDGE_{root_node_id}_{input_node_id}",
            source_node_id=root_node_id,
            target_node_id=input_node_id,
            relationship_type="DERIVED_FROM",
            label="Inflow Boundary Energy",
            is_dashed=False,
        ))

        # B. Downstream Child Entities (Meters or Child Transformers)
        downstream_node_ids: List[str] = []
        for idx, src in enumerate(dossier.source_measurements):
            src_node_id = f"NODE_SRC_CHILD_{src.entity_code}"
            downstream_node_ids.append(src_node_id)
            nodes.append(GraphNodeSchema(
                node_id=src_node_id,
                node_type="SOURCE_MEASUREMENT",
                visual_state="OBSERVED_EVIDENCE",
                label=f"Recorded Telemetry: {src.entity_code}",
                subtitle=f"{src.entity_type} ({src.readings_count} intervals)",
                entity_code=src.entity_code,
                timestamp_or_period=f"{dossier.time_window_start} to {dossier.time_window_end}",
                metric_value=round(src.total_energy_kwh, 2),
                unit=src.unit,
                data_status=src.validation_status,
                calculation_formula=f"E_rec = SUM({src.entity_code}.readings)",
                supporting_evidence_ids=[f"EV-SRC-{src.entity_code}"],
                missing_evidence_list=[],
                reasoning_rule="RULE_AGGREGATE_DOWNSTREAM_ACCUMULATION",
                verification_status="VERIFIED",
                is_simulated=src.is_simulated,
                metadata={
                    "readings_count": src.readings_count,
                    "interval_minutes": src.interval_minutes,
                    "validation_status": src.validation_status,
                },
            ))
            edges.append(GraphEdgeSchema(
                edge_id=f"EDGE_{root_node_id}_{src_node_id}",
                source_node_id=root_node_id,
                target_node_id=src_node_id,
                relationship_type="DERIVED_FROM",
                label="Downstream Energy Delivery",
                is_dashed=False,
            ))

        # ----------------------------------------------------------------------
        # 3. Data-Quality Finding Nodes (CALCULATED_FINDING / OBSERVED_EVIDENCE)
        # ----------------------------------------------------------------------
        dq_node_ids: List[str] = []
        if dossier.data_quality_findings:
            for idx, finding in enumerate(dossier.data_quality_findings):
                dq_node_id = f"NODE_DQ_{finding.rule_code}_{idx}"
                dq_node_ids.append(dq_node_id)
                nodes.append(GraphNodeSchema(
                    node_id=dq_node_id,
                    node_type="DATA_QUALITY_FINDING",
                    visual_state="CALCULATED_FINDING",
                    label=f"Audit Finding: {finding.rule_code}",
                    subtitle=f"{finding.dimension} ({finding.severity})",
                    entity_code=finding.target_entity,
                    timestamp_or_period=f"{dossier.time_window_start}",
                    metric_value=1.0 if not finding.passed else 0.0,
                    unit="FLAG",
                    data_status="FLAGGED" if not finding.passed else "VALID",
                    calculation_formula=f"AuditRule({finding.rule_code})",
                    supporting_evidence_ids=[f"EV-DQ-{finding.rule_code}"],
                    missing_evidence_list=[],
                    reasoning_rule=finding.rule_code,
                    verification_status="VERIFIED",
                    is_simulated=True,
                    metadata={
                        "dimension": finding.dimension,
                        "severity": finding.severity,
                        "diagnostic_message": finding.diagnostic_message,
                        "recommended_action": finding.recommended_action,
                    },
                ))
                # Link finding to target child or root
                target_src = next((nid for nid in downstream_node_ids if finding.target_entity in nid), input_node_id)
                edges.append(GraphEdgeSchema(
                    edge_id=f"EDGE_{target_src}_{dq_node_id}",
                    source_node_id=target_src,
                    target_node_id=dq_node_id,
                    relationship_type="AUDITED_BY",
                    label="Quality Audit Evaluation",
                    is_dashed=False,
                ))
        else:
            # Clean audit node
            clean_dq_id = f"NODE_DQ_CLEAN_{dossier.boundary_asset_code}"
            dq_node_ids.append(clean_dq_id)
            nodes.append(GraphNodeSchema(
                node_id=clean_dq_id,
                node_type="DATA_QUALITY_FINDING",
                visual_state="CALCULATED_FINDING",
                label="10-Point Data Quality Audit: 100% Passed",
                subtitle="Zero telemetry packet corruption or intervals missing",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=f"{dossier.time_window_start} to {dossier.time_window_end}",
                metric_value=100.0,
                unit="%",
                data_status="VALID",
                calculation_formula="PassRate = (PassedRules / TotalRules) * 100",
                supporting_evidence_ids=["EV-DQ-CLEAN-ALL"],
                missing_evidence_list=[],
                reasoning_rule="RULE_10_POINT_AUDIT_SUITE",
                verification_status="VERIFIED",
                is_simulated=True,
                metadata={"status": "PASSED_ALL_10_POINTS"},
            ))
            edges.append(GraphEdgeSchema(
                edge_id=f"EDGE_{root_node_id}_{clean_dq_id}",
                source_node_id=root_node_id,
                target_node_id=clean_dq_id,
                relationship_type="AUDITED_BY",
                label="10-Point Quality Audit",
                is_dashed=False,
            ))

        # ----------------------------------------------------------------------
        # 4. Hypothesis Nodes (HYPOTHESIS)
        # ----------------------------------------------------------------------
        hyp_node_ids: List[str] = []
        for h in hypotheses:
            hyp_node_id = f"NODE_HYP_{h.code}"
            hyp_node_ids.append(hyp_node_id)
            nodes.append(GraphNodeSchema(
                node_id=hyp_node_id,
                node_type="HYPOTHESIS_EXPLANATION",
                visual_state="HYPOTHESIS",
                label=f"Hypothesis: {h.title}",
                subtitle=f"Category: {h.category} | Plausibility: {h.plausibility}",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=f"{dossier.time_window_start} to {dossier.time_window_end}",
                metric_value=round(h.confidence_score * 100, 1),
                unit="%",
                data_status="HYPOTHETICAL",
                calculation_formula=f"MultiHypothesisEvaluation({h.code})",
                supporting_evidence_ids=[ev.evidence_id for ev in h.supporting_evidence],
                missing_evidence_list=h.missing_evidence,
                reasoning_rule=f"FORENSIC_RULE_{h.code}",
                verification_status=h.investigation_status,
                is_simulated=True,
                metadata={
                    "code": h.code,
                    "confidence_rationale": h.confidence_rationale,
                    "investigation_priority": h.investigation_priority,
                    "plausibility": h.plausibility,
                    "supporting_count": len(h.supporting_evidence),
                    "contradicting_count": len(h.contradicting_evidence),
                },
            ))

            # Connect discrepancy to hypothesis
            edges.append(GraphEdgeSchema(
                edge_id=f"EDGE_{root_node_id}_{hyp_node_id}",
                source_node_id=root_node_id,
                target_node_id=hyp_node_id,
                relationship_type="EXPLAINED_BY",
                label=f"Plausibility: {h.plausibility}",
                is_dashed=h.plausibility not in ("HIGH", "MEDIUM"),
            ))

            # Connect relevant data quality finding to hypothesis
            for dq_id in dq_node_ids:
                edges.append(GraphEdgeSchema(
                    edge_id=f"EDGE_{dq_id}_{hyp_node_id}",
                    source_node_id=dq_id,
                    target_node_id=hyp_node_id,
                    relationship_type="INFORMS",
                    label="Informs Plausibility",
                    is_dashed=True,
                ))

        # ----------------------------------------------------------------------
        # 5. Verification Action Nodes (RECOMMENDATION)
        # ----------------------------------------------------------------------
        # Top recommended hypothesis
        top_hyp = next((h for h in hypotheses if h.title == prioritization.top_recommended_hypothesis), hypotheses[0])
        action_node_ids: List[str] = []
        for step_idx, step_desc in enumerate(top_hyp.recommended_verification_steps[:3]):
            action_node_id = f"NODE_ACTION_{top_hyp.code}_{step_idx + 1}"
            action_node_ids.append(action_node_id)
            nodes.append(GraphNodeSchema(
                node_id=action_node_id,
                node_type="VERIFICATION_ACTION",
                visual_state="RECOMMENDATION",
                label=f"Action Step {step_idx + 1}: {step_desc[:45]}...",
                subtitle=f"Target: {top_hyp.title} (Priority: {top_hyp.investigation_priority})",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period="SCHEDULED_TRIAGE",
                metric_value=step_idx + 1,
                unit="STEP",
                data_status="HYPOTHETICAL",
                calculation_formula="ActionSequence(PriorityScore)",
                supporting_evidence_ids=[],
                missing_evidence_list=[],
                reasoning_rule="RULE_PROGRESSIVE_TRIAGE_PHASE",
                verification_status="PENDING_FIELD_CHECK",
                is_simulated=True,
                metadata={"full_description": step_desc, "step_number": step_idx + 1},
            ))

            # Connect hypothesis to verification action
            top_hyp_node_id = f"NODE_HYP_{top_hyp.code}"
            edges.append(GraphEdgeSchema(
                edge_id=f"EDGE_{top_hyp_node_id}_{action_node_id}",
                source_node_id=top_hyp_node_id,
                target_node_id=action_node_id,
                relationship_type="RECOMMENDS",
                label="Action Recommendation",
                is_dashed=False,
            ))

        # ----------------------------------------------------------------------
        # 6. Investigation Outcome Node (CONFIRMED_OUTCOME)
        # ----------------------------------------------------------------------
        outcome_node_id = f"NODE_OUTCOME_{dossier.boundary_asset_code}"
        nodes.append(GraphNodeSchema(
            node_id=outcome_node_id,
            node_type="INVESTIGATION_OUTCOME",
            visual_state="CONFIRMED_OUTCOME",
            label=f"Outcome: {dossier.neutral_classification}",
            subtitle=f"Priority Score: {prioritization.total_priority_score:.1f}/100 ({prioritization.priority_level})",
            entity_code=dossier.boundary_asset_code,
            timestamp_or_period=f"{dossier.time_window_start} to {dossier.time_window_end}",
            metric_value=round(prioritization.total_priority_score, 1),
            unit="SCORE",
            data_status="VALID",
            calculation_formula="ForensicClassification(NeutralProtocol)",
            supporting_evidence_ids=[root_node_id],
            missing_evidence_list=[],
            reasoning_rule="RULE_NEUTRAL_FORENSIC_TRIAGE",
            verification_status="VERIFIED",
            is_simulated=True,
            metadata={
                "classification_reason": dossier.classification_reason,
                "operational_action_summary": prioritization.operational_action_summary,
            },
        ))

        # Link verification actions to outcome
        for action_id in action_node_ids:
            edges.append(GraphEdgeSchema(
                edge_id=f"EDGE_{action_id}_{outcome_node_id}",
                source_node_id=action_id,
                target_node_id=outcome_node_id,
                relationship_type="LEADS_TO",
                label="Resolves Toward Outcome",
                is_dashed=False,
            ))

        # Graph Summary Metrics
        summary = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes_by_visual_state": {
                "OBSERVED_EVIDENCE": len([n for n in nodes if n.visual_state == "OBSERVED_EVIDENCE"]),
                "CALCULATED_FINDING": len([n for n in nodes if n.visual_state == "CALCULATED_FINDING"]),
                "HYPOTHESIS": len([n for n in nodes if n.visual_state == "HYPOTHESIS"]),
                "RECOMMENDATION": len([n for n in nodes if n.visual_state == "RECOMMENDATION"]),
                "CONFIRMED_OUTCOME": len([n for n in nodes if n.visual_state == "CONFIRMED_OUTCOME"]),
            },
            "top_recommended_hypothesis": prioritization.top_recommended_hypothesis,
            "priority_score": prioritization.total_priority_score,
            "priority_level": prioritization.priority_level,
        }

        return InvestigationGraphResponse(
            boundary_asset_code=dossier.boundary_asset_code,
            boundary_asset_name=dossier.boundary_asset_name,
            voltage_class=dossier.voltage_class,
            analysis_period_start=str(dossier.time_window_start),
            analysis_period_end=str(dossier.time_window_end),
            nodes=nodes,
            edges=edges,
            summary=summary,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

