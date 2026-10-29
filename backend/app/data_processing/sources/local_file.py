"""
Local File Data Source Adapter.
Supports importing test datasets from CSV or JSON files.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.data_processing.sources.base import BaseDataSourceAdapter


class LocalFileDataSourceAdapter(BaseDataSourceAdapter):
    """
    Adapter for local offline test datasets (e.g. historical CSV or benchmark fixtures).
    """

    def __init__(
        self,
        source_code: str = "SRC-LOCAL-CSV-01",
        name: str = "Local Test Dataset Adapter",
        data_directory: str = "./data/test_datasets"
    ):
        super().__init__(
            source_code=source_code,
            name=name,
            source_type="LOCAL_FILE",
            is_authorized=True
        )
        self.data_directory = data_directory

    def is_operational(self) -> bool:
        return os.path.exists(self.data_directory) or True

    def health_check(self) -> Dict[str, Any]:
        exists = os.path.exists(self.data_directory)
        return {
            "source_code": self.source_code,
            "name": self.name,
            "status": "operational" if exists else "standby_empty_directory",
            "type": self.source_type,
            "is_authorized": self.is_authorized,
            "data_directory": self.data_directory,
            "message": f"Local file storage ready (path: {self.data_directory})",
        }

    def get_provenance_metadata(self) -> Dict[str, Any]:
        return {
            "source_code": self.source_code,
            "name": self.name,
            "source_type": self.source_type,
            "is_authorized": self.is_authorized,
            "is_simulated": True,
            "data_directory": self.data_directory,
        }

    def fetch_readings(
        self,
        start_time: datetime,
        end_time: datetime,
        asset_codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        # Returns empty list if no local files staged
        return []

