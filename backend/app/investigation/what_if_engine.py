"""
What-If Simulation and Before-and-After Comparison Engine.
Level 5: Evidence Traceability and What-If Analysis.

Features:
1. Supports 5 Repeatable What-If Scenarios:
   - SCENARIO 1: A delayed reading becomes available (packet latency resolved).
   - SCENARIO 2: Measurement intervals are aligned (15-min resampled to 60-min).
   - SCENARIO 3: A simulated mapping error is corrected (GIS topology re-mapped).
   - SCENARIO 4: A duplicate record is removed (telemetry collision deduplication).
   - SCENARIO 5: A documented data-quality issue is corrected (CT polarity, voltage spike).
2. Before-and-After Comparative Analysis:
   - Computes original vs revised accounting dossiers.
   - Computes exact mathematical delta (kWh and %).
   - Computes data quality warning resolution diff.
   - Tracks hypothesis plausibility and confidence shifts.
3. Strict Data Protection Mandates:
   - NEVER mutates or overwrites primary telemetry records.
   - Isolates simulations entirely in-memory.
   - Persists what-if records separately in ScenarioRun & AuditLog.
   - Enforces that hypothetical corrections cannot automatically close or resolve real field cases.
"""

import copy
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.accounting.data_quality import QualityFinding
from app.accounting.engine import AccountingDossier, EnergyAccountingEngine
from app.ai_services.hypothesis_engine import HypothesisAnalysis, HypothesisGenerationEngine
from app.ai_services.prioritizer import InvestigationPrioritizer, PrioritizationReport
from app.database.models import AuditLog, ScenarioRun
from app.schemas.what_if import (
    AccountingDeltaSchema,
    BeforeAfterComparisonResponse,
    DataProtectionGuaranteeSchema,
    DifferenceSummarySchema,
    WhatIfCatalogItemSchema,
    WhatIfCorrectionRequest,
)

logger = logging.getLogger("gridguard.what_if")


class WhatIfCatalog:
    """Catalog of supported what-if scenarios with descriptions and default parameters."""

    SCENARIOS = {
        "DELAYED_READINGS_ARRIVED": WhatIfCatalogItemSchema(
            scenario_type="DELAYED_READINGS_ARRIVED",
            title="A Delayed Downstream Reading Becomes Available",
            category="TELECOMMUNICATION_LATENCY",
            description="Simulates the arrival of delayed telemetry packets from downstream aggregate meters (e.g., buffered afternoon packets from 14:00 to 18:00 UTC).",
            typical_impact="Reduces apparent discrepancy by recovering delayed kWh, restoring boundary balance within technical loss bounds.",
            default_parameters={"delayed_kwh_recovered": 16.5, "target_meter_code": "AGG-MTR-DT102-A"},
        ),
        "ALIGN_MEASUREMENT_INTERVALS": WhatIfCatalogItemSchema(
            scenario_type="ALIGN_MEASUREMENT_INTERVALS",
            title="Measurement Intervals are Aligned",
            category="TEMPORAL_SYNCHRONIZATION",
            description="Resamples mixed 15-minute and 60-minute telemetry into unified, synchronized 60-minute integration windows.",
            typical_impact="Eliminates ERR_INTERVAL_MISMATCH quality audit warnings and harmonizes boundary balance integration.",
            default_parameters={"target_interval_minutes": 60},
        ),
        "CORRECT_TOPOLOGICAL_MAPPING": WhatIfCatalogItemSchema(
            scenario_type="CORRECT_TOPOLOGICAL_MAPPING",
            title="A Simulated Topological Mapping Error is Corrected",
            category="GIS_NETWORK_TOPOLOGY",
            description="Simulates reassigning a cluster meter erroneously mapped to an adjacent feeder back to its true physical transformer.",
            typical_impact="Adds unmapped downstream deliveries to the boundary, restoring feeder balance and eliminating apparent deficits.",
            default_parameters={"reassigned_meter_code": "AGG-MTR-DT102-B", "meter_energy_kwh": 312.4},
        ),
        "REMOVE_DUPLICATE_RECORDS": WhatIfCatalogItemSchema(
            scenario_type="REMOVE_DUPLICATE_RECORDS",
            title="A Duplicate Telemetry Record is Removed",
            category="DATA_INTEGRITY_DEDUPLICATION",
            description="Deduplicates dual telemetry packets transmitted for identical timestamps, retaining the single verified reading.",
            typical_impact="Eliminates ERR_DUPLICATE_RECORD warning and prevents over-counting of downstream consumption.",
            default_parameters={"duplicate_kwh_removed": 25.8},
        ),
        "CORRECT_DATA_QUALITY_ISSUES": WhatIfCatalogItemSchema(
            scenario_type="CORRECT_DATA_QUALITY_ISSUES",
            title="A Documented Data-Quality Issue is Corrected",
            category="SENSOR_CALIBRATION_REPAIR",
            description="Corrects sensor calibration errors: inverts reversed CT polarity (-kWh -> +kWh) and caps extreme overvoltage spikes to nominal 230V.",
            typical_impact="Resolves ERR_NEGATIVE_ENERGY and ERR_VOLTAGE_SPIKE findings and stabilizes balance calculations.",
            default_parameters={"negative_reading_reversal_kwh": 42.5, "voltage_surge_clamped_volts": 230.0},
        ),
    }

    @classmethod
    def list_catalog(cls) -> List[WhatIfCatalogItemSchema]:
        return list(cls.SCENARIOS.values())


class WhatIfSimulationEngine:
    """
    Executes in-memory what-if simulations with mathematical before-and-after comparison.
    Ensures complete isolation from production database tables.
    """

    @classmethod
    def run_simulation(
        cls,
        db: Session,
        request: WhatIfCorrectionRequest,
    ) -> BeforeAfterComparisonResponse:
        """
        Executes a hypothetical what-if scenario on a boundary asset, comparing before vs after.
        """
        asset_code = request.boundary_asset_code
        scenario_type = request.scenario_type.upper().strip()
        params = request.parameters or {}

        # 1. Fetch Original Baseline Dossier (Deterministic Ground Truth)
        original_dossier = EnergyAccountingEngine.reconcile_boundary(
            db=db,
            boundary_asset_code=asset_code,
        )
        original_hypotheses = HypothesisGenerationEngine.analyze_discrepancy(original_dossier)
        original_prioritization = InvestigationPrioritizer.compute_priority(original_dossier, original_hypotheses)

        # 2. Build In-Memory Revised Dossier Copy (Zero Database Mutation!)
        revised_dossier = copy.deepcopy(original_dossier)
        assumption_text = ""
        resolved_warnings: List[str] = []
        scenario_title = WhatIfCatalog.SCENARIOS.get(scenario_type, WhatIfCatalogItemSchema(
            scenario_type=scenario_type,
            title="Custom What-If Assumption",
            category="CUSTOM",
            description="Custom parameter override",
            typical_impact="Varies",
            default_parameters={},
        )).title

        # ----------------------------------------------------------------------
        # Scenario 1: Delayed Readings Arrived
        # ----------------------------------------------------------------------
        if scenario_type == "DELAYED_READINGS_ARRIVED":
            delayed_kwh = float(params.get("delayed_kwh_recovered", 16.5))
            target_meter = params.get("target_meter_code", "AGG-MTR-DT102-A")
            assumption_text = (
                f"Hypothetical assumption: Delayed AMR cellular telemetry containing {delayed_kwh:.2f} kWh "
                f"from {target_meter} has arrived and is integrated into the downstream accounting balance."
            )

            # Revise downstream recorded energy
            revised_dossier.recorded_downstream_energy_kwh += delayed_kwh
            revised_dossier.gross_discrepancy_kwh = max(0.0, revised_dossier.energy_entering_boundary_kwh - revised_dossier.recorded_downstream_energy_kwh)
            revised_dossier.unaccounted_energy_kwh = max(
                -revised_dossier.sensor_uncertainty_kwh,
                revised_dossier.energy_entering_boundary_kwh - revised_dossier.recorded_downstream_energy_kwh - revised_dossier.other_accounted_flows_kwh,
            )
            revised_dossier.discrepancy_percentage = round(
                (revised_dossier.gross_discrepancy_kwh / max(revised_dossier.energy_entering_boundary_kwh, 1.0)) * 100.0, 2
            )
            resolved_warnings.append("ERR_MISSING_READING [Delayed packets arrived]")
            resolved_warnings.append("FLAG_DOWNSTREAM_LATENCY_DEFICIT")

        # ----------------------------------------------------------------------
        # Scenario 2: Align Measurement Intervals
        # ----------------------------------------------------------------------
        elif scenario_type == "ALIGN_MEASUREMENT_INTERVALS":
            target_interval = int(params.get("target_interval_minutes", 60))
            assumption_text = (
                f"Hypothetical assumption: Resampled all downstream telemetry to synchronized {target_interval}-minute "
                "integration intervals, eliminating sub-hourly boundary interval skew."
            )
            # Minor alignment reconciliation adjustments
            resolved_warnings.append("ERR_INTERVAL_MISMATCH [15-min and 60-min intervals aligned]")
            # Remove interval mismatch from findings
            revised_dossier.data_quality_findings = [
                f for f in revised_dossier.data_quality_findings if f.rule_code != "ERR_INTERVAL_MISMATCH"
            ]

        # ----------------------------------------------------------------------
        # Scenario 3: Correct Topological Mapping Error
        # ----------------------------------------------------------------------
        elif scenario_type == "CORRECT_TOPOLOGICAL_MAPPING":
            mapped_meter = params.get("reassigned_meter_code", "AGG-MTR-DT102-B")
            mapped_kwh = float(params.get("meter_energy_kwh", 312.4))
            assumption_text = (
                f"Hypothetical assumption: Reassigned consumer cluster meter {mapped_meter} "
                f"({mapped_kwh:.1f} kWh) from adjacent feeder to {asset_code} per updated GIS single-line diagram."
            )
            # If original discrepancy had negative loss or missing child:
            revised_dossier.recorded_downstream_energy_kwh += mapped_kwh
            revised_dossier.gross_discrepancy_kwh = abs(revised_dossier.energy_entering_boundary_kwh - revised_dossier.recorded_downstream_energy_kwh)
            revised_dossier.unaccounted_energy_kwh = revised_dossier.energy_entering_boundary_kwh - revised_dossier.recorded_downstream_energy_kwh - revised_dossier.other_accounted_flows_kwh
            revised_dossier.discrepancy_percentage = round(
                (revised_dossier.gross_discrepancy_kwh / max(revised_dossier.energy_entering_boundary_kwh, 1.0)) * 100.0, 2
            )
            resolved_warnings.append("ERR_TOPOLOGICAL_MAPPING_MISMATCH [Reassigned cluster to correct DT]")

        # ----------------------------------------------------------------------
        # Scenario 4: Remove Duplicate Records
        # ----------------------------------------------------------------------
        elif scenario_type == "REMOVE_DUPLICATE_RECORDS":
            dup_kwh = float(params.get("duplicate_kwh_removed", 25.8))
            assumption_text = (
                f"Hypothetical assumption: Removed duplicate telemetry packets ({dup_kwh:.2f} kWh) "
                "caused by gateway transmission retries."
            )
            revised_dossier.recorded_downstream_energy_kwh = max(0.0, revised_dossier.recorded_downstream_energy_kwh - dup_kwh)
            revised_dossier.gross_discrepancy_kwh = abs(revised_dossier.energy_entering_boundary_kwh - revised_dossier.recorded_downstream_energy_kwh)
            revised_dossier.unaccounted_energy_kwh = revised_dossier.energy_entering_boundary_kwh - revised_dossier.recorded_downstream_energy_kwh - revised_dossier.other_accounted_flows_kwh
            revised_dossier.discrepancy_percentage = round(
                (revised_dossier.gross_discrepancy_kwh / max(revised_dossier.energy_entering_boundary_kwh, 1.0)) * 100.0, 2
            )
            resolved_warnings.append("ERR_DUPLICATE_RECORD [Removed collided packets]")
            revised_dossier.data_quality_findings = [
                f for f in revised_dossier.data_quality_findings if f.rule_code != "ERR_DUPLICATE_RECORD"
            ]

        # ----------------------------------------------------------------------
        # Scenario 5: Correct Data Quality Issues
        # ----------------------------------------------------------------------
        elif scenario_type == "CORRECT_DATA_QUALITY_ISSUES":
            inverted_kwh = float(params.get("negative_reading_reversal_kwh", 42.5))
            assumption_text = (
                f"Hypothetical assumption: Inverted reversed CT polarity reading ({inverted_kwh:.1f} kWh) "
                "and clamped voltage spikes to nominal 230V."
            )
            revised_dossier.recorded_downstream_energy_kwh += (inverted_kwh * 2)  # from negative to positive
            revised_dossier.gross_discrepancy_kwh = abs(revised_dossier.energy_entering_boundary_kwh - revised_dossier.recorded_downstream_energy_kwh)
            revised_dossier.unaccounted_energy_kwh = revised_dossier.energy_entering_boundary_kwh - revised_dossier.recorded_downstream_energy_kwh - revised_dossier.other_accounted_flows_kwh
            revised_dossier.discrepancy_percentage = round(
                (revised_dossier.gross_discrepancy_kwh / max(revised_dossier.energy_entering_boundary_kwh, 1.0)) * 100.0, 2
            )
            resolved_warnings.append("ERR_NEGATIVE_ENERGY [Reversed CT polarity corrected]")
            resolved_warnings.append("ERR_VOLTAGE_SPIKE [Clamped to 230V nominal]")
            revised_dossier.data_quality_findings = [
                f for f in revised_dossier.data_quality_findings if f.rule_code not in ("ERR_NEGATIVE_ENERGY", "ERR_VOLTAGE_SPIKE")
            ]

        else:
            assumption_text = f"Hypothetical custom parameter adjustments applied to boundary {asset_code}."

        # Re-classify revised dossier
        if abs(revised_dossier.unaccounted_energy_kwh) <= (revised_dossier.sensor_uncertainty_kwh * 1.5):
            revised_dossier.neutral_classification = "NORMAL_TECHNICAL_LOSS"
            revised_dossier.classification_reason = (
                f"Under this hypothetical correction, the residual discrepancy "
                f"({revised_dossier.discrepancy_percentage:.2f}%) falls fully within normal technical loss bounds and Class 0.5 sensor uncertainty."
            )
        else:
            revised_dossier.neutral_classification = "UNRECONCILED_RESIDUAL_REQUIRING_INVESTIGATION"

        # 3. Re-evaluate Hypotheses on Revised Dossier
        revised_hypotheses = HypothesisGenerationEngine.analyze_discrepancy(revised_dossier)
        revised_prioritization = InvestigationPrioritizer.compute_priority(revised_dossier, revised_hypotheses)

        # 4. Compute Mathematical Deltas
        delta_unaccounted = revised_dossier.unaccounted_energy_kwh - original_dossier.unaccounted_energy_kwh
        delta_discrepancy_pct = revised_dossier.discrepancy_percentage - original_dossier.discrepancy_percentage
        delta_downstream = revised_dossier.recorded_downstream_energy_kwh - original_dossier.recorded_downstream_energy_kwh
        delta_tech_loss = revised_dossier.other_accounted_flows_kwh - original_dossier.other_accounted_flows_kwh
        classification_changed = revised_dossier.neutral_classification != original_dossier.neutral_classification
        discrepancy_resolved = revised_dossier.neutral_classification == "NORMAL_TECHNICAL_LOSS"

        # 5. Build Hypotheses Shift Map
        orig_top = original_prioritization.top_recommended_hypothesis
        rev_top = revised_prioritization.top_recommended_hypothesis
        hyp_shifts = {
            "original_top_hypothesis": orig_top,
            "revised_top_hypothesis": rev_top,
            "top_hypothesis_changed": orig_top != rev_top,
            "original_priority_score": original_prioritization.total_priority_score,
            "revised_priority_score": revised_prioritization.total_priority_score,
            "delta_priority_score": round(revised_prioritization.total_priority_score - original_prioritization.total_priority_score, 1),
        }

        # 6. Data Protection: Persist Scenario Run Separately
        scenario_run_id = str(uuid.uuid4())
        scenario_record = ScenarioRun(
            id=scenario_run_id,
            scenario_code=f"WHAT_IF_{scenario_type}",
            scenario_name=f"What-If Analysis: {scenario_title}",
            seed=42,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            status="COMPLETED",
            parameters={
                "boundary_asset_code": asset_code,
                "scenario_type": scenario_type,
                "parameters": params,
                "provenance": request.simulated_provenance,
            },
            records_generated_count=0,  # Zero production records created
            summary_metrics={
                "original_unaccounted_kwh": original_dossier.unaccounted_energy_kwh,
                "revised_unaccounted_kwh": revised_dossier.unaccounted_energy_kwh,
                "delta_unaccounted_kwh": delta_unaccounted,
                "discrepancy_resolved": discrepancy_resolved,
            },
            is_simulated=True,
        )
        db.add(scenario_record)

        # Audit Log Entry
        audit_entry = AuditLog(
            id=str(uuid.uuid4()),
            actor_id="FORENSIC_ANALYST",
            actor_role="INVESTIGATOR",
            action="WHAT_IF_SANDBOX_SIMULATION",
            entity_type="BOUNDARY_ASSET",
            entity_id=asset_code,
            details={
                "scenario_type": scenario_type,
                "scenario_run_id": scenario_run_id,
                "data_protection": "STRICT_READ_ONLY_IMMUTABLE",
            },
            timestamp=datetime.now(timezone.utc),
        )
        db.add(audit_entry)
        db.commit()

        # 7. Construct Before-and-After Comparison Response
        data_protection = DataProtectionGuaranteeSchema(
            original_records_unmodified=True,
            scenario_run_id=scenario_run_id,
            correction_provenance=request.simulated_provenance,
            real_case_auto_resolution_prevented=True,
            audit_notice=(
                "Forensic Integrity Guarantee: Original telemetry readings in distribution_boundary_readings "
                "and consumption_readings remain strictly unmodified. This what-if analysis was evaluated in an isolated "
                "in-memory simulation sandbox. Real-world operational cases cannot be closed without physical field verification."
            ),
        )

        return BeforeAfterComparisonResponse(
            boundary_asset_code=asset_code,
            boundary_asset_name=original_dossier.boundary_asset_name,
            scenario_type=scenario_type,
            scenario_title=scenario_title,
            assumption_description=assumption_text,
            original_accounting=AccountingDeltaSchema(
                energy_entering_kwh=round(original_dossier.energy_entering_boundary_kwh, 2),
                recorded_downstream_kwh=round(original_dossier.recorded_downstream_energy_kwh, 2),
                other_accounted_flows_kwh=round(original_dossier.other_accounted_flows_kwh, 2),
                gross_discrepancy_kwh=round(original_dossier.gross_discrepancy_kwh, 2),
                unaccounted_energy_kwh=round(original_dossier.unaccounted_energy_kwh, 2),
                discrepancy_percentage=round(original_dossier.discrepancy_percentage, 2),
                neutral_classification=original_dossier.neutral_classification,
                classification_reason=original_dossier.classification_reason,
            ),
            revised_accounting=AccountingDeltaSchema(
                energy_entering_kwh=round(revised_dossier.energy_entering_boundary_kwh, 2),
                recorded_downstream_kwh=round(revised_dossier.recorded_downstream_energy_kwh, 2),
                other_accounted_flows_kwh=round(revised_dossier.other_accounted_flows_kwh, 2),
                gross_discrepancy_kwh=round(revised_dossier.gross_discrepancy_kwh, 2),
                unaccounted_energy_kwh=round(revised_dossier.unaccounted_energy_kwh, 2),
                discrepancy_percentage=round(revised_dossier.discrepancy_percentage, 2),
                neutral_classification=revised_dossier.neutral_classification,
                classification_reason=revised_dossier.classification_reason,
            ),
            differences=DifferenceSummarySchema(
                delta_unaccounted_kwh=round(delta_unaccounted, 2),
                delta_discrepancy_pct=round(delta_discrepancy_pct, 2),
                delta_downstream_kwh=round(delta_downstream, 2),
                delta_technical_loss_kwh=round(delta_tech_loss, 2),
                classification_changed=classification_changed,
                original_classification=original_dossier.neutral_classification,
                revised_classification=revised_dossier.neutral_classification,
                discrepancy_resolved=discrepancy_resolved,
            ),
            original_quality_warnings_count=len(original_dossier.data_quality_findings),
            revised_quality_warnings_count=len(revised_dossier.data_quality_findings),
            resolved_warnings=resolved_warnings,
            hypotheses_shift=hyp_shifts,
            remaining_uncertainty_kwh=round(revised_dossier.sensor_uncertainty_kwh, 2),
            remaining_uncertainty_pct=round(revised_dossier.remaining_uncertainty_percent, 2),
            data_protection=data_protection,
            executed_at=datetime.now(timezone.utc).isoformat(),
        )

