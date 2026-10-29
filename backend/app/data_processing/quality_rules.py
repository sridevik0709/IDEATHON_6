"""
Data Integrity and Quality Audit Engine.
Validates telemetry timestamps, units, electrical ranges, and flags duplicate or corrupted packets.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Set, Tuple
from pydantic import BaseModel, Field


class QualityAuditFinding(BaseModel):
    dimension: str = Field(..., description="COMPLETENESS, TIMELINESS, PLAUSIBILITY, CONSISTENCY, INTEGRITY")
    passed: bool = Field(..., description="True if check passed")
    error_code: str = Field(default="VALID", description="Audit classification code")
    message: str = Field(..., description="Audit diagnostic description")
    score: float = Field(default=1.0, description="Quality index (0.0 to 1.0)")


ALLOWED_UNITS: Set[str] = {"KWH", "MWH", "KW", "MW", "VOLTS", "AMPERES", "HERTZ", "V", "A", "HZ"}


def audit_consumption_record(record: Dict[str, Any], current_time: datetime = None) -> List[QualityAuditFinding]:
    """
    Evaluates data integrity for a single downstream aggregate meter reading.
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    findings: List[QualityAuditFinding] = []

    # 1. Measurement Unit Validation
    unit = str(record.get("unit", "")).upper()
    if unit not in ALLOWED_UNITS:
        findings.append(
            QualityAuditFinding(
                dimension="INTEGRITY",
                passed=False,
                error_code="ERR_INVALID_UNIT",
                message=f"Measurement unit '{unit}' is unrecognized. Expected one of: {sorted(ALLOWED_UNITS)}",
                score=0.0
            )
        )
    else:
        findings.append(
            QualityAuditFinding(
                dimension="INTEGRITY",
                passed=True,
                error_code="VALID",
                message=f"Measurement unit '{unit}' verified.",
                score=1.0
            )
        )

    # 2. Timestamp Validation (No future timestamps, must be timezone-aware or valid date)
    ts = record.get("timestamp")
    if isinstance(ts, str):
        try:
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            findings.append(
                QualityAuditFinding(
                    dimension="TIMELINESS",
                    passed=False,
                    error_code="ERR_MALFORMED_TIMESTAMP",
                    message=f"Timestamp string '{record.get('timestamp')}' cannot be parsed as ISO-8601.",
                    score=0.0
                )
            )
            ts = None

    if ts:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        # Check future timestamp (allow 5-minute skew tolerance)
        max_allowed = current_time.timestamp() + 300
        if ts.timestamp() > max_allowed:
            findings.append(
                QualityAuditFinding(
                    dimension="TIMELINESS",
                    passed=False,
                    error_code="ERR_TIMESTAMP_FUTURE",
                    message=f"Timestamp '{ts.isoformat()}' lies in the future (current system time: {current_time.isoformat()}).",
                    score=0.0
                )
            )
        else:
            findings.append(
                QualityAuditFinding(
                    dimension="TIMELINESS",
                    passed=True,
                    error_code="VALID",
                    message="Timestamp falls within accepted observation horizon.",
                    score=1.0
                )
            )

    # 3. Energy Plausibility (Non-negative energy)
    energy = record.get("energy_kwh")
    if energy is None:
        findings.append(
            QualityAuditFinding(
                dimension="COMPLETENESS",
                passed=False,
                error_code="ERR_MISSING_ENERGY_VALUE",
                message="Mandatory active energy field 'energy_kwh' is missing or null.",
                score=0.0
            )
        )
    elif energy < 0:
        findings.append(
            QualityAuditFinding(
                dimension="PLAUSIBILITY",
                passed=False,
                error_code="ERR_NEGATIVE_ENERGY",
                message=f"Plausibility failure: Negative energy value ({energy} kWh) recorded on unidirectional meter.",
                score=0.0
            )
        )
    elif energy > 50000:  # Implausible consumption for single aggregate meter in one interval
        findings.append(
            QualityAuditFinding(
                dimension="PLAUSIBILITY",
                passed=False,
                error_code="ERR_ENERGY_OUT_OF_BOUNDS",
                message=f"Plausibility failure: Energy value ({energy} kWh) exceeds maximum physical aggregate capacity.",
                score=0.2
            )
        )
    else:
        findings.append(
            QualityAuditFinding(
                dimension="PLAUSIBILITY",
                passed=True,
                error_code="VALID",
                message="Energy value satisfies physical bound constraints.",
                score=1.0
            )
        )

    # 4. Provenance and Simulation Tagging Validation
    if "is_simulated" not in record:
        findings.append(
            QualityAuditFinding(
                dimension="INTEGRITY",
                passed=False,
                error_code="ERR_MISSING_SIMULATION_FLAG",
                message="Provenance error: Record lacks explicit 'is_simulated' classification flag.",
                score=0.0
            )
        )

    return findings


def audit_boundary_record(record: Dict[str, Any], current_time: datetime = None) -> List[QualityAuditFinding]:
    """
    Evaluates data integrity for a distribution boundary reading (Substation, Feeder, or DT input).
    """
    findings = audit_consumption_record(record, current_time)

    # Additional boundary physics checks: Voltage & Frequency
    voltage = record.get("voltage_v")
    if voltage is not None:
        if voltage < 0:
            findings.append(
                QualityAuditFinding(
                    dimension="PLAUSIBILITY",
                    passed=False,
                    error_code="ERR_NEGATIVE_VOLTAGE",
                    message=f"Invalid negative RMS voltage: {voltage} V",
                    score=0.0
                )
            )
        elif voltage > 350.0 and record.get("boundary_type") == "TRANSFORMER_SECONDARY":
            # 230V LV secondary should not exceed 350V
            findings.append(
                QualityAuditFinding(
                    dimension="PLAUSIBILITY",
                    passed=False,
                    error_code="ERR_VOLTAGE_SPIKE",
                    message=f"Severe overvoltage surge: {voltage} V detected on LV boundary",
                    score=0.0
                )
            )

    freq = record.get("frequency_hz")
    if freq is not None:
        if freq < 45.0 or freq > 55.0:
            findings.append(
                QualityAuditFinding(
                    dimension="PLAUSIBILITY",
                    passed=False,
                    error_code="ERR_FREQUENCY_INSTABILITY",
                    message=f"Severe grid frequency excursion: {freq} Hz outside statutory 45-55 Hz band",
                    score=0.0
                )
            )

    return findings


def detect_duplicates(records: List[Dict[str, Any]], key_fields: Tuple[str, ...]) -> Set[str]:
    """
    Identifies duplicate records within a batch based on composite key fields.
    Returns set of duplicate record identifiers.
    """
    seen: Set[Tuple[Any, ...]] = set()
    duplicates: Set[str] = set()

    for r in records:
        key = tuple(r.get(f) for f in key_fields)
        if key in seen:
            duplicates.add(str(r.get("id") or key))
        else:
            seen.add(key)

    return duplicates

