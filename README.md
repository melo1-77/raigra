# RAIGRA — Responsible AI Governance Readiness Assessment

RAIGRA helps organisations understand how prepared they are to deploy and govern AI responsibly.  
The tool focuses on the practical side of governance — the processes, controls and culture that determine whether AI can be deployed safely and ethically inside an organisation.

> Developed by **Melvin Riley** as part of an independent research and policy project.  
> Live demo: **https://raigra.streamlit.app/**

## 🎥 Walkthrough video

[![RAIGRA demo video](https://img.youtube.com/vi/YOUR_VIDEO_ID/hqdefault.jpg)](https://youtu.be/YOUR_VIDEO_ID)

---

## What RAIGRA measures

The assessment covers five domains that consistently show up in AI failure cases, regulatory expectations and good practice guidelines:

| Domain | Focus |
|--------|-------|
| Governance & Policy | Accountability, oversight, risk management |
| Data Privacy & Protection | DPIAs, lawful basis, retention, consent |
| Technical Controls & Monitoring | Drift, incident response, robustness, auditability |
| Ethics & Societal Impact | Fairness, accessibility, user well-being |
| Organisational Capability | Training, roles, skills, operational maturity |

After completing the questionnaire, RAIGRA generates:

- A readiness score (0–100)
- A risk band with interpretation
- Per-category breakdown
- Prioritised recommendations
- A **PDF report**
- **Historical trend tracking** for organisations that reassess over time

---

## Why this approach

Many AI governance assessments are either:
- purely academic and impractical to implement, or
- checkbox-style tools that don’t support real change.

RAIGRA sits between those extremes — fast enough for early conversations, structured enough to shape a roadmap.

Current prototype features:
- End-to-end Streamlit assessment workflow
- Automated PDF report
- Sector- and organisation-specific weighting
- Text-based governance signal extraction
- Website context summarisation
- Historical trend tracking
- ML research prototype for predictive scoring (not live in-app)

---

## Modelling (research layer)

The repository includes a notebook:  
`model/raigra_ml_prototype.ipynb`

It:
- builds a synthetic dataset mirroring RAIGRA-style assessments
- trains a **RandomForestRegressor** to estimate readiness
- evaluates model performance (RMSE + R²)
- visualises feature importance

This is not a production model.  
It demonstrates how RAIGRA could evolve once real labelled assessments exist.

---
## Project structure

```text
raigra/
  app/                  # Streamlit application
    app.py
    pdf_report.py
    scoring.py
    questions.py
    nlp_utils.py
  docs/
    assessments.csv     # stored evaluations
    contacts.csv
  model/
    raigra_ml_prototype.ipynb
  requirements.txt

## Run locally
git clone https://github.com/melo1-77/raigra.git
cd raigra
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py

Deployment

The app is deployed on Streamlit Cloud:
https://raigra.streamlit.app/

Any push to the main branch automatically redeploys.

⸻

Roadmap

Planned upgrades:
	•	Live ML-powered scoring
	•	SHAP-based interpretability for organisations
	•	Sector-specific action plans
	•	Admin dashboard for portfolio-level analytics
	•	Export to policy templates and implementation plans

⸻

Contact

If you’d like to explore pilots, research collaboration or governance consulting:

mriley.official@gmail.com

⸻

Licence

Shared for academic and research use.
Commercial use requires permission.