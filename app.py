"""Streamlit UI for VoxCPM + Ollama multi-agent wiki and speech workflows."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from orchestrator import VoxCPMOrchestrator
from smoke_test import run_workspace_smoke_test
from speech import SpeechServiceError, VoxSpeechService
from utils import load_config


def _load_sample_task(sample_file: str) -> str:
    path = Path("sample_tasks") / sample_file
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _inject_ui_theme() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: "IBM Plex Sans", sans-serif;
}

.main {
    background: radial-gradient(circle at 0% 0%, #f0f8ff 0%, #f7fbff 35%, #ffffff 100%);
}

.hero {
    border: 1px solid #d9e7ff;
    border-radius: 18px;
    padding: 20px;
    background: linear-gradient(135deg, rgba(242,248,255,0.92), rgba(255,255,255,0.96));
    box-shadow: 0 14px 32px rgba(36, 74, 114, 0.08);
    margin-bottom: 14px;
}

.hero-title {
    font-family: "Space Grotesk", sans-serif;
    font-weight: 700;
    font-size: 1.75rem;
    color: #143255;
    margin: 0;
}

.hero-sub {
    color: #38516e;
    margin-top: 8px;
    margin-bottom: 0;
}

.card {
    border-radius: 14px;
    border: 1px solid #d9e6f5;
    background: #ffffff;
    padding: 12px 14px;
    box-shadow: 0 8px 18px rgba(24, 56, 92, 0.06);
    margin-bottom: 10px;
}

.metric-title {
    color: #4f6480;
    font-size: 0.82rem;
    margin-bottom: 4px;
}

.metric-value {
    color: #102b47;
    font-weight: 700;
    font-size: 1.08rem;
    margin: 0;
}
</style>
""",
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="VoxCPM Multi-Agent Workspace", page_icon=":microphone:", layout="wide")
_inject_ui_theme()

st.markdown(
    """
<div class="hero">
  <p class="hero-title">VoxCPM Multi-Agent Workspace</p>
  <p class="hero-sub">Orchestrator plus multilingual speech studio with one-click smoke testing and local-first artifacts.</p>
</div>
""",
    unsafe_allow_html=True,
)

config = load_config("config.yaml")
speech_service = VoxSpeechService(config)
speech_status = speech_service.dependency_status()

if "task_text" not in st.session_state:
    st.session_state["task_text"] = "Create a wiki page on renewable energy with key technologies and future outlook."

if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

if "last_transcript" not in st.session_state:
    st.session_state["last_transcript"] = ""

if "smoke_test_result" not in st.session_state:
    st.session_state["smoke_test_result"] = None

with st.sidebar:
    st.header("Workspace Controls")
    preset = st.selectbox(
        "Task preset",
        options=["(none)", "renewable_energy.txt", "company_strategy.md"],
        index=0,
    )
    if st.button("Load preset", use_container_width=True) and preset != "(none)":
        st.session_state["task_text"] = _load_sample_task(preset)

    st.divider()
    st.subheader("Speech Capability")
    st.write(
        {
            "tts_ready": speech_status.ready_for_tts,
            "stt_ready": speech_status.ready_for_stt,
            "voxcpm": speech_status.voxcpm_available,
            "funasr": speech_status.funasr_available,
            "soundfile": speech_status.soundfile_available,
        }
    )
    if not speech_status.ready_for_tts or not speech_status.ready_for_stt:
        st.caption("Install optional speech dependencies for full multilingual STT/TTS support.")

    st.divider()
    st.subheader("One-Click Smoke Test")
    if st.button("Run Full Workspace Smoke Test", use_container_width=True):
        with st.spinner("Running orchestrator plus multilingual STT/TTS smoke test..."):
            try:
                st.session_state["smoke_test_result"] = run_workspace_smoke_test(
                    config_path="config.yaml",
                    task="Create a concise wiki page on renewable energy in 5 sections.",
                    speech_text="Hello world. This is VoxCPM multilingual speech verification.",
                    language="auto",
                    snapshot_path="docs/snapshots/09_ui_smoke_test.json",
                )
            except Exception as exc:
                st.error(f"Smoke test failed: {exc}")
            else:
                st.success("Smoke test completed and snapshot refreshed.")


