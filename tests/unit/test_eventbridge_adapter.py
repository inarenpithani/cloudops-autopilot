from datetime import datetime, timezone

from cloudops_engine.events.eventbridge_adapter import (
    adapt_eventbridge_event,
)


def create_eventbridge_event() -> dict:
    """Create a deterministic EventBridge event for testing."""

    return {
        "id": "test-001",
        "source": "cloudops.autopilot",
        "detail-type": "CloudOps Incident",
        "time": "2026-09-27T10:00:00Z",
        "detail": {
            "incident_id": "test-001",
            "severity": "HIGH",
        },
    }


def test_eventbridge_event_is_converted_to_cloud_event():
    event = create_eventbridge_event()

    result = adapt_eventbridge_event(event)

    assert result.event_id == "test-001"
    assert result.event_type == "CloudOps Incident"
    assert result.source == "cloudops.autopilot"
    assert result.timestamp == datetime(
        2026,
        9,
        27,
        10,
        0,
        tzinfo=timezone.utc,
    )
    assert result.payload == {
        "incident_id": "test-001",
        "severity": "HIGH",
    }