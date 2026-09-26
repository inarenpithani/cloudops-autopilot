from cloudops_engine.detection.service_detector import (
    detect_unhealthy_service,
)


def test_unhealthy_service_creates_incident():
    incident = detect_unhealthy_service(
        health_statuses=[False, False, False],
        resource="orders-api",
    )

    assert incident is not None
    assert incident.incident_type == "SERVICE_UNHEALTHY"
    assert incident.severity == "HIGH"
    assert incident.resource == "orders-api"


def test_healthy_service_does_not_create_incident():
    incident = detect_unhealthy_service(
        health_statuses=[True, True, True],
        resource="orders-api",
    )

    assert incident is None


def test_non_consecutive_unhealthy_checks_do_not_create_incident():
    incident = detect_unhealthy_service(
        health_statuses=[False, True, False],
        resource="orders-api",
    )

    assert incident is None


def test_insufficient_health_checks_do_not_create_incident():
    incident = detect_unhealthy_service(
        health_statuses=[False, False],
        resource="orders-api",
    )

    assert incident is None