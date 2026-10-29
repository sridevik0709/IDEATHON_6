"""
Data Source Registry for GridGuard Nexus X.
Provides lookup, cataloging, and lifecycle management for all active adapters.
"""

from typing import Dict, List, Optional
from app.data_processing.sources.base import BaseDataSourceAdapter
from app.data_processing.sources.local_file import LocalFileDataSourceAdapter
from app.data_processing.sources.synthetic import SyntheticDataSourceAdapter
from app.data_processing.sources.utility import UtilityIntegrationAdapter


class DataSourceRegistry:
    _instance: Optional["DataSourceRegistry"] = None
    _adapters: Dict[str, BaseDataSourceAdapter] = {}

    def __init__(self):
        self._register_default_adapters()

    @classmethod
    def get_instance(cls) -> "DataSourceRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _register_default_adapters(self):
        synthetic = SyntheticDataSourceAdapter()
        local_file = LocalFileDataSourceAdapter()
        utility = UtilityIntegrationAdapter()

        self.register(synthetic)
        self.register(local_file)
        self.register(utility)

    def register(self, adapter: BaseDataSourceAdapter):
        self._adapters[adapter.source_code] = adapter

    def get_adapter(self, source_code: str) -> Optional[BaseDataSourceAdapter]:
        return self._adapters.get(source_code)

    def list_adapters(self) -> List[Dict[str, any]]:
        return [adapter.health_check() for adapter in self._adapters.values()]


registry = DataSourceRegistry.get_instance()

