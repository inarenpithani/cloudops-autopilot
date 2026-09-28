NOTIFIABLE_STATES = {
    "DETECTED",
    "REMEDIATING",
    "RESOLVED",
}


def should_notify(state: str) -> bool:
    """Return whether an incident lifecycle state should trigger a notification."""

    return state in NOTIFIABLE_STATES