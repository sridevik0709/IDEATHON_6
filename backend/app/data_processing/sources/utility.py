"""
Utility Enterprise Integration Adapter.
Represents future integration with DISCOM / utility SCADA, MDMS, and GIS APIs.
Strictly unoperational unless explicitly configured, credentialed, and network-verified.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from app.data_processing.sources.base import BaseDataSourceAdapter


class UtilityIntegrationAdapter(BaseDataSourceAdapter):
    """
    Adapter skeleton for authorized enterprise utility connectivity.
    Strictly reports unconfigured/unauthorized state until production contracts are bound.
    """

    def __init__(
        self,
        source_code: str = "SRC-UTILITY-SCADA-01",
        name: str = "Enterprise Utility SCADA Stream",
        api_endpoint: Optional[str] = None
    ):
        super().__init__(
            source_code=source_code,
            name=name,
            source_type="UTILITY_SCADA",
            is_authorized=False  # Strictly False by default per engineering restrictions
        )
        self.api_endpoint = api_endpoint

    def is_operational(self) -> bool:
        # Never claim operational status without active credentials and verified probe
        return False

    def health_check(self) -> Dict[str, Any]:
        return {
            "source_code": self.source_code,
            "name": self.name,
            "status": "UNCONFIGURED_PENDING_UTILITY_AUTHORIZATION",
            "type": self.source_type,
            "is_authorized": False,
            "is_operational": False,
            "message": "Real utility integration is not configured. Awaiting utility API authorization tokens.",
        }

    def get_provenance_metadata(self) -> Dict[str, Any]:
        return {
            "source_code": self.source_code,
            "name": self.name,
            "source_type": self.source_type,
            "is_authorized": False,
            "is_simulated": False,
            "status": "PENDING_AUTHORIZATION",
            "compliance_note": "Engineering restriction: Real utility integration disabled until production clearance.",
        }

    def fetch_readings(
        self,
        start_time: datetime,
        end_time: datetime,
        asset_codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        raise RuntimeError(
            f"Cannot fetch readings from {self.source_code}: Data source is unconfigured and unauthorized."
        )

