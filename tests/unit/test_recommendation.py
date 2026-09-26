from cloudops_engine.detection.detector import detect_high_cpu
from cloudops_engine.remediation.recommendation import recommend_action


def test_medium_risk_high_cpu_recommendation():
    incident = detect_high_cpu(
        [92, 94, 96],
        resource="i-05e3bbde2a13509f7",
    )

    recommendation = recommend_action(
        incident,
        "MEDIUM",
    )

    assert recommendation == (
        "Collect additional metrics and investigate "
        "the top CPU-consuming processes."
    )


def test_low_risk_high_cpu_recommendation():
    incident = detect_high_cpu(
        [92, 94, 96],
        resource="i-05e3bbde2a13509f7",
    )

    recommendation = recommend_action(
        incident,
        "LOW",
    )

    assert recommendation == (
        "Monitor CPU utilization and collect "
        "additional diagnostic data."
    )