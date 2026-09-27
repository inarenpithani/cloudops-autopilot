from datetime import datetime
from typing import Any

from cloudops_engine.events.models import CloudEvent


def adapt_eventbridge_event(event: dict[str, Any]) -> CloudEvent:
    """Convert an AWS EventBridge event into a CloudEvent."""

    return CloudEvent(
        event_id=event["id"],
        event_type=event["detail-type"],
        source=event["source"],
        timestamp=datetime.fromisoformat(
            event["time"].replace("Z", "+00:00")
        ),
        payload=event.get("detail", {}),
    )