"""Streamlit UI for VoxCPM + Ollama multi-agent and speech workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from orchestrator import VoxCPMOrchestrator
from smoke_test import run_workspace_smoke_test
from speech import SpeechServiceError, VoxSpeechService
from utils import load_config

LANG_OPTIONS = ["auto", "en", "zh", "es", "fr", "de", "hi", "ja", "ko", "ar", "ru", "pt", "it", "tr"]
VOICE_PRESETS = {
    "Studio Neutral": "Clear, neutral, and production-ready narration.",
    "Executive Brief": "Confident executive presentation voice with concise phrasing.",
    "Customer Success": "Warm, reassuring, and service-oriented voice with steady pacing.",
    "Explainer": "Energetic explainer voice with crisp emphasis on key ideas.",
    "Custom": "",
}
OUTPUT_DIR = Path("outputs")
SPEECH_DIR = OUTPUT_DIR / "speech"
LOG_PATH = OUTPUT_DIR / "agent_logs.jsonl"
SNAPSHOT_DIR = Path("docs/snapshots")
SMOKE_TEST_SNAPSHOT = SNAPSHOT_DIR / "09_ui_smoke_test.json"


def _load_sample_task(sample_file: str) -> str:
    path = Path("sample_tasks") / sample_file
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _set_state_defaults() -> None:
    defaults = {
        "task_text": "Create a wiki page on renewable energy with key technologies and future outlook.",
        "tts_text": "Hello. This is a multilingual speech synthesis demo using VoxCPM.",
        "last_result": None,
        "last_transcript": "",
        "last_tts_result": None,
        "smoke_test_result": None,
        "selected_preset": "(none)",
        "voice_preset": "Studio Neutral",
        "voice_direction": VOICE_PRESETS["Studio Neutral"],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _inject_ui_theme() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Manrope:wght@400;500;600;700&display=swap');

:root {
    --bg: #eef3f7;
    --panel: rgba(255, 255, 255, 0.88);
    --panel-strong: rgba(255, 255, 255, 0.96);
    --line: #d7e3ea;
    --ink: #102532;
    --muted: #597384;
    --accent: #0f7c82;
    --accent-deep: #0b5d63;
    --warm: #ef8354;
    --shadow: 0 20px 50px rgba(18, 42, 58, 0.10);
}

html, body, [class*="css"] {
    font-family: "Manrope", sans-serif;
    color: var(--ink);
}

.stApp {
    background:
        radial-gradient(circle at 0% 0%, rgba(15, 124, 130, 0.12), transparent 30%),
        radial-gradient(circle at 100% 0%, rgba(239, 131, 84, 0.12), transparent 28%),
        linear-gradient(180deg, #eef4f7 0%, #f8fafb 55%, #ffffff 100%);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(12, 32, 44, 0.96), rgba(16, 42, 58, 0.96));
    border-right: 1px solid rgba(215, 227, 234, 0.10);
}

[data-testid="stSidebar"] * {
    color: #eff7fb;
}

[data-testid="stSidebar"] .stButton button,
[data-testid="stSidebar"] .stDownloadButton button {
    background: linear-gradient(135deg, #0f7c82, #18a0aa);
    color: #ffffff;
    border: 0;
    border-radius: 14px;
    font-weight: 700;
}

.shell-hero {
    padding: 32px 34px;
    border-radius: 28px;
    background: linear-gradient(135deg, #0a1e2a 0%, #0e3340 50%, #12404e 100%);
    box-shadow: 0 24px 56px rgba(10, 30, 42, 0.35);
    position: relative;
    overflow: hidden;
    margin-bottom: 18px;
}

.shell-hero:before,
.shell-hero:after {
    content: "";
    position: absolute;
    border-radius: 999px;
    filter: blur(2px);
}

.shell-hero:before {
    width: 320px;
    height: 320px;
    right: -100px;
    top: -140px;
    background: rgba(239, 131, 84, 0.08);
}

.shell-hero:after {
    width: 260px;
    height: 260px;
    right: 140px;
    bottom: -170px;
    background: rgba(15, 124, 130, 0.10);
}

.eyebrow {
    display: inline-block;
    font-size: 0.74rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #5ee6e8;
    font-weight: 600;
    margin-bottom: 10px;
}

.hero-title {
    font-family: "Space Grotesk", sans-serif;
    color: #ffffff;
    font-size: 2.1rem;
    font-weight: 700;
    line-height: 1.15;
    margin: 0 0 12px 0;
    max-width: 720px;
    text-shadow: 0 2px 12px rgba(0, 0, 0, 0.4);
}

.hero-copy {
    color: #c8dfe8;
    max-width: 760px;
    margin: 0;
    font-size: 1rem;
    line-height: 1.55;
}

.hero-strip {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 18px;
}

.hero-pill {
    border: 1px solid rgba(255, 255, 255, 0.22);
    border-radius: 999px;
    padding: 9px 16px;
    color: #ffffff;
    background: rgba(255, 255, 255, 0.12);
    font-size: 0.88rem;
    font-weight: 500;
    backdrop-filter: blur(4px);
}

.section-card {
    background: #ffffff;
    border: 1px solid #e2eaef;
    border-radius: 20px;
    padding: 22px 22px 18px 22px;
    box-shadow: 0 4px 16px rgba(18, 42, 58, 0.06);
}

.section-card + .section-card {
    margin-top: 14px;
}

.metric-card {
    min-height: 126px;
    border-radius: 20px;
    padding: 20px;
    background: #ffffff;
    border: 1px solid #e2eaef;
    box-shadow: 0 4px 16px rgba(18, 42, 58, 0.06);
}

.metric-label {
    color: #6b8999;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 0 0 8px 0;
    text-transform: uppercase;
    letter-spacing: 0.10em;
}

.metric-value {
    font-family: "Space Grotesk", sans-serif;
    color: #0a1e2a;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
}

.metric-note {
    color: #7a9aab;
    margin-top: 10px;
    font-size: 0.88rem;
    line-height: 1.45;
}

.status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 10px;
}

.status-chip {
    border-radius: 14px;
    padding: 14px 14px 12px 14px;
    border: 1px solid #e2eaef;
    background: #f7fafb;
}

.status-chip strong {
    display: block;
    font-size: 0.82rem;
    font-weight: 600;
    color: #6b8999;
    margin-bottom: 6px;
}

.status-chip span {
    font-weight: 700;
    font-size: 0.95rem;
    color: #0a1e2a;
}

.status-ok span {
    color: #0a8c50;
}

.status-warn span {
    color: #c45d1a;
}

.brand-panel {
    padding: 18px;
    border-radius: 16px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    margin-bottom: 14px;
}

.brand-title {
    font-family: "Space Grotesk", sans-serif;
    margin: 0;
    font-size: 1.1rem;
    font-weight: 700;
    color: #ffffff;
}

.brand-copy {
    margin: 8px 0 0 0;
    color: #a0c4d4;
    font-size: 0.9rem;
    line-height: 1.5;
}

.flow-list {
    margin: 0;
    padding-left: 18px;
    color: #3d5a6b;
}

.flow-list li {
    margin-bottom: 10px;
    line-height: 1.55;
}

.artifact-list {
    border: 1px dashed var(--line);
    border-radius: 18px;
    padding: 14px;
    background: rgba(255,255,255,0.60);
}

.snapshot-frame {
    border-radius: 18px;
    border: 1px solid var(--line);
    background: rgba(255,255,255,0.84);
    padding: 12px;
}

[data-baseweb="tab-list"] {
    gap: 10px;
}

button[data-baseweb="tab"] {
    border-radius: 999px;
    padding: 10px 18px;
    background: #f4f8fa;
    border: 1px solid #dde7ec;
    color: #3d5a6b;
    font-weight: 600;
    font-size: 0.9rem;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: #0e3340;
    border-color: #0e3340;
    color: #ffffff;
}

.stButton button,
.stDownloadButton button {
    border-radius: 12px;
    border: 1px solid #d0dce3;
    font-weight: 600;
    font-size: 0.88rem;
    color: #1a3a4a;
}

.stButton button[kind="primary"] {
    background: #0e3340;
    color: #ffffff;
    border: 0;
}

.stButton button[kind="primary"]:hover {
    background: #164a5c;
}
</style>
""",
        unsafe_allow_html=True,
    )


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_run_history(limit: int = 12) -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in reversed(LOG_PATH.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            continue
        if len(entries) >= limit:
            break
    return entries


def _workspace_inventory() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SPEECH_DIR.mkdir(parents=True, exist_ok=True)
    markdown_outputs = sorted(OUTPUT_DIR.glob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True)
    speech_outputs = sorted(SPEECH_DIR.glob("*.wav"), key=lambda item: item.stat().st_mtime, reverse=True)
    snapshots = sorted(SNAPSHOT_DIR.glob("*"), key=lambda item: item.stat().st_mtime, reverse=True) if SNAPSHOT_DIR.exists() else []
    history = _read_run_history()
    return {
        "markdown_outputs": markdown_outputs,
        "speech_outputs": speech_outputs,
        "snapshots": snapshots,
        "history": history,
        "latest_output": markdown_outputs[0] if markdown_outputs else None,
        "latest_speech": speech_outputs[0] if speech_outputs else None,
    }


def _status_class(is_ready: bool) -> str:
    return "status-ok" if is_ready else "status-warn"


def _metric_card(title: str, value: str, note: str) -> str:
    return (
        "<div class='metric-card'>"
        f"<p class='metric-label'>{title}</p>"
        f"<p class='metric-value'>{value}</p>"
        f"<div class='metric-note'>{note}</div>"
        "</div>"
    )


def _save_uploaded_file(uploaded_file: Any, prefix: str) -> str:
    destination = OUTPUT_DIR / f"{prefix}-{uploaded_file.name}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(uploaded_file.read())
    return str(destination)


def _sync_text_actions() -> None:
    if st.button("Use transcript as task", key="use_transcript_as_task", use_container_width=True):
        transcript = st.session_state.get("last_transcript", "").strip()
        if transcript:
            st.session_state["task_text"] = transcript
            st.success("Transcript moved into the task composer.")
        else:
            st.warning("No transcript is available yet.")

    if st.button("Send final output to speech", key="send_output_to_speech", use_container_width=True):
        result = st.session_state.get("last_result")
        if result is not None:
            st.session_state["tts_text"] = result.final_output
            st.success("Latest final output moved into the speech composer.")
        else:
            st.warning("Run the orchestrator first to generate final output.")


st.set_page_config(page_title="VoxCPM Multi-Agent Workspace", page_icon=":studio_microphone:", layout="wide")
_inject_ui_theme()
_set_state_defaults()

config = load_config("config.yaml")
speech_service = VoxSpeechService(config)
speech_status = speech_service.dependency_status()
inventory = _workspace_inventory()
latest_smoke_test = st.session_state.get("smoke_test_result") or _read_json(SMOKE_TEST_SNAPSHOT)

st.markdown(
    f"""
<div class="shell-hero">
  <div class="eyebrow">Local AI Operations Workspace</div>
  <h1 class="hero-title">Production-style control center for agent orchestration, multilingual speech, and validation evidence.</h1>
  <p class="hero-copy">This workspace now combines command-center visibility, orchestration authoring, voice conditioning, run history, artifact inspection, and snapshot browsing in a single Streamlit surface.</p>
  <div class="hero-strip">
    <div class="hero-pill">Backend: {config['agents']['planner']['model']} planner + Ollama stack</div>
    <div class="hero-pill">Speech: {'TTS/STT ready' if speech_status.ready_for_tts and speech_status.ready_for_stt else 'Partial dependency readiness'}</div>
    <div class="hero-pill">Artifacts: {len(inventory['markdown_outputs'])} markdown, {len(inventory['speech_outputs'])} audio, {len(inventory['snapshots'])} snapshots</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
<div class="brand-panel">
  <p class="brand-title">VoxCPM Operator Console</p>
  <p class="brand-copy">Production-style workspace for local agent operations, multilingual speech generation, and validation evidence.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.subheader("Task Presets")
    st.selectbox(
        "Sample workflow",
        options=["(none)", "renewable_energy.txt", "company_strategy.md"],
        key="selected_preset",
    )
    if st.button("Load selected preset", key="load_preset_sidebar", use_container_width=True):
        if st.session_state["selected_preset"] != "(none)":
            st.session_state["task_text"] = _load_sample_task(st.session_state["selected_preset"])

    st.divider()
    st.subheader("Workspace Readiness")
    st.markdown(
        f"""
<div class="status-grid">
  <div class="status-chip {_status_class(speech_status.voxcpm_available)}"><strong>VoxCPM</strong><span>{'Ready' if speech_status.voxcpm_available else 'Missing'}</span></div>
  <div class="status-chip {_status_class(speech_status.funasr_available)}"><strong>FunASR</strong><span>{'Ready' if speech_status.funasr_available else 'Missing'}</span></div>
  <div class="status-chip {_status_class(speech_status.soundfile_available)}"><strong>soundfile</strong><span>{'Ready' if speech_status.soundfile_available else 'Missing'}</span></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("One-Click Validation")
    if st.button("Run full workspace smoke test", key="run_smoke_test_sidebar", use_container_width=True):
        with st.spinner("Running orchestrator and multilingual speech validation..."):
            try:
                st.session_state["smoke_test_result"] = run_workspace_smoke_test(
                    config_path="config.yaml",
                    task="Create a concise wiki page on renewable energy in 5 sections.",
                    speech_text="Hello world. This is VoxCPM multilingual speech verification.",
                    language="auto",
                    snapshot_path=str(SMOKE_TEST_SNAPSHOT),
                )
            except Exception as exc:
                st.error(f"Smoke test failed: {exc}")
            else:
                st.success("Validation completed and snapshot refreshed.")

    st.caption("Use the smoke test before demos or README updates to refresh the latest validation artifact.")

top_metrics = st.columns(4)
last_backend = latest_smoke_test.get("orchestrator", {}).get("backend", "not-run") if isinstance(latest_smoke_test, dict) else "not-run"
top_metrics[0].markdown(
    _metric_card("Agent backend", last_backend, "Latest validated backend used by the orchestrator."),
    unsafe_allow_html=True,
)
top_metrics[1].markdown(
    _metric_card("Run history", str(len(inventory["history"])), "Recent workflow executions loaded from JSONL logs."),
    unsafe_allow_html=True,
)
top_metrics[2].markdown(
    _metric_card("Speech assets", str(len(inventory["speech_outputs"])), "Persisted multilingual audio files in outputs/speech."),
    unsafe_allow_html=True,
)
top_metrics[3].markdown(
    _metric_card("Snapshots", str(len(inventory["snapshots"])), "Documented validation and UI evidence stored in docs/snapshots."),
    unsafe_allow_html=True,
)

tab_command, tab_orchestrator, tab_speech, tab_ops = st.tabs(
    ["Command Center", "Agent Studio", "Speech Lab", "Operations and Snapshots"]
)

with tab_command:
    left_col, right_col = st.columns([1.1, 0.9])

    with left_col:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Operational Flows")
        st.markdown(
            """
<ol class="flow-list">
  <li>Compose or load a task, then run the agent chain from Agent Studio.</li>
  <li>Convert transcripts into fresh tasks or route final outputs into the speech composer.</li>
  <li>Use prompt audio conditioning in Speech Lab for more directed voice generation.</li>
  <li>Inspect run history, artifact previews, and snapshot evidence from the Operations tab.</li>
  <li>Refresh production-readiness evidence with the one-click smoke test before sharing results.</li>
</ol>
""",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Cross-Workflow Shortcuts")
        action_cols = st.columns(2)
        with action_cols[0]:
            _sync_text_actions()
        with action_cols[1]:
            if st.button("Load latest markdown into task", key="load_latest_markdown_task", use_container_width=True):
                latest_output = inventory["latest_output"]
                if latest_output is None:
                    st.warning("No saved markdown artifact is available yet.")
                else:
                    st.session_state["task_text"] = latest_output.read_text(encoding="utf-8")
                    st.success("Latest markdown artifact moved into the task composer.")

            if st.button("Load transcript into speech", key="load_transcript_speech", use_container_width=True):
                transcript = st.session_state.get("last_transcript", "").strip()
                if transcript:
                    st.session_state["tts_text"] = transcript
                    st.success("Transcript moved into the speech composer.")
                else:
                    st.warning("No transcript is available yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Capability Matrix")
        st.markdown(
            f"""
<div class="status-grid">
  <div class="status-chip {_status_class(True)}"><strong>Orchestration</strong><span>Ready</span></div>
  <div class="status-chip {_status_class(speech_status.ready_for_tts)}"><strong>TTS</strong><span>{'Ready' if speech_status.ready_for_tts else 'Blocked'}</span></div>
  <div class="status-chip {_status_class(speech_status.ready_for_stt)}"><strong>STT</strong><span>{'Ready' if speech_status.ready_for_stt else 'Blocked'}</span></div>
  <div class="status-chip {_status_class(isinstance(latest_smoke_test, dict))}"><strong>Smoke Test</strong><span>{'Available' if isinstance(latest_smoke_test, dict) else 'Missing'}</span></div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Latest Validation Snapshot")
        if isinstance(latest_smoke_test, dict):
            st.json(latest_smoke_test)
        else:
            st.info("Run the one-click smoke test to populate the latest validation summary.")
        st.markdown("</div>", unsafe_allow_html=True)

with tab_orchestrator:
    compose_col, output_col = st.columns([1.05, 0.95])

    with compose_col:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Task Composer")
        st.text_area(
            "Task",
            key="task_text",
            height=240,
            placeholder="Create a multilingual wiki article, strategy note, or analyst brief.",
        )
        workflow_cols = st.columns([1.4, 1.1])
        with workflow_cols[0]:
            run_workflow = st.button("Run multi-agent workflow", key="run_agent_workflow", type="primary", use_container_width=True)
        with workflow_cols[1]:
            if st.button("Reset composer", key="reset_task_text", use_container_width=True):
                st.session_state["task_text"] = ""
        st.caption("The orchestrator uses the Researcher -> Summarizer -> Planner -> Communicator chain and persists markdown plus JSONL logs.")
        st.markdown("</div>", unsafe_allow_html=True)

        if run_workflow:
            task_text = st.session_state.get("task_text", "").strip()
            if not task_text:
                st.warning("Provide a task before running the workflow.")
            else:
                with st.spinner("Running the multi-agent orchestration pipeline..."):
                    try:
                        orchestrator = VoxCPMOrchestrator(config_path="config.yaml")
                        st.session_state["last_result"] = orchestrator.run(task=task_text)
                    except Exception as exc:
                        st.error(f"Pipeline failed: {exc}")
                    else:
                        st.success(f"Workflow completed using backend: {st.session_state['last_result'].backend}")

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Recent Run History")
        history = _read_run_history(limit=8)
        if not history:
            st.info("No orchestration runs have been logged yet.")
        else:
            labels = [
                f"{entry.get('timestamp', 'unknown')} | {entry.get('backend', 'n/a')} | {Path(entry.get('output_file', 'n/a')).name}"
                for entry in history
            ]
            selected_label = st.selectbox("Select recent run", options=labels, key="recent_run_select")
            selected_entry = history[labels.index(selected_label)]
            st.json(
                {
                    "timestamp": selected_entry.get("timestamp"),
                    "backend": selected_entry.get("backend"),
                    "task": selected_entry.get("task"),
                    "output_file": selected_entry.get("output_file"),
                }
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with output_col:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Delivery Panel")
        result = st.session_state.get("last_result")
        if result is None:
            st.info("Run the orchestrator to populate metadata, final output, and handoff trace.")
        else:
            metric_cols = st.columns(3)
            metric_cols[0].metric("Backend", result.backend)
            metric_cols[1].metric("Messages", len(result.messages))
            metric_cols[2].metric("Output saved", "Yes")
            st.markdown(result.final_output)
            st.download_button(
                "Download latest markdown",
                data=result.final_output,
                file_name=Path(result.output_file).name,
                mime="text/markdown",
                use_container_width=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Agent Handoff Trace")
        if result is None:
            st.caption("The handoff trace appears after a workflow run.")
        else:
            for index, message in enumerate(result.messages, start=1):
                with st.expander(f"{index}. {message.sender} -> {message.recipient}"):
                    st.markdown(message.content)
                    st.json(message.metadata)
        st.markdown("</div>", unsafe_allow_html=True)

with tab_speech:
    speech_left, speech_right = st.columns([0.95, 1.05])

    with speech_left:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Speech-to-Text")
        speech_lang = st.selectbox("Language", LANG_OPTIONS, index=0, key="speech_language_select")
        uploaded_audio = st.file_uploader(
            "Upload audio for transcription",
            type=["wav", "mp3", "m4a", "flac"],
            key="speech_upload",
        )
        if st.button("Transcribe audio", key="transcribe_audio_button", use_container_width=True):
            if not uploaded_audio:
                st.warning("Upload an audio file before running transcription.")
            else:
                input_path = _save_uploaded_file(uploaded_audio, "stt-input")
                with st.spinner("Transcribing audio with FunASR SenseVoice..."):
                    try:
                        stt_result = speech_service.transcribe(input_path, language=speech_lang)
                    except SpeechServiceError as exc:
                        st.error(str(exc))
                    except Exception as exc:
                        st.error(f"Unexpected STT error: {exc}")
                    else:
                        transcript = stt_result["transcript"]
                        st.session_state["last_transcript"] = transcript
                        if transcript:
                            st.session_state["tts_text"] = transcript
                        st.success("Transcription completed.")
                        st.text_area("Transcript", value=transcript, height=180, key="transcript_preview")
                        st.json({"language": stt_result["language"], "model": stt_result["model"]})
        if not speech_status.ready_for_stt:
            st.warning("STT dependencies missing. Install FunASR and ensure ffmpeg is available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with speech_right:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Text-to-Speech and Voice Conditioning")
        selected_voice = st.selectbox("Voice profile", list(VOICE_PRESETS.keys()), key="voice_preset")
        default_instruction = VOICE_PRESETS[selected_voice]
        if selected_voice != "Custom" and st.session_state.get("voice_direction") != default_instruction:
            st.session_state["voice_direction"] = default_instruction
        control_instruction = st.text_input(
            "Voice direction",
            key="voice_direction",
        )
        st.text_area("Text to synthesize", key="tts_text", height=200)
        with st.expander("Prompt audio conditioning", expanded=False):
            prompt_audio = st.file_uploader(
                "Optional prompt WAV",
                type=["wav"],
                key="prompt_audio_upload",
            )
            st.text_input(
                "Prompt transcript",
                value="",
                key="prompt_text_input",
                placeholder="Describe or transcribe the prompt audio if available.",
            )

        tts_action_cols = st.columns(2)
        with tts_action_cols[0]:
            generate_tts = st.button("Generate speech", key="generate_speech_button", type="primary", use_container_width=True)
        with tts_action_cols[1]:
            speak_output = st.button("Read latest final output", key="speak_latest_output_button", use_container_width=True)

        if speak_output:
            result = st.session_state.get("last_result")
            if result is None:
                st.warning("No final output is available yet.")
            else:
                st.session_state["tts_text"] = result.final_output
                generate_tts = True

        if generate_tts:
            prompt_wav_path = None
            prompt_audio_file = st.session_state.get("prompt_audio_upload")
            if prompt_audio_file is not None:
                prompt_wav_path = _save_uploaded_file(prompt_audio_file, "tts-prompt")

            with st.spinner("Synthesizing speech with VoxCPM..."):
                try:
                    tts_result = speech_service.synthesize(
                        text=st.session_state.get("tts_text", ""),
                        language=st.session_state.get("speech_language_select", "auto"),
                        control_instruction=control_instruction,
                        prompt_wav_path=prompt_wav_path,
                        prompt_text=st.session_state.get("prompt_text_input", ""),
                    )
                except SpeechServiceError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Unexpected TTS error: {exc}")
                else:
                    st.session_state["last_tts_result"] = tts_result
                    audio_bytes = Path(tts_result["audio_path"]).read_bytes()
                    st.success("Speech generated successfully.")
                    st.audio(audio_bytes, format="audio/wav")
                    st.download_button(
                        label="Download WAV",
                        data=audio_bytes,
                        file_name=Path(tts_result["audio_path"]).name,
                        mime="audio/wav",
                        use_container_width=True,
                    )
                    st.json(tts_result)
        if not speech_status.ready_for_tts:
            st.warning("TTS dependencies missing. Install soundfile and VoxCPM from source.")
        st.markdown("</div>", unsafe_allow_html=True)

with tab_ops:
    ops_left, ops_right = st.columns([1.0, 1.0])

    with ops_left:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Artifact Browser")
        markdown_outputs = inventory["markdown_outputs"]
        speech_outputs = inventory["speech_outputs"]
        if markdown_outputs:
            selected_md = st.selectbox(
                "Markdown artifact",
                options=[file_path.name for file_path in markdown_outputs[:12]],
                key="markdown_artifact_select",
            )
            selected_md_path = next(path for path in markdown_outputs if path.name == selected_md)
            st.markdown("<div class='artifact-list'>", unsafe_allow_html=True)
            st.markdown(selected_md_path.read_text(encoding="utf-8"))
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No markdown outputs found yet.")

        if speech_outputs:
            selected_wav = st.selectbox(
                "Speech artifact",
                options=[file_path.name for file_path in speech_outputs[:12]],
                key="speech_artifact_select",
            )
            selected_wav_path = next(path for path in speech_outputs if path.name == selected_wav)
            st.audio(selected_wav_path.read_bytes(), format="audio/wav")
        else:
            st.info("No speech artifacts found yet.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Log Record Inspector")
        history = inventory["history"]
        if history:
            history_labels = [
                f"{entry.get('timestamp', 'unknown')} | {entry.get('backend', 'n/a')} | {Path(entry.get('output_file', 'n/a')).name}"
                for entry in history
            ]
            history_selected = st.selectbox("Logged run", options=history_labels, key="ops_history_select")
            selected_history = history[history_labels.index(history_selected)]
            st.json(selected_history)
        else:
            st.info("No JSONL history is available yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with ops_right:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Snapshot Center")
        if inventory["snapshots"]:
            snapshot_name = st.selectbox(
                "Available snapshot",
                options=[path.name for path in inventory["snapshots"]],
                key="snapshot_select",
            )
            snapshot_path = next(path for path in inventory["snapshots"] if path.name == snapshot_name)
            st.markdown("<div class='snapshot-frame'>", unsafe_allow_html=True)
            if snapshot_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                st.image(str(snapshot_path), caption=snapshot_path.name, use_container_width=True)
            elif snapshot_path.suffix.lower() == ".json":
                snapshot_data = _read_json(snapshot_path)
                if snapshot_data is not None:
                    st.json(snapshot_data)
                else:
                    st.code(snapshot_path.read_text(encoding="utf-8"))
            elif snapshot_path.suffix.lower() in {".md", ".txt"}:
                st.code(snapshot_path.read_text(encoding="utf-8"), language="markdown")
            else:
                st.code(snapshot_path.read_text(encoding="utf-8"))
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No snapshot artifacts are present.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Current Workspace Summary")
        st.json(
            {
                "markdown_outputs": len(markdown_outputs),
                "speech_outputs": len(speech_outputs),
                "snapshots": len(inventory["snapshots"]),
                "last_transcript_chars": len(st.session_state.get("last_transcript", "")),
                "smoke_test_available": isinstance(latest_smoke_test, dict),
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.caption(
    "Keep Ollama running with ollama serve. For multilingual speech, install FunASR, soundfile, ffmpeg, and VoxCPM from source."
)
