from dataclasses import dataclass
from datetime import datetime


@dataclass
class Evidence:
    source: str
    signal: str
    value: str
    observed_at: datetime
    description: str