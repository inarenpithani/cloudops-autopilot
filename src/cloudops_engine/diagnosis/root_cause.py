from cloudops_engine.models.diagnosis import DiagnosisResult
from cloudops_engine.models.evidence import Evidence
from cloudops_engine.models.incident import Incident


def diagnose_incident(
    incident: Incident,
    evidence: list[Evidence],
) -> DiagnosisResult:
    if incident.incident_type == "HIGH_CPU":
        cpu_evidence = [
            evidence_item
            for evidence_item in evidence
            if evidence_item.signal == "CPUUtilization"
        ]

        cpu_values = [
            evidence_item.value
            for evidence_item in cpu_evidence
        ]

        numeric_cpu_values = [
            float(value.rstrip("%"))
            for value in cpu_values
        ]

        evidence_count = len(numeric_cpu_values)

        if evidence_count == 0:
            return DiagnosisResult(
                probable_cause="Unknown",
                confidence=0.0,
                evidence=[],
                explanation=(
                    "Insufficient evidence to determine the probable cause "
                    "of the high CPU incident."
                ),
            )

        average_cpu = sum(numeric_cpu_values) / evidence_count

        if average_cpu >= 95.0:
            signal_strength = "Very strong"
        elif average_cpu >= 90.0:
            signal_strength = "Strong"
        else:
            signal_strength = "Moderate"

        if evidence_count >= 3:
            base_confidence = 0.85
        elif evidence_count == 2:
            base_confidence = 0.70
        else:
            base_confidence = 0.50

        if average_cpu >= 95.0:
            confidence = min(base_confidence + 0.05, 1.0)
        elif average_cpu < 90.0:
            confidence = max(base_confidence - 0.10, 0.0)
        else:
            confidence = base_confidence

        return DiagnosisResult(
            probable_cause=(
                "Sustained high CPU utilization on the affected "
                "compute instance."
            ),
            confidence=confidence,
            evidence=cpu_values,
            explanation=(
                "The diagnosis is based on persistent CPU utilization "
                "above the configured threshold, supported by "
                f"{evidence_count} CloudWatch CPU evidence datapoint(s). "
                f"Signal strength: {signal_strength}."
            ),
        )

    return DiagnosisResult(
        probable_cause="Unknown",
        confidence=0.0,
        evidence=[],
        explanation="Insufficient evidence to determine the probable cause.",
    )