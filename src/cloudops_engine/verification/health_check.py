def verify_cpu_recovery(
    cpu_usage: float,
    threshold: float = 90.0,
) -> bool:
    return cpu_usage <= threshold