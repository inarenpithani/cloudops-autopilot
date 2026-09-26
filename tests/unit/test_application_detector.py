from cloudops_engine.detection.application_detector import (
    detect_application_5xx,
)


def test_application_5xx_creates_incident():
    incident = detect_application_5xx(
        error_rates=[6.0, 8.0, 7.0],
        resource="orders-api",
    )

    assert incident is not None
    assert incident.incident_type == "APPLICATION_5XX"
    assert incident.severity == "HIGH"
    assert incident.resource == "orders-api"


def test_normal_5xx_rate_does_not_create_incident():
    incident = detect_application_5xx(
        error_rates=[1.0, 2.0, 3.0],
        resource="orders-api",
    )

    assert incident is None


def test_non_consecutive_5xx_breaches_do_not_create_incident():
    incident = detect_application_5xx(
        error_rates=[6.0, 2.0, 7.0],
        resource="orders-api",
    )

    assert incident is None


def test_insufficient_5xx_datapoints_do_not_create_incident():
    incident = detect_application_5xx(
        error_rates=[6.0, 7.0],
        resource="orders-api",
    )

    assert incident is None