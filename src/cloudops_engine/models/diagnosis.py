from dataclasses import dataclass


@dataclass
class DiagnosisResult:
    probable_cause: str
    confidence: float
    evidence: list[str]
    explanation: str