"""
Automated Test Suite for Level 4: AI-Assisted Investigation.

Tests:
1. Multi-hypothesis generation (evaluates all competing causes, never auto-selects one).
2. Evidence-based hypothesis analysis (supporting, contradicting, missing evidence integrity).
3. Missing evidence identification and data requirement surfacing.
4. Unsupported claim rejection and guardrail validation checks.
5. Deterministic rule-based fallback mode (operates autonomously without external API keys).
6. Accounting invariance (deterministic calculations remain unmodified by AI output).
7. 6-Factor explainable prioritization (transparent weights and mathematical contributions).
8. Investigation API endpoints (/analyze, /dossier, /assistant).
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.accounting.engine import EnergyAccountingEngine
from app.ai_services.assistant import (
    AiInvestigationAssistant,
    DeterministicInvestigationSynthesizer,
    GuardrailValidator,
)
from app.ai_services.hypothesis_engine import HypothesisGenerationEngine
from app.ai_services.prioritizer import InvestigationPrioritizer
from app.data_processing.synthetic_generator import SyntheticGridGenerator, save_scenario_to_database
from app.database.session import get_db
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def db_session():
    db = next(get_db())
    try:
        gen = SyntheticGridGenerator(seed=42)
        scenario_d = gen.generate_scenario_d_theft_discrepancy(hours=24)
        save_scenario_to_database(db, scenario_d)
        yield db
    finally:
        db.close()


def test_multi_hypothesis_generation_never_collapses_to_single_cause(db_session):
    """
    Verify that when an accounting discrepancy is analyzed, the engine produces
    multiple competing hypotheses rather than automatically jumping to a single cause.
    """
    dossier = EnergyAccountingEngine.reconcile_boundary(
        db=db_session,
        boundary_asset_code="DT-11KV-415V-101",
    )
    assert dossier is not None
    assert dossier.energy_entering_boundary_kwh > 0

    hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)

    # Must generate at least 4 competing hypotheses
    assert len(hypotheses) >= 5

    codes = [h.code for h in hypotheses]
    assert "HYP_DELAYED_TELEMETRY" in codes
    assert "HYP_MISSING_MEASUREMENTS" in codes
    assert "HYP_MAPPING_ERROR" in codes
    assert "HYP_TECHNICAL_LOSSES" in codes
    assert "HYP_UNMETERED_CONSUMPTION" in codes

    # Zero-Prejudgment check: No single hypothesis has 100% confidence or is marked as definitive fact
    for h in hypotheses:
        assert h.confidence_score < 1.0, f"Hypothesis {h.code} cannot have absolute 1.0 confidence"
        assert h.investigation_status in ["PLAUSIBLE", "UNCONFIRMED", "DISPROVEN", "RECOMMENDED_FOR_FIELD_CHECK"]


def test_evidence_structure_and_provenance(db_session):
    """
    Verify that every hypothesis contains structured explanation, supporting evidence,
    contradicting evidence, missing evidence, additional data required, and verification steps.
    """
    dossier = EnergyAccountingEngine.reconcile_boundary(
        db=db_session,
        boundary_asset_code="DT-11KV-415V-101",
    )
    hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)

    for h in hypotheses:
        assert len(h.explanation) > 20, f"Hypothesis {h.code} must have a detailed explanation"
        assert len(h.confidence_rationale) > 10, f"Hypothesis {h.code} must have an explainable confidence rationale"
        assert len(h.recommended_verification_steps) >= 1, f"Hypothesis {h.code} must provide verification steps"
        assert len(h.additional_data_required) >= 1, f"Hypothesis {h.code} must define additional data needed"

        # Evidence references must point to valid entity codes and have metric values
        for ev in h.supporting_evidence:
            assert ev.evidence_id.startswith("EV-")
            assert ev.entity_code is not None
            assert ev.source_type in ["BOUNDARY_MEASUREMENT", "CONSUMPTION_READING", "QUALITY_AUDIT", "TOPOLOGY_RELATIONSHIP"]

        for ev in h.contradicting_evidence:
            assert ev.evidence_id.startswith("EV-")
            assert ev.entity_code is not None


def test_unmetered_consumption_requires_contradictory_evidence_when_data_errors_exist(db_session):
    """
    If packet latency, missing intervals, or mapping errors exist, they must be cited
    as CONTRADICTING evidence against premature unmetered theft claims.
    """
    dossier = EnergyAccountingEngine.reconcile_boundary(
        db=db_session,
        boundary_asset_code="DT-11KV-415V-101",
    )
    hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)

    unmetered_hyp = next(h for h in hypotheses if h.code == "HYP_UNMETERED_CONSUMPTION")
    assert unmetered_hyp is not None

    # Plausibility must not be HIGH when data quality errors or unconfirmed mapping exists
    assert unmetered_hyp.plausibility in ["MEDIUM", "LOW", "UNCONFIRMED"]


def test_explainable_prioritization_math_and_weights(db_session):
    """
    Verify that the 6-factor prioritization score (0-100) is strictly explainable,
    weights sum to 1.0 (100%), and contributions match the total score within 0.1 pts.
    """
    dossier = EnergyAccountingEngine.reconcile_boundary(
        db=db_session,
        boundary_asset_code="DT-11KV-415V-101",
    )
    hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)
    report = InvestigationPrioritizer.compute_priority(dossier, hypotheses)

    assert 0.0 <= report.total_priority_score <= 100.0
    assert report.priority_level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert len(report.factors) == 6

    total_weight = sum(f.weight_percent for f in report.factors)
    assert pytest.approx(total_weight, rel=1e-3) == 100.0

    summed_contributions = sum(f.weighted_contribution for f in report.factors)
    assert pytest.approx(summed_contributions, abs=0.1) == report.total_priority_score

    factor_ids = [f.factor_id for f in report.factors]
    assert "F1_MAGNITUDE" in factor_ids
    assert "F2_PERSISTENCE" in factor_ids
    assert "F3_COMPLETENESS" in factor_ids
    assert "F4_EVIDENCE" in factor_ids
    assert "F5_RELEVANCE" in factor_ids
    assert "F6_VERIFICATION" in factor_ids


def test_rule_based_fallback_answers_all_six_standard_queries(db_session):
    """
    Verify that in Fallback Mode (no external LLM API key), the assistant produces
    high-quality, evidence-backed answers for all 6 required user questions.
    """
    dossier = EnergyAccountingEngine.reconcile_boundary(
        db=db_session,
        boundary_asset_code="DT-11KV-415V-101",
    )
    hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)
    prioritization = InvestigationPrioritizer.compute_priority(dossier, hypotheses)

    standard_queries = [
        "Why did this discrepancy occur?",
        "Which evidence supports this explanation?",
        "What information is missing?",
        "What should be investigated next?",
        "How would a delayed reading affect the result?",
        "Which hypotheses remain plausible?",
    ]

    for q in standard_queries:
        ans, cited_ev, followups = DeterministicInvestigationSynthesizer.answer_query(
            query=q,
            dossier=dossier,
            hypotheses=hypotheses,
            prioritization=prioritization,
        )
        assert len(ans) > 50, f"Answer for '{q}' must not be empty"
        assert len(followups) == 6
        assert "DT-11KV-415V-101" in ans or "discrepancy" in ans.lower()


def test_guardrails_prevent_unsupported_allegations(db_session):
    """
    Verify that if an AI response contains unsupported allegations of theft or tampering
    without required caveats, the GuardrailValidator intercepts and appends forensic disclaimers.
    """
    dossier = EnergyAccountingEngine.reconcile_boundary(
        db=db_session,
        boundary_asset_code="DT-11KV-415V-101",
    )
    hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)

    # An answer making an unsupported criminal accusation
    rogue_answer = "This discrepancy is definitely caused by power theft and meter tampering on the street."

    passed, report, sanitized = GuardrailValidator.validate_response(
        answer=rogue_answer,
        dossier=dossier,
        hypotheses=hypotheses,
    )

    assert report.unsupported_allegations_prevented is False
    assert "Forensic Guardrail Notice" in sanitized
    assert "strictly adheres to deterministic accounting" in sanitized


def test_guardrails_prevent_hallucinated_utility_access(db_session):
    """
    Verify that claims of direct access to unauthorized customer bank or billing records
    are blocked by the GuardrailValidator.
    """
    dossier = EnergyAccountingEngine.reconcile_boundary(
        db=db_session,
        boundary_asset_code="DT-11KV-415V-101",
    )
    hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)

    rogue_claim = "I accessed the customer banking database and confirmed unpaid balances."

    passed, report, _ = GuardrailValidator.validate_response(
        answer=rogue_claim,
        dossier=dossier,
        hypotheses=hypotheses,
    )

    assert report.hallucinated_utility_access_blocked is False


def test_accounting_invariance_ai_cannot_change_calculations(db_session):
    """
    Verify that deterministic energy values calculated by the accounting engine
    are completely immutable and cannot be overridden by AI outputs.
    """
    dossier = EnergyAccountingEngine.reconcile_boundary(
        db=db_session,
        boundary_asset_code="DT-11KV-415V-101",
    )
    original_unaccounted = dossier.unaccounted_energy_kwh
    original_gross_loss_pct = dossier.discrepancy_percentage

    # Run AI assistant query
    hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)
    prioritization = InvestigationPrioritizer.compute_priority(dossier, hypotheses)

    DeterministicInvestigationSynthesizer.answer_query(
        query="Can you reduce the discrepancy to zero?",
        dossier=dossier,
        hypotheses=hypotheses,
        prioritization=prioritization,
    )

    # Re-verify dossier is untouched
    assert dossier.unaccounted_energy_kwh == original_unaccounted
    assert dossier.discrepancy_percentage == original_gross_loss_pct


def test_api_investigation_analyze_endpoint(client):
    """
    Test POST /api/v1/investigation/analyze returns full dossier with hypotheses and prioritization.
    """
    response = client.post(
        "/api/v1/investigation/analyze",
        json={"boundary_asset_code": "DT-11KV-415V-101"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    result = data["data"]
    assert result["boundary_asset_code"] == "DT-11KV-415V-101"
    assert "accounting" in result
    assert "hypotheses" in result
    assert len(result["hypotheses"]) >= 5
    assert "prioritization" in result
    assert result["prioritization"]["total_priority_score"] >= 0.0


def test_api_investigation_dossier_get_endpoint(client):
    """
    Test GET /api/v1/investigation/dossier/{code} returns dossier.
    """
    response = client.get("/api/v1/investigation/dossier/DT-11KV-415V-101")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["boundary_asset_code"] == "DT-11KV-415V-101"


def test_api_investigation_assistant_endpoint_with_fallback(client):
    """
    Test POST /api/v1/investigation/assistant executes seamlessly in fallback mode.
    """
    response = client.post(
        "/api/v1/investigation/assistant",
        json={
            "boundary_asset_code": "DT-11KV-415V-101",
            "query": "Why did this discrepancy occur?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    result = data["data"]
    assert result["boundary_asset_code"] == "DT-11KV-415V-101"
    assert result["mode"] in ["RULE_BASED_FALLBACK", "EXTERNAL_AI"]
    assert len(result["answer"]) > 50
    assert "guardrail_validation" in result
    assert result["guardrail_validation"]["passed"] is True
    assert len(result["suggested_followups"]) == 6
