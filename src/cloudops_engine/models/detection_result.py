from dataclasses import dataclass

from cloudops_engine.models.evidence import Evidence
from cloudops_engine.models.incident import Incident


@dataclass
class DetectionResult:
    incident: Incident
    evidence: list[Evidence]