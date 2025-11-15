from __future__ import annotations

import base64
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
    :root {
        --card-bg: #ffffff;
        --card-border: #e2e8f0;
        --text-color: #0f172a;
        --subtle-text: #475569;
        --accent-bg: #eef2ff;
        --hero-grad: radial-gradient(circle at top left, #312e81, #0f172a);
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --card-bg: #111827;
            --card-border: #1f2937;
            --text-color: #f8fafc;
            --subtle-text: #94a3b8;
            --accent-bg: #1e293b;
            --hero-grad: radial-gradient(circle at top left, #4338ca, #0b1120);
        }
    }
    .meeting-hero {
        background: var(--hero-grad);
        border-radius: 24px;
        padding: 38px;
        color: #f8fafc;
        margin-bottom: 1.5rem;
        box-shadow: 0 25px 40px rgba(15, 23, 42, 0.35);
    }
    .meeting-hero h1 {font-size: 2.5rem !important; margin-bottom: 0.4rem;}
    .meeting-hero p {font-size: 1.05rem; opacity: 0.9;}
    .hero-pill {
        display: inline-flex;
        gap: 0.6rem;
        align-items: center;
        padding: 0.3rem 0.9rem;
        background: rgba(248, 250, 252, 0.15);
        border-radius: 999px;
        font-size: 0.9rem;
    }
    .metric-card {
        background: var(--card-bg);
        border-radius: 18px;
        padding: 20px;
        border: 1px solid var(--card-border);
        box-shadow: 0 20px 30px rgba(15, 23, 42, 0.08);
    }
    .metric-card h3 {color: var(--subtle-text); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.08em; margin:0;}
    .metric-card p {font-size: 1.9rem; margin: 0.35rem 0 0; font-weight: 600; color: var(--text-color);}
    .insight-card {
        background: var(--card-bg);
        border-radius: 18px;
        padding: 1.15rem;
        border: 1px solid var(--card-border);
        box-shadow: 0 10px 18px rgba(15, 23, 42, 0.12);
        margin-bottom: 1rem;
    }
    .insight-card h4 {margin-bottom: 0.4rem; color: var(--text-color);}
    .support-card {
        border-left: 4px solid #4f46e5;
        padding: 0.5rem 0.8rem;
        background: var(--accent-bg);
        border-radius: 10px;
        margin-top: 0.4rem;
        font-size: 0.92rem;
        color: var(--subtle-text);
    }
    .timeline-meta {
        display: flex;
        gap: 1rem;
        font-size: 0.92rem;
        color: var(--subtle-text);
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb=\"tab-list\"] {gap: 0.5rem;}
    .stTabs [data-baseweb=\"tab\"] {
        padding: 0.55rem 1.25rem;
        border-radius: 999px;
        background: rgba(148, 163, 184, 0.35);
        color: var(--text-color);
    }
    .visual-card {
        position: relative;
        overflow: hidden;
        border-radius: 18px;
        border: 1px solid var(--card-border);
        box-shadow: 0 15px 30px rgba(15, 23, 42, 0.18);
        margin-bottom: 1.2rem;
        background: var(--card-bg);
    }
    .visual-card img {width: 100%; height: 240px; object-fit: cover; display: block;}
    .visual-card .visual-meta {
        padding: 0.9rem 1rem 1.1rem;
        color: var(--text-color);
    }
    .visual-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        background: var(--accent-bg);
        font-size: 0.85rem;
        color: var(--subtle-text);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def _image_to_base64(path: str) -> str:
    try:
        data = Path(path).read_bytes()
    except FileNotFoundError:
        return ""
    return base64.b64encode(data).decode("utf-8")

st.markdown(
    """
    <div class="meeting-hero">
        <div class="hero-pill">AI-powered minutes • Transcript + Vision</div>
        <h1>Meeting Intelligence Dashboard</h1>
        <p>Surface priorities, accountable owners, and context hints from meeting transcripts. Use <strong>Rapid Demo</strong> for instant walkthroughs or switch to <strong>Custom Analysis</strong> when you're ready to upload material.</p>
    </div>
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
        st.dataframe(action_df, width="stretch")
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
        st.dataframe(decision_df, width="stretch")
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
        st.dataframe(visual_df, width="stretch")
        preview_cols = st.columns(min(3, len(visual_records)))
        for idx, record in enumerate(visual_records):
            col = preview_cols[idx % len(preview_cols)]
            with col:
                encoded = _image_to_base64(record["image_path"])
                if encoded:
                    col.markdown(
                        f"""
                        <div class='visual-card'>
                            <img src='data:image/png;base64,{encoded}' alt='{record['caption']}'>
                            <div class='visual-meta'>
                                <strong>{record['caption']}</strong>
                                <div class='visual-tag'>📌 {record['linked_topics']}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    col.info(record["caption"])
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
