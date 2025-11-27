import streamlit as st
from pathlib import Path
import pandas as pd

import requests
from bs4 import BeautifulSoup
from transformers import pipeline

from questions import QUESTIONS, LIKERT_OPTIONS, YESNO_OPTIONS
from scoring import compute_scores, generate_recommendations, get_category_weights
from pdf_report import build_pdf_report

CAT_LIST = [
    "Governance & Policy",
    "Data Privacy & Protection",
    "Technical Controls & Monitoring",
    "Ethics & Societal Impact",
    "Organisational Readiness & Capability",
]

# ---------- Page config ----------
st.set_page_config(
    page_title="Responsible AI Governance Readiness Assessment",
    page_icon="✅",
    layout="wide",
)


# ---------- Email / contacts storage ----------
def store_contact(org_name: str, email: str, country: str, industry: str):
    """
    Append contact details to a local CSV file (docs/contacts.csv).
    In a production deployment, this would be replaced with a secure database.
    """
    if not email:
        return  # don't store empty emails

    data = {
        "org_name": [org_name or ""],
        "email": [email],
        "country": [country or ""],
        "industry": [industry or ""],
        "source": ["raigra_mvp"],
    }

    contacts_path = Path("docs") / "contacts.csv"
    df_new = pd.DataFrame(data)

    if contacts_path.exists():
        df_existing = pd.read_csv(contacts_path)
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(contacts_path, index=False)

def store_assessment(
    org_name: str,
    org_type: str,
    industry: str,
    country: str,
    email: str,
    overall_score: float,
    band_label: str,
    category_scores: dict,
):
    """
    Append a single assessment record to docs/assessments.csv for historical tracking.
    """
    from datetime import datetime

    assessments_path = Path("docs") / "assessments.csv"
    assessments_path.parent.mkdir(exist_ok=True, parents=True)

    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "org_name": org_name or "",
        "org_type": org_type or "",
        "industry": industry or "",
        "country": country or "",
        "email": email or "",
        "overall_score": overall_score,
        "band": band_label,
    }

    # Flatten per-category scores
    for cat, score in category_scores.items():
        col_name = f"cat_{cat.replace(' ', '_').lower()}"
        row[col_name] = score

    df_new = pd.DataFrame([row])

    if assessments_path.exists():
        df_existing = pd.read_csv(assessments_path)
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(assessments_path, index=False)

def analyse_text_signals(text: str) -> dict:
    """
    Very simple rule-based NLP to extract strengths and potential gaps
    from free text describing AI use / governance (and optional website summary).
    """
    text_l = text.lower()

    CAT_LIST = {
        "Governance & accountability": [
            "governance",
            "board",
            "oversight",
            "committee",
            "risk",
            "policy",
            "framework",
        ],
        "Data protection & privacy": [
            "gdpr",
            "data protection",
            "dpo",
            "privacy",
            "dpi",
            "dpia",
            "consent",
            "data minimisation",
            "retention",
        ],
        "Technical controls & monitoring": [
            "monitoring",
            "drift",
            "versioning",
            "mlflow",
            "alert",
            "testing",
            "logging",
            "audit log",
        ],
        "Ethics & societal impact": [
            "ethics",
            "ethical",
            "fairness",
            "bias",
            "inclusion",
            "impact assessment",
            "human rights",
        ],
        "Organisational readiness & skills": [
            "training",
            "capability",
            "upskilling",
            "roles",
            "accountabilities",
            "centre of excellence",
            "playbook",
        ],
    }

    strengths = []
    gaps = []
    present = {}

    for cat, keywords in CAT_LIST.items():
        hits = [kw for kw in keywords if kw in text_l]
        present[cat] = len(hits) > 0
        if hits:
            strengths.append(f"Mentions {cat.lower()} (e.g. {', '.join(hits[:3])}).")

    for cat, has_signal in present.items():
        if not has_signal:
            gaps.append(
                f"No explicit mention of {cat.lower()} – consider documenting how this is handled."
            )

    red_flag_phrases = [
        "no policy",
        "not compliant",
        "no governance",
        "no oversight",
        "no consent",
    ]
    red_hits = [p for p in red_flag_phrases if p in text_l]
    for phrase in red_hits:
        gaps.append(
            f"Potential red flag phrase detected: '{phrase}' – this area may need urgent review."
        )

    return {"strengths": strengths, "gaps": gaps} 
# ---------- NLP: website scraping + summarisation ----------

@st.cache_resource
def get_summariser():
    """
    Load a summarisation pipeline once and reuse it.
    """
    return pipeline(
        "summarization",
        model="facebook/bart-large-cnn",
        tokenizer="facebook/bart-large-cnn",
    )


from urllib.parse import urlparse, urljoin  # make sure this is at the top of app.py with your imports


