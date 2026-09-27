from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class CloudEvent:
    event_id: str
    event_type: str
    source: str
    timestamp: datetime
    payload: dict[str, Any]
