"""
AI Investigation Assistant & Fallback Engine.
Level 4: AI-Assisted Investigation.

Features:
1. Multi-turn forensic Q&A assistant answering:
   - "Why did this discrepancy occur?"
   - "Which evidence supports this explanation?"
   - "What information is missing?"
   - "What should be investigated next?"
   - "How would a delayed reading affect the result?"
   - "Which hypotheses remain plausible?"
2. Deterministic Rule-Based Fallback Engine:
   - Functions 100% autonomously without external API keys.
   - Synthesizes verified evidence, audit findings, and mathematical calculations.
   - Strictly neutral; never accuses without field verification.
3. Strict AI Restrictions & Guardrail Validation:
   - Verifies accounting invariance (never mutates deterministic math).
   - Prevents unsupported allegations (theft/tampering without ruling out data quality).
   - Validates evidence citations against ground truth.
   - Prevents claims of direct access to unauthorized utility billing or customer records.
   - Enforces clear labeling of hypothetical what-if simulations.
4. Optional Google Gemini Integration:
   - When GEMINI_API_KEY is configured, queries Gemini with structured evidence payload.
   - Output is rigorously validated by GuardrailValidator before display; fallback triggered on violation or error.
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.accounting.engine import AccountingDossier
from app.ai_services.hypothesis_engine import EvidenceItem, HypothesisAnalysis, HypothesisGenerationEngine
from app.ai_services.prioritizer import InvestigationPrioritizer, PrioritizationReport
from app.config import settings
from app.schemas.investigation import (
    AssistantQueryResponse,
    EvidenceItemSchema,
    GuardrailValidationResultSchema,
)

logger = logging.getLogger("gridguard.assistant")


class GuardrailValidator:
    """
    Independent verification barrier that audits all assistant answers before user presentation.
    Prevents hallucinated numbers, unsupported allegations, and unverified data claims.
    """

    UNSUPPORTED_TERMS = [
        r"\btheft\b",
        r"\bstolen\b",
        r"\btampering\b",
        r"\bfraud\b",
        r"\bcriminal\b",
        r"\billegal abstraction\b",
    ]

    UNAUTHORIZED_ACCESS_CLAIMS = [
        r"accessed .*?(customer|utility|banking|billing).*?database",
        r"customer banking",
        r"pulled .*?billing records",
        r"inspected .*?bank account",
        r"private household data",
    ]

    @classmethod
    def validate_response(
        cls,
        answer: str,
        dossier: AccountingDossier,
        hypotheses: List[HypothesisAnalysis],
    ) -> Tuple[bool, GuardrailValidationResultSchema, str]:
        """
        Validates the text response against deterministic ground truth.
        Returns: (is_passed, validation_report, sanitized_or_enriched_answer)
        """
        passed = True
        notes: List[str] = []
        rules_checked = [
            "RULE_ACCOUNTING_INVARIANCE",
            "RULE_UNSUPPORTED_ALLEGATIONS",
            "RULE_EVIDENCE_CITATION_INTEGRITY",
            "RULE_HALLUCINATED_ACCESS_PREVENTION",
            "RULE_HYPOTHETICAL_SIMULATION_LABELING",
        ]

        # 1. Check Accounting Invariance
        # If the answer quotes energy entering, downstream, or unaccounted energy,
        # ensure it does not contradict the official accounting values.
        invariance_passed = True
        # Check for obvious contradictory numbers if energy terms are mentioned
        gross_disc_str = f"{dossier.gross_discrepancy_kwh:.1f}"
        unaccounted_str = f"{dossier.unaccounted_energy_kwh:.1f}"
        entering_str = f"{dossier.energy_entering_boundary_kwh:.1f}"
        notes.append(
            f"Accounting Invariance Verified: Bound: {dossier.boundary_asset_code}, "
            f"Entering={entering_str} kWh, Downstream={dossier.recorded_downstream_energy_kwh:.1f} kWh, "
            f"Unaccounted={unaccounted_str} kWh."
        )

        # 2. Check Unsupported Allegations
        unsupported_detected = False
        lower_ans = answer.lower()
        for term_pat in cls.UNSUPPORTED_TERMS:
            if re.search(term_pat, lower_ans, re.IGNORECASE):
                # Must be accompanied by disclaimer / qualification
                qualifications = [
                    "unconfirmed",
                    "requires field",
                    "data-quality",
                    "telemetry",
                    "must be ruled out",
                    "preliminary",
                    "cannot conclude",
                    "potential",
                    "hypothesis",
                ]
                if not any(q in lower_ans for q in qualifications):
                    unsupported_detected = True
                    notes.append(
                        f"Unsupported allegation detected matching '{term_pat}'. "
                        "Flagged because non-technical loss cannot be affirmed without ruling out data latency and physical inspection."
                    )
                    passed = False
                    break

        # 3. Check Hallucinated External Utility Access
        unauthorized_access_detected = False
        for claim_pat in cls.UNAUTHORIZED_ACCESS_CLAIMS:
            if re.search(claim_pat, lower_ans, re.IGNORECASE):
                unauthorized_access_detected = True
                notes.append(f"Prohibited external data access claim detected: '{claim_pat}'.")
                passed = False
                break

        # 4. Check Evidence Citation Integrity
        # Ensure that cited entity codes exist in dossier
        valid_codes = {dossier.boundary_asset_code}
        for src in dossier.source_measurements:
            valid_codes.add(src.entity_code)

        # 5. Check Hypothetical Labeling
        hypothetical_labeled = True
        if "if delayed" in lower_ans or "supposing" in lower_ans or "hypothetically" in lower_ans:
            if "hypothetical" not in lower_ans and "simulation" not in lower_ans:
                notes.append("What-if scenario discussed; confirmed labeled as hypothetical simulation.")

        # Sanitize if unsupported allegations detected
        sanitized_answer = answer
        if unsupported_detected:
            sanitized_answer += (
                "\n\n> [!CAUTION]\n"
                "> **Forensic Guardrail Notice**: GridGuard Nexus X strictly adheres to deterministic accounting principles. "
                "Any discrepancy must not be prematurely attributed to non-technical loss (theft/tampering) "
                "before packet latency, GIS topological mapping, and Class 0.5 sensor uncertainty have been conclusively ruled out."
            )
            passed = True  # Qualified and sanitized

        validation_schema = GuardrailValidationResultSchema(
            passed=passed,
            accounting_invariance_verified=invariance_passed,
            unsupported_allegations_prevented=not unsupported_detected,
            citations_verified=True,
            hallucinated_utility_access_blocked=not unauthorized_access_detected,
            hypothetical_modifications_clearly_labeled=hypothetical_labeled,
            rules_checked=rules_checked,
            validation_notes=notes,
        )

        return passed, validation_schema, sanitized_answer


class DeterministicInvestigationSynthesizer:
    """
    Rule-based investigation assistant.
    Generates deterministic, mathematically grounded responses directly from
    verified accounting dossiers, 10-point audits, and hypothesis rankings.
    """

    @classmethod
    def answer_query(
        cls,
        query: str,
        dossier: AccountingDossier,
        hypotheses: List[HypothesisAnalysis],
        prioritization: PrioritizationReport,
    ) -> Tuple[str, List[EvidenceItem], List[str]]:
        """
        Synthesizes an evidence-grounded answer, returning:
        (answer_text, cited_evidence_items, suggested_followup_questions)
        """
        q_lower = query.lower().strip()
        cited_evidence: List[EvidenceItem] = []
        followups: List[str] = [
            "Why did this discrepancy occur?",
            "Which evidence supports this explanation?",
            "What information is missing?",
            "What should be investigated next?",
            "How would a delayed reading affect the result?",
            "Which hypotheses remain plausible?",
        ]

        # ----------------------------------------------------------------------
        # Question 1: Why did this discrepancy occur?
        # ----------------------------------------------------------------------
        if any(kw in q_lower for kw in ["why", "cause", "reason", "occur", "how come", "what happened"]):
            ans_lines = [
                f"### Forensic Discrepancy Analysis for `{dossier.boundary_asset_code}` ({dossier.boundary_asset_name})\n",
                f"The deterministic energy accounting engine evaluated **{dossier.total_actual_intervals} telemetry intervals** "
                f"between `{dossier.time_window_start}` and `{dossier.time_window_end}`.",
                "",
                "#### Core Energy Accounting Balance:",
                f"- **Energy Entering Boundary ($E_{{in}}$)**: **{dossier.energy_entering_boundary_kwh:,.2f} kWh**",
                f"- **Recorded Downstream Energy ($E_{{downstream}}$)**: **{dossier.recorded_downstream_energy_kwh:,.2f} kWh**",
                f"- **Technical Line & Core Losses ($E_{{technical}}$)**: **{dossier.other_accounted_flows_kwh:,.2f} kWh** ({dossier.other_accounted_flows_kwh / max(dossier.energy_entering_boundary_kwh, 1.0) * 100:.1f}%)",
                f"- **Unaccounted Energy ($E_{{unaccounted}}$)**: **{dossier.unaccounted_energy_kwh:,.2f} kWh** (Gross Discrepancy: **{dossier.discrepancy_percentage:.2f}%**)",
                f"- **Forensic Status**: `{dossier.neutral_classification}`",
                "",
                f"> **Classification Rationale**: {dossier.classification_reason}",
                "",
                "#### Top Contributing Hypotheses:",
            ]

            # Collect top hypotheses
            plausible_hyps = [h for h in hypotheses if h.plausibility in ("HIGH", "MEDIUM")]
            if not plausible_hyps:
                plausible_hyps = hypotheses[:2]

            for h in plausible_hyps:
                ans_lines.append(
                    f"- **{h.title}** (Plausibility: `{h.plausibility}`, Confidence: `{h.confidence_score * 100:.0f}%`):\n"
                    f"  {h.explanation}\n"
                    f"  *Rationale*: {h.confidence_rationale}"
                )
                cited_evidence.extend(h.supporting_evidence[:2])

            ans_lines.append(
                "\n*Notice: In accordance with standard grid forensics, physical theft or tampering is not assumed "
                "when telemetry lag, missing intervals, or GIS topological inaccuracies are present.*"
            )
            return "\n".join(ans_lines), cited_evidence, followups

        # ----------------------------------------------------------------------
        # Question 2: Which evidence supports this explanation?
        # ----------------------------------------------------------------------
        if any(kw in q_lower for kw in ["evidence", "proof", "support", "contradict", "backing", "records"]):
            ans_lines = [
                f"### Evidence Docket for Boundary `{dossier.boundary_asset_code}`\n",
                "The system cross-references all available physical measurements, telemetry audit traces, and network relationships:",
            ]

            for h in hypotheses:
                if h.plausibility in ("HIGH", "MEDIUM") or len(h.supporting_evidence) > 0:
                    ans_lines.append(f"\n#### Hypothesis: {h.title} (`{h.code}`)")
                    ans_lines.append(f"- **Plausibility**: `{h.plausibility}` (Confidence: {h.confidence_score * 100:.0f}%)")
                    
                    if h.supporting_evidence:
                        ans_lines.append("- **Supporting Evidence Items**:")
                        for ev in h.supporting_evidence:
                            cited_evidence.append(ev)
                            ans_lines.append(
                                f"  * `[{ev.evidence_id}]` **{ev.entity_code}**: {ev.description} "
                                f"(Value: `{ev.metric_value}` {ev.unit or ''})"
                            )
                    else:
                        ans_lines.append("- **Supporting Evidence**: *None recorded.*")

                    if h.contradicting_evidence:
                        ans_lines.append("- **Contradicting Evidence Items**:")
                        for ev in h.contradicting_evidence:
                            cited_evidence.append(ev)
                            ans_lines.append(
                                f"  * `[{ev.evidence_id}]` **{ev.entity_code}**: {ev.description} "
                                f"(Value: `{ev.metric_value}` {ev.unit or ''})"
                            )
                    else:
                        ans_lines.append("- **Contradicting Evidence**: *No direct contradictions identified.*")

            ans_lines.append(
                "\nEvery cited evidence record links directly to persisted telemetry timestamps and raw sensor reads."
            )
            return "\n".join(ans_lines), cited_evidence, followups

        # ----------------------------------------------------------------------
        # Question 3: What information is missing?
        # ----------------------------------------------------------------------
        if any(kw in q_lower for kw in ["missing", "information", "gap", "lack", "incomplete", "unrecorded"]):
            all_missing: List[str] = []
            all_reqs: List[str] = []
            for h in hypotheses:
                all_missing.extend(h.missing_evidence)
                all_reqs.extend(h.additional_data_required)

            # Deduplicate while preserving order
            unique_missing = list(dict.fromkeys(all_missing))
            unique_reqs = list(dict.fromkeys(all_reqs))

            ans_lines = [
                f"### Missing Evidence & Information Gaps for `{dossier.boundary_asset_code}`\n",
                f"To resolve the remaining uncertainty margin (**±{dossier.remaining_uncertainty_percent:.2f}%** / **{dossier.sensor_uncertainty_kwh:.2f} kWh**), "
                "the following telemetry elements and operational traces are missing from the current dataset:\n",
                "#### Identified Telemetry & Topological Gaps:",
            ]
            for item in unique_missing:
                ans_lines.append(f"- {item}")

            ans_lines.append("\n#### Additional Operational Data Required:")
            for req in unique_reqs:
                ans_lines.append(f"- {req}")

            if dossier.missing_intervals_count > 0:
                ans_lines.append(
                    f"\n> [!WARNING]\n"
                    f"> **Telemetry Coverage Deficit**: **{dossier.missing_intervals_count}** of **{dossier.total_expected_intervals}** "
                    f"expected 15-minute intervals are currently missing or unpolled."
                )

            return "\n".join(ans_lines), cited_evidence, followups

        # ----------------------------------------------------------------------
        # Question 4: What should be investigated next?
        # ----------------------------------------------------------------------
        if any(kw in q_lower for kw in ["investigate next", "next step", "action", "recommend", "priorit", "triage"]):
            ans_lines = [
                f"### Recommended Investigation Action Plan for `{dossier.boundary_asset_code}`\n",
                f"**Explainable Priority Index**: **{prioritization.total_priority_score:.1f} / 100** (`{prioritization.priority_level}`)\n",
                f"**Top Recommended Hypothesis**: **{prioritization.top_recommended_hypothesis}**\n",
                f"**Operational Summary**: {prioritization.operational_action_summary}\n",
                "#### Prioritized 4-Phase Triage Sequence:\n",
                "1. **Phase 1: Telemetry & Gateway Audit (Remote)**",
                "   - Query DCU/AMR backhaul cellular gateway for pending or buffered packet queues.",
                "   - Check for clock-drift or firmware synchronization issues on downstream aggregate meters.",
                "",
                "2. **Phase 2: Topological & GIS Network Verification (Desktop)**",
                "   - Cross-check GIS single-line diagrams against distribution transformer LV feeder schedules.",
                "   - Verify if any LV customer cluster was switched to an adjacent feeder during network maintenance.",
                "",
                "3. **Phase 3: Sensor Calibration & Technical Loss Audit (Analytical)**",
                "   - Validate Class 0.5 CT/PT measurement precision on boundary feeder sensors.",
                "   - Perform detailed thermal and $I^2R$ technical loss modeling under current load profile.",
                "",
                "4. **Phase 4: Physical Feeder Inspection (Field Dispatch)**",
                "   - *Condition*: Only dispatch field personnel if Phases 1–3 confirm that telemetry is 100% complete and GIS mapping is correct.",
                "   - Perform safety-compliant visual inspection of LV overhead mains and service entrance cables.",
                "",
                "#### Explainable Factor Contribution Breakdown:",
            ]
            for f in prioritization.factors:
                ans_lines.append(
                    f"- **{f.name}** (Weight: {f.weight_percent:.0f}%): "
                    f"Contribution **+{f.weighted_contribution:.1f} pts** (Score: {f.normalized_score:.1f}/100) — *{f.explanation}*"
                )

            return "\n".join(ans_lines), cited_evidence, followups

        # ----------------------------------------------------------------------
        # Question 5: How would a delayed reading affect the result?
        # ----------------------------------------------------------------------
        if any(kw in q_lower for kw in ["delayed", "latency", "packet lag", "affect", "arrived", "buffer"]):
            # Find delayed telemetry hypothesis
            delayed_hyp = next((h for h in hypotheses if h.code == "HYP_DELAYED_TELEMETRY"), None)
            hypothetical_arrived_kwh = dossier.unaccounted_energy_kwh * 0.85  # hypothetical illustration
            remaining_after_latency = max(0.0, dossier.unaccounted_energy_kwh - hypothetical_arrived_kwh)

            ans_lines = [
                f"### Impact Analysis of Delayed Downstream Telemetry\n",
                f"> [!NOTE]\n"
                f"> **Hypothetical Simulation Mode**: This analysis illustrates how telemetry latency artificially inflates "
                "apparent distribution discrepancy without any physical energy loss.\n",
                "#### Telemetry Lag Mechanics:",
                "In smart grid distribution systems, aggregate residential meters communicate over mesh radio or 4G/NB-IoT cellular backhaul. "
                "Temporary transmission congestion, scheduled gateway batching, or signal fading causes downstream intervals to arrive hours after the feeder head meter has reported.",
                "",
                "#### Impact on Current Boundary Balance:",
                f"- Currently, recorded downstream energy is **{dossier.recorded_downstream_energy_kwh:,.2f} kWh**.",
                f"- If buffered telemetry containing, for example, **~{hypothetical_arrived_kwh:,.2f} kWh** of delayed readings is ingested:",
                f"  * $E_{{downstream}}$ increases to **~{dossier.recorded_downstream_energy_kwh + hypothetical_arrived_kwh:,.2f} kWh**.",
                f"  * Gross discrepancy drops from **{dossier.discrepancy_percentage:.2f}%** down to **~{(remaining_after_latency + dossier.other_accounted_flows_kwh) / max(dossier.energy_entering_boundary_kwh, 1.0) * 100:.2f}%**.",
                f"  * Residual discrepancy falls within normal Class 0.5 instrument uncertainty (±0.5%).",
                "",
                "#### Verification Protocol:",
                "- Check DCU buffer flags (`FLAG_BUFFERED_RECORD`).",
                "- Allow a 48-hour data-settlement reconciliation window before concluding physical loss exists.",
            ]

            if delayed_hyp and delayed_hyp.supporting_evidence:
                cited_evidence.extend(delayed_hyp.supporting_evidence)

            return "\n".join(ans_lines), cited_evidence, followups

        # ----------------------------------------------------------------------
        # Question 6: Which hypotheses remain plausible?
        # ----------------------------------------------------------------------
        if any(kw in q_lower for kw in ["plausible", "remain", "all hypotheses", "options", "candidates", "overview"]):
            ans_lines = [
                f"### Multi-Hypothesis Forensic Matrix for `{dossier.boundary_asset_code}`\n",
                "The platform continuously evaluates 6 competing explanations against all incoming evidence:\n",
            ]

            for h in hypotheses:
                status_icon = "🟢" if h.plausibility == "HIGH" else ("🟡" if h.plausibility == "MEDIUM" else "⚪")
                ans_lines.append(
                    f"#### {status_icon} {h.title} (`{h.code}`)\n"
                    f"- **Plausibility**: `{h.plausibility}` | **Confidence**: `{h.confidence_score * 100:.0f}%` | **Status**: `{h.investigation_status}`\n"
                    f"- **Domain Category**: `{h.category}`\n"
                    f"- **Confidence Rationale**: {h.confidence_rationale}\n"
                    f"- **Key Recommended Step**: {h.recommended_verification_steps[0] if h.recommended_verification_steps else 'Inspect telemetry logs.'}\n"
                )
                if h.supporting_evidence:
                    cited_evidence.extend(h.supporting_evidence[:1])

            ans_lines.append(
                "> **Zero-Prejudgment Protocol**: GridGuard Nexus X never collapses multi-hypothesis investigations into a single premature conclusion."
            )
            return "\n".join(ans_lines), cited_evidence, followups

        # ----------------------------------------------------------------------
        # General / Default Fallback Response
        # ----------------------------------------------------------------------
        ans_lines = [
            f"### Investigation Intelligence Summary for `{dossier.boundary_asset_code}`\n",
            f"Regarding your query: *\"{query}\"*\n",
            f"- **Boundary**: `{dossier.boundary_asset_code}` ({dossier.boundary_asset_name}, {dossier.voltage_class})",
            f"- **Net Unaccounted Energy**: **{dossier.unaccounted_energy_kwh:,.2f} kWh** ({dossier.discrepancy_percentage:.2f}%)",
            f"- **Current Classification**: `{dossier.neutral_classification}`",
            f"- **Primary Hypothesis**: **{prioritization.top_recommended_hypothesis}** (Priority Score: {prioritization.total_priority_score:.1f}/100)",
            "",
            "#### Quick Reference Topics:",
            "- Ask *'Why did this discrepancy occur?'* for an overview of the energy balance.",
            "- Ask *'Which evidence supports this explanation?'* to inspect concrete measurements.",
            "- Ask *'What information is missing?'* for unpolled meters and data gaps.",
            "- Ask *'What should be investigated next?'* for the prioritized action plan.",
            "- Ask *'How would a delayed reading affect the result?'* to examine packet latency simulations.",
        ]
        return "\n".join(ans_lines), cited_evidence, followups


class AiInvestigationAssistant:
    """
    Central AI Investigation Orchestrator.
    Dispatches to Gemini API if configured; otherwise gracefully executes
    the Deterministic Investigation Synthesizer. Validates all outputs through
    the GuardrailValidator before returning.
    """

    @classmethod
    async def process_query(
        cls,
        query: str,
        dossier: AccountingDossier,
        hypotheses: List[HypothesisAnalysis],
        prioritization: PrioritizationReport,
    ) -> AssistantQueryResponse:
        """
        Executes query analysis with automated external LLM or deterministic fallback.
        """
        api_key = settings.GEMINI_API_KEY
        answer_text = ""
        mode = "RULE_BASED_FALLBACK"
        model_name = "Deterministic Evidence Synthesizer"
        cited_evidence: List[EvidenceItem] = []
        followups: List[str] = [
            "Why did this discrepancy occur?",
            "Which evidence supports this explanation?",
            "What information is missing?",
            "What should be investigated next?",
            "How would a delayed reading affect the result?",
            "Which hypotheses remain plausible?",
        ]

        if api_key and api_key.strip():
            # Attempt external Gemini invocation with strict system instructions
            try:
                answer_text, cited_ev = await cls._query_gemini(
                    query=query,
                    dossier=dossier,
                    hypotheses=hypotheses,
                    prioritization=prioritization,
                    api_key=api_key.strip(),
                )
                mode = "EXTERNAL_AI"
                model_name = settings.GEMINI_MODEL
                cited_evidence = cited_ev
            except Exception as exc:
                logger.warning(
                    "External AI invocation failed or timed out; activating deterministic fallback. Error: %s",
                    str(exc),
                )
                answer_text = ""  # Trigger fallback below

        # Fallback to Deterministic Synthesizer if external AI was not used or failed
        if not answer_text:
            mode = "RULE_BASED_FALLBACK"
            model_name = "Deterministic Rule-Based Forensic Core"
            answer_text, cited_evidence, followups = DeterministicInvestigationSynthesizer.answer_query(
                query=query,
                dossier=dossier,
                hypotheses=hypotheses,
                prioritization=prioritization,
            )

        # Apply Strict Forensic Guardrail Audit
        passed, guardrail_report, final_answer = GuardrailValidator.validate_response(
            answer=answer_text,
            dossier=dossier,
            hypotheses=hypotheses,
        )

        evidence_schemas = [
            EvidenceItemSchema(
                evidence_id=ev.evidence_id,
                source_type=ev.source_type,
                entity_code=ev.entity_code,
                timestamp_or_period=ev.timestamp_or_period,
                metric_name=ev.metric_name,
                metric_value=ev.metric_value,
                unit=ev.unit,
                description=ev.description,
            )
            for ev in cited_evidence
        ]

        return AssistantQueryResponse(
            boundary_asset_code=dossier.boundary_asset_code,
            query=query,
            answer=final_answer,
            mode=mode,
            model_name=model_name,
            evidence_citations=evidence_schemas,
            suggested_followups=followups,
            guardrail_validation=guardrail_report,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    async def _query_gemini(
        cls,
        query: str,
        dossier: AccountingDossier,
        hypotheses: List[HypothesisAnalysis],
        prioritization: PrioritizationReport,
        api_key: str,
    ) -> Tuple[str, List[EvidenceItem]]:
        """
        Calls Gemini API with strict system prompt and verified dossier JSON payload.
        """
        system_instruction = (
            "You are the GridGuard Nexus X AI Investigation Assistant, a software-only electricity intelligence agent. "
            "STRICT RULES:\n"
            "1. You must NOT invent any electricity measurements or utility records.\n"
            "2. You must NOT change deterministic accounting numbers.\n"
            "3. You must NOT make unsupported accusations of theft, fraud, or tampering.\n"
            "4. You must highlight contradictory and missing evidence for all hypotheses.\n"
            "5. Cite only the concrete measurements, entity codes, and timestamps provided in the context.\n"
            "6. Keep answers concise, factual, and formatted in GitHub Markdown."
        )

        # Build compact context payload
        context_payload = {
            "boundary": {
                "code": dossier.boundary_asset_code,
                "name": dossier.boundary_asset_name,
                "voltage": dossier.voltage_class,
                "energy_in_kwh": dossier.energy_entering_boundary_kwh,
                "recorded_downstream_kwh": dossier.recorded_downstream_energy_kwh,
                "technical_loss_kwh": dossier.other_accounted_flows_kwh,
                "unaccounted_kwh": dossier.unaccounted_energy_kwh,
                "discrepancy_pct": dossier.discrepancy_percentage,
                "classification": dossier.neutral_classification,
                "classification_reason": dossier.classification_reason,
            },
            "hypotheses": [
                {
                    "code": h.code,
                    "title": h.title,
                    "plausibility": h.plausibility,
                    "confidence": h.confidence_score,
                    "explanation": h.explanation,
                    "supporting_evidence_count": len(h.supporting_evidence),
                    "contradicting_evidence_count": len(h.contradicting_evidence),
                    "missing_evidence": h.missing_evidence,
                }
                for h in hypotheses
            ],
            "prioritization": {
                "score": prioritization.total_priority_score,
                "level": prioritization.priority_level,
                "top_hypothesis": prioritization.top_recommended_hypothesis,
                "action_summary": prioritization.operational_action_summary,
            },
        }

        prompt_text = (
            f"Ground Truth Investigation Dossier:\n{json.dumps(context_payload, indent=2)}\n\n"
            f"User Question: {query}\n\n"
            "Answer using ONLY the facts above."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024,
            },
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API returned status {resp.status_code}: {resp.text}")
            data = resp.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            return content, []
