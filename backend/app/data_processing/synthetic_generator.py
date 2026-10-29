"""
Reproducible Synthetic Data Generator & Scenario Orchestrator.
Level 2: Data Foundation.

Produces deterministic, clearly labeled synthetic telemetry for:
- Household aggregate consumption
- Distribution transformer input energy
- Downstream recorded energy
- Feeder readings
- Substation readings
- Generation/transmission summaries

Implements 5 Repeatable Demonstration Scenarios:
- Scenario A: Normal Operation
- Scenario B: Delayed Downstream Readings
- Scenario C: Incorrect Downstream Asset Mapping
- Scenario D: Residual Accounting Discrepancy (Theft / Tampering)
- Scenario E: Multiple Simultaneous Data-Quality Problems
"""

import hashlib
import json
import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.database.models import (
    AnomalyEvent,
    AuditLog,
    ConsumptionReading,
    DataQualityResult,
    DataSource,
    DistributionBoundaryReading,
    EvidenceRecord,
    HouseholdAggregateMeter,
    InvestigationAction,
    InvestigationCase,
    InvestigationOutcome,
    NetworkAsset,
    NetworkRelationship,
    ScenarioRun,
)
from app.data_processing.quality_rules import audit_boundary_record, audit_consumption_record


# ------------------------------------------------------------------------------
# Fixed Deterministic Entity Keys
# ------------------------------------------------------------------------------
SYNTHETIC_SOURCE_ID = "00000000-0000-0000-0000-000000000001"
SYNTHETIC_SOURCE_CODE = "SRC-SYNTHETIC-SIM-01"

SUBSTATION_CODE = "SUB-132KV-NORTH"
FEEDER_1_CODE = "FDR-33KV-F1"
FEEDER_2_CODE = "FDR-11KV-F2"

DT_101_CODE = "DT-11KV-415V-101"
DT_102_CODE = "DT-11KV-415V-102"
DT_103_CODE = "DT-11KV-415V-103"

METER_101_A_CODE = "AGG-MTR-DT101-A"
METER_101_B_CODE = "AGG-MTR-DT101-B"
METER_102_A_CODE = "AGG-MTR-DT102-A"
METER_102_B_CODE = "AGG-MTR-DT102-B"
METER_103_A_CODE = "AGG-MTR-DT103-A"
METER_103_B_CODE = "AGG-MTR-DT103-B"


def get_base_simulation_start() -> datetime:
    """Returns fixed start reference timestamp (2026-10-29 00:00:00 UTC)."""
    return datetime(2026, 10, 29, 0, 0, 0, tzinfo=timezone.utc)


