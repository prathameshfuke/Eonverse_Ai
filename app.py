from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.analysis.data_structures import MeetingReport
from src.analysis.pipeline import build_meeting_report

SAMPLE_TRANSCRIPT = Path("data/samples/meetingbank_housing_snippet.jsonl")
SAMPLE_REPORT = Path("data/samples/meetingbank_housing_snippet_report.json")

st.set_page_config(page_title="Meeting Intelligence Dashboard", layout="wide", page_icon="📋")

st.markdown(
    """
    <style>
    .meeting-hero {
        background: radial-gradient(circle at top left, #312e81, #0f172a);
        border-radius: 24px;
        padding: 38px;
        color: #f8fafc;
        margin-bottom: 1.5rem;
        box-shadow: 0 25px 40px rgba(15, 23, 42, 0.35);
    }
    .meeting-hero h1 {font-size: 2.5rem !important; margin-bottom: 0.6rem;}
    .meeting-hero p {font-size: 1.08rem; opacity: 0.9;}
    .metric-card {
        background: #ffffff;
        border-radius: 18px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 20px 30px rgba(15, 23, 42, 0.08);
    }
    .metric-card h3 {color: #64748b; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.08em; margin:0;}
    .metric-card p {font-size: 1.9rem; margin: 0.35rem 0 0; font-weight: 600; color: #0f172a;}
    .insight-card {
        background: #fff;
        border-radius: 18px;
        padding: 1.15rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 18px rgba(15, 23, 42, 0.08);
        margin-bottom: 1rem;
    }
    .insight-card h4 {margin-bottom: 0.4rem;}
    .support-card {
        border-left: 4px solid #4f46e5;
        padding: 0.5rem 0.8rem;
        background: #eef2ff;
        border-radius: 10px;
        margin-top: 0.4rem;
        font-size: 0.92rem;
    }
    .timeline-meta {
        display: flex;
        gap: 1rem;
        font-size: 0.92rem;
        color: #475569;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab-list"] {gap: 0.5rem;}
    .stTabs [data-baseweb="tab"] {
        padding: 0.55rem 1.25rem;
        border-radius: 999px;
        background: #e2e8f0;
        color: #0f172a;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

mode = st.sidebar.radio(
    "Mode",
    ["Rapid demo (cached)", "Custom analysis"],
    help="Use the cached demo for instant results or run full analysis with your own files.",
)

if mode == "Rapid demo (cached)":
    if not SAMPLE_REPORT.exists():
        st.error("Cached sample report missing. Please run a custom analysis to regenerate it.")
        st.stop()
    st.sidebar.success("Loaded cached MeetingBank snippet – no model runtime needed.")
    cached_payload = json.loads(SAMPLE_REPORT.read_text(encoding="utf-8"))
    report = MeetingReport.from_dict(cached_payload)
else:
    tmp_root = Path(tempfile.mkdtemp(prefix="meeting_dash_"))
    try:
        st.sidebar.markdown("### Transcript source")
        use_sample = st.sidebar.checkbox(
            "Use built-in MeetingBank snippet", value=False, help="Runs the lightweight snippet file."
        )

        transcript_file = None
        transcript_path: Path
        if use_sample:
            transcript_path = SAMPLE_TRANSCRIPT
            jsonl_limit = 5
        else:
            transcript_file = st.file_uploader("Transcript (txt/jsonl)", type=["txt", "jsonl"])
            if transcript_file is None:
                st.info("Upload a transcript or toggle the built-in snippet.")
                st.stop()
            transcript_path = tmp_root / Path(transcript_file.name).name
            transcript_path.write_bytes(transcript_file.read())
            jsonl_limit = None

        st.sidebar.markdown("### Optional screenshots")
        image_files = st.file_uploader(
            "Screenshots (png/jpg)", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True
        )

        image_dir = tmp_root / "images"
        if image_files:
            image_dir.mkdir(exist_ok=True)
            for file in image_files:
                content = file.read()
                target = image_dir / file.name
                target.write_bytes(content)
                st.image(content, caption=file.name, use_column_width=True)
        else:
            image_dir = None

        with st.spinner("Running meeting analysis..."):
            report = build_meeting_report(
                transcript_path,
                image_dir,
                jsonl_limit=jsonl_limit,
            )
    finally:
        if tmp_root and tmp_root.exists():
            shutil.rmtree(tmp_root, ignore_errors=True)

action_records = report.action_records()
decision_records = report.decision_records()
visual_records = report.visual_records()

metrics = [
    ("Action Items", len(action_records), "Owners tracked"),
    ("Decisions", len(decision_records), "Agenda outcomes"),
    ("Visual Cues", len(visual_records), "Slides/screenshots analyzed"),
]
metric_cols = st.columns(len(metrics))
for col, (title, value, helper) in zip(metric_cols, metrics):
    col.markdown(
        f"""
        <div class="metric-card">
            <h3>{title}</h3>
            <p>{value}</p>
            <small>{helper}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

summary_tab, actions_tab, decisions_tab, visuals_tab, exports_tab = st.tabs(
    ["Summary", "Action Log", "Decision Log", "Visual Evidence", "Exports"]
)

with summary_tab:
    st.markdown("### Agenda Pulse")
    st.write(report.agenda_summary)
    st.markdown(
        """
        <div class="support-card">
            <strong>Tip:</strong> Pair summaries with the action & decision logs to brief stakeholders in under a minute.
        </div>
        """,
        unsafe_allow_html=True,
    )

with actions_tab:
    if action_records:
        action_df = pd.DataFrame(action_records)
        st.dataframe(action_df, use_container_width=True)
        st.markdown("#### Owner timeline")
        for item in action_records:
            actions_tab.markdown(
                f"""
                <div class=\"insight-card\">
                    <h4>{item['action_item']}</h4>
                    <div class=\"timeline-meta\">
                        <span>👤 {item['responsible'] or 'Unassigned'}</span>
                        <span>🗓 {item['deadline'] or 'No date'}</span>
                    </div>
                    <div class=\"support-card\">{item['support'] or 'No supporting quote recorded.'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No action items detected.")

with decisions_tab:
    if decision_records:
        decision_df = pd.DataFrame(decision_records)
        st.dataframe(decision_df, use_container_width=True)
        st.markdown("#### Decision highlights")
        for item in decision_records:
            decisions_tab.markdown(
                f"""
                <div class=\"insight-card\">
                    <h4>{item['decision']}</h4>
                    <div class=\"support-card\">{item['support'] or 'No supporting quote recorded.'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No decisions detected.")

with visuals_tab:
    if visual_records:
        visual_df = pd.DataFrame(visual_records)
        st.dataframe(visual_df, use_container_width=True)
        preview_cols = st.columns(min(3, len(visual_records)))
        for idx, record in enumerate(visual_records):
            col = preview_cols[idx % len(preview_cols)]
            with col:
                col.image(record["image_path"], caption=record["caption"], use_column_width=True)
    else:
        st.info("No screenshots analyzed.")

with exports_tab:
    st.markdown("#### Shareable downloads")
    if action_records:
        st.download_button(
            label="Download Action Items (CSV)",
            data=pd.DataFrame(action_records).to_csv(index=False),
            file_name="actions.csv",
            mime="text/csv",
        )
    if decision_records:
        st.download_button(
            label="Download Decisions (CSV)",
            data=pd.DataFrame(decision_records).to_csv(index=False),
            file_name="decisions.csv",
            mime="text/csv",
        )
    st.download_button(
        label="Download Dashboard (Markdown)",
        data=report.as_markdown_table().encode("utf-8"),
        file_name="meeting_summary.md",
        mime="text/markdown",
    )
