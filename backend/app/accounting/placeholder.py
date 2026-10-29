"""
Architectural boundary guard for Energy Accounting module.
Level 1 explicitly reserves accounting logic for subsequent milestones.
"""

from typing import Dict


class AccountingModuleStatus:
    NAME: str = "Energy Accounting Service"
    LEVEL_TARGET: str = "Level 2"
    STATUS: str = "standby"
    DESCRIPTION: str = "Feeder balancing, transmission loss reconciliation, and billing discrepancies"

    @classmethod
    def get_status(cls) -> Dict[str, str]:
        return {
            "name": cls.NAME,
            "target": cls.LEVEL_TARGET,
            "status": cls.STATUS,
            "description": cls.DESCRIPTION,
        }
