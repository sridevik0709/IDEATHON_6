"""
Common Data Source Interface for GridGuard Nexus X.
Provides an extensible abstraction for synthetic generators, local file batches,
and future utility enterprise adapters.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IngestBatchMetadata(BaseModel):
    batch_id: str = Field(..., description="Unique batch tracking identifier")
    source_code: str = Field(..., description="Source identifier")
    source_type: str = Field(..., description="SYNTHETIC, LOCAL_FILE, UTILITY_SCADA, UTILITY_MDMS")
    record_count: int = Field(..., description="Number of records contained in batch")
    is_simulated: bool = Field(default=True, description="Strict separation flag for synthetic vs real data")
    ingested_at: datetime = Field(..., description="Timestamp of ingestion")
    provenance_notes: str = Field(..., description="Lineage details")


class BaseDataSourceAdapter(ABC):
    """
    Abstract base class establishing the contract for all telemetry and asset data sources.
    """

    def __init__(self, source_code: str, name: str, source_type: str, is_authorized: bool = False):
        self.source_code = source_code
        self.name = name
        self.source_type = source_type
        self.is_authorized = is_authorized

    @abstractmethod
    def is_operational(self) -> bool:
        """Indicates whether adapter is currently reachable and accepting queries."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform diagnostic handshake with data source."""
        pass

    @abstractmethod
    def get_provenance_metadata(self) -> Dict[str, Any]:
        """Returns traceability and authorization metadata."""
        pass

    @abstractmethod
    def fetch_readings(
        self,
        start_time: datetime,
        end_time: datetime,
        asset_codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch time-series boundary or consumption records."""
        pass

