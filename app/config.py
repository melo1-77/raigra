# app/config.py

CATEGORY_WEIGHTS = {
    "Governance & Policy": 0.30,
    "Data Privacy & Protection": 0.25,
    "Technical Controls & Monitoring": 0.20,
    "Ethics & Societal Impact": 0.15,
    "Organisational Readiness & Capability": 0.10,
}

READINESS_BANDS = [
    (80, 100, "AI Ready", "Strong governance and controls; low regulatory risk."),
    (60, 79, "Near Ready", "Solid foundation with some gaps to close."),
    (40, 59, "Emerging", "Foundational elements in place but significant weaknesses."),
    (0, 39, "High Risk", "Limited governance; urgent remediation required."),
]
