from cloudops_engine.verification.health_check import verify_cpu_recovery


def test_cpu_recovery_success():
    assert verify_cpu_recovery(60) is True


def test_cpu_recovery_failure():
    assert verify_cpu_recovery(95) is False