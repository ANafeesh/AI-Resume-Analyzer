"""Streamlit web application for Resume Analyzer and Job Description Matcher."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.extractor import extract_resume_text
from src.matcher import match_resume_to_job
from src.parser import parse_resume
from src.report import generate_json_report, generate_markdown_report, generate_txt_report
from src.suggestions import generate_suggestions
from src.utils import get_logger, get_project_root

logger = get_logger("streamlit_app")
ROOT_DIR = get_project_root()
SAMPLE_DIR = ROOT_DIR / "tests" / "sample_data"

# Page configuration
st.set_page_config(
    page_title="AI Resume Analyzer & Matcher",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #ffffff;
        padding: 24px 28px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.9rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .main-header p {
        margin: 6px 0 0 0;
        font-size: 0.95rem;
        color: #94a3b8;
    }
    
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .score-container {
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
    }
    .score-high {
        background: #f0fdf4;
        border: 2px solid #86efac;
        color: #15803d;
    }
    .score-med {
        background: #fffbeb;
        border: 2px solid #fde68a;
        color: #b45309;
    }
    .score-low {
        background: #fef2f2;
        border: 2px solid #fecaca;
        color: #b91c1c;
    }
    
    .skill-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin: 3px 4px 3px 0;
    }
    .badge-matched {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    .badge-missing {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .badge-candidate {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #bae6fd;
    }
    
    .suggestion-box {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-size: 0.93rem;
    }
    .gap-box {
        background-color: #fff7ed;
        border-left: 4px solid #f97316;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-size: 0.93rem;
    }
    .weak-box {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-size: 0.93rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_header() -> None:
    """Render top application hero banner."""
    st.markdown(
        """
        <div class="main-header">
            <h1>📄 AI Resume Analyzer & Job Matcher</h1>
            <p>Upload your resume to extract candidate intelligence, analyze keyword gaps, and get instant job-fit scoring.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_sample_resume_text() -> str:
    """Load text of the bundled sample resume."""
    path = SAMPLE_DIR / "sample_resume.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def load_sample_jd_text() -> str:
    """Load text of the bundled sample job description."""
    path = SAMPLE_DIR / "sample_job_description.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def display_score_card(score: float, formula_explanation: str) -> None:
    """Render the score card and progress gauge with transparent formula."""
    if score >= 75:
        score_class = "score-high"
        tag = "Strong Match"
    elif score >= 50:
        score_class = "score-med"
        tag = "Moderate Match"
    else:
        score_class = "score-low"
        tag = "Low Match / Significant Gaps"

    st.markdown(
        f"""
        <div class="score-container {score_class}">
            <div style="font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Overall Match Score</div>
            <div style="font-size: 3.5rem; font-weight: 800; line-height: 1.1;">{score}%</div>
            <div style="font-size: 1.05rem; font-weight: 600; margin-top: 4px;">{tag}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, max(0.0, score / 100.0)))
    with st.expander("ℹ️ How is this score calculated? (Transparent Formula)", expanded=False):
        st.info(formula_explanation)


def display_overview_tab(resume: dict[str, Any], match: dict[str, Any]) -> None:
    """Render Overview tab with top metrics, category coverage, and summary."""
    c1, c2, c3, c4 = st.columns(4)

    total_cand_skills = len(match.get("candidate_all_skills", []))
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{total_cand_skills}</div>
                <div class="metric-label">Skills Found</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        matched_cnt = match.get("total_matched_skills", 0)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #16a34a;">{matched_cnt}</div>
                <div class="metric-label">Matched Skills</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        missing_cnt = match.get("total_missing_skills", 0)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #dc2626;">{missing_cnt}</div>
                <div class="metric-label">Missing Skills</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        years = resume.get("years_of_experience", "Not found")
        years_display = f"{years} yrs" if isinstance(years, (int, float)) else str(years)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{years_display}</div>
                <div class="metric-label">Est. Experience</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Section-level score breakdown if JD provided
    if match.get("has_jd"):
        sec_scores = match.get("section_scores", {})
        st.subheader("Section-Level Alignment")
        col_s, col_e, col_ed = st.columns(3)
        with col_s:
            st.metric("Technical Skills Match", f"{sec_scores.get('skills_score', 0)}%")
        with col_e:
            st.metric("Experience Relevance", f"{sec_scores.get('experience_score', 0)}%")
        with col_ed:
            st.metric("Education Alignment", f"{sec_scores.get('education_score', 0)}%")

    st.markdown("---")
    st.subheader("📊 Skill Category Breakdown")

    # Prepare DataFrame for category chart
    cand_by_cat = match.get("candidate_skills_by_category", {})
    matched_by_cat = match.get("matched_by_category", {})
    missing_by_cat = match.get("missing_by_category", {})

    chart_data: list[dict[str, Any]] = []
    for cat in cand_by_cat:
        cand_count = len(cand_by_cat.get(cat, []))
        mat_count = len(matched_by_cat.get(cat, []))
        mis_count = len(missing_by_cat.get(cat, []))
        if cand_count > 0 or mat_count > 0 or mis_count > 0:
            chart_data.append({
                "Category": cat,
                "Resume Skills": cand_count,
                "Matched (in JD)": mat_count,
                "Missing (from JD)": mis_count,
            })

    if chart_data:
        df = pd.DataFrame(chart_data).set_index("Category")
        st.bar_chart(df[["Resume Skills", "Matched (in JD)", "Missing (from JD)"]])
    else:
        st.info("No categorized skills detected yet.")


def display_keywords_tab(match: dict[str, Any]) -> None:
    """Render Keywords & Skills tab."""
    has_jd = match.get("has_jd", False)

    if not has_jd:
        st.info("No Job Description was provided. Below are the skills extracted from your resume organized by category.")
        cand_by_cat = match.get("candidate_skills_by_category", {})
        for cat, skills in cand_by_cat.items():
            if skills:
                st.markdown(f"**{cat}** ({len(skills)})")
                badges_html = "".join([f'<span class="skill-badge badge-candidate">{s}</span>' for s in skills])
                st.markdown(f"<div>{badges_html}</div><br>", unsafe_allow_html=True)
        return

    st.subheader("🎯 Matched vs. Missing Skills")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ✅ Matched Keywords")
        matched_by_cat = match.get("matched_by_category", {})
        has_any_matched = False
        for cat, skills in matched_by_cat.items():
            if skills:
                has_any_matched = True
                st.markdown(f"**{cat}**")
                badges_html = "".join([f'<span class="skill-badge badge-matched">{s}</span>' for s in skills])
                st.markdown(f"<div>{badges_html}</div><br>", unsafe_allow_html=True)
        if not has_any_matched:
            st.warning("No direct skill matches found with this job description.")

    with col2:
        st.markdown("#### ❌ Missing Keywords (Skill Gaps)")
        missing_by_cat = match.get("missing_by_category", {})
        has_any_missing = False
        for cat, skills in missing_by_cat.items():
            if skills:
                has_any_missing = True
                st.markdown(f"**{cat}**")
                badges_html = "".join([f'<span class="skill-badge badge-missing">{s}</span>' for s in skills])
                st.markdown(f"<div>{badges_html}</div><br>", unsafe_allow_html=True)
        if not has_any_missing:
            st.success("Outstanding! You match all catalogued skills mentioned in the job description.")

    # High frequency terms
    frequent = match.get("frequent_terms", [])
    if frequent:
        st.markdown("---")
        st.subheader("🔍 Important Job Description Keywords")
        st.caption("Top contextual non-stopword terms frequent in the target job description:")
        term_cols = st.columns(4)
        for idx, (term, count) in enumerate(frequent):
            with term_cols[idx % 4]:
                st.markdown(f"**`{term}`** — {count}x")


def display_suggestions_tab(suggestions: dict[str, Any]) -> None:
    """Render actionable suggestions and weak-signal detection."""
    crit = suggestions.get("critical_gaps", [])
    if crit:
        st.markdown("### 🚨 High-Priority Keyword Gaps")
        for tip in crit:
            st.markdown(f'<div class="gap-box"><strong>Gap:</strong> {tip}</div>', unsafe_allow_html=True)

    weak = suggestions.get("weak_signals", [])
    if weak:
        st.markdown("### ⚠️ Resume Weak Signals Detected")
        for signal in weak:
            st.markdown(f'<div class="weak-box"><strong>Caution:</strong> {signal}</div>', unsafe_allow_html=True)

    content = suggestions.get("content_improvements", [])
    if content:
        st.markdown("### 💡 Content & Formatting Recommendations")
        for rec in content:
            st.markdown(f'<div class="suggestion-box">{rec}</div>', unsafe_allow_html=True)

    verbs = suggestions.get("recommended_action_verbs", [])
    if verbs:
        st.markdown("---")
        st.markdown("#### 🚀 Recommended Action Verbs to Strengthen Experience")
        verbs_html = "".join([f'<span class="skill-badge badge-candidate">{v}</span>' for v in verbs])
        st.markdown(f"<div>{verbs_html}</div>", unsafe_allow_html=True)


def display_extracted_data_tab(resume: dict[str, Any]) -> None:
    """Render extracted candidate profile and structured sections."""
    st.subheader("👤 Candidate Contact Details")
    c1, c2 = st.columns(2)

    with c1:
        st.write(f"**Full Name:** {resume.get('name', 'Not found')}")
        st.write(f"**Email:** {resume.get('email', 'Not found')}")
        st.write(f"**Phone:** {resume.get('phone', 'Not found')}")

    with c2:
        links = resume.get("links", {})
        st.write(f"**LinkedIn:** {links.get('linkedin', 'Not found')}")
        st.write(f"**GitHub:** {links.get('github', 'Not found')}")
        st.write(f"**Portfolio / Website:** {links.get('portfolio', 'Not found')}")

    st.markdown("---")
    st.subheader("🎓 Education Entries")
    edu_list = resume.get("education", [])
    if edu_list:
        for idx, item in enumerate(edu_list, 1):
            st.markdown(f"**{idx}. {item.get('degree', 'Degree')}** ({item.get('year', 'Year')})")
            if item.get("institution") and item["institution"] != "Not found":
                st.caption(f"Institution: {item['institution']}")
            st.text(item.get("entry", ""))
    else:
        st.info("No structured education entries detected.")

    st.markdown("---")
    st.subheader("💼 Work Experience Entries")
    exp_list = resume.get("experience", [])
    if exp_list:
        for idx, item in enumerate(exp_list, 1):
            st.markdown(f"**{idx}. {item.get('headline', 'Experience')}** — *{item.get('dates', 'Dates')}*")
            bullets = item.get("bullets", [])
            for b in bullets:
                st.markdown(f"- {b}")
            st.write("")
    else:
        st.info("No structured work experience entries detected.")


def main() -> None:
    """Main application loop."""
    render_header()

    # Session State Initialization
    if "analysis_bundle" not in st.session_state:
        st.session_state["analysis_bundle"] = None
    if "job_description_input" not in st.session_state:
        st.session_state["job_description_input"] = ""

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        uploaded_file = st.file_uploader(
            "Upload Resume",
            type=["pdf", "docx", "txt"],
            help="Upload your resume in PDF, DOCX, or TXT format.",
        )

        st.subheader("Target Job Description")
        st.caption("Paste the target job description below for match scoring & gap analysis:")

        # Button to quickly test with sample data
        if st.button("📋 Load Sample Data Demo", help="Preload sample resume and job description"):
            st.session_state["job_description_input"] = load_sample_jd_text()
            st.session_state["sample_resume_active"] = True
            st.success("Loaded sample JD and resume!")

        jd_text = st.text_area(
            "Job Description (optional)",
            value=st.session_state.get("job_description_input", ""),
            height=200,
            placeholder="Paste job description requirements, responsibilities, and qualifications here...",
        )

        analyze_button = st.button("🚀 Analyze Resume", type="primary", use_container_width=True)

        if st.button("🔄 Reset / Clear", use_container_width=True):
            st.session_state["analysis_bundle"] = None
            st.session_state["job_description_input"] = ""
            st.session_state.pop("sample_resume_active", None)
            st.rerun()

    # Trigger Analysis
    if analyze_button:
        resume_raw_text = ""
        error_msg: str | None = None

        if uploaded_file is not None:
            # Extract from user uploaded stream in memory (no disk storage)
            with st.spinner("Extracting text from resume..."):
                try:
                    file_bytes = io.BytesIO(uploaded_file.getvalue())
                    resume_raw_text, error_msg = extract_resume_text(
                        file_bytes,
                        explicit_extension=Path(uploaded_file.name).suffix.lower(),
                    )
                except Exception as ex:
                    logger.error("Error reading uploaded file: %s", ex, exc_info=True)
                    error_msg = f"Failed to process uploaded file: {ex}"
        elif st.session_state.get("sample_resume_active", False):
            # Use sample resume text
            resume_raw_text = load_sample_resume_text()
        else:
            st.warning("Please upload a resume file (PDF, DOCX, or TXT) or click 'Load Sample Data Demo' to proceed.")
            return

        if error_msg:
            st.error(f"❌ {error_msg}")
            return

        if not resume_raw_text.strip():
            st.error("❌ The uploaded document contained no readable text. Please check the file and try again.")
            return

        with st.spinner("Analyzing resume content and matching keywords..."):
            try:
                parsed_resume = parse_resume(resume_raw_text)
                match_result = match_resume_to_job(parsed_resume, jd_text)
                suggestions_result = generate_suggestions(parsed_resume, match_result, jd_text)

                st.session_state["analysis_bundle"] = {
                    "resume": parsed_resume,
                    "match": match_result,
                    "suggestions": suggestions_result,
                    "raw_jd": jd_text,
                }
                st.success("✅ Analysis completed successfully!")
            except Exception as e:
                logger.error("Error during analysis pipeline: %s", e, exc_info=True)
                st.error("An error occurred while analyzing the resume. Please check logs for details.")
                return

    # Display Results if Available
    bundle = st.session_state.get("analysis_bundle")
    if bundle:
        resume_data = bundle["resume"]
        match_data = bundle["match"]
        suggestions_data = bundle["suggestions"]

        # Score display if JD provided
        if match_data.get("has_jd"):
            display_score_card(
                match_data["overall_score"],
                match_data["formula_explanation"],
            )

        # Tab Navigation
        tab_overview, tab_keywords, tab_suggestions, tab_extracted = st.tabs([
            "📊 Overview",
            "🎯 Keywords & Skills",
            "💡 Actionable Suggestions",
            "📋 Extracted Data",
        ])

        with tab_overview:
            display_overview_tab(resume_data, match_data)

        with tab_keywords:
            display_keywords_tab(match_data)

        with tab_suggestions:
            display_suggestions_tab(suggestions_data)

        with tab_extracted:
            display_extracted_data_tab(resume_data)

        # Export Section
        st.markdown("---")
        st.subheader("📥 Export Full Analysis Report")
        col_json, col_md, col_txt = st.columns(3)

        cand_name = resume_data.get("name", "candidate").replace(" ", "_").lower()

        with col_json:
            json_report = generate_json_report(bundle)
            st.download_button(
                label="Download JSON Report",
                data=json_report,
                file_name=f"resume_analysis_{cand_name}.json",
                mime="application/json",
                use_container_width=True,
            )

        with col_md:
            md_report = generate_markdown_report(bundle)
            st.download_button(
                label="Download Markdown Report",
                data=md_report,
                file_name=f"resume_analysis_{cand_name}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with col_txt:
            txt_report = generate_txt_report(bundle)
            st.download_button(
                label="Download Plain Text Report",
                data=txt_report,
                file_name=f"resume_analysis_{cand_name}.txt",
                mime="text/plain",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()