tab_orchestrator, tab_speech, tab_artifacts = st.tabs(["Multi-Agent Orchestrator", "Speech Studio", "Artifacts and Logs"])

with tab_orchestrator:
    st.subheader("Task Orchestration")
    user_task = st.text_area(
        "Task",
        value=st.session_state["task_text"],
        height=180,
        placeholder="Example: Create a multilingual wiki article on renewable energy with citations and a concise conclusion.",
    )

    if st.button("Run Multi-Agent Workflow", type="primary", use_container_width=True):
        if not user_task.strip():
            st.warning("Please provide a task before running the workflow.")
        else:
            with st.spinner("Running Researcher -> Summarizer -> Planner -> Communicator..."):
                try:
                    orchestrator = VoxCPMOrchestrator(config_path="config.yaml")
                    st.session_state["last_result"] = orchestrator.run(task=user_task.strip())
                except Exception as exc:
                    st.error(f"Pipeline failed: {exc}")
                else:
                    st.success(f"Completed using backend: {st.session_state['last_result'].backend}")

    result = st.session_state.get("last_result")
    if result:
        c1, c2, c3 = st.columns(3)
        c1.markdown(
            '<div class="card"><p class="metric-title">Backend</p><p class="metric-value">'
            + str(result.backend)
            + "</p></div>",
            unsafe_allow_html=True,
        )
        c2.markdown(
            '<div class="card"><p class="metric-title">Messages</p><p class="metric-value">'
            + str(len(result.messages))
            + "</p></div>",
            unsafe_allow_html=True,
        )
        c3.markdown(
            '<div class="card"><p class="metric-title">Output File</p><p class="metric-value">Saved</p></div>',
            unsafe_allow_html=True,
        )

        left, right = st.columns([1, 2])
        with left:
            st.subheader("Run Metadata")
            st.json({"task": result.task, "output_file": result.output_file, "backend": result.backend})
        with right:
            st.subheader("Final Output")
            st.markdown(result.final_output)

        st.subheader("Agent Handoff Trace")
        for index, message in enumerate(result.messages, start=1):
            with st.expander(f"{index}. {message.sender} -> {message.recipient}"):
                st.markdown(message.content)
                st.json(message.metadata)

with tab_speech:
    st.subheader("Multilingual Speech Studio")
    st.caption("Use VoxCPM for TTS and SenseVoice (FunASR) for STT. Language can be auto-detected.")

    lang_options = ["auto", "en", "zh", "es", "fr", "de", "hi", "ja", "ko", "ar", "ru", "pt", "it", "tr"]
    speech_lang = st.selectbox("Language", lang_options, index=0)

    st.markdown("### Speech-to-Text")
    uploaded_audio = st.file_uploader("Upload audio for transcription", type=["wav", "mp3", "m4a", "flac"])
    stt_col1, stt_col2 = st.columns([1, 3])
    with stt_col1:
        stt_clicked = st.button("Transcribe Audio", use_container_width=True)
    with stt_col2:
        if not speech_status.ready_for_stt:
            st.warning("STT dependencies missing. Install: pip install funasr")

    if stt_clicked:
        if not uploaded_audio:
            st.warning("Please upload an audio file first.")
        else:
            tmp_path = Path("outputs") / f"stt-input-{uploaded_audio.name}"
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_bytes(uploaded_audio.read())
            with st.spinner("Transcribing audio..."):
                try:
                    stt_result = speech_service.transcribe(str(tmp_path), language=speech_lang)
                    st.session_state["last_transcript"] = stt_result["transcript"]
                except SpeechServiceError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Unexpected STT error: {exc}")
                else:
                    st.success("Transcription complete.")
                    st.text_area("Transcript", value=stt_result["transcript"], height=120)
                    st.json({"language": stt_result["language"], "model": stt_result["model"]})

    st.markdown("### Text-to-Speech")
    tts_text = st.text_area(
        "Text to synthesize",
        value=st.session_state.get("last_transcript")
        or "Hello. This is a multilingual speech synthesis demo using VoxCPM.",
        height=120,
    )
    control_instruction = st.text_input(
        "Voice control instruction (optional)",
        value="Warm and professional voice, medium pace.",
    )

    tts_col1, tts_col2 = st.columns([1, 3])
    with tts_col1:
        tts_clicked = st.button("Generate Speech", type="primary", use_container_width=True)
    with tts_col2:
        if not speech_status.ready_for_tts:
            st.warning(
                "TTS dependencies missing. Install: pip install soundfile && pip install git+https://github.com/OpenBMB/VoxCPM.git"
            )

    if tts_clicked:
        with st.spinner("Synthesizing speech..."):
            try:
                tts_result = speech_service.synthesize(
                    text=tts_text,
                    language=speech_lang,
                    control_instruction=control_instruction,
                )
            except SpeechServiceError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Unexpected TTS error: {exc}")
            else:
                out_audio_path = Path(tts_result["audio_path"])
                audio_bytes = out_audio_path.read_bytes()
                st.success("Speech generated successfully.")
                st.audio(audio_bytes, format="audio/wav")
                st.download_button(
                    label="Download WAV",
                    data=audio_bytes,
                    file_name=out_audio_path.name,
                    mime="audio/wav",
                )
                st.json(
                    {
                        "audio_path": tts_result["audio_path"],
                        "sample_rate": tts_result["sample_rate"],
                        "duration_seconds": round(tts_result["duration_seconds"], 2),
                        "language": tts_result["language"],
                        "model": tts_result["model"],
                    }
                )

with tab_artifacts:
    st.subheader("Saved Artifacts")
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    recent_outputs = sorted(output_dir.glob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True)[:10]
    speech_dir = output_dir / "speech"
    speech_dir.mkdir(parents=True, exist_ok=True)
    speech_outputs = sorted(speech_dir.glob("*.wav"), key=lambda item: item.stat().st_mtime, reverse=True)[:10]

    st.markdown("### Latest Markdown Outputs")
    if not recent_outputs:
        st.info("No markdown outputs found yet.")
    else:
        for file_path in recent_outputs:
            st.write(str(file_path))

    st.markdown("### Latest Speech Outputs")
    if not speech_outputs:
        st.info("No speech artifacts found yet.")
    else:
        for wav_file in speech_outputs:
            st.write(str(wav_file))

    st.markdown("### Last Run Log Record")
    log_path = output_dir / "agent_logs.jsonl"
    if log_path.exists():
        lines = log_path.read_text(encoding="utf-8").splitlines()
        if lines:
            try:
                st.json(json.loads(lines[-1]))
            except Exception:
                st.code(lines[-1])
        else:
            st.info("Run log is empty.")
    else:
        st.info("Run log not found yet.")

    st.markdown("### Latest Workspace Smoke Test")
    smoke_test_result = st.session_state.get("smoke_test_result")
    smoke_test_path = Path("docs/snapshots/09_ui_smoke_test.json")
    if smoke_test_result is None and smoke_test_path.exists():
        try:
            smoke_test_result = json.loads(smoke_test_path.read_text(encoding="utf-8"))
        except Exception:
            smoke_test_result = None

    if smoke_test_result is None:
        st.info("No UI-triggered smoke test snapshot found yet.")
    else:
        st.json(smoke_test_result)

st.divider()
st.caption("Tip: keep Ollama running with `ollama serve`. For speech support, install VoxCPM + FunASR dependencies.")
