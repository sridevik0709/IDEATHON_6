"""
Synthetic Data Source Adapter.
Powers repeatable demonstration scenarios with deterministic seeds.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.data_processing.sources.base import BaseDataSourceAdapter


class SyntheticDataSourceAdapter(BaseDataSourceAdapter):
    """
    Adapter for generating clearly labeled simulated telemetry.
    Strictly flags all generated data with `is_simulated = True`.
    """

    def __init__(
        self,
        source_code: str = "SRC-SYNTHETIC-SIM-01",
        name: str = "Synthetic Grid Demonstration Engine",
        seed: int = 42
    ):
        super().__init__(
            source_code=source_code,
            name=name,
            source_type="SYNTHETIC",
            is_authorized=True  # Built-in synthetic demonstration engine is authorized by design
        )
        self.seed = seed
        self._operational = True

    def is_operational(self) -> bool:
        return self._operational

    def health_check(self) -> Dict[str, Any]:
        return {
            "source_code": self.source_code,
            "name": self.name,
            "status": "operational",
            "type": self.source_type,
            "is_authorized": self.is_authorized,
            "is_simulated": True,
            "message": "Deterministic synthetic generator operational with seed support",
        }

    def get_provenance_metadata(self) -> Dict[str, Any]:
        return {
            "source_code": self.source_code,
            "name": self.name,
            "source_type": self.source_type,
            "is_authorized": self.is_authorized,
            "is_simulated": True,
            "license": "Internal Synthetic Demo Engine",
            "generator_module": "app.data_processing.synthetic_generator",
            "default_seed": self.seed,
        }

    def fetch_readings(
        self,
        start_time: datetime,
        end_time: datetime,
        asset_codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        # Deferred import to prevent circular dependency
        from app.data_processing.synthetic_generator import generate_baseline_telemetry
        return generate_baseline_telemetry(start_time=start_time, end_time=end_time, seed=self.seed)

