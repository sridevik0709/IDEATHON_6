"""
Architectural boundary guard for AI & Investigation module.
Level 1 explicitly reserves machine learning and neural anomaly detectors for subsequent milestones.
"""

from typing import Dict


class AIServicesModuleStatus:
    NAME: str = "AI Grid Intelligence & Forensic Auditor"
    LEVEL_TARGET: str = "Level 3"
    STATUS: str = "standby"
    DESCRIPTION: str = "Non-technical loss detection, tampering classification, automated case builder"

    @classmethod
    def get_status(cls) -> Dict[str, str]:
        return {
            "name": cls.NAME,
            "target": cls.LEVEL_TARGET,
            "status": cls.STATUS,
            "description": cls.DESCRIPTION,
        }
