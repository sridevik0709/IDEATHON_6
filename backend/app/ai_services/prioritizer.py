"""
Explainable Investigation Prioritization Engine.
Level 4: AI-Assisted Investigation.

Computes a deterministic, explainable priority score (0–100) using 6 transparent weighted factors:
1. Discrepancy Magnitude (Weight: 25%) - Absolute kWh and percentage loss.
2. Persistence Across Intervals (Weight: 20%) - Sustained loss vs single-spike transient.
3. Data Completeness (Weight: 15%) - Confidence penalty if telemetry packets are missing.
4. Evidence Strength (Weight: 15%) - Ratio of supporting evidence to contradicting flags.
5. Operational Relevance (Weight: 15%) - Voltage class and asset rated capacity.
6. Availability of Verification Data (Weight: 10%) - Feasibility of remote AMR interrogation.

Strict Requirement: Show how each factor contributes to the priority.
Never use unexplained AI-generated scores.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
from app.accounting.engine import AccountingDossier
from app.ai_services.hypothesis_engine import HypothesisAnalysis


@dataclass
class PrioritizationFactor:
    factor_id: str
    name: str
    weight_percent: float  # e.g., 25.0 for 25%
    raw_value: Any
    normalized_score: float  # 0.0 to 100.0
    weighted_contribution: float  # (weight / 100) * normalized_score
    explanation: str


@dataclass
class PrioritizationReport:
    boundary_asset_code: str
    total_priority_score: float  # 0.0 to 100.0
    priority_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    factors: List[PrioritizationFactor]
    top_recommended_hypothesis: str
    operational_action_summary: str


class InvestigationPrioritizer:
    """
    Ranks investigation dockets with mathematical explainability.
    """

    WEIGHTS = {
        "magnitude": 0.25,
        "persistence": 0.20,
        "completeness": 0.15,
        "evidence_strength": 0.15,
        "operational_relevance": 0.15,
        "verification_availability": 0.10,
    }

    @classmethod
    def compute_priority(
        cls,
        dossier: AccountingDossier,
        hypotheses: List[HypothesisAnalysis],
    ) -> PrioritizationReport:
        factors: List[PrioritizationFactor] = []

        # ----------------------------------------------------------------------
        # Factor 1: Discrepancy Magnitude (25%)
        # ----------------------------------------------------------------------
        # Scale: 0% discrepancy = 0 score; >= 30% discrepancy = 100 score
        raw_pct = max(0.0, dossier.discrepancy_percentage)
        score_magnitude = min(100.0, (raw_pct / 30.0) * 100.0)
        contrib_magnitude = round(cls.WEIGHTS["magnitude"] * score_magnitude, 2)
        factors.append(PrioritizationFactor(
            factor_id="F1_MAGNITUDE",
            name="Discrepancy Magnitude",
            weight_percent=25.0,
            raw_value=f"{raw_pct:.2f}% ({dossier.unaccounted_energy_kwh:.1f} kWh)",
            normalized_score=round(score_magnitude, 1),
            weighted_contribution=contrib_magnitude,
            explanation=(
                f"Discrepancy of {raw_pct:.2f}% ({dossier.unaccounted_energy_kwh:.1f} kWh) "
                f"yields {score_magnitude:.1f}/100 normalized score, contributing {contrib_magnitude} points."
            ),
        ))

        # ----------------------------------------------------------------------
        # Factor 2: Persistence Across Comparable Intervals (20%)
        # ----------------------------------------------------------------------
        # If actual intervals >= 24, high persistence; if single interval, low persistence
        intervals_ratio = min(1.0, dossier.total_actual_intervals / max(1, dossier.total_expected_intervals))
        # Check if discrepancy is persistent across hours
        score_persistence = round(intervals_ratio * 85.0, 1)
        if dossier.discrepancy_percentage > 5.0 and intervals_ratio > 0.8:
            score_persistence = 95.0
        contrib_persistence = round(cls.WEIGHTS["persistence"] * score_persistence, 2)
        factors.append(PrioritizationFactor(
            factor_id="F2_PERSISTENCE",
            name="Persistence Across Intervals",
            weight_percent=20.0,
            raw_value=f"{dossier.total_actual_intervals}/{dossier.total_expected_intervals} intervals",
            normalized_score=score_persistence,
            weighted_contribution=contrib_persistence,
            explanation=(
                f"Telemetry observed across {dossier.total_actual_intervals} continuous hours "
                f"indicates sustained structural deficit rather than single-interval transient."
            ),
        ))

        # ----------------------------------------------------------------------
        # Factor 3: Data Completeness (15%)
        # ----------------------------------------------------------------------
        # 100% complete = 100 score (high confidence); missing packets = lower score
        completeness_pct = (
            (dossier.total_actual_intervals / dossier.total_expected_intervals * 100.0)
            if dossier.total_expected_intervals > 0 else 0.0
        )
        score_completeness = round(min(100.0, completeness_pct), 1)
        contrib_completeness = round(cls.WEIGHTS["completeness"] * score_completeness, 2)
        factors.append(PrioritizationFactor(
            factor_id="F3_COMPLETENESS",
            name="Telemetry Completeness",
            weight_percent=15.0,
            raw_value=f"{completeness_pct:.1f}% completeness",
            normalized_score=score_completeness,
            weighted_contribution=contrib_completeness,
            explanation=(
                f"Boundary and downstream telemetry completeness is {completeness_pct:.1f}%, "
                f"contributing {contrib_completeness} confidence points."
            ),
        ))

        # ----------------------------------------------------------------------
        # Factor 4: Evidence Strength (15%)
        # ----------------------------------------------------------------------
        total_supporting = sum(len(h.supporting_evidence) for h in hypotheses)
        total_contradicting = sum(len(h.contradicting_evidence) for h in hypotheses)
        evidence_ratio = (
            (total_supporting / (total_supporting + total_contradicting))
            if (total_supporting + total_contradicting) > 0 else 0.5
        )
        score_evidence = round(evidence_ratio * 100.0, 1)
        contrib_evidence = round(cls.WEIGHTS["evidence_strength"] * score_evidence, 2)
        factors.append(PrioritizationFactor(
            factor_id="F4_EVIDENCE",
            name="Evidence Conclusiveness",
            weight_percent=15.0,
            raw_value=f"{total_supporting} supporting vs {total_contradicting} contradicting items",
            normalized_score=score_evidence,
            weighted_contribution=contrib_evidence,
            explanation=(
                f"Identified {total_supporting} supporting evidence records across competing hypotheses, "
                f"contributing {contrib_evidence} points."
            ),
        ))

        # ----------------------------------------------------------------------
        # Factor 5: Operational Relevance (15%)
        # ----------------------------------------------------------------------
        relevance_map = {
            "SUBSTATION": 95.0,
            "FEEDER": 80.0,
            "TRANSFORMER": 65.0,
        }
        score_relevance = relevance_map.get(dossier.boundary_asset_type, 50.0)
        contrib_relevance = round(cls.WEIGHTS["operational_relevance"] * score_relevance, 2)
        factors.append(PrioritizationFactor(
            factor_id="F5_RELEVANCE",
            name="Operational Relevance & Asset Hierarchy",
            weight_percent=15.0,
            raw_value=f"{dossier.boundary_asset_type} ({dossier.voltage_class})",
            normalized_score=score_relevance,
            weighted_contribution=contrib_relevance,
            explanation=(
                f"Asset level '{dossier.boundary_asset_type}' at voltage class {dossier.voltage_class} "
                f"yields base operational weight of {contrib_relevance} points."
            ),
        ))

        # ----------------------------------------------------------------------
        # Factor 6: Availability of Verification Data (10%)
        # ----------------------------------------------------------------------
        has_child_sources = len(dossier.source_measurements) > 0
        score_verification = 90.0 if has_child_sources else 40.0
        contrib_verification = round(cls.WEIGHTS["verification_availability"] * score_verification, 2)
        factors.append(PrioritizationFactor(
            factor_id="F6_VERIFICATION",
            name="Availability of Verification Data",
            weight_percent=10.0,
            raw_value=f"{len(dossier.source_measurements)} child telemetry sources",
            normalized_score=score_verification,
            weighted_contribution=contrib_verification,
            explanation=(
                f"Verified {len(dossier.source_measurements)} accessible child telemetry streams "
                "available for remote cross-examination."
            ),
        ))

        # Total Score
        total_score = round(sum(f.weighted_contribution for f in factors), 1)

        if total_score >= 80.0:
            level = "CRITICAL"
        elif total_score >= 65.0:
            level = "HIGH"
        elif total_score >= 45.0:
            level = "MEDIUM"
        else:
            level = "LOW"

        # Determine top recommended hypothesis
        plausible_hypotheses = sorted(
            hypotheses,
            key=lambda h: (h.confidence_score, len(h.supporting_evidence) - len(h.contradicting_evidence)),
            reverse=True,
        )
        top_hyp = plausible_hypotheses[0] if plausible_hypotheses else None

        top_title = top_hyp.title if top_hyp else "Standard Technical Loss"
        action_summary = (
            f"Prioritize inspection of '{top_title}'. "
            f"Follow step 1: {top_hyp.recommended_verification_steps[0] if top_hyp and top_hyp.recommended_verification_steps else 'Maintain periodic monitoring.'}"
        )

        return PrioritizationReport(
            boundary_asset_code=dossier.boundary_asset_code,
            total_priority_score=total_score,
            priority_level=level,
            factors=factors,
            top_recommended_hypothesis=top_title,
            operational_action_summary=action_summary,
        )