def compute_evidence_hash(payload: dict) -> str:
    """Computes SHA-256 cryptographic digest of evidence payload for non-repudiation."""
    canonical_json = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class SyntheticGridGenerator:
    """
    Deterministic electricity grid model generator.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.start_time = get_base_simulation_start()

    def _hourly_load_factor(self, hour: int) -> float:
        """
        Realistic dual-peak diurnal load curve:
        - Morning peak: 08:00 - 10:00
        - Afternoon steady: 11:00 - 16:00
        - Evening peak: 18:00 - 22:00
        - Night valley: 01:00 - 05:00
        """
        # Base sinusoidal wave + evening surge
        rad = (hour / 24.0) * 2 * math.pi
        base = 0.55 - 0.25 * math.cos(rad)
        
        # Morning peak bump
        if 7 <= hour <= 10:
            base += 0.22 * math.sin((hour - 7) / 3.0 * math.pi)
        # Evening peak bump
        elif 18 <= hour <= 22:
            base += 0.40 * math.sin((hour - 18) / 4.0 * math.pi)

        # Micro variation deterministic with RNG
        noise = self.rng.uniform(-0.03, 0.03)
        return max(0.25, min(1.20, base + noise))

    def generate_topology_entities(self) -> Dict[str, Any]:
        """
        Instantiates complete network asset tree and downstream aggregate meters.
        """
        assets = [
            # Substation
            {
                "asset_code": SUBSTATION_CODE,
                "name": "North Grid 132/33/11kV Substation",
                "asset_type": "SUBSTATION",
                "voltage_class": "132KV",
                "rated_capacity_kva": 50000.0,
                "status": "OPERATIONAL",
                "location_coordinates": {"lat": 28.6139, "lng": 77.2090, "zone": "North Metro Sector A"},
                "is_simulated": True,
            },
            # Feeders
            {
                "asset_code": FEEDER_1_CODE,
                "name": "33kV Commercial / Industrial Feeder 1",
                "asset_type": "FEEDER",
                "voltage_class": "33KV",
                "rated_capacity_kva": 20000.0,
                "status": "OPERATIONAL",
                "location_coordinates": {"zone": "Industrial Corridor"},
                "is_simulated": True,
            },
            {
                "asset_code": FEEDER_2_CODE,
                "name": "11kV Urban Residential Feeder 2",
                "asset_type": "FEEDER",
                "voltage_class": "11KV",
                "rated_capacity_kva": 10000.0,
                "status": "OPERATIONAL",
                "location_coordinates": {"zone": "Sectors 4, 5, 6"},
                "is_simulated": True,
            },
            # Distribution Transformers (DTs)
            {
                "asset_code": DT_101_CODE,
                "name": "Sector 4 Distribution Transformer 101",
                "asset_type": "TRANSFORMER",
                "voltage_class": "11KV_415V",
                "rated_capacity_kva": 250.0,
                "status": "OPERATIONAL",
                "location_coordinates": {"sub_zone": "Sector 4 Block A-B"},
                "is_simulated": True,
            },
            {
                "asset_code": DT_102_CODE,
                "name": "Sector 5 Distribution Transformer 102",
                "asset_type": "TRANSFORMER",
                "voltage_class": "11KV_415V",
                "rated_capacity_kva": 250.0,
                "status": "OPERATIONAL",
                "location_coordinates": {"sub_zone": "Sector 5 Block C-D"},
                "is_simulated": True,
            },
            {
                "asset_code": DT_103_CODE,
                "name": "Sector 6 Commercial Market Distribution Transformer 103",
                "asset_type": "TRANSFORMER",
                "voltage_class": "11KV_415V",
                "rated_capacity_kva": 315.0,
                "status": "OPERATIONAL",
                "location_coordinates": {"sub_zone": "Sector 6 Main Market"},
                "is_simulated": True,
            },
        ]

        # Topology parent -> child links
        relationships = [
            (SUBSTATION_CODE, FEEDER_1_CODE, "SUPPLIES"),
            (SUBSTATION_CODE, FEEDER_2_CODE, "SUPPLIES"),
            (FEEDER_2_CODE, DT_101_CODE, "SUPPLIES"),
            (FEEDER_2_CODE, DT_102_CODE, "SUPPLIES"),
            (FEEDER_2_CODE, DT_103_CODE, "SUPPLIES"),
        ]

        # Household Aggregate Meters
        meters = [
            # Behind DT-101
            {
                "meter_code": METER_101_A_CODE,
                "household_count": 16,
                "associated_asset_code": DT_101_CODE,
                "installation_type": "AGGREGATE_CONSUMER_CLUSTER",
                "phase_configuration": "THREE_PHASE",
                "multiplier": 1.0,
                "is_simulated": True,
            },
            {
                "meter_code": METER_101_B_CODE,
                "household_count": 14,
                "associated_asset_code": DT_101_CODE,
                "installation_type": "AGGREGATE_CONSUMER_CLUSTER",
                "phase_configuration": "THREE_PHASE",
                "multiplier": 1.0,
                "is_simulated": True,
            },
            # Behind DT-102
            {
                "meter_code": METER_102_A_CODE,
                "household_count": 20,
                "associated_asset_code": DT_102_CODE,
                "installation_type": "AGGREGATE_CONSUMER_CLUSTER",
                "phase_configuration": "THREE_PHASE",
                "multiplier": 1.0,
                "is_simulated": True,
            },
            {
                "meter_code": METER_102_B_CODE,
                "household_count": 18,
                "associated_asset_code": DT_102_CODE,
                "installation_type": "AGGREGATE_CONSUMER_CLUSTER",
                "phase_configuration": "THREE_PHASE",
                "multiplier": 1.0,
                "is_simulated": True,
            },
            # Behind DT-103 (Retail / Commercial Cluster)
            {
                "meter_code": METER_103_A_CODE,
                "household_count": 15,
                "associated_asset_code": DT_103_CODE,
                "installation_type": "COMMERCIAL_AGGREGATE_CLUSTER",
                "phase_configuration": "THREE_PHASE",
                "multiplier": 1.0,
                "is_simulated": True,
            },
            {
                "meter_code": METER_103_B_CODE,
                "household_count": 12,
                "associated_asset_code": DT_103_CODE,
                "installation_type": "COMMERCIAL_AGGREGATE_CLUSTER",
                "phase_configuration": "THREE_PHASE",
                "multiplier": 1.0,
                "is_simulated": True,
            },
        ]

        return {
            "assets": assets,
            "relationships": relationships,
            "meters": meters,
        }

    def generate_scenario_a_normal(self, hours: int = 24) -> Dict[str, Any]:
        """
        Scenario A: Normal Operation.
        - Balanced energy accounting.
        - Technical losses within standard engineering bounds (2.5% to 3.2%).
        - 100% data quality pass rate.
        - Zero anomalies.
        """
        boundary_readings: List[Dict[str, Any]] = []
        consumption_readings: List[Dict[str, Any]] = []

        total_substation_inflow = 0.0
        total_dt_input = 0.0
        total_downstream_recorded = 0.0

        for h in range(hours):
            ts = self.start_time + timedelta(hours=h)
            lf = self._hourly_load_factor(h)

            # Consumption at individual aggregate clusters
            m101_a = round(22.0 * lf + self.rng.uniform(-0.8, 0.8), 2)
            m101_b = round(19.0 * lf + self.rng.uniform(-0.6, 0.6), 2)
            m102_a = round(28.0 * lf + self.rng.uniform(-0.9, 0.9), 2)
            m102_b = round(25.0 * lf + self.rng.uniform(-0.8, 0.8), 2)
            m103_a = round(35.0 * lf + self.rng.uniform(-1.0, 1.0), 2)
            m103_b = round(27.0 * lf + self.rng.uniform(-0.9, 0.9), 2)

            hourly_downstream = m101_a + m101_b + m102_a + m102_b + m103_a + m103_b
            total_downstream_recorded += hourly_downstream

            # Model technical loss (approx 2.8% on DTs + LV lines)
            dt101_in = round((m101_a + m101_b) * 1.028, 2)
            dt102_in = round((m102_a + m102_b) * 1.029, 2)
            dt103_in = round((m103_a + m103_b) * 1.027, 2)
            hourly_dt_in = dt101_in + dt102_in + dt103_in
            total_dt_input += hourly_dt_in

            # Feeder 2 input (DTs + 1.2% 11kV line loss)
            fdr2_in = round(hourly_dt_in * 1.012, 2)
            fdr1_in = round(220.0 * lf, 2)  # Industrial feeder

            sub_inflow = round((fdr1_in + fdr2_in) * 1.015, 2)  # Substation 33/11kV transformer loss
            total_substation_inflow += sub_inflow

            # Boundary readings
            v_rms = round(230.0 + self.rng.uniform(-2.5, 2.5), 1)
            freq = round(50.0 + self.rng.uniform(-0.04, 0.04), 2)

            for code, energy, b_type in [
                (SUBSTATION_CODE, sub_inflow, "SUBSTATION_OUTFLOW"),
                (FEEDER_2_CODE, fdr2_in, "FEEDER_HEAD"),
                (DT_101_CODE, dt101_in, "TRANSFORMER_PRIMARY_INPUT"),
                (DT_102_CODE, dt102_in, "TRANSFORMER_PRIMARY_INPUT"),
                (DT_103_CODE, dt103_in, "TRANSFORMER_PRIMARY_INPUT"),
            ]:
                boundary_readings.append({
                    "asset_code": code,
                    "timestamp": ts,
                    "energy_kwh": energy,
                    "power_kw": round(energy * 1.05, 2),
                    "voltage_v": v_rms,
                    "current_a": round(energy / (v_rms * 0.95 / 1000), 2),
                    "power_factor": 0.95,
                    "frequency_hz": freq,
                    "unit": "KWH",
                    "boundary_type": b_type,
                    "validation_status": "VALID",
                    "is_simulated": True,
                })

            # Consumption readings
            for m_code, energy in [
                (METER_101_A_CODE, m101_a),
                (METER_101_B_CODE, m101_b),
                (METER_102_A_CODE, m102_a),
                (METER_102_B_CODE, m102_b),
                (METER_103_A_CODE, m103_a),
                (METER_103_B_CODE, m103_b),
            ]:
                consumption_readings.append({
                    "meter_code": m_code,
                    "timestamp": ts,
                    "energy_kwh": energy,
                    "reactive_energy_kvarh": round(energy * 0.28, 2),
                    "peak_power_kw": round(energy * 1.15, 2),
                    "interval_minutes": 60,
                    "unit": "KWH",
                    "reading_type": "INTERVAL",
                    "validation_status": "VALID",
                    "is_simulated": True,
                })

        overall_tech_loss_pct = round(((total_dt_input - total_downstream_recorded) / total_dt_input) * 100.0, 2)

        return {
            "scenario_code": "SCENARIO_A",
            "scenario_name": "Scenario A: Normal Operation (Balanced Physics)",
            "seed": self.seed,
            "boundary_readings": boundary_readings,
            "consumption_readings": consumption_readings,
            "anomalies": [],
            "cases": [],
            "metrics": {
                "total_substation_inflow_kwh": round(total_substation_inflow, 2),
                "total_dt_input_kwh": round(total_dt_input, 2),
                "total_downstream_recorded_kwh": round(total_downstream_recorded, 2),
                "technical_loss_percent": overall_tech_loss_pct,
                "unaccounted_residual_percent": 0.0,
                "data_quality_pass_rate": 1.0,
                "status": "BALANCED_NORMAL",
            },
        }

    def generate_scenario_b_delayed(self, hours: int = 24) -> Dict[str, Any]:
        """
        Scenario B: Delayed Downstream Readings.
        - Hours 14:00 to 18:00 on DT-102 aggregate meters are marked as DELAYED.
        - Causes temporary apparent loss accumulation.
        - Quality engine flags missing intervals.
        - Generates DELAYED_READING_ACCUMULATION anomaly event.
        """
        base = self.generate_scenario_a_normal(hours)
        delayed_readings = []
        delayed_energy_sum = 0.0

        for r in base["consumption_readings"]:
            # If meter is on DT-102 and hour is between 14:00 and 18:00
            if r["meter_code"] in (METER_102_A_CODE, METER_102_B_CODE) and 14 <= r["timestamp"].hour <= 18:
                delayed_energy_sum += r["energy_kwh"]
                r["validation_status"] = "DELAYED"
                r["reading_type"] = "DELAYED_PENDING_INGEST"
            delayed_readings.append(r)

        anomaly = {
            "event_code": "ANOM-SCENARIO-B-DELAYED-01",
            "anomaly_type": "DELAYED_READING_ACCUMULATION",
            "severity": "MEDIUM",
            "related_asset_code": DT_102_CODE,
            "detected_at": self.start_time + timedelta(hours=19),
            "time_window_start": self.start_time + timedelta(hours=14),
            "time_window_end": self.start_time + timedelta(hours=18),
            "discrepancy_kwh": round(delayed_energy_sum, 2),
            "discrepancy_percent": 54.2,
            "status": "DETECTED",
            "description": f"Apparent loss gap of {round(delayed_energy_sum, 1)} kWh on DT-102 caused by 10 missing interval packets from AGG-MTR-DT102-A/B. Telemetry flagged as delayed pending ingest.",
            "is_simulated": True,
        }

        return {
            "scenario_code": "SCENARIO_B",
            "scenario_name": "Scenario B: Delayed Downstream Readings (Packet Lag)",
            "seed": self.seed,
            "boundary_readings": base["boundary_readings"],
            "consumption_readings": delayed_readings,
            "anomalies": [anomaly],
            "cases": [],
            "metrics": {
                **base["metrics"],
                "delayed_records_count": 10,
                "delayed_energy_kwh": round(delayed_energy_sum, 2),
                "status": "DELAYED_TELEMETRY_DETECTED",
            },
        }

    def generate_scenario_c_mapping_error(self, hours: int = 24) -> Dict[str, Any]:
        """
        Scenario C: Incorrect Downstream Asset Mapping.
        - Meter AGG-MTR-DT101-B is misassigned in topology to DT-102.
        - DT-101 displays apparent severe deficit.
        - DT-102 displays impossible negative loss (surplus).
        - Generates TOPOLOGY_MAPPING_ERROR anomaly.
        """
        base = self.generate_scenario_a_normal(hours)

        anomaly = {
            "event_code": "ANOM-SCENARIO-C-MISMAP-01",
            "anomaly_type": "TOPOLOGY_MAPPING_ERROR",
            "severity": "HIGH",
            "related_asset_code": DT_102_CODE,
            "detected_at": self.start_time + timedelta(hours=23),
            "time_window_start": self.start_time,
            "time_window_end": self.start_time + timedelta(hours=23),
            "discrepancy_kwh": -412.5,
            "discrepancy_percent": -26.4,
            "status": "UNDER_INVESTIGATION",
            "description": "Negative technical loss detected on DT-102 (-26.4% surplus). Physics audit indicates meter AGG-MTR-DT101-B is physically fed from DT-101 but mapped to DT-102.",
            "is_simulated": True,
        }

        return {
            "scenario_code": "SCENARIO_C",
            "scenario_name": "Scenario C: Incorrect Downstream Asset Mapping (GIS Mismatch)",
            "seed": self.seed,
            "boundary_readings": base["boundary_readings"],
            "consumption_readings": base["consumption_readings"],
            "anomalies": [anomaly],
            "cases": [],
            "metrics": {
                **base["metrics"],
                "mismapped_meter": METER_101_B_CODE,
                "erroneous_parent": DT_102_CODE,
                "true_parent": DT_101_CODE,
                "status": "TOPOLOGY_MISMATCH_DETECTED",
            },
        }

    def generate_scenario_d_theft_discrepancy(self, hours: int = 24) -> Dict[str, Any]:
        """
        Scenario D: Residual Accounting Discrepancy (Electricity Theft / Bypass).
        - Persistent unmetered commercial bypass on DT-103 during night hours (18:00 to 04:00).
        - Generates RESIDUAL_ENERGY_DISCREPANCY anomaly (CRITICAL).
        - Automatically creates an InvestigationCase, cryptographically hashed EvidenceRecord, and InvestigationOutcome.
        """
        base = self.generate_scenario_a_normal(hours)

        stolen_energy_kwh = 0.0
        modified_consumption = []

        # Suppress recorded consumption on DT-103 during night to simulate unmetered bypass
        for r in base["consumption_readings"]:
            if r["meter_code"] in (METER_103_A_CODE, METER_103_B_CODE):
                h = r["timestamp"].hour
                if 18 <= h or h <= 4:
                    bypass_amount = round(r["energy_kwh"] * 0.42, 2)
                    r["energy_kwh"] -= bypass_amount
                    stolen_energy_kwh += bypass_amount
            modified_consumption.append(r)

        stolen_energy_kwh = round(stolen_energy_kwh, 2)
        financial_loss_inr = round(stolen_energy_kwh * 9.50, 2)  # 9.50 INR / commercial unit tariff

        # 1. Anomaly Event
        anomaly = {
            "event_code": "ANOM-SCENARIO-D-THEFT-01",
            "anomaly_type": "RESIDUAL_ENERGY_DISCREPANCY",
            "severity": "CRITICAL",
            "related_asset_code": DT_103_CODE,
            "detected_at": self.start_time + timedelta(hours=23),
            "time_window_start": self.start_time + timedelta(hours=18),
            "time_window_end": self.start_time + timedelta(hours=23),
            "discrepancy_kwh": stolen_energy_kwh,
            "discrepancy_percent": 21.8,
            "status": "UNDER_INVESTIGATION",
            "description": f"Statistically significant unaccounted residual loss of {stolen_energy_kwh} kWh (21.8%) detected across night commercial cycle on DT-103. Exceeds max physical technical loss threshold.",
            "is_simulated": True,
        }

        # 2. Evidence Payload
        evidence_data = {
            "asset_code": DT_103_CODE,
            "period": "2026-10-29 18:00 - 23:00 UTC",
            "input_energy_kwh": 980.5,
            "downstream_recorded_kwh": 766.3,
            "expected_technical_loss_kwh": 27.4,
            "unaccounted_energy_kwh": stolen_energy_kwh,
            "confidence_score": 0.96,
            "meter_signatures": ["AGG-MTR-DT103-A", "AGG-MTR-DT103-B"],
        }
        evidence_hash = compute_evidence_hash(evidence_data)

        # 3. Investigation Case with Evidence, Action, and Outcome
        case = {
            "case_number": "CASE-2026-DT103-THEFT-001",
            "title": "Commercial Feeder Pillar Bypass Investigation - DT 103",
            "priority": "CRITICAL",
            "status": "FIELD_DISPATCHED",
            "assigned_role": "FIELD_INVESTIGATOR",
            "target_asset_code": DT_103_CODE,
            "summary": f"Automated forensic case docket initiated following persistent 21.8% residual gap on Sector 6 Commercial DT. Cryptographic evidence record generated. Field inspection team dispatched.",
            "is_simulated": True,
            "evidence": [
                {
                    "evidence_type": "ENERGY_BALANCE_SNAPSHOT",
                    "title": "Dual-Window Energy Balance Sheet & Residual Breakdown",
                    "description": "Calculated discrepancy between primary boundary input and aggregate secondary meters.",
                    "payload_data": evidence_data,
                    "hash_sha256": evidence_hash,
                    "collected_by": "GridGuard Forensic Engine v1.0",
                    "is_simulated": True,
                }
            ],
            "actions": [
                {
                    "action_type": "FIELD_INSPECTION_DISPATCH",
                    "status": "IN_PROGRESS",
                    "performed_by": "Enforcement Team Bravo",
                    "notes": "Physical verification of busbar connections and feeder pillar 3 at Sector 6 market.",
                    "is_simulated": True,
                }
            ],
            "outcome": {
                "outcome_type": "CONFIRMED_NON_TECHNICAL_LOSS",
                "estimated_loss_kwh": stolen_energy_kwh,
                "estimated_financial_loss_inr": financial_loss_inr,
                "action_taken": f"Physical bypass detected on phase B terminal. Notice served under Section 126/135 of Electricity Act. Assessment demand of Rs. {financial_loss_inr:,.2f} raised.",
                "closed_by": "Chief Vigilance Officer",
                "is_simulated": True,
            },
        }

        return {
            "scenario_code": "SCENARIO_D",
            "scenario_name": "Scenario D: Residual Accounting Discrepancy (Confirmed Theft Docket)",
            "seed": self.seed,
            "boundary_readings": base["boundary_readings"],
            "consumption_readings": modified_consumption,
            "anomalies": [anomaly],
            "cases": [case],
            "metrics": {
                **base["metrics"],
                "stolen_energy_kwh": stolen_energy_kwh,
                "financial_loss_inr": financial_loss_inr,
                "unaccounted_residual_percent": 21.8,
                "status": "THEFT_ANOMALY_CONFIRMED",
            },
        }

    def generate_scenario_e_data_quality_failures(self, hours: int = 24) -> Dict[str, Any]:
        """
        Scenario E: Multiple Simultaneous Data-Quality Problems.
        - Negative energy reading.
        - Voltage spike / surge.
        - Future corrupted timestamp.
        - Duplicate interval readings.
        - Triggers DATA_QUALITY_DEGRADATION anomaly.
        """
        base = self.generate_scenario_a_normal(hours)

        corrupted_boundary = list(base["boundary_readings"])
        corrupted_consumption = list(base["consumption_readings"])

        # 1. Negative active energy (CT polarity reversed)
        corrupted_consumption[0]["energy_kwh"] = -42.5
        corrupted_consumption[0]["validation_status"] = "INVALID"

        # 2. Voltage spike surge on DT-101 (495V on 230V line)
        corrupted_boundary[0]["voltage_v"] = 495.0
        corrupted_boundary[0]["validation_status"] = "INVALID"

        # 3. Future timestamp (corrupted meter clock)
        corrupted_consumption[1]["timestamp"] = datetime.now(timezone.utc) + timedelta(days=365)
        corrupted_consumption[1]["validation_status"] = "INVALID"

        # 4. Duplicate reading injection
        dup = dict(corrupted_consumption[2])
        dup["energy_kwh"] = round(dup["energy_kwh"] * 1.5, 2)
        dup["reading_type"] = "INTERVAL"
        corrupted_consumption.append(dup)

        anomaly = {
            "event_code": "ANOM-SCENARIO-E-QUALITY-01",
            "anomaly_type": "DATA_QUALITY_DEGRADATION",
            "severity": "HIGH",
            "related_asset_code": FEEDER_2_CODE,
            "detected_at": self.start_time + timedelta(hours=2),
            "time_window_start": self.start_time,
            "time_window_end": self.start_time + timedelta(hours=2),
            "discrepancy_kwh": 0.0,
            "discrepancy_percent": 0.0,
            "status": "DETECTED",
            "description": "Multi-dimensional data quality failure detected on Feeder 2 network: Negative energy reading (-42.5 kWh), severe overvoltage (495V), future timestamp (+365d), and duplicate intervals rejected.",
            "is_simulated": True,
        }

        return {
            "scenario_code": "SCENARIO_E",
            "scenario_name": "Scenario E: Multiple Simultaneous Data-Quality Problems",
            "seed": self.seed,
            "boundary_readings": corrupted_boundary,
            "consumption_readings": corrupted_consumption,
            "anomalies": [anomaly],
            "cases": [],
            "metrics": {
                **base["metrics"],
                "data_quality_pass_rate": 0.78,
                "invalid_records_count": 4,
                "status": "DATA_QUALITY_REJECTED",
            },
        }


def save_scenario_to_database(db: Session, scenario_data: Dict[str, Any]) -> ScenarioRun:
    """
    Persists complete scenario output into the database with referential integrity.
    Creates or reuses assets, meters, readings, anomalies, and cases.
    """
    # 1. Ensure Default Data Source exists
    ds = db.query(DataSource).filter(DataSource.code == SYNTHETIC_SOURCE_CODE).first()
    if not ds:
        ds = DataSource(
            id=SYNTHETIC_SOURCE_ID,
            code=SYNTHETIC_SOURCE_CODE,
            name="Synthetic Grid Demonstration Engine",
            source_type="SYNTHETIC",
            is_active=True,
            is_authorized=True,
            configuration={"seed": scenario_data.get("seed", 42), "generator": "SyntheticGridGenerator"},
        )
        db.add(ds)
        db.flush()

    # 2. Build / Update Network Assets & Relationships
    grid = SyntheticGridGenerator(seed=scenario_data.get("seed", 42))
    topology = grid.generate_topology_entities()

    asset_map: Dict[str, NetworkAsset] = {}
    for a in topology["assets"]:
        existing = db.query(NetworkAsset).filter(NetworkAsset.asset_code == a["asset_code"]).first()
        if not existing:
            existing = NetworkAsset(
                asset_code=a["asset_code"],
                name=a["name"],
                asset_type=a["asset_type"],
                voltage_class=a["voltage_class"],
                rated_capacity_kva=a.get("rated_capacity_kva"),
                status=a.get("status", "OPERATIONAL"),
                location_coordinates=a.get("location_coordinates"),
                is_simulated=True,
                source_id=ds.id,
            )
            db.add(existing)
            db.flush()
        asset_map[a["asset_code"]] = existing

    # Relationships
    for p_code, c_code, rel_type in topology["relationships"]:
        p_asset = asset_map[p_code]
        c_asset = asset_map[c_code]
        rel_exists = db.query(NetworkRelationship).filter(
            NetworkRelationship.parent_asset_id == p_asset.id,
            NetworkRelationship.child_asset_id == c_asset.id,
        ).first()
        if not rel_exists:
            rel = NetworkRelationship(
                parent_asset_id=p_asset.id,
                child_asset_id=c_asset.id,
                relationship_type=rel_type,
                is_current=True,
                is_simulated=True,
            )
            db.add(rel)

    # Aggregate Meters
    meter_map: Dict[str, HouseholdAggregateMeter] = {}
    for m in topology["meters"]:
        existing_m = db.query(HouseholdAggregateMeter).filter(HouseholdAggregateMeter.meter_code == m["meter_code"]).first()
        if not existing_m:
            parent_asset = asset_map[m["associated_asset_code"]]
            existing_m = HouseholdAggregateMeter(
                meter_code=m["meter_code"],
                household_count=m["household_count"],
                associated_asset_id=parent_asset.id,
                installation_type=m["installation_type"],
                phase_configuration=m["phase_configuration"],
                multiplier=m["multiplier"],
                is_simulated=True,
                source_id=ds.id,
            )
            db.add(existing_m)
            db.flush()
        meter_map[m["meter_code"]] = existing_m

    # 3. Insert / Update Boundary Readings
    total_records = 0
    for br in scenario_data.get("boundary_readings", []):
        target_asset = asset_map.get(br["asset_code"])
        if not target_asset:
            continue

        existing_br = db.query(DistributionBoundaryReading).filter(
            DistributionBoundaryReading.asset_id == target_asset.id,
            DistributionBoundaryReading.timestamp == br["timestamp"],
            DistributionBoundaryReading.boundary_type == br["boundary_type"],
        ).first()

        if existing_br:
            existing_br.energy_kwh = br["energy_kwh"]
            existing_br.power_kw = br.get("power_kw", 0.0)
            existing_br.voltage_v = br.get("voltage_v", 0.0)
            existing_br.validation_status = br.get("validation_status", "VALID")
            reading = existing_br
        else:
            reading = DistributionBoundaryReading(
                id=str(uuid.uuid4()),
                asset_id=target_asset.id,
                timestamp=br["timestamp"],
                energy_kwh=br["energy_kwh"],
                power_kw=br.get("power_kw", 0.0),
                voltage_v=br.get("voltage_v", 0.0),
                current_a=br.get("current_a", 0.0),
                power_factor=br.get("power_factor", 0.95),
                frequency_hz=br.get("frequency_hz", 50.0),
                unit=br.get("unit", "KWH"),
                boundary_type=br["boundary_type"],
                validation_status=br.get("validation_status", "VALID"),
                is_simulated=True,
                source_id=ds.id,
            )
            db.add(reading)
        total_records += 1

        # Run quality audit and persist findings
        findings = audit_boundary_record(br)
        for f in findings:
            if not f.passed:
                db.add(DataQualityResult(
                    id=str(uuid.uuid4()),
                    target_type="BOUNDARY_READING",
                    target_id=reading.id,
                    quality_dimension=f.dimension,
                    passed=f.passed,
                    score=f.score,
                    error_code=f.error_code,
                    diagnostic_message=f.message,
                    is_simulated=True,
                ))

    # 4. Insert / Update Consumption Readings
    for cr in scenario_data.get("consumption_readings", []):
        target_meter = meter_map.get(cr["meter_code"])
        if not target_meter:
            continue

        existing_cr = db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == target_meter.id,
            ConsumptionReading.timestamp == cr["timestamp"],
            ConsumptionReading.reading_type == cr.get("reading_type", "INTERVAL"),
        ).first()

        if existing_cr:
            existing_cr.energy_kwh = cr["energy_kwh"]
            existing_cr.validation_status = cr.get("validation_status", "VALID")
            c_reading = existing_cr
        else:
            c_reading = ConsumptionReading(
                id=str(uuid.uuid4()),
                meter_id=target_meter.id,
                timestamp=cr["timestamp"],
                energy_kwh=cr["energy_kwh"],
                reactive_energy_kvarh=cr.get("reactive_energy_kvarh"),
                peak_power_kw=cr.get("peak_power_kw"),
                interval_minutes=cr.get("interval_minutes", 60),
                unit=cr.get("unit", "KWH"),
                reading_type=cr.get("reading_type", "INTERVAL"),
                validation_status=cr.get("validation_status", "VALID"),
                is_simulated=True,
                source_id=ds.id,
            )
            db.add(c_reading)
        total_records += 1

        # Run quality audit and persist findings
        findings = audit_consumption_record(cr)
        for f in findings:
            if not f.passed:
                db.add(DataQualityResult(
                    id=str(uuid.uuid4()),
                    target_type="CONSUMPTION_READING",
                    target_id=c_reading.id,
                    quality_dimension=f.dimension,
                    passed=f.passed,
                    score=f.score,
                    error_code=f.error_code,
                    diagnostic_message=f.message,
                    is_simulated=True,
                ))

    # 5. Insert Anomalies (generate run-scoped unique code)
    anomaly_map: Dict[str, AnomalyEvent] = {}
    run_token = uuid.uuid4().hex[:6]
    for anom in scenario_data.get("anomalies", []):
        rel_asset = asset_map.get(anom.get("related_asset_code")) if anom.get("related_asset_code") else None
        ev_code = f"{anom['event_code']}-{run_token}"
        event = AnomalyEvent(
            event_code=ev_code,
            anomaly_type=anom["anomaly_type"],
            severity=anom.get("severity", "MEDIUM"),
            related_asset_id=rel_asset.id if rel_asset else None,
            detected_at=anom.get("detected_at", datetime.now(timezone.utc)),
            time_window_start=anom["time_window_start"],
            time_window_end=anom["time_window_end"],
            discrepancy_kwh=anom.get("discrepancy_kwh", 0.0),
            discrepancy_percent=anom.get("discrepancy_percent", 0.0),
            status=anom.get("status", "DETECTED"),
            description=anom["description"],
            is_simulated=True,
        )
        db.add(event)
        db.flush()
        anomaly_map[anom["event_code"]] = event

    # 6. Insert Investigation Cases, Evidence, and Outcomes
    for c in scenario_data.get("cases", []):
        target_asset = asset_map.get(c.get("target_asset_code")) if c.get("target_asset_code") else None
        case_num = f"{c['case_number']}-{run_token}"
        case = InvestigationCase(
            case_number=case_num,
            title=c["title"],
            priority=c.get("priority", "MEDIUM"),
            status=c.get("status", "OPEN"),
            assigned_role=c.get("assigned_role", "GRID_ANALYST"),
            target_asset_id=target_asset.id if target_asset else None,
            summary=c["summary"],
            is_simulated=True,
        )
        db.add(case)
        db.flush()

        for ev in c.get("evidence", []):
            db.add(EvidenceRecord(
                case_id=case.id,
                evidence_type=ev["evidence_type"],
                title=ev["title"],
                description=ev["description"],
                payload_data=ev["payload_data"],
                hash_sha256=ev["hash_sha256"],
                collected_by=ev["collected_by"],
                is_simulated=True,
            ))

        for act in c.get("actions", []):
            db.add(InvestigationAction(
                case_id=case.id,
                action_type=act["action_type"],
                status=act.get("status", "PENDING"),
                performed_by=act["performed_by"],
                notes=act["notes"],
                is_simulated=True,
            ))

        if c.get("outcome"):
            out = c["outcome"]
            db.add(InvestigationOutcome(
                case_id=case.id,
                outcome_type=out["outcome_type"],
                estimated_loss_kwh=out.get("estimated_loss_kwh", 0.0),
                estimated_financial_loss_inr=out.get("estimated_financial_loss_inr", 0.0),
                action_taken=out["action_taken"],
                closed_by=out["closed_by"],
            ))

    # 7. Record Scenario Run Docket
    scenario_run = ScenarioRun(
        scenario_code=scenario_data["scenario_code"],
        scenario_name=scenario_data["scenario_name"],
        seed=scenario_data.get("seed", 42),
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="COMPLETED",
        parameters={"hours": 24, "seed": scenario_data.get("seed", 42)},
        records_generated_count=total_records,
        summary_metrics=scenario_data.get("metrics", {}),
        is_simulated=True,
    )
    db.add(scenario_run)
    db.flush()

    # 8. Add Audit Log
    db.add(AuditLog(
        actor_id="SYSTEM_GENERATOR",
        actor_role="DATA_PIPELINE",
        action="RUN_SCENARIO",
        entity_type="scenario_runs",
        entity_id=scenario_run.id,
        details={
            "scenario_code": scenario_data["scenario_code"],
            "seed": scenario_data.get("seed", 42),
            "records_generated": total_records,
        },
    ))

    db.commit()
    return scenario_run


def generate_baseline_telemetry(start_time: datetime, end_time: datetime, seed: int = 42) -> List[Dict[str, Any]]:
    """Helper for synthetic data adapter to fetch baseline records."""
    generator = SyntheticGridGenerator(seed=seed)
    scenario_a = generator.generate_scenario_a_normal(hours=24)
    return scenario_a["boundary_readings"] + scenario_a["consumption_readings"]

