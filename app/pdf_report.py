from io import BytesIO
from typing import Dict, Optional

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

CAT_LIST = [
    "Governance & Policy",
    "Data Privacy & Protection",
    "Technical Controls & Monitoring",
    "Ethics & Societal Impact",
    "Organisational Readiness & Capability",
]

BAND_STYLES = {
    "High risk": {"colour": colors.red, "label": "High risk"},
    "Emerging": {"colour": colors.orange, "label": "Emerging"},
    "Near-ready": {"colour": colors.HexColor("#FFC107"), "label": "Near-ready"},
    "Ready": {"colour": colors.green, "label": "Ready"},
}

def build_pdf_report(
    org_name: str,
    org_type: str,
    industry: str,
    country: str,
    email: str,
    context_text: str,
    overall_score: float,
    band_label: str,
    band_desc: str,
    category_scores: Dict[str, float],
    recommendations: Dict[str, str],
    governance_summary: Optional[str] = None,
    text_insights: Optional[dict] = None,
    regulatory_note: Optional[str] = None,
) -> BytesIO:
    """
    Build a simple, consulting-style PDF report and return it as a BytesIO buffer.
    """

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    title = "AI Governance Readiness Report"
    org_line = org_name or "Unnamed organisation"

    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Paragraph(org_line, styles["Heading3"]))
    elements.append(Spacer(1, 12))

    # Summary / band with coloured badge
    summary_text = f"<b>Overall readiness score:</b> {overall_score:.1f}/100"

    elements.append(Paragraph(summary_text, styles["Normal"]))
    elements.append(Spacer(1, 6))

    band_style = BAND_STYLES.get(band_label, {"colour": colors.grey})
    band_colour = band_style["colour"]

    band_table = Table(
        [[f"Readiness band: {band_label}"]],
        hAlign="LEFT",
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), band_colour),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        ),
    )
    elements.append(band_table)
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(band_desc, styles["Italic"]))
    elements.append(Spacer(1, 12))

    # Organisation profile
    elements.append(Paragraph("Organisation profile", styles["Heading2"]))
    profile_lines = [
        f"<b>Type:</b> {org_type}",
        f"<b>Sector:</b> {industry}",
        f"<b>Country / region:</b> {country or 'Not specified'}",
        f"<b>Contact email:</b> {email or 'Not provided'}",
    ]
    for line in profile_lines:
        elements.append(Paragraph(line, styles["Normal"]))
    if context_text:
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("<b>AI context (self-described):</b>", styles["Normal"]))
        elements.append(Paragraph(context_text, styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Regulatory context
    if regulatory_note:
        elements.append(Paragraph("Regulatory context (high level)", styles["Heading2"]))
        elements.append(Paragraph(regulatory_note, styles["Normal"]))
        elements.append(Spacer(1, 12))

    # Governance summary
    if governance_summary:
        elements.append(Paragraph("Governance summary from organisation website", styles["Heading2"]))
        elements.append(Paragraph(governance_summary, styles["Normal"]))
        elements.append(Spacer(1, 12))

    # Text-based governance insights
    if text_insights:
        strengths = text_insights.get("strengths", [])
        gaps = text_insights.get("gaps", [])

        elements.append(Paragraph("Text-based governance signals", styles["Heading2"]))

        if strengths:
            elements.append(Paragraph("<b>Detected strengths:</b>", styles["Normal"]))
            for s in strengths:
                elements.append(Paragraph(f"• {s}", styles["Normal"]))
            elements.append(Spacer(1, 6))

        if gaps:
            elements.append(Paragraph("<b>Potential gaps or blind spots:</b>", styles["Normal"]))
            for g in gaps:
                elements.append(Paragraph(f"• {g}", styles["Normal"]))
            elements.append(Spacer(1, 12))

    # Category scores table
    elements.append(Paragraph("Category scores", styles["Heading2"]))

    # Build a table of category scores with simple traffic-light styling
    table_data = [["Category", "Score (0–100)", "Status"]]
    row_styles = []

    for idx, (cat, score) in enumerate(category_scores.items(), start=1):
        status = "Strength" if score >= 75 else "Developing" if score >= 50 else "Priority gap"

        table_data.append([cat, f"{score:.1f}", status])

        # Row colour: light green / amber / red based on status
        if score >= 75:
            bg = colors.HexColor("#E6F4EA")  # light green
        elif score >= 50:
            bg = colors.HexColor("#FFF4E5")  # light amber
        else:
            bg = colors.HexColor("#FDECEA")  # light red

        row_styles.append(("BACKGROUND", (0, idx), (-1, idx), bg))

    cat_table = Table(table_data, hAlign="LEFT")
    cat_table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ]
    cat_table_style.extend(row_styles)
    cat_table.setStyle(TableStyle(cat_table_style))

    elements.append(cat_table)
    elements.append(Spacer(1, 12))

    # Recommendations
    elements.append(Paragraph("High-level recommendations", styles["Heading2"]))
    for cat, text in recommendations.items():
        elements.append(Paragraph(f"<b>{cat}</b>", styles["Normal"]))
        elements.append(Paragraph(text, styles["Normal"]))
        elements.append(Spacer(1, 4))

    # Historical trend (if available)
    try:
        assessments_path = Path("docs") / "assessments.csv"
        if assessments_path.exists() and email:
            df_all = pd.read_csv(assessments_path)

            df_org = df_all[df_all["email"] == email]
            if len(df_org) >= 2:
                df_org = df_org.sort_values("timestamp")

                # --- Overall readiness trend chart ---
                fig, ax = plt.subplots(figsize=(5, 3))
                ax.plot(
                    pd.to_datetime(df_org["timestamp"]),
                    df_org["overall_score"],
                    marker="o",
                )
                ax.set_title("Overall readiness trend")
                ax.set_xlabel("Assessment date/time")
                ax.set_ylabel("Score (0–100)")
                ax.grid(True)

                img_buffer = BytesIO()
                plt.tight_layout()
                fig.savefig(img_buffer, format="PNG")
                plt.close(fig)
                img_buffer.seek(0)

                elements.append(Spacer(1, 12))
                elements.append(Paragraph("Historical readiness trend", styles["Heading2"]))
                elements.append(Image(img_buffer, width=400, height=250))
                elements.append(Spacer(1, 8))

                # --- Overall change since last assessment ---
                last_two = df_org.tail(2)
                prev_overall = last_two["overall_score"].iloc[0]
                latest_overall = last_two["overall_score"].iloc[1]
                delta_overall = latest_overall - prev_overall

                elements.append(
                    Paragraph(
                        f"Overall readiness changed by {delta_overall:+.1f} points "
                        f"between the last two assessments "
                        f"({prev_overall:.1f} → {latest_overall:.1f} on a 0–100 scale).",
                        styles["Normal"],
                    )
                )
                elements.append(Spacer(1, 8))

                # --- Category trend summary table (latest vs previous) ---
                latest = df_org.iloc[-1]
                previous = df_org.iloc[-2]

                table_data = [["Category", "Latest score", "Change vs previous"]]

                for cat in CAT_LIST:
                    col_name = "cat_" + cat.replace(" ", "_").lower()
                    if col_name in df_org.columns:
                        latest_val = latest.get(col_name, None)
                        prev_val = previous.get(col_name, None)
                        if pd.notna(latest_val) and pd.notna(prev_val):
                            delta_cat = latest_val - prev_val
                            table_data.append(
                                [
                                    cat,
                                    f"{latest_val:.1f}",
                                    f"{delta_cat:+.1f}",
                                ]
                            )

                if len(table_data) > 1:
                    elements.append(
                        Paragraph(
                            "Category trends (comparing the last two assessments)",
                            styles["Heading3"],
                        )
                    )
                    cat_table = Table(table_data, hAlign="LEFT")
                    cat_table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                            ]
                        )
                    )
                    elements.append(cat_table)
                    elements.append(Spacer(1, 12))
    except Exception:
        # If anything goes wrong, we silently skip the trend chart for the PDF
        pass

    # Footer
    elements.append(Spacer(1, 18))
    elements.append(
        Paragraph(
            "This report is generated by a prototype AI governance readiness assessment tool. "
            "It is indicative only and does not constitute legal advice.",
            styles["Italic"],
        )
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer
