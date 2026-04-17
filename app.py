"""Streamlit UI for VoxCPM + Ollama multi-agent wiki generation."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from orchestrator import VoxCPMOrchestrator


def _load_sample_task(sample_file: str) -> str:
    path = Path("sample_tasks") / sample_file
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


st.set_page_config(page_title="VoxCPM Multi-Agent Wiki", page_icon=":brain:", layout="wide")
st.title("VoxCPM + Ollama Multi-Agent Wiki Studio")
st.caption("Researcher -> Summarizer -> Planner -> Communicator")

with st.sidebar:
    st.header("Task Presets")
    preset = st.selectbox(
        "Choose a sample task",
        options=["(none)", "renewable_energy.txt", "company_strategy.md"],
        index=0,
    )
    if st.button("Load Preset", use_container_width=True) and preset != "(none)":
        st.session_state["task_text"] = _load_sample_task(preset)

if "task_text" not in st.session_state:
    st.session_state["task_text"] = "Create a wiki page on renewable energy."

user_task = st.text_area(
    "Enter your task",
    value=st.session_state["task_text"],
    height=180,
    placeholder="Example: Create a wiki page on renewable energy with key technologies, policy trends, and future outlook.",
)

run_clicked = st.button("Run Multi-Agent Pipeline", type="primary", use_container_width=True)

if run_clicked:
    if not user_task.strip():
        st.warning("Please provide a task before running the pipeline.")
    else:
        with st.spinner("Running agents with Ollama..."):
            try:
                orchestrator = VoxCPMOrchestrator(config_path="config.yaml")
                result = orchestrator.run(task=user_task.strip())
            except Exception as exc:
                st.error(f"Pipeline failed: {exc}")
            else:
                st.success(f"Completed using backend: {result.backend}")

                left, right = st.columns([1, 2])
                with left:
                    st.subheader("Run Metadata")
                    st.write({"task": result.task, "output_file": result.output_file, "backend": result.backend})

                with right:
                    st.subheader("Final Output")
                    st.markdown(result.final_output)

                st.subheader("Agent Conversation Log")
                for index, message in enumerate(result.messages, start=1):
                    with st.expander(f"{index}. {message.sender} → {message.recipient}"):
                        st.markdown(message.content)
                        st.json(message.metadata)

                st.info(f"Saved markdown output to: {result.output_file}")

st.divider()
st.caption("Tip: ensure Ollama is running locally (`ollama serve`) and selected models are pulled.")
