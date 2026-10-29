"""
Schemas for health diagnostics, platform information, and validation contracts.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SubsystemHealth(BaseModel):
    name: str = Field(..., description="Subsystem name")
    status: str = Field(..., description="Status: 'operational', 'standby', 'degraded', or 'disconnected'")
    details: Optional[str] = Field(default=None, description="Diagnostic notes")
    ready: bool = Field(..., description="Readiness flag for request routing")


class HealthStatusData(BaseModel):
    status: str = Field(default="healthy", description="Overall platform status")
    project: str = Field(default="GRIDGUARD NEXUS X", description="Platform identifier")
    version: str = Field(default="2.0.0-level2", description="Release version")
    stage: str = Field(default="LEVEL 2: DATA FOUNDATION", description="Active project milestone")
    environment: str = Field(default="development", description="Runtime environment")
    uptime_seconds: float = Field(..., description="Seconds since process startup")
    database: SubsystemHealth = Field(..., description="Persistent storage status")
    subsystems: List[SubsystemHealth] = Field(default_factory=list, description="Registered domain modules")


class VersionInfoData(BaseModel):
    project_name: str = Field(..., description="Formal project name")
    version: str = Field(..., description="Semantic version string")
    stage: str = Field(..., description="Current milestone level")
    api_prefix: str = Field(..., description="API prefix path")
    supported_protocols: List[str] = Field(
        default=["HTTP/1.1", "JSON REST"],
        description="Supported wire transport protocols"
    )
    capabilities: Dict[str, str] = Field(
        default={
            "foundation": "Active (Level 1)",
            "energy_accounting": "Reserved (Level 2)",
            "telemetry_stream": "Reserved (Level 2)",
            "ai_investigation": "Reserved (Level 3)"
        },
        description="Declared capabilities"
    )


class ValidationProbeRequest(BaseModel):
    """
    Sample telemetry envelope request to demonstrate strict Pydantic input validation.
    """
    station_id: str = Field(
        ...,
        min_length=3,
        max_length=32,
        pattern=r"^[A-Z0-9_\-]+$",
        description="Alphanumeric station/feeder identifier (uppercase, digits, hyphen, underscore)"
    )
    grid_frequency_hz: float = Field(
        ...,
        ge=45.0,
        le=65.0,
        description="Nominal electrical frequency in Hz (e.g. 50.0 for 50Hz grid or 60.0 for 60Hz grid)"
    )
    voltage_rms: float = Field(
        ...,
        ge=0.0,
        le=500000.0,
        description="RMS Voltage in Volts (e.g. 230.0 for LV, 11000.0 for 11kV distribution)"
    )
    feeder_count: int = Field(
        ...,
        ge=1,
        le=128,
        description="Number of monitored distribution feeder circuits"
    )


class ValidationProbeResponse(BaseModel):
    valid: bool = Field(default=True, description="Indicates whether payload passed all validation rules")
    received_station: str = Field(..., description="Normalized station ID")
    nominal_band: str = Field(..., description="Frequency band categorization (e.g. 50Hz Grid / 60Hz Grid)")
    voltage_class: str = Field(..., description="Voltage tier: LV, MV, or EHV")
