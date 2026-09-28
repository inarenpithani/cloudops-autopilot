from cloudops_engine.events.models import CloudEvent


def handle_event(event: CloudEvent) -> str:
    """Handle an incoming CloudOps event."""

    if event.event_type in {"cloud_incident", "CloudOps Incident"}:
        return "cloud_incident"

    raise ValueError(f"Unsupported event type: {event.event_type}")