# app/questions.py

from dataclasses import dataclass
from typing import List

@dataclass
class Question:
    id: str
    text: str
    category: str
    qtype: str          # "likert" or "yesno"
    help_text: str = ""

CATEGORIES = [
    "Governance & Policy",
    "Data Privacy & Protection",
    "Technical Controls & Monitoring",
    "Ethics & Societal Impact",
    "Organisational Readiness & Capability",
]

LIKERT_OPTIONS = {
    "Not at all": 1,
    "Limited": 2,
    "Developing": 3,
    "Established": 4,
    "Best practice": 5,
}

YESNO_OPTIONS = {
    "No": 0,
    "Yes": 1,
}

QUESTIONS: List[Question] = [
    # Governance & Policy
    Question(
        id="gov_policy",
        category="Governance & Policy",
        qtype="yesno",
        text="Do you have a documented AI governance policy approved by senior leadership?",
    ),
    Question(
        id="gov_owner",
        category="Governance & Policy",
        qtype="yesno",
        text="Is there a named accountable owner for AI systems and their outcomes?",
    ),
    Question(
        id="gov_vendor",
        category="Governance & Policy",
        qtype="likert",
        text="To what extent are third-party AI vendors assessed for governance and risk?",
    ),

    # Data Privacy & Protection
    Question(
        id="dp_minimisation",
        category="Data Privacy & Protection",
        qtype="likert",
        text="To what extent is data minimisation applied to AI training and inference data?",
    ),
    Question(
        id="dp_dpia",
        category="Data Privacy & Protection",
        qtype="yesno",
        text="Are Data Protection Impact Assessments (DPIAs) conducted for AI use cases involving personal data?",
    ),

    # Technical Controls & Monitoring
    Question(
        id="tech_versioning",
        category="Technical Controls & Monitoring",
        qtype="likert",
        text="How mature is your model and dataset version control (e.g. registries, dataset tracking)?",
    ),
    Question(
        id="tech_monitoring",
        category="Technical Controls & Monitoring",
        qtype="likert",
        text="How systematically do you monitor AI systems in production for drift, failures, or misuse?",
    ),

    # Ethics & Societal Impact
    Question(
        id="eth_impact",
        category="Ethics & Societal Impact",
        qtype="likert",
        text="To what extent are ethical impact assessments integrated into AI project approval?",
    ),
    Question(
        id="eth_stakeholders",
        category="Ethics & Societal Impact",
        qtype="likert",
        text="How regularly are affected stakeholders consulted for high-impact AI systems?",
    ),

    # Organisational Readiness & Capability
    Question(
        id="org_training",
        category="Organisational Readiness & Capability",
        qtype="likert",
        text="How widely is responsible AI training provided to staff involved in AI development or procurement?",
    ),
    Question(
        id="org_roles",
        category="Organisational Readiness & Capability",
        qtype="yesno",
        text="Are roles and responsibilities clearly defined across the AI lifecycle (e.g. product owner, data steward)?",
    ),
]

