from dataclasses import dataclass
from datetime import datetime


@dataclass
class Incident:
    incident_id: str
    incident_type: str
    severity: str
    resource: str
    detected_at: datetime
    status: str
    description: str