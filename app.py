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

# Enhanced modern styling with proper light/dark mode support
st.markdown(
    """
    <style>
    /* Light mode defaults */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Dark mode overrides */
    [data-theme="dark"] [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    .meeting-hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 3rem;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .meeting-hero h1 {
        font-size: 2.8rem !important;
        margin-bottom: 0.5rem;
        font-weight: 700;
        background: linear-gradient(to right, #ffffff, #e0e7ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .meeting-hero p {
        font-size: 1.1rem;
        opacity: 0.95;
        line-height: 1.6;
    }
    
    .hero-pill {
        display: inline-flex;
        gap: 0.5rem;
        align-items: center;
        padding: 0.4rem 1rem;
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border-radius: 50px;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    /* Metric cards - Light mode */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(102, 126, 234, 0.15);
    }
    
    /* Metric cards - Dark mode */
    [data-theme="dark"] .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    [data-theme="dark"] .metric-card:hover {
        box-shadow: 0 12px 24px rgba(102, 126, 234, 0.2);
    }
    
    .metric-card h3 {
        color: #64748b;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 0;
        font-weight: 600;
    }
    
    [data-theme="dark"] .metric-card h3 {
        color: #94a3b8;
    }
    
    .metric-card p {
        font-size: 2.2rem;
        margin: 0.5rem 0;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .metric-card small {
        color: #64748b;
        font-size: 0.85rem;
    }
    
    [data-theme="dark"] .metric-card small {
        color: #94a3b8;
    }
    
    /* Insight cards - Light mode */
    .insight-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .insight-card:hover {
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        transform: translateX(4px);
    }
    
    /* Insight cards - Dark mode */
    [data-theme="dark"] .insight-card {
        background: #1e293b;
        border: 1px solid #334155;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    [data-theme="dark"] .insight-card:hover {
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
    }
    
    .insight-card h4 {
        margin-bottom: 0.8rem;
        color: #1e293b;
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    [data-theme="dark"] .insight-card h4 {
        color: #f1f5f9;
    }
    
    /* Support card - Light mode */
    .support-card {
        border-left: 4px solid #667eea;
        padding: 0.75rem 1rem;
        background: #f0f4ff;
        border-radius: 8px;
        margin-top: 0.75rem;
        font-size: 0.9rem;
        color: #475569;
        line-height: 1.6;
    }
    
    /* Support card - Dark mode */
    [data-theme="dark"] .support-card {
        background: #1e293b;
        color: #cbd5e1;
        border-left-color: #8b5cf6;
    }
    
    .timeline-meta {
        display: flex;
        gap: 1.5rem;
        font-size: 0.9rem;
        color: #64748b;
        flex-wrap: wrap;
        margin-top: 0.5rem;
    }
    
    [data-theme="dark"] .timeline-meta {
        color: #94a3b8;
    }
    
    .timeline-meta span {
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        background: white;
        color: #475569;
        border: 1px solid #e5e7eb;
        font-weight: 500;
    }
    
    [data-theme="dark"] .stTabs [data-baseweb="tab"] {
        background: #1e293b;
        color: #cbd5e1;
        border-color: #334155;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
    }
    
    /* Visual cards - Light mode */
    .visual-card {
        position: relative;
        overflow: hidden;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
        background: white;
        transition: all 0.3s ease;
    }
    
    .visual-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
    }
    
    /* Visual cards - Dark mode */
    [data-theme="dark"] .visual-card {
        background: #1e293b;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    [data-theme="dark"] .visual-card:hover {
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
    }
    
    .visual-card img {
        width: 100%;
        height: 240px;
        object-fit: cover;
        display: block;
    }
    
    .visual-card .visual-meta {
        padding: 1rem 1.25rem;
        color: #1e293b;
    }
    
    [data-theme="dark"] .visual-card .visual-meta {
        color: #f1f5f9;
    }
    
    .visual-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.3rem 0.8rem;
        border-radius: 50px;
        background: #f0f4ff;
        font-size: 0.85rem;
        color: #667eea;
        font-weight: 500;
        margin-top: 0.5rem;
    }
    
    [data-theme="dark"] .visual-tag {
        background: #312e81;
        color: #c7d2fe;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Info boxes */
    .stInfo {
        background: #f0f9ff !important;
        border-left: 4px solid #0ea5e9 !important;
        border-radius: 8px !important;
    }
    
    [data-theme="dark"] .stInfo {
        background: #1e293b !important;
        border-left-color: #38bdf8 !important;
    }
    
    /* Success boxes */
    .stSuccess {
        background: #f0fdf4 !important;
        border-left: 4px solid #22c55e !important;
        border-radius: 8px !important;
    }
    
    [data-theme="dark"] .stSuccess {
        background: #1e293b !important;
        border-left-color: #4ade80 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def _image_to_base64(path: str) -> str:
    """Convert image file to base64 string for HTML embedding."""
    try:
        data = Path(path).read_bytes()
    except FileNotFoundError:
        return ""
    return base64.b64encode(data).decode("utf-8")

st.markdown(
    """
    <div class="meeting-hero">
        <div class="hero-pill">✨ AI-powered minutes • Transcript + Vision</div>
        <h1>Meeting Intelligence Dashboard</h1>
        <p>Surface priorities, accountable owners, and context hints from meeting transcripts. Use <strong>Rapid Demo</strong> for instant walkthroughs or switch to <strong>Custom Analysis</strong> when you're ready to upload material.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

mode = st.sidebar.radio(
    "🎯 Mode",
    ["Rapid demo (cached)", "Custom analysis"],
    help="Use the cached demo for instant results or run full analysis with your own files.",
)

if mode == "Rapid demo (cached)":
    if not SAMPLE_REPORT.exists():
        st.error("Cached sample report missing. Please run a custom analysis to regenerate it.")
        st.stop()
    st.sidebar.success("✅ Loaded cached MeetingBank snippet – no model runtime needed.")
    cached_payload = json.loads(SAMPLE_REPORT.read_text(encoding="utf-8"))
    report = MeetingReport.from_dict(cached_payload)
else:
    tmp_root = Path(tempfile.mkdtemp(prefix="meeting_dash_"))
    try:
        st.sidebar.markdown("### 📄 Transcript source")
        use_sample = st.sidebar.checkbox(
            "Use built-in MeetingBank snippet", value=False, help="Runs the lightweight snippet file."
        )

        transcript_file = None
        transcript_path: Path
        if use_sample:
            transcript_path = SAMPLE_TRANSCRIPT
            jsonl_limit = 5
        else:
            transcript_file = st.sidebar.file_uploader("Transcript (txt/jsonl)", type=["txt", "jsonl"])
            if transcript_file is None:
                st.info("📤 Upload a transcript or toggle the built-in snippet to get started.")
                st.stop()
            transcript_path = tmp_root / Path(transcript_file.name).name
            transcript_path.write_bytes(transcript_file.read())
            jsonl_limit = None

        st.sidebar.markdown("### 🖼️ Optional screenshots")
        image_files = st.sidebar.file_uploader(
            "Screenshots (png/jpg)", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True
        )

        image_dir = tmp_root / "images"
        if image_files:
            image_dir.mkdir(exist_ok=True)
            for file in image_files:
                content = file.read()
                target = image_dir / file.name
                target.write_bytes(content)
        else:
            image_dir = None

        with st.spinner("🔄 Running meeting analysis..."):
            report = build_meeting_report(
                transcript_path,
                image_dir,
                jsonl_limit=jsonl_limit,
            )
    finally:
        if tmp_root and tmp_root.exists():
            shutil.rmtree(tmp_root, ignore_errors=True)

# Extract data from report
action_records = report.action_records()
decision_records = report.decision_records()
visual_records = report.visual_records()

# Display metrics
metrics = [
    ("📋 Action Items", len(action_records), "Owners tracked"),
    ("✅ Decisions", len(decision_records), "Agenda outcomes"),
    ("🎨 Visual Cues", len(visual_records), "Slides analyzed"),
]

st.markdown("### 📊 Key Metrics")
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

st.markdown("---")

# Create tabs
summary_tab, actions_tab, decisions_tab, visuals_tab, exports_tab = st.tabs(
    ["📝 Summary", "🎯 Action Log", "✅ Decision Log", "🖼️ Visual Evidence", "💾 Exports"]
)

with summary_tab:
    st.markdown("### 🎯 Agenda Pulse")
    st.write(report.agenda_summary)
    st.markdown(
        """
        <div class="support-card">
            <strong>💡 Pro Tip:</strong> Pair summaries with the action & decision logs to brief stakeholders in under a minute.
        </div>
        """,
        unsafe_allow_html=True,
    )

with actions_tab:
    if action_records:
        st.markdown("### 📊 Action Items Overview")
        action_df = pd.DataFrame(action_records)
        st.dataframe(action_df, width='stretch', hide_index=True)
        
        st.markdown("### 👥 Owner Timeline")
        for item in action_records:
            st.markdown(
                f"""
                <div class="insight-card">
                    <h4>{item['action_item']}</h4>
                    <div class="timeline-meta">
                        <span>👤 {item['responsible'] or 'Unassigned'}</span>
                        <span>🗓️ {item['deadline'] or 'No date'}</span>
                    </div>
                    <div class="support-card">{item['support'] or 'No supporting quote recorded.'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("ℹ️ No action items detected in this meeting.")

with decisions_tab:
    if decision_records:
        st.markdown("### 📊 Decisions Overview")
        decision_df = pd.DataFrame(decision_records)
        st.dataframe(decision_df, width='stretch', hide_index=True)
        
        st.markdown("### 🎯 Decision Highlights")
        for item in decision_records:
            st.markdown(
                f"""
                <div class="insight-card">
                    <h4>{item['decision']}</h4>
                    <div class="support-card">{item['support'] or 'No supporting quote recorded.'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("ℹ️ No decisions detected in this meeting.")

with visuals_tab:
    if visual_records:
        st.markdown("### 📊 Visual Content Overview")
        visual_df = pd.DataFrame(visual_records)
        st.dataframe(visual_df, width='stretch', hide_index=True)
        
        st.markdown("### 🖼️ Screenshot Gallery")
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
        st.info("ℹ️ No screenshots analyzed in this meeting.")

with exports_tab:
    st.markdown("### 💾 Shareable Downloads")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if action_records:
            st.download_button(
                label="📥 Download Action Items (CSV)",
                data=pd.DataFrame(action_records).to_csv(index=False),
                file_name="actions.csv",
                mime="text/csv",
                width='stretch',
            )
    
    with col2:
        if decision_records:
            st.download_button(
                label="📥 Download Decisions (CSV)",
                data=pd.DataFrame(decision_records).to_csv(index=False),
                file_name="decisions.csv",
                mime="text/csv",
                width='stretch',
            )
    
    with col3:
        st.download_button(
            label="📥 Download Summary (MD)",
            data=report.as_markdown_table().encode("utf-8"),
            file_name="meeting_summary.md",
            mime="text/markdown",
            width='stretch',
        )
    
    st.markdown(
        """
        <div class="support-card">
            <strong>📤 Export Options:</strong> Download action items and decisions as CSV for easy import into project management tools, or get the full summary as Markdown for documentation.
        </div>
        """,
        unsafe_allow_html=True,
    )