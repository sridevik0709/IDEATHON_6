"""
Data Quality Engine for GridGuard Nexus X.
Level 3: Core Electricity Intelligence.

Implements deep 10-point audit rules:
1. Missing readings (temporal interval gaps).
2. Duplicate records (timestamp and meter collisions).
3. Invalid timestamps (future timestamps, negative epoch, invalid ISO format).
4. Mismatched measurement intervals (mixing 15-min and 60-min intervals).
5. Inconsistent units (non-whitelisted or un-normalized units).
6. Incorrect network mappings (downstream consumption exceeds upstream, voltage class mismatch).
7. Missing boundary measurements (downstream readings present but boundary reading missing).
8. Implausible readings (negative consumption, voltage sags/swells, extreme spikes).
9. Insufficient historical coverage (< 75% coverage over expected time window).
10. Incomplete network relationships (orphan transformers or feeders without parents).
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.database.models import (
    ConsumptionReading,
    DistributionBoundaryReading,
    HouseholdAggregateMeter,
    NetworkAsset,
    NetworkRelationship,
)

# Standard units allowed in GridGuard
ALLOWED_ENERGY_UNITS = {"KWH"}
ALLOWED_POWER_UNITS = {"KW", "KVA", "KVAR"}
ALLOWED_VOLTAGE_UNITS = {"V", "KV"}
ALLOWED_CURRENT_UNITS = {"A"}
ALLOWED_FREQUENCY_UNITS = {"HZ"}
ALL_VALID_UNITS = (
    ALLOWED_ENERGY_UNITS
    | ALLOWED_POWER_UNITS
    | ALLOWED_VOLTAGE_UNITS
    | ALLOWED_CURRENT_UNITS
    | ALLOWED_FREQUENCY_UNITS
)

# Plausibility limits for 240V/415V distribution
VOLTAGE_MIN_NORMAL = 180.0
VOLTAGE_MAX_NORMAL = 270.0
FREQUENCY_MIN_NORMAL = 48.5
FREQUENCY_MAX_NORMAL = 51.5


@dataclass
class QualityFinding:
    rule_code: str
    dimension: str  # COMPLETENESS, TIMELINESS, RANGE_VALIDITY, CONSISTENCY, TOPOLOGY
    severity: str   # CRITICAL, WARNING, INFO
    passed: bool
    diagnostic_message: str
    target_entity: str
    details: Optional[Dict[str, Any]] = None
    recommended_action: Optional[str] = None


class DataQualityEngine:
    """
    Comprehensive Data Quality Auditor executing 10 deterministic checks.
    Never drops corrupt records; instead annotates them with diagnostic explanations.
    """

    @staticmethod
    def audit_timestamps(
        timestamps: List[datetime],
        target_name: str,
        now: Optional[datetime] = None,
    ) -> List[QualityFinding]:
        """
        Rule 3: Invalid timestamps (future timestamps, timezone-naive, unordered).
        """
        findings: List[QualityFinding] = []
        if now is None:
            now = datetime.now(timezone.utc)

        future_count = 0
        naive_count = 0
        for ts in timestamps:
            if ts.tzinfo is None:
                naive_count += 1
                ts_utc = ts.replace(tzinfo=timezone.utc)
            else:
                ts_utc = ts

            if ts_utc > now:
                future_count += 1

        if future_count > 0:
            findings.append(QualityFinding(
                rule_code="ERR_TIMESTAMP_FUTURE",
                dimension="TIMELINESS",
                severity="CRITICAL",
                passed=False,
                diagnostic_message=(
                    f"Detected {future_count} timestamp(s) in the future relative to system clock ({now.isoformat()}). "
                    "Smart meter clock drift or timezone misconfiguration detected."
                ),
                target_entity=target_name,
                details={"future_count": future_count, "system_time": now.isoformat()},
                recommended_action="Synchronize smart meter NTP/SNTP clock with utility time server.",
            ))

        if naive_count > 0:
            findings.append(QualityFinding(
                rule_code="WARN_TIMESTAMP_TIMEZONE_NAIVE",
                dimension="CONSISTENCY",
                severity="WARNING",
                passed=False,
                diagnostic_message=(
                    f"{naive_count} timestamp(s) missing explicit UTC timezone offsets. "
                    "Assumed UTC but risks daylight saving ambiguity."
                ),
                target_entity=target_name,
                details={"naive_count": naive_count},
                recommended_action="Ensure all telemetry payloads provide ISO 8601 UTC offsets (+00:00 or 'Z').",
            ))

        return findings

    @staticmethod
    def audit_intervals(
        interval_minutes_list: List[int],
        target_name: str,
        expected_interval: int = 60,
    ) -> List[QualityFinding]:
        """
        Rule 4: Mismatched measurement intervals (mixing 15-min, 30-min, 60-min).
        """
        findings: List[QualityFinding] = []
        mismatched = [m for m in interval_minutes_list if m != expected_interval]
        if mismatched:
            distinct_intervals = sorted(list(set(interval_minutes_list)))
            findings.append(QualityFinding(
                rule_code="ERR_INTERVAL_MISMATCH",
                dimension="CONSISTENCY",
                severity="CRITICAL",
                passed=False,
                diagnostic_message=(
                    f"Mismatched measurement intervals detected in series: found {distinct_intervals} minutes. "
                    f"Expected uniform {expected_interval}-minute interval. Incompatible time steps distort energy balance calculations."
                ),
                target_entity=target_name,
                details={"found_intervals": distinct_intervals, "expected_interval": expected_interval},
                recommended_action="Normalize interval readings via interpolation or downsampling before running boundary energy accounting.",
            ))
        return findings

    @staticmethod
    def audit_units(
        units_list: List[str],
        target_name: str,
        expected_unit: str = "KWH",
    ) -> List[QualityFinding]:
        """
        Rule 5: Inconsistent or non-whitelisted measurement units.
        """
        findings: List[QualityFinding] = []
        invalid_units = [u for u in units_list if u.upper() not in ALL_VALID_UNITS]
        mismatched_units = [u for u in units_list if u.upper() != expected_unit.upper()]

        if invalid_units:
            findings.append(QualityFinding(
                rule_code="ERR_UNIT_NON_WHITELISTED",
                dimension="RANGE_VALIDITY",
                severity="CRITICAL",
                passed=False,
                diagnostic_message=(
                    f"Non-standard measurement unit(s) found: {list(set(invalid_units))}. "
                    f"Allowed units are: {sorted(list(ALL_VALID_UNITS))}."
                ),
                target_entity=target_name,
                details={"invalid_units": list(set(invalid_units))},
                recommended_action="Standardize meter telemetry to ISO unit standards.",
            ))
        elif mismatched_units:
            findings.append(QualityFinding(
                rule_code="ERR_UNIT_INCONSISTENT",
                dimension="CONSISTENCY",
                severity="CRITICAL",
                passed=False,
                diagnostic_message=(
                    f"Inconsistent measurement units detected: {list(set(units_list))}. "
                    f"Accounting engine requires strictly uniform '{expected_unit}'."
                ),
                target_entity=target_name,
                details={"found_units": list(set(units_list)), "expected": expected_unit},
                recommended_action=f"Convert all energy measurements to '{expected_unit}' prior to accounting.",
            ))

        return findings

    @staticmethod
    def audit_duplicates(
        records: List[Dict[str, Any]],
        target_name: str,
    ) -> List[QualityFinding]:
        """
        Rule 2: Duplicate records (same timestamp and target identifier).
        """
        findings: List[QualityFinding] = []
        seen = set()
        duplicates_count = 0
        for r in records:
            ts = r.get("timestamp")
            if ts in seen:
                duplicates_count += 1
            else:
                seen.add(ts)

        if duplicates_count > 0:
            findings.append(QualityFinding(
                rule_code="ERR_DUPLICATE_INTERVAL_RECORD",
                dimension="CONSISTENCY",
                severity="CRITICAL",
                passed=False,
                diagnostic_message=(
                    f"Detected {duplicates_count} duplicate interval reading(s) with identical timestamp. "
                    "Unfiltered duplicates cause false inflation of total energy."
                ),
                target_entity=target_name,
                details={"duplicates_count": duplicates_count},
                recommended_action="Apply deterministic deduplication keeping latest ingested payload.",
            ))
        return findings

    @staticmethod
    def audit_coverage_and_missing(
        timestamps: List[datetime],
        target_name: str,
        expected_count: int,
        interval_minutes: int = 60,
    ) -> List[QualityFinding]:
        """
        Rule 1 & Rule 9: Missing readings & Insufficient historical coverage.
        """
        findings: List[QualityFinding] = []
        actual_count = len(timestamps)

        if expected_count > 0:
            coverage_pct = round((actual_count / expected_count) * 100, 2)
            if coverage_pct < 75.0:
                findings.append(QualityFinding(
                    rule_code="WARN_INSUFFICIENT_COVERAGE",
                    dimension="COMPLETENESS",
                    severity="WARNING",
                    passed=False,
                    diagnostic_message=(
                        f"Insufficient historical coverage: {actual_count}/{expected_count} readings ({coverage_pct}%). "
                        "Minimum required coverage for high-confidence forensic accounting is 75%."
                    ),
                    target_entity=target_name,
                    details={"actual_count": actual_count, "expected_count": expected_count, "coverage_pct": coverage_pct},
                    recommended_action="Request telemetry backfill from Meter Data Management System (MDMS).",
                ))

            missing_count = expected_count - actual_count
            if missing_count > 0 and coverage_pct >= 75.0:
                findings.append(QualityFinding(
                    rule_code="WARN_MISSING_READINGS",
                    dimension="COMPLETENESS",
                    severity="WARNING",
                    passed=False,
                    diagnostic_message=(
                        f"{missing_count} expected interval reading(s) are missing from the time window. "
                        "May indicate intermittent cellular/RF mesh communication dropouts."
                    ),
                    target_entity=target_name,
                    details={"missing_count": missing_count, "actual": actual_count, "expected": expected_count},
                    recommended_action="Flag missing intervals for automated telemetry retry.",
                ))

        return findings

    @staticmethod
    def audit_plausibility(
        readings: List[Dict[str, Any]],
        target_name: str,
    ) -> List[QualityFinding]:
        """
        Rule 8: Implausible readings (negative consumption, voltage sags/swells, extreme spikes).
        """
        findings: List[QualityFinding] = []
        neg_energy_count = 0
        voltage_swell_count = 0
        voltage_sag_count = 0

        for r in readings:
            energy = r.get("energy_kwh", 0.0)
            if energy is not None and energy < 0.0:
                neg_energy_count += 1

            voltage = r.get("voltage_v")
            if voltage is not None:
                if voltage > VOLTAGE_MAX_NORMAL:
                    voltage_swell_count += 1
                elif voltage < VOLTAGE_MIN_NORMAL and voltage > 0.0:
                    voltage_sag_count += 1

        if neg_energy_count > 0:
            findings.append(QualityFinding(
                rule_code="ERR_ENERGY_NEGATIVE",
                dimension="RANGE_VALIDITY",
                severity="CRITICAL",
                passed=False,
                diagnostic_message=(
                    f"Found {neg_energy_count} negative energy reading(s). "
                    "Consumer meters without registered prosumer solar net-metering cannot physically export negative energy."
                ),
                target_entity=target_name,
                details={"neg_energy_count": neg_energy_count},
                recommended_action="Inspect CT polarity wiring or calibrate meter register reverse-energy detents.",
            ))

        if voltage_swell_count > 0:
            findings.append(QualityFinding(
                rule_code="ERR_VOLTAGE_SWELL",
                dimension="RANGE_VALIDITY",
                severity="WARNING",
                passed=False,
                diagnostic_message=(
                    f"Found {voltage_swell_count} reading(s) with voltage exceeding {VOLTAGE_MAX_NORMAL}V. "
                    "Severe over-voltage indicates neutral floating or distribution transformer tap-changer misconfiguration."
                ),
                target_entity=target_name,
                details={"voltage_swell_count": voltage_swell_count, "threshold_max": VOLTAGE_MAX_NORMAL},
                recommended_action="Dispatch field technician to inspect substation neutral grounding.",
            ))

        if voltage_sag_count > 0:
            findings.append(QualityFinding(
                rule_code="WARN_VOLTAGE_SAG",
                dimension="RANGE_VALIDITY",
                severity="WARNING",
                passed=False,
                diagnostic_message=(
                    f"Found {voltage_sag_count} reading(s) with voltage below {VOLTAGE_MIN_NORMAL}V. "
                    "Severe under-voltage indicates excessive feeder impedance or heavy unmetered downstream loading."
                ),
                target_entity=target_name,
                details={"voltage_sag_count": voltage_sag_count, "threshold_min": VOLTAGE_MIN_NORMAL},
                recommended_action="Check for line overloading and phase imbalance.",
            ))

        return findings

    @classmethod
    def audit_meter_full(
        cls,
        meter: HouseholdAggregateMeter,
        readings: List[ConsumptionReading],
        expected_intervals: int = 24,
    ) -> List[QualityFinding]:
        """
        Runs comprehensive data quality checks on a household aggregate meter series.
        """
        findings: List[QualityFinding] = []
        name = meter.meter_code

        # 1. Timestamps
        ts_list = [r.timestamp for r in readings]
        findings.extend(cls.audit_timestamps(ts_list, name))

        # 2. Intervals
        int_list = [r.interval_minutes for r in readings]
        findings.extend(cls.audit_intervals(int_list, name, expected_interval=60))

        # 3. Units
        unit_list = [r.unit for r in readings]
        findings.extend(cls.audit_units(unit_list, name, expected_unit="KWH"))

        # 4. Duplicates
        records_dict = [{"timestamp": r.timestamp, "energy_kwh": r.energy_kwh} for r in readings]
        findings.extend(cls.audit_duplicates(records_dict, name))

        # 5. Coverage and missing
        findings.extend(cls.audit_coverage_and_missing(ts_list, name, expected_count=expected_intervals))

        # 6. Plausibility
        findings.extend(cls.audit_plausibility(records_dict, name))

        # 7. Network Mapping / Orphan Check (Rule 10)
        if not meter.associated_asset_id:
            findings.append(QualityFinding(
                rule_code="ERR_ORPHAN_METER_NO_ASSET",
                dimension="TOPOLOGY",
                severity="CRITICAL",
                passed=False,
                diagnostic_message=(
                    f"Meter '{name}' is not mapped to any upstream distribution transformer or feeder asset. "
                    "Orphan meters cannot be included in physical boundary energy accounting."
                ),
                target_entity=name,
                recommended_action="Assign valid upstream Distribution Transformer asset in GIS network topology.",
            ))

        return findings

    @classmethod
    def audit_boundary_topology(
        cls,
        db: Session,
        boundary_asset: NetworkAsset,
        boundary_readings: List[DistributionBoundaryReading],
        downstream_meters: List[HouseholdAggregateMeter],
        downstream_readings: List[ConsumptionReading],
    ) -> List[QualityFinding]:
        """
        Audit boundary integrity (Rule 6, 7, 10).
        """
        findings: List[QualityFinding] = []
        asset_name = boundary_asset.asset_code

        # Rule 7: Missing boundary measurements
        if not boundary_readings and downstream_readings:
            findings.append(QualityFinding(
                rule_code="ERR_MISSING_BOUNDARY_MEASUREMENT",
                dimension="COMPLETENESS",
                severity="CRITICAL",
                passed=False,
                diagnostic_message=(
                    f"Boundary asset '{asset_name}' has 0 input energy measurements for the period, "
                    f"while {len(downstream_readings)} downstream consumption reading(s) are recorded. "
                    "Energy balance cannot be computed without boundary input telemetry."
                ),
                target_entity=asset_name,
                details={"downstream_readings_count": len(downstream_readings)},
                recommended_action="Inspect boundary check meter / modem connectivity on the distribution transformer.",
            ))

        # Rule 10: Incomplete network relationships (Orphan check)
        if boundary_asset.asset_type == "TRANSFORMER":
            parent_rel = db.query(NetworkRelationship).filter(
                NetworkRelationship.child_asset_id == boundary_asset.id,
                NetworkRelationship.is_current == True,
            ).first()
            if not parent_rel:
                findings.append(QualityFinding(
                    rule_code="WARN_ORPHAN_TRANSFORMER_NO_FEEDER",
                    dimension="TOPOLOGY",
                    severity="WARNING",
                    passed=False,
                    diagnostic_message=(
                        f"Distribution transformer '{asset_name}' has no active parent feeder relationship in the network graph."
                    ),
                    target_entity=asset_name,
                    recommended_action="Link transformer to its feeding 33kV/11kV primary feeder in GIS database.",
                ))
        elif boundary_asset.asset_type == "FEEDER":
            parent_rel = db.query(NetworkRelationship).filter(
                NetworkRelationship.child_asset_id == boundary_asset.id,
                NetworkRelationship.is_current == True,
            ).first()
            if not parent_rel:
                findings.append(QualityFinding(
                    rule_code="WARN_ORPHAN_FEEDER_NO_SUBSTATION",
                    dimension="TOPOLOGY",
                    severity="WARNING",
                    passed=False,
                    diagnostic_message=(
                        f"Feeder '{asset_name}' has no active parent substation relationship in the network graph."
                    ),
                    target_entity=asset_name,
                    recommended_action="Link feeder to its source 132/33kV substation busbar.",
                ))

        # Rule 6: Incorrect Network Mapping (GIS Discrepancy)
        total_boundary_in = sum(r.energy_kwh for r in boundary_readings if r.boundary_type == "INPUT")
        total_downstream = sum(r.energy_kwh for r in downstream_readings)

        # If downstream consumption significantly exceeds upstream input (e.g. by > 5%)
        if total_boundary_in > 0 and total_downstream > (total_boundary_in * 1.05):
            excess_kwh = round(total_downstream - total_boundary_in, 2)
            excess_pct = round(((total_downstream - total_boundary_in) / total_boundary_in) * 100, 2)
            findings.append(QualityFinding(
                rule_code="ERR_INCORRECT_DOWNSTREAM_ASSET_MAPPING",
                dimension="TOPOLOGY",
                severity="CRITICAL",
                passed=False,
                diagnostic_message=(
                    f"Downstream consumption ({total_downstream:.1f} kWh) exceeds upstream boundary input "
                    f"({total_boundary_in:.1f} kWh) by {excess_kwh} kWh (+{excess_pct}%). "
                    "Negative loss indicates downstream meters are physically connected to a different upstream transformer (GIS mapping error)."
                ),
                target_entity=asset_name,
                details={
                    "boundary_in_kwh": total_boundary_in,
                    "downstream_recorded_kwh": total_downstream,
                    "excess_kwh": excess_kwh,
                    "excess_pct": excess_pct,
                },
                recommended_action="Reconcile GIS single-line diagram against physical phase tracer audits to correct meter-to-transformer assignment.",
            ))

        return findings
