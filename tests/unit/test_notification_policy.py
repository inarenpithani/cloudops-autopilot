from cloudops_engine.notifications.policy import should_notify


def test_detected_state_should_notify():
    assert should_notify("DETECTED") is True


def test_remediating_state_should_notify():
    assert should_notify("REMEDIATING") is True


def test_resolved_state_should_notify():
    assert should_notify("RESOLVED") is True


def test_non_notifiable_states_should_not_notify():
    assert should_notify("ACKNOWLEDGED") is False
    assert should_notify("INVESTIGATING") is False
    assert should_notify("VERIFYING") is False