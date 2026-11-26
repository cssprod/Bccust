"""
BC Parenting Log - Local-first evidence log for BC family law custody cases.
Run: streamlit run app.py
"""
import os
import logging
from datetime import datetime
from typing import Dict, List

import streamlit as st
import pandas as pd

from lib.parser import parse_messages, chunk_messages, format_chunk_for_llm
from lib.analyzer import InfractionAnalyzer
from lib.exporter import export_pdf, export_csv, export_xlsx, LEGAL_DISCLAIMER
from lib.prompts import BC_FLA_SYSTEM_PROMPT, INFRACTION_SCHEMA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="BC Parenting Log", page_icon="⚖️", layout="wide")

# ---------------------------- Session state ----------------------------
if "step" not in st.session_state:
    st.session_state.step = "setup"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "infractions" not in st.session_state:
    st.session_state.infractions = []
if "case_info" not in st.session_state:
    st.session_state.case_info = {}
if "sender_aliases" not in st.session_state:
    st.session_state.sender_aliases = {}
if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""

# ---------------------------- Sidebar ----------------------------
with st.sidebar:
    st.title("⚖️ BC Parenting Log")
    st.caption("Local-first evidence organizer — nothing leaves your machine")

    st.divider()
    st.subheader("Privacy & Anonymizer")
    parent1 = st.text_input("Your name (Parent 1)", key="p1")
    parent2 = st.text_input("Co-parent name (Parent 2)", key="p2")
    child = st.text_input("Child name(s)", key="child")

    if any([parent1, parent2, child]):
        aliases = {}
        if parent1:
            aliases[parent1] = "[Applicant]"
        if parent2:
            aliases[parent2] = "[Respondent]"
        if child:
            aliases[child] = "[Child]"
        st.session_state.sender_aliases = aliases
        st.success("Anonymizer active — names will be redacted before AI analysis")

    st.divider()
    st.subheader("Model Settings")
    model = st.selectbox("Ollama model", ["llama3.1:8b", "mistral-nemo", "qwen2.5:14b", "llama3.2:3b"],
                         index=0)
    chunk_size = st.slider("Messages per chunk", 20, 100, 50)
    st.caption("Smaller chunks = more accurate, more API calls")

    st.divider()
    if st.button("Reset / New Case"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ---------------------------- Step 1: Setup ----------------------------
if st.session_state.step == "setup":
    st.header("Step 1 — Case Setup")
    st.markdown(
        "Enter your case details. All data stays on your computer. "
        "The AI model runs locally via Ollama — no text is sent over the internet."
    )

    col1, col2 = st.columns(2)
    with col1:
        case_name = st.text_input("Case name / file number")
        court = st.selectbox("Court", ["BC Provincial Court", "BC Supreme Court"])
    with col2:
        st.write("")  # spacing
        st.write("")

    st.info(LEGAL_DISCLAIMER)

    if st.button("Continue to Input", type="primary"):
        st.session_state.case_info = {
            "case_name": case_name,
            "court": court,
            "file_number": case_name,
        }
        st.session_state.step = "input"
        st.rerun()

# ---------------------------- Step 2: Input ----------------------------
elif st.session_state.step == "input":
    st.header("Step 2 — Paste or Upload Conversation")

    st.markdown("Paste your raw text conversation, or upload a .txt/.csv export.")
    st.caption("Supported formats: iMessage, WhatsApp, SMS, or any `Sender: Message` style export.")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        raw_text = st.text_area(
            "Conversation text",
            height=300,
            placeholder="Paste your message thread here...",
            key="raw_text_area",
        )
        uploaded = st.file_uploader("Or upload .txt / .csv", type=["txt", "csv"])

    with col_right:
        st.subheader("Preview")
        if raw_text or uploaded:
            text_to_parse = raw_text or ""
            if uploaded:
                text_to_parse = uploaded.read().decode("utf-8")
            messages = parse_messages(text_to_parse, st.session_state.sender_aliases)
            st.session_state.messages = messages
            st.session_state.raw_text = text_to_parse
            st.metric("Messages parsed", len(messages))
            if messages:
                preview_df = pd.DataFrame([
                    {
                        "Time": m.timestamp.strftime("%Y-%m-%d %I:%M %p"),
                        "Sender": m.sender,
                        "Message": m.body[:80] + ("…" if len(m.body) > 80 else ""),
                    }
                    for m in messages[:10]
                ])
                st.dataframe(preview_df, use_container_width=True, hide_index=True)
        else:
            st.info("No text parsed yet.")

    st.divider()
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Analyze Conversation", type="primary", disabled=not st.session_state.messages):
            st.session_state.step = "analyze"
            st.rerun()
    with col_btn2:
        if st.button("Back"):
            st.session_state.step = "setup"
            st.rerun()

# ---------------------------- Step 3: Analyze ----------------------------
elif st.session_state.step == "analyze":
    st.header("Step 3 — AI Analysis")
    st.caption("Running locally via Ollama. This may take a minute for long conversations.")

    if st.session_state.infractions:
        # Already analyzed — show results and let user continue
        pass
    else:
        with st.status("Analyzing conversation…", expanded=True) as status:
            try:
                analyzer = InfractionAnalyzer(model=model)
                chunks = chunk_messages(st.session_state.messages, chunk_size=chunk_size)
                st.write(f"Split into {len(chunks)} chunk(s)")

                all_infractions = []
                for i, chunk in enumerate(chunks):
                    chunk_text = format_chunk_for_llm(chunk)
                    st.write(f"Analyzing chunk {i + 1}/{len(chunks)} ({len(chunk)} messages)")
                    infractions = analyzer.analyze_chunk(chunk_text)
                    all_infractions.extend(infractions)

                # Verify quotes against original text
                verified = analyzer.verify_quotes(all_infractions, st.session_state.raw_text)
                st.session_state.infractions = verified

                status.update(
                    label=f"Analysis complete — {len(verified)} verified infractions found",
                    state="complete",
                )
            except Exception as exc:
                status.update(label=f"Analysis failed: {exc}", state="error")
                st.error(
                    "Make sure Ollama is running (`ollama serve`) and you've pulled a model "
                    "(e.g., `ollama pull llama3.1:8b`)."
                )
                st.stop()

    # Show results
    infractions = st.session_state.infractions
    st.metric("Verified Infractions", len(infractions))

    if infractions:
        # Category filter
        categories = sorted({inf.get("category", "") for inf in infractions})
        selected_cats = st.multiselect("Filter by category", categories, default=categories)

        filtered = [inf for inf in infractions if inf.get("category", "") in selected_cats]

        # Editable table
        st.subheader("Evidence Log")
        st.caption("Objective Summary cells are editable — refine before export.")

        rows = []
        for i, inf in enumerate(filtered, 1):
            rows.append({
                "Exhibit #": f"EX-{i:02d}",
                "Date & Time": inf.get("timestamp", ""),
                "Category": inf.get("category", ""),
                "Severity": inf.get("severity", ""),
                "Verbatim Quote": inf.get("verbatim_quote", ""),
                "Objective Summary": inf.get("objective_summary", ""),
                "Has Screenshot": False,
            })

        df = pd.DataFrame(rows)
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Has Screenshot": st.column_config.CheckboxColumn("Screenshot attached?"),
                "Objective Summary": st.column_config.TextColumn("Objective Summary", width="large"),
            },
            num_rows="fixed",
        )

        st.session_state.infractions = [
            {
                "timestamp": r["Date & Time"],
                "category": r["Category"],
                "severity": r["Severity"],
                "verbatim_quote": r["Verbatim Quote"],
                "context_before_after": "",
                "objective_summary": r["Objective Summary"],
            }
            for _, r in edited_df.iterrows()
        ]

        st.divider()
        st.subheader("Export")
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            if st.button("Export PDF", type="primary"):
                os.makedirs("exports", exist_ok=True)
                path = f"exports/evidence_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                export_pdf(st.session_state.infractions, path, st.session_state.case_info)
                st.success(f"PDF saved: {path}")
                with open(path, "rb") as f:
                    st.download_button("Download PDF", f, file_name=os.path.basename(path), mime="application/pdf")
        with col_e2:
            if st.button("Export CSV"):
                os.makedirs("exports", exist_ok=True)
                path = f"exports/evidence_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                export_csv(st.session_state.infractions, path)
                st.success(f"CSV saved: {path}")
                with open(path, "rb") as f:
                    st.download_button("Download CSV", f, file_name=os.path.basename(path), mime="text/csv")
        with col_e3:
            if st.button("Export Excel"):
                os.makedirs("exports", exist_ok=True)
                path = f"exports/evidence_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                export_xlsx(st.session_state.infractions, path)
                st.success(f"Excel saved: {path}")
                with open(path, "rb") as f:
                    st.download_button("Download Excel", f, file_name=os.path.basename(path), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("Re-analyze"):
            st.session_state.infractions = []
            st.rerun()
    with col_b2:
        if st.button("Back to Input"):
            st.session_state.step = "input"
            st.rerun()

# ---------------------------- Footer ----------------------------
st.divider()
st.caption(LEGAL_DISCLAIMER)
st.caption("⚖️ BC Parenting Log — Local-first. Runs via Ollama on your machine. Nothing leaves your computer.")