def scrape_and_summarise(url: str) -> str:
    """
    Fetch key governance / privacy / AI-related pages for a site (where available),
    extract the most relevant paragraph text, and return a short summary.

    If we can't confidently extract anything useful, we fall back to a generic
    governance / AI readiness overview instead of returning nothing.
    """
    try:
        if not url:
            return (
                "No website URL was provided. This summary focuses on general AI governance "
                "considerations rather than organisation-specific policies."
            )

        # Normalise URL
        if not url.startswith("http"):
            url = "https://" + url.strip("/")

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return (
                "The URL provided does not appear to be valid. "
                "This summary focuses on general AI governance considerations."
            )

        base = f"{parsed.scheme}://{parsed.netloc}"

        # Pages that are likely to contain governance / privacy / AI content
        candidate_paths = [
            "",  # homepage
            "/privacy",
            "/privacy-policy",
            "/data",
            "/data-protection",
            "/governance",
            "/corporate-governance",
            "/responsible-ai",
            "/ai",
            "/ai-ethics",
            "/ethics",
            "/responsibility",
            "/trust",
            "/legal",
            "/terms",
        ]

        governance_keywords = [
            "governance",
            "board",
            "oversight",
            "risk",
            "audit",
            "compliance",
            "regulator",
            "policy",
            "framework",
            "ethics",
            "responsible",
            "ai",
            "artificial intelligence",
            "data protection",
            "privacy",
            "gdpr",
            "dpo",
            "impact assessment",
            "dpi",
            "dpia",
        ]

        relevant_paragraphs = []
        all_paragraphs = []

        for path in candidate_paths:
            full_url = urljoin(base, path)
            try:
                resp = requests.get(full_url, timeout=8)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                paragraphs = [p.get_text(separator=" ").strip() for p in soup.find_all("p")]

                for p_text in paragraphs:
                    if not p_text:
                        continue
                    all_paragraphs.append(p_text)
                    lower = p_text.lower()
                    if any(kw in lower for kw in governance_keywords):
                        relevant_paragraphs.append(p_text)
            except Exception:
                # If any individual page fails, just skip it and move on
                continue

        # Decide what text to summarise
        if relevant_paragraphs:
            # Best case: we found paragraphs that explicitly mention governance / AI / privacy
            combined_text = " ".join(relevant_paragraphs)
            source_note = (
                "Summary based on governance, privacy, and AI-related sections found on the website "
                "(e.g. privacy, data protection, governance, or ethics pages)."
            )
        elif len(" ".join(all_paragraphs)) > 600:
            # Second best: we didn't find explicit keywords, but the site has enough text to summarise
            combined_text = " ".join(all_paragraphs)
            source_note = (
                "Summary based on general website content; explicit governance or AI policy language "
                "could not be confidently identified."
            )
        else:
            # Fallback: barely any content, or nothing useful detected
            return (
                "We were unable to extract detailed governance or AI policy information from the website. "
                "However, organisations considering AI deployment typically need to:\n\n"
                "- Define clear governance structures and accountable owners for AI systems.\n"
                "- Document data protection measures (e.g. legal basis, DPIAs, retention and minimisation).\n"
                "- Monitor AI models for performance, drift, misuse, and unintended consequences.\n"
                "- Consider ethics and societal impact, especially for high-risk use cases.\n"
                "- Build organisational capability through training, playbooks, and clear roles.\n\n"
                "You can use the rest of this report to prioritise which of these areas to formalise next."
            )

        # Truncate to a safe length for the summariser
        if len(combined_text) > 8000:
            combined_text = combined_text[:8000]

        summariser = get_summariser()
        summary = summariser(
            combined_text,
            max_length=240,
            min_length=90,
            do_sample=False,
        )
        return summary[0]["summary_text"] + "\n\n" + source_note

    except Exception:
        # Absolute fallback: website unreachable or summariser failed
        return (
            "We were unable to reliably access or summarise the organisation's website. "
            "This assessment therefore focuses on your questionnaire responses. "
            "As a next step, consider publishing a clear AI governance and data protection statement "
            "that explains how you manage risk, oversight, and accountability."
        )


# ---------- Main app ----------

def main():
    # SIDEBAR
    with st.sidebar:
        st.markdown("### About this tool")
        st.write(
            "This tool provides a structured, board-level view of how prepared your organisation is "
            "to design, deploy, and oversee AI responsibly."
        )
        st.markdown("**What you get**")
        st.write(
            "- A readiness score (0–100) and risk band for AI governance.\n"
            "- A breakdown across governance, privacy, technical controls, ethics, and capability.\n"
            "- A concise action list you can use with senior leaders or programme owners."
        )
        st.markdown("---")
        st.caption(
            "Developed as part of a responsible AI governance toolkit. Results are indicative and "
            "designed to support internal discussion, not to replace legal or regulatory advice."
        )
    # MAIN HEADER
    st.markdown("## AI Governance Readiness Assessment")

    st.markdown(
        """
    Use this assessment to get a **clear, structured view** of how ready your organisation is to use AI in a safe,
    compliant and accountable way.

    In around 5–7 minutes you will:
    - receive an overall AI readiness score (0–100) and risk band,
    - see strengths and gaps across five governance domains, and
    - generate a PDF report you can use in board packs, steering groups, or programme reviews.
        """
    )

    st.info(
        "Use the outputs to prioritise actions, brief senior stakeholders, and track progress over time "
        "as you strengthen AI governance and data protection practices."
    )

    st.caption(
        "This is an indicative self-assessment, not legal or regulatory advice. It is intended to support internal "
        "discussion, planning and challenge."
    )

    st.markdown("---")

    # ORG PROFILE SECTION
    st.markdown("### Organisation profile")

    col1, col2 = st.columns(2)
    with col1:
        org_name = st.text_input(
            "Organisation name",
            placeholder="e.g. Acme Health, City of X, NGO Y",
        )
        org_type = st.selectbox(
            "Organisation type",
            options=[
                "Private company",
                "Public sector body",
                "Non-profit / NGO",
                "Startup / scaleup",
                "Educational institution",
                "Other / not specified",
            ],
            index=3,
        )
    with col2:
        industry = st.selectbox(
            "Primary sector",
            options=[
                "Healthcare",
                "Financial services",
                "Public administration",
                "Education",
                "Retail / e-commerce",
                "Technology",
                "Media / culture",
                "Other / mixed",
            ],
        )
        country = st.text_input(
            "Country / region",
            placeholder="e.g. United Kingdom, EU, Global",
        )
        email = st.text_input(
            "Contact email for updates",
            placeholder="e.g. governance@organisation.org",
        )
        st.caption(
            "Email is used to register interest in future versions of this tool. No emails are sent from this demo."
        )

    organisation_url = st.text_input(
        "Organisation website URL",
        placeholder="e.g. https://www.example.org",
    )

    context_text = st.text_area(
        "Describe your current use of AI or data-driven systems",
        placeholder="e.g. We use AI for triaging support tickets and fraud detection across EU markets...",
        help="This contextual description can be used in future iterations to generate richer, tailored recommendations.",
    )

    st.markdown("### Assessment")

    responses = {}

    # QUESTIONS
    for cat in CAT_LIST:
        with st.expander(cat, expanded=True):
            for q in [q for q in QUESTIONS if q.category == cat]:
                if q.qtype == "likert":
                    label = st.select_slider(
                        q.text,
                        options=list(LIKERT_OPTIONS.keys()),
                        value="Developing",
                    )
                    responses[q.id] = LIKERT_OPTIONS[label]
                elif q.qtype == "yesno":
                    label = st.radio(
                        q.text,
                        options=list(YESNO_OPTIONS.keys()),
                        horizontal=True,
                    )
                    responses[q.id] = YESNO_OPTIONS[label]

    st.markdown("---")

    # BUTTON + RESULTS
    if st.button("Generate readiness score and summary", type="primary"):

        # Validation of mandatory fields
        missing_fields = []
        if not org_name:
            missing_fields.append("Organisation name")
        if not org_type:
            missing_fields.append("Organisation type")
        if not industry:
            missing_fields.append("Industry")
        if not country:
            missing_fields.append("Country / region")
        if not email:
            missing_fields.append("Contact email")
        if not context_text:
            missing_fields.append("AI context description")

        if missing_fields:
            st.error(
                "Please complete all fields before generating results.\n\nMissing: "
                + ", ".join(missing_fields)
            )
            return

        # Compute scores with org-specific weighting
        overall, category_scores, band_info = compute_scores(
            responses,
            org_type=org_type,
            industry=industry,
        )
        recs = generate_recommendations(category_scores)
        band_label, band_desc = band_info

        # Persist this assessment for historical tracking
        store_assessment(
            org_name=org_name,
            org_type=org_type,
            industry=industry,
            country=country,
            email=email,
            overall_score=overall,
            band_label=band_label,
            category_scores=category_scores,
        )
        # Governance summary from website
        governance_summary = None
        if organisation_url:
            with st.spinner("Analysing organisation website for governance context..."):
                governance_summary = scrape_and_summarise(organisation_url)
            st.markdown("### Governance and policy signals from website")
            st.write(governance_summary)
            st.markdown("---")

        # NLP insights from AI context + (optional) website summary
        analysis_source = context_text
        if governance_summary:
            analysis_source += "\n\n" + governance_summary

        text_insights = analyse_text_signals(analysis_source)

        # Save contacts locally
        store_contact(org_name, email, country, industry)

        # Results header
        st.markdown("## Results overview")

        # Weighting explanation
        from scoring import get_category_weights
        weights = get_category_weights(org_type, industry)
        top_two = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:2]
        st.caption(
            f"Based on your organisation type and industry, the scoring places most weight on "
            f"{top_two[0][0]} and {top_two[1][0]}."
        )

        # Profile
        st.markdown("#### Organisation profile (for interpretation)")
        st.write(
            f"**Type:** {org_type}  \n"
            f"**Sector:** {industry}  \n"
            f"**Country / region:** {country or 'Not specified'}"
        )
        st.write("**AI context (as described):**")
        st.write(context_text)

        # Metrics
        mcol1, mcol2, mcol3 = st.columns(3)
        with mcol1:
            st.metric("Overall readiness score", f"{overall:.1f}/100")
        with mcol2:
            st.metric("Readiness band", band_label)
        with mcol3:
            weakest_cat = min(category_scores, key=category_scores.get)
            st.metric("Weakest area", weakest_cat)

        st.caption(band_desc)

        # Category scores
        st.markdown("### Category scores")
        for cat in CAT_LIST:
            st.progress(min(int(category_scores.get(cat, 0)), 100))
            st.write(f"**{cat}**: {category_scores.get(cat, 0):.1f}/100")

        # Recommendations
        st.markdown("### High-level recommendations")
        for cat, text in recs.items():
            st.write(f"**{cat}** — {text}")

        # Text-based AI governance insights
        st.markdown("### Text-based governance signals")

        strengths = text_insights.get("strengths", [])
        gaps = text_insights.get("gaps", [])

        if strengths:
            st.markdown("**Detected strengths (from your description and website):**")
            for s in strengths:
                st.write(f"- {s}")

        if gaps:
            st.markdown("**Potential gaps or blind spots:**")
            for g in gaps:
                st.write(f"- {g}")

        # PDF report
        pdf_buffer = build_pdf_report(
            org_name=org_name,
            org_type=org_type,
            industry=industry,
            country=country,
            email=email,
            context_text=context_text,
            overall_score=overall,
            band_label=band_label,
            band_desc=band_desc,
            category_scores=category_scores,
            recommendations=recs,
            governance_summary=governance_summary,
            text_insights=text_insights,  
        )

        st.download_button(
            "Download PDF report",
            data=pdf_buffer,
            file_name="ai_readiness_report.pdf",
            mime="application/pdf",
        )

         # Historical tracking – show previous assessments for this org/email
        assessments_path = Path("docs") / "assessments.csv"
        if assessments_path.exists():
            df_all = pd.read_csv(assessments_path)

            # Prefer to filter by email (more unique), fall back to org_name
            if email:
                df_org = df_all[df_all["email"] == email]
            elif org_name:
                df_org = df_all[df_all["org_name"] == org_name]
            else:
                df_org = df_all.copy()

            if len(df_org) > 0:
                st.markdown("### Previous assessments for this organisation")

                # Sort by timestamp
                df_org = df_org.sort_values("timestamp")

                # Change since last assessment (overall score)
                if len(df_org) >= 2:
                    last_two = df_org.tail(2)
                    prev_score = last_two["overall_score"].iloc[0]
                    latest_score = last_two["overall_score"].iloc[1]
                    delta = latest_score - prev_score

                    st.markdown("#### Change since last assessment")
                    st.metric(
                        label="Overall readiness change",
                        value=f"{latest_score:.1f}/100",
                        delta=f"{delta:+.1f} points",
                    )
                    st.caption(
                        f"Overall readiness changed by {delta:+.1f} points between the last two assessments "
                        f"({prev_score:.1f} → {latest_score:.1f} on a 0–100 scale)."
                    )
                st.dataframe(
                    df_org[
                        [
                            "timestamp",
                            "overall_score",
                            "band",
                            "org_type",
                            "industry",
                        ]
                    ],
                    use_container_width=True,
                )

                # Trend chart for overall score
                if len(df_org) > 1:
                    df_trend = df_org.copy()
                    df_trend["timestamp"] = pd.to_datetime(df_trend["timestamp"])
                    df_trend = df_trend.set_index("timestamp")

                    st.markdown("#### Overall readiness trend")
                    st.line_chart(
                        df_trend["overall_score"],
                        use_container_width=True,
                    )

                    # Per-category trend (choose a category to inspect)
                    st.markdown("#### Category trend (select area to inspect)")
                    selected_cat = st.selectbox(
                        "Category",
                        options=CAT_LIST,
                        key="trend_category_select",
                    )

                    cat_col = "cat_" + selected_cat.replace(" ", "_").lower()

                    if cat_col in df_trend.columns:
                        st.line_chart(
                            df_trend[cat_col],
                            use_container_width=True,
                        )
                    else:
                        st.info(
                            "No historical data stored yet for this category column. "
                            "Run a few more assessments to populate the trend."
                        )
if __name__ == "__main__":
    main()
