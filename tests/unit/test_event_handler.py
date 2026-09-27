from datetime import datetime, timezone

import pytest

from cloudops_engine.events.handler import handle_event
from cloudops_engine.events.models import CloudEvent


def create_event(event_type: str) -> CloudEvent:
    """Create a deterministic CloudEvent for testing."""

    return CloudEvent(
        event_id="test-001",
        event_type=event_type,
        source="test",
        timestamp=datetime(
            2026,
            9,
            27,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        payload={},
    )


def test_cloud_incident_event_is_handled():
    event = create_event("cloud_incident")

    result = handle_event(event)

    assert result == "cloud_incident"


def test_unsupported_event_type_is_rejected():
    event = create_event("unknown_event")

    with pytest.raises(
        ValueError,
        match="Unsupported event type: unknown_event",
    ):
        handle_event(event)