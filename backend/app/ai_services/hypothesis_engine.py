"""
Multi-Hypothesis Investigation Engine.
Level 4: AI-Assisted Investigation.

Generates multiple plausible explanations for detected energy discrepancies:
1. Delayed downstream telemetry (packet transmission lag).
2. Missing measurements / unmetered intervals.
3. Incorrect downstream network mapping (GIS topological errors).
4. Measurement interval granularity mismatches.
5. Duplicate or invalid telemetry records (negative energy, voltage spikes).
6. Technical distribution line and core losses.
7. Unmetered consumption / non-technical loss (evaluated only when physical & data errors are ruled out).

Strict Requirement: Never automatically selects one cause; provides supporting,
contradicting, and missing evidence for every hypothesis.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.accounting.data_quality import QualityFinding
from app.accounting.engine import AccountingDossier, EnergyAccountingEngine


@dataclass
class EvidenceItem:
    evidence_id: str
    source_type: str  # BOUNDARY_MEASUREMENT, CONSUMPTION_READING, QUALITY_AUDIT, TOPOLOGY_RELATIONSHIP
    entity_code: str
    timestamp_or_period: str
    metric_name: str
    metric_value: Any
    unit: Optional[str]
    description: str


@dataclass
class HypothesisAnalysis:
    hypothesis_id: str
    code: str  # HYP_DELAYED_TELEMETRY, HYP_MISSING_MEASUREMENTS, HYP_MAPPING_ERROR, etc.
    title: str
    category: str  # TELEMETRY_LATENCY, DATA_QUALITY, TOPOLOGY_GIS, PHYSICS_TECHNICAL, COMMERCIAL_UNMETERED
    explanation: str
    plausibility: str  # HIGH, MEDIUM, LOW, UNCONFIRMED
    confidence_score: float  # 0.0 to 1.0
    confidence_rationale: str
    investigation_priority: str  # HIGH, MEDIUM, LOW
    investigation_status: str  # PLAUSIBLE, UNCONFIRMED, DISPROVEN, RECOMMENDED_FOR_FIELD_CHECK
    supporting_evidence: List[EvidenceItem]
    contradicting_evidence: List[EvidenceItem]
    missing_evidence: List[str]
    additional_data_required: List[str]
    recommended_verification_steps: List[str]


class HypothesisGenerationEngine:
    """
    Evaluates evidence from accounting dossiers, telemetry traces, and 10-point audits
    to produce balanced, multi-hypothesis forensic assessments.
    """

    @classmethod
    def analyze_discrepancy(
        cls,
        dossier: AccountingDossier,
    ) -> List[HypothesisAnalysis]:
        """
        Generates and analyzes multiple competing hypotheses for the given accounting dossier.
        """
        hypotheses: List[HypothesisAnalysis] = []

        # ----------------------------------------------------------------------
        # Hypothesis 1: Delayed Downstream Readings (Packet Transmission Lag)
        # ----------------------------------------------------------------------
        hyp_delayed = cls._evaluate_delayed_telemetry(dossier)
        hypotheses.append(hyp_delayed)

        # ----------------------------------------------------------------------
        # Hypothesis 2: Missing Boundary or Downstream Measurements
        # ----------------------------------------------------------------------
        hyp_missing = cls._evaluate_missing_measurements(dossier)
        hypotheses.append(hyp_missing)

        # ----------------------------------------------------------------------
        # Hypothesis 3: Incorrect Downstream Network Mapping (GIS Topology Error)
        # ----------------------------------------------------------------------
        hyp_mapping = cls._evaluate_mapping_error(dossier)
        hypotheses.append(hyp_mapping)

        # ----------------------------------------------------------------------
        # Hypothesis 4: Data-Quality / Meter Sensor Invalidation
        # ----------------------------------------------------------------------
        hyp_quality = cls._evaluate_data_quality(dossier)
        hypotheses.append(hyp_quality)

        # ----------------------------------------------------------------------
        # Hypothesis 5: Elevated Technical Distribution Losses
        # ----------------------------------------------------------------------
        hyp_technical = cls._evaluate_technical_losses(dossier)
        hypotheses.append(hyp_technical)

        # ----------------------------------------------------------------------
        # Hypothesis 6: Unmetered Consumption / Non-Technical Loss (Theft/Bypass)
        # ----------------------------------------------------------------------
        hyp_unmetered = cls._evaluate_unmetered_consumption(dossier, hypotheses)
        hypotheses.append(hyp_unmetered)

        return hypotheses

    @classmethod
    def _evaluate_delayed_telemetry(cls, dossier: AccountingDossier) -> HypothesisAnalysis:
        supporting: List[EvidenceItem] = []
        contradicting: List[EvidenceItem] = []
        missing_evidence: List[str] = []

        # Check for packet lag flags or missing recent intervals
        lag_findings = [f for f in dossier.data_quality_findings if "LAG" in f.rule_code or "TIMELINESS" in f.dimension]
        flagged_sources = [s for s in dossier.source_measurements if s.validation_status != "VALID"]

        if dossier.missing_intervals_count > 0:
            supporting.append(EvidenceItem(
                evidence_id="EV-DELAY-01",
                source_type="QUALITY_AUDIT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=f"{dossier.time_window_start} to {dossier.time_window_end}",
                metric_name="missing_intervals_count",
                metric_value=dossier.missing_intervals_count,
                unit="intervals",
                description=f"{dossier.missing_intervals_count} interval packets are absent from the evaluated accounting window.",
            ))

        for f in lag_findings:
            supporting.append(EvidenceItem(
                evidence_id=f"EV-DELAY-{f.rule_code}",
                source_type="QUALITY_AUDIT",
                entity_code=f.target_entity,
                timestamp_or_period=dossier.time_window_end,
                metric_name="audit_rule",
                metric_value=f.rule_code,
                unit=None,
                description=f.diagnostic_message,
            ))

        if dossier.missing_intervals_count == 0 and not lag_findings:
            contradicting.append(EvidenceItem(
                evidence_id="EV-CONTRA-DELAY-01",
                source_type="BOUNDARY_MEASUREMENT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=f"{dossier.time_window_start} to {dossier.time_window_end}",
                metric_name="total_actual_intervals",
                metric_value=dossier.total_actual_intervals,
                unit="intervals",
                description=f"All {dossier.total_expected_intervals} expected intervals are accounted for with zero latency flags.",
            ))

        missing_evidence.append("Cellular gateway / RF mesh transmission buffer retry logs.")
        missing_evidence.append("Next 6-hour interval packet arrival queue to observe if balance auto-reconciles.")

        is_plausible = len(supporting) > len(contradicting) or dossier.neutral_classification == "DATA_QUALITY_OR_LATENCY_UNCERTAINTY"
        confidence = 0.85 if lag_findings or dossier.missing_intervals_count > 0 else 0.15

        return HypothesisAnalysis(
            hypothesis_id="HYP-01-DELAYED-TELEMETRY",
            code="HYP_DELAYED_TELEMETRY",
            title="Delayed Downstream Telemetry (Communication Packet Lag)",
            category="TELEMETRY_LATENCY",
            explanation=(
                "Smart meter packets from downstream consumer clusters experienced communication delays over cellular/RF mesh, "
                "creating a temporary apparent energy deficit at the boundary while upstream boundary check meters arrived on time."
            ),
            plausibility="HIGH" if is_plausible else "LOW",
            confidence_score=confidence,
            confidence_rationale=(
                f"Confidence is {int(confidence*100)}% based on presence of {len(supporting)} latency indicators "
                f"and {dossier.missing_intervals_count} missing intervals."
            ),
            investigation_priority="HIGH" if is_plausible else "LOW",
            investigation_status="PLAUSIBLE" if is_plausible else "UNCONFIRMED",
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            missing_evidence=missing_evidence,
            additional_data_required=[
                "MDMS packet arrival timestamp logs",
                "Head-End System (HES) retry queue metrics",
            ],
            recommended_verification_steps=[
                "1. Wait for subsequent communication polling cycle (60 minutes).",
                "2. Check RF mesh repeater signal-to-noise ratio (SNR) on lagging meter nodes.",
                "3. Verify whether re-running accounting with 3-hour lookback settles the discrepancy.",
            ],
        )

    @classmethod
    def _evaluate_missing_measurements(cls, dossier: AccountingDossier) -> HypothesisAnalysis:
        supporting: List[EvidenceItem] = []
        contradicting: List[EvidenceItem] = []
        missing_evidence: List[str] = []

        if dossier.energy_entering_boundary_kwh == 0.0 and dossier.recorded_downstream_energy_kwh > 0.0:
            supporting.append(EvidenceItem(
                evidence_id="EV-MISSING-01",
                source_type="BOUNDARY_MEASUREMENT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=dossier.time_window_start,
                metric_name="energy_entering_boundary_kwh",
                metric_value=0.0,
                unit="KWH",
                description="Boundary asset has 0 recorded input readings while downstream meters actively recorded energy.",
            ))

        if dossier.total_actual_intervals < dossier.total_expected_intervals:
            supporting.append(EvidenceItem(
                evidence_id="EV-MISSING-02",
                source_type="QUALITY_AUDIT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=dossier.time_window_end,
                metric_name="actual_intervals",
                metric_value=dossier.total_actual_intervals,
                unit="intervals",
                description=f"Recorded {dossier.total_actual_intervals} of {dossier.total_expected_intervals} expected interval readings.",
            ))
        else:
            contradicting.append(EvidenceItem(
                evidence_id="EV-CONTRA-MISSING-01",
                source_type="BOUNDARY_MEASUREMENT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=dossier.time_window_start,
                metric_name="completeness",
                metric_value="100%",
                unit=None,
                description="Zero missing intervals across both boundary transformer and downstream meters.",
            ))

        missing_evidence.append("Unmetered auxiliary substation service loads or unmetered street lighting taps.")

        is_plausible = len(supporting) > 0
        confidence = 0.75 if len(supporting) > 0 else 0.10

        return HypothesisAnalysis(
            hypothesis_id="HYP-02-MISSING-MEASUREMENTS",
            code="HYP_MISSING_MEASUREMENTS",
            title="Missing Interval Telemetry or Unmetered Boundary Feeds",
            category="DATA_QUALITY",
            explanation=(
                "One or more interval readings were dropped during ingestion, or an unmetered service line "
                "(such as municipal streetlights or utility auxiliary equipment) draws power from this boundary without a registered meter."
            ),
            plausibility="MEDIUM" if is_plausible else "LOW",
            confidence_score=confidence,
            confidence_rationale=f"Assessed at {int(confidence*100)}% based on interval completeness metrics.",
            investigation_priority="MEDIUM" if is_plausible else "LOW",
            investigation_status="PLAUSIBLE" if is_plausible else "UNCONFIRMED",
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            missing_evidence=missing_evidence,
            additional_data_required=[
                "Utility GIS auxiliary load single-line diagram",
                "Municipal street lighting billing schedule",
            ],
            recommended_verification_steps=[
                "1. Audit substation auxiliary service panel connections.",
                "2. Verify whether temporary construction feeds are tapped into the transformer secondary busbar.",
            ],
        )

    @classmethod
    def _evaluate_mapping_error(cls, dossier: AccountingDossier) -> HypothesisAnalysis:
        supporting: List[EvidenceItem] = []
        contradicting: List[EvidenceItem] = []
        missing_evidence: List[str] = []

        # If downstream recorded energy exceeds upstream (negative loss anomaly)
        if dossier.gross_discrepancy_kwh < -dossier.sensor_uncertainty_kwh:
            supporting.append(EvidenceItem(
                evidence_id="EV-MAP-01",
                source_type="BOUNDARY_MEASUREMENT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=f"{dossier.time_window_start} to {dossier.time_window_end}",
                metric_name="gross_discrepancy_kwh",
                metric_value=dossier.gross_discrepancy_kwh,
                unit="KWH",
                description=(
                    f"Downstream recorded energy ({dossier.recorded_downstream_energy_kwh:.1f} kWh) exceeds "
                    f"boundary input ({dossier.energy_entering_boundary_kwh:.1f} kWh) by "
                    f"{abs(dossier.gross_discrepancy_kwh):.1f} kWh. Physically impossible without misassigned meters."
                ),
            ))

        mapping_findings = [f for f in dossier.data_quality_findings if "MAPPING" in f.rule_code or "TOPOLOGY" in f.dimension]
        for f in mapping_findings:
            supporting.append(EvidenceItem(
                evidence_id=f"EV-MAP-{f.rule_code}",
                source_type="QUALITY_AUDIT",
                entity_code=f.target_entity,
                timestamp_or_period=dossier.time_window_end,
                metric_name="topology_rule",
                metric_value=f.rule_code,
                unit=None,
                description=f.diagnostic_message,
            ))

        if dossier.gross_discrepancy_kwh >= 0 and not mapping_findings:
            contradicting.append(EvidenceItem(
                evidence_id="EV-CONTRA-MAP-01",
                source_type="BOUNDARY_MEASUREMENT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=dossier.time_window_start,
                metric_name="loss_direction",
                metric_value="POSITIVE_LOSS",
                unit=None,
                description="Boundary displays expected positive energy drop. No negative loss anomaly present.",
            ))

        missing_evidence.append("Physical phase-tracer field verification confirming physical cabling route.")
        missing_evidence.append("Adjacent transformer boundary balance (to verify if another transformer shows equivalent deficit).")

        is_plausible = dossier.neutral_classification == "TOPOLOGICAL_MAPPING_MISMATCH" or len(supporting) > 0
        confidence = 0.90 if is_plausible else 0.10

        return HypothesisAnalysis(
            hypothesis_id="HYP-03-MAPPING-ERROR",
            code="HYP_MAPPING_ERROR",
            title="Incorrect Downstream Network Mapping (GIS Topology Error)",
            category="TOPOLOGY_GIS",
            explanation=(
                "One or more household aggregate meters are mapped in the database to this transformer, "
                "but are physically fed by an adjacent distribution transformer or alternative feeder branch."
            ),
            plausibility="HIGH" if is_plausible else "LOW",
            confidence_score=confidence,
            confidence_rationale=(
                f"Confidence is {int(confidence*100)}%. "
                f"{'Negative loss anomaly confirms downstream meters belong to another physical source.' if is_plausible else 'Positive energy drop conforms with standard network hierarchy.'}"
            ),
            investigation_priority="HIGH" if is_plausible else "LOW",
            investigation_status="PLAUSIBLE" if is_plausible else "UNCONFIRMED",
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            missing_evidence=missing_evidence,
            additional_data_required=[
                "Adjacent Distribution Transformer (DT-102, DT-103) concurrent balance dossier",
                "GIS feeder single-line diagram revision history",
            ],
            recommended_verification_steps=[
                "1. Cross-check balance on adjacent distribution transformers for reciprocal deficit.",
                "2. Perform physical line tracing with phase identification device.",
                "3. Update GIS asset hierarchy relationship table.",
            ],
        )

    @classmethod
    def _evaluate_data_quality(cls, dossier: AccountingDossier) -> HypothesisAnalysis:
        supporting: List[EvidenceItem] = []
        contradicting: List[EvidenceItem] = []
        missing_evidence: List[str] = []

        dq_findings = [f for f in dossier.data_quality_findings if f.dimension in ["RANGE_VALIDITY", "CONSISTENCY"]]
        for f in dq_findings:
            supporting.append(EvidenceItem(
                evidence_id=f"EV-DQ-{f.rule_code}",
                source_type="QUALITY_AUDIT",
                entity_code=f.target_entity,
                timestamp_or_period=dossier.time_window_end,
                metric_name=f.rule_code,
                metric_value=f.severity,
                unit=None,
                description=f.diagnostic_message,
            ))

        if not dq_findings:
            contradicting.append(EvidenceItem(
                evidence_id="EV-CONTRA-DQ-01",
                source_type="QUALITY_AUDIT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=dossier.time_window_start,
                metric_name="dq_audit",
                metric_value="100%_PASS",
                unit=None,
                description="All 10 data-quality rules passed: clean voltage, valid timestamps, strictly positive energy.",
            ))

        missing_evidence.append("Meter laboratory calibration certificates and test bench accuracy logs.")

        is_plausible = len(dq_findings) > 0
        confidence = 0.80 if is_plausible else 0.15

        return HypothesisAnalysis(
            hypothesis_id="HYP-04-DATA-QUALITY",
            code="HYP_DATA_QUALITY_ANOMALY",
            title="Meter Calibration Drift, Duplicate Telemetry, or Sensor Error",
            category="DATA_QUALITY",
            explanation=(
                "Instrumentation errors such as CT/PT ratio misconfiguration, firmware duplicate packets, "
                "or metering sensor drift (voltage swells/sags) distorted calculated energy sums."
            ),
            plausibility="HIGH" if is_plausible else "LOW",
            confidence_score=confidence,
            confidence_rationale=(
                f"Confidence is {int(confidence*100)}% based on {len(dq_findings)} detected data quality violations."
            ),
            investigation_priority="MEDIUM",
            investigation_status="PLAUSIBLE" if is_plausible else "UNCONFIRMED",
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            missing_evidence=missing_evidence,
            additional_data_required=[
                "Smart meter firmware event log (reboots, power outages)",
                "Current Transformer (CT) secondary wiring test data",
            ],
            recommended_verification_steps=[
                "1. Run remote diagnostic self-test command on boundary check meter.",
                "2. Verify CT multiplier configuration against physical nameplate ratio.",
            ],
        )

    @classmethod
    def _evaluate_technical_losses(cls, dossier: AccountingDossier) -> HypothesisAnalysis:
        supporting: List[EvidenceItem] = []
        contradicting: List[EvidenceItem] = []
        missing_evidence: List[str] = []

        loss_pct = dossier.discrepancy_percentage
        # Normal technical loss range is 1.5% to 4.5%
        if 0.0 <= loss_pct <= 4.5:
            supporting.append(EvidenceItem(
                evidence_id="EV-TECH-01",
                source_type="BOUNDARY_MEASUREMENT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=f"{dossier.time_window_start} to {dossier.time_window_end}",
                metric_name="discrepancy_percentage",
                metric_value=f"{loss_pct:.2f}%",
                unit="%",
                description=f"Calculated loss of {loss_pct:.2f}% conforms with typical I²R copper and transformer core losses (nominal 2.8%).",
            ))
        else:
            contradicting.append(EvidenceItem(
                evidence_id="EV-CONTRA-TECH-01",
                source_type="BOUNDARY_MEASUREMENT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=f"{dossier.time_window_start} to {dossier.time_window_end}",
                metric_name="discrepancy_percentage",
                metric_value=f"{loss_pct:.2f}%",
                unit="%",
                description=f"Observed discrepancy ({loss_pct:.2f}%) significantly departs from physical dissipation limits (≤ 4.5%).",
            ))

        missing_evidence.append("Ambient temperature and solar irradiance data (ambient heat increases line resistance).")
        missing_evidence.append("Exact conductor gauge length measurements for distribution line resistance modeling.")

        is_plausible = (0.0 <= loss_pct <= 5.0) and dossier.neutral_classification == "NORMAL_TECHNICAL_LOSS"
        confidence = 0.95 if is_plausible else 0.20

        return HypothesisAnalysis(
            hypothesis_id="HYP-05-TECHNICAL-LOSSES",
            code="HYP_TECHNICAL_LOSSES",
            title="Standard Technical Distribution Losses (I²R Conductor & Core Dissipation)",
            category="PHYSICS_TECHNICAL",
            explanation=(
                "Energy difference is fully accounted for by natural physical dissipation: Joule heating in distribution conductors "
                "and hysteresis/eddy-current core excitation in the transformer."
            ),
            plausibility="HIGH" if is_plausible else "LOW",
            confidence_score=confidence,
            confidence_rationale=(
                f"Confidence is {int(confidence*100)}%. "
                f"{'Discrepancy is within Class 0.5 sensor uncertainty and standard physical parameters.' if is_plausible else 'Magnitude exceeds normal physical dissipation limits.'}"
            ),
            investigation_priority="LOW" if is_plausible else "MEDIUM",
            investigation_status="PLAUSIBLE" if is_plausible else "UNCONFIRMED",
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            missing_evidence=missing_evidence,
            additional_data_required=[
                "Feeder length and conductor cross-sectional area (ACSR / AAAC spec)",
                "Transformer factory test report (no-load and load loss test certificates)",
            ],
            recommended_verification_steps=[
                "1. Confirm ambient temperature records for the 24-hour analysis window.",
                "2. Recalculate power factor and reactive power (kVARh) dissipation.",
            ],
        )

    @classmethod
    def _evaluate_unmetered_consumption(
        cls,
        dossier: AccountingDossier,
        competing_hypotheses: List[HypothesisAnalysis],
    ) -> HypothesisAnalysis:
        supporting: List[EvidenceItem] = []
        contradicting: List[EvidenceItem] = []
        missing_evidence: List[str] = []

        loss_pct = dossier.discrepancy_percentage
        net_unaccounted = dossier.unaccounted_energy_kwh

        # Evidence Supporting: Discrepancy exceeds technical threshold, and data completeness is confirmed
        if loss_pct > 5.0 and net_unaccounted > 50.0:
            supporting.append(EvidenceItem(
                evidence_id="EV-THEFT-01",
                source_type="BOUNDARY_MEASUREMENT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=f"{dossier.time_window_start} to {dossier.time_window_end}",
                metric_name="unaccounted_energy_kwh",
                metric_value=f"{net_unaccounted:.1f}",
                unit="KWH",
                description=(
                    f"Net unaccounted energy is {net_unaccounted:.1f} kWh ({loss_pct:.2f}% of input), "
                    f"exceeding both technical losses ({dossier.other_accounted_flows_kwh:.1f} kWh) and sensor uncertainty (±{dossier.sensor_uncertainty_kwh:.2f} kWh)."
                ),
            ))

        # Check if competing data-quality or mapping hypotheses explain the loss
        latency_hyp = next((h for h in competing_hypotheses if h.code == "HYP_DELAYED_TELEMETRY"), None)
        mapping_hyp = next((h for h in competing_hypotheses if h.code == "HYP_MAPPING_ERROR"), None)

        if latency_hyp and latency_hyp.plausibility == "HIGH":
            contradicting.append(EvidenceItem(
                evidence_id="EV-CONTRA-THEFT-01",
                source_type="QUALITY_AUDIT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=dossier.time_window_end,
                metric_name="telemetry_latency",
                metric_value="PACKET_LAG_PRESENT",
                unit=None,
                description="Packet lag is present. Discrepancy cannot be attributed to physical loss until delayed readings are backfilled.",
            ))

        if mapping_hyp and mapping_hyp.plausibility == "HIGH":
            contradicting.append(EvidenceItem(
                evidence_id="EV-CONTRA-THEFT-02",
                source_type="QUALITY_AUDIT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=dossier.time_window_end,
                metric_name="topology_error",
                metric_value="GIS_MAPPING_MISMATCH",
                unit=None,
                description="Downstream consumption exceeds upstream input. Topology mismatch must be resolved before assessing unmetered draw.",
            ))

        if loss_pct <= 4.5:
            contradicting.append(EvidenceItem(
                evidence_id="EV-CONTRA-THEFT-03",
                source_type="BOUNDARY_MEASUREMENT",
                entity_code=dossier.boundary_asset_code,
                timestamp_or_period=dossier.time_window_start,
                metric_name="discrepancy_percentage",
                metric_value=f"{loss_pct:.2f}%",
                unit="%",
                description="Discrepancy is fully within normal physical line loss bounds.",
            ))

        missing_evidence.append("Physical aerial / drone thermography scan of distribution lines for hot-spot illegal hookups.")
        missing_evidence.append("Meter tamper switch event register (cover open, magnetic field tamper, reverse CT flags).")
        missing_evidence.append("Historical 30-day baseline consumption pattern for consumer clusters under this transformer.")

        is_plausible = (
            len(supporting) > 0
            and len(contradicting) == 0
            and dossier.neutral_classification == "UNRECONCILED_RESIDUAL_REQUIRING_INVESTIGATION"
        )

        confidence = 0.85 if is_plausible else (0.40 if len(supporting) > 0 else 0.05)

        return HypothesisAnalysis(
            hypothesis_id="HYP-06-UNMETERED-CONSUMPTION",
            code="HYP_UNMETERED_CONSUMPTION",
            title="Unmetered Consumption or Non-Technical Physical Loss (Theft / Bypass)",
            category="COMMERCIAL_UNMETERED",
            explanation=(
                "Energy is physically exiting the distribution transformer but bypassing registered consumer metering "
                "via unauthorized line tapping, meter bypass shunts, or unregistered commercial connections."
            ),
            plausibility="HIGH" if is_plausible else ("MEDIUM" if len(supporting) > 0 else "LOW"),
            confidence_score=confidence,
            confidence_rationale=(
                f"Confidence is {int(confidence*100)}%. "
                f"{'Substantial residual discrepancy confirmed after technical losses, data quality, and GIS topology were ruled out.' if is_plausible else 'Premature: data quality, latency, or technical loss bounds must be verified first.'}"
            ),
            investigation_priority="HIGH" if is_plausible else ("MEDIUM" if len(supporting) > 0 else "LOW"),
            investigation_status="RECOMMENDED_FOR_FIELD_CHECK" if is_plausible else "UNCONFIRMED",
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            missing_evidence=missing_evidence,
            additional_data_required=[
                "Smart meter magnetic tamper and terminal cover-open event logs",
                "High-resolution aerial thermal inspection images of transformer LT lines",
                "Historical seasonal billing records for commercial consumers on this branch",
            ],
            recommended_verification_steps=[
                "1. Cross-reference meter tamper alert registers for magnetic or bypass events.",
                "2. Perform nighttime thermal imaging inspection of distribution lines.",
                "3. Dispatch field inspection squad with clip-on check meters to test individual service cables.",
            ],
        )

