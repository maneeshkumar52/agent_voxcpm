# VoxCPM + Ollama Multi-Agent and Speech Workspace

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-black.svg)](https://ollama.com/)
[![VoxCPM](https://img.shields.io/badge/Speech-VoxCPM%20%2B%20FunASR-teal.svg)](https://github.com/OpenBMB/VoxCPM)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Production-ready local AI system where specialized agents collaborate on knowledge tasks and speech workflows. The project now includes:

- Multi-agent orchestration for content generation
- VoxCPM multilingual TTS
- FunASR (SenseVoice) multilingual STT
- Streamlit production-style workspace with command center, orchestration studio, speech lab, and operations console

## Table of Contents

- [What Is Included](#what-is-included)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Run](#run)
- [Step-by-Step Walkthrough](#step-by-step-walkthrough)
  - [Walkthrough 1 — Environment Setup](#walkthrough-1--environment-setup-and-readiness-check)
  - [Walkthrough 2 — Command Center](#walkthrough-2--command-center-workspace-overview)
  - [Walkthrough 3 — Agent Studio](#walkthrough-3--agent-studio-multi-agent-wiki-generation)
  - [Walkthrough 4 — Speech Lab](#walkthrough-4--speech-lab-multilingual-tts-and-stt)
  - [Walkthrough 5 — Operations and Snapshots](#walkthrough-5--operations-and-snapshots-artifact-inspection)
  - [Walkthrough 6 — Smoke Test and E2E Validation](#walkthrough-6--one-click-smoke-test-and-e2e-validation)
  - [Walkthrough 7 — Sidebar Features](#walkthrough-7--sidebar-features)
  - [Quick Reference: UI at a Glance](#quick-reference-ui-at-a-glance)
  - [Snapshot Index](#snapshot-index)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [License](#license)

## What Is Included

### Multi-Agent Pipeline

- Researcher gathers context from local docs and external context hooks.
- Summarizer condenses findings into concise insights.
- Planner structures output into actionable sections.
- Communicator produces final wiki-ready markdown.

### Speech Capabilities

- TTS: VoxCPM model (`openbmb/VoxCPM2`) for multilingual speech generation.
- STT: FunASR SenseVoice (`iic/SenseVoiceSmall`) for multilingual transcription.
- Speech output persistence in `outputs/speech/*.wav`.

## Architecture

```text
User (Streamlit Workspace)
        |
        +--> Multi-Agent Orchestrator
        |       |
        |       +--> Researcher -> Summarizer -> Planner -> Communicator -> Markdown Output
        |                                                   |
        |                                                   +--> outputs/*.md
        |                                                   +--> outputs/agent_logs.jsonl
        |
        +--> Speech Studio
                |
                +--> VoxCPM TTS (text -> wav)
                +--> FunASR STT (audio -> text)
                |
                +--> outputs/speech/*.wav

Backends:
- Ollama for agent reasoning models
- VoxCPM for multilingual TTS
- FunASR SenseVoice for multilingual STT
```

## Project Structure

```text
agent_voxcpm/
├── app.py
├── orchestrator.py
├── speech.py
├── ollama_client.py
├── utils.py
├── config.yaml
├── requirements.txt
├── Dockerfile
├── README.md
├── scripts/
│   └── e2e_validate.py
├── agents/
│   ├── researcher.py
│   ├── summarizer.py
│   ├── planner.py
│   └── communicator.py
├── sample_tasks/
├── outputs/
└── docs/
    └── snapshots/
```

## Setup

### Prerequisites

| Requirement | macOS | Windows |
|-------------|-------|---------|
| Python | 3.11+ ([python.org](https://www.python.org/) or `brew install python@3.11`) | 3.11+ ([python.org](https://www.python.org/) — check *Add to PATH* during install) |
| Ollama | [ollama.com](https://ollama.com/) or `brew install ollama` | [ollama.com](https://ollama.com/) (Windows installer) |
| ffmpeg | `brew install ffmpeg` | `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH |
| Git | Pre-installed or `brew install git` | [git-scm.com](https://git-scm.com/download/win) |

### Install

#### macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install git+https://github.com/OpenBMB/VoxCPM.git
brew install ffmpeg
```

#### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install git+https://github.com/OpenBMB/VoxCPM.git
winget install ffmpeg
```

> **Note:** On Windows, if `winget` is unavailable, download ffmpeg from [ffmpeg.org](https://ffmpeg.org/download.html), extract, and add the `bin` folder to your system PATH.

#### Platform-Specific Notes

| Difference | macOS | Windows |
|------------|-------|---------|
| Virtual env activation | `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` (PowerShell) or `.venv\Scripts\activate.bat` (CMD) |
| ffmpeg install | `brew install ffmpeg` | `winget install ffmpeg` or manual download |
| VoxCPM / PyTorch | Works out of the box on Apple Silicon (MPS) and Intel | CPU-only by default; for GPU add `--index-url https://download.pytorch.org/whl/cu121` when installing torch |
| soundfile backend | Uses system libsndfile (installed with Homebrew) | Bundled with the `soundfile` pip package — no extra step |
| Ollama | `brew install ollama` or download from website | Windows installer from [ollama.com](https://ollama.com/) |

### Ollama Models

```bash
ollama serve
ollama pull llama3
ollama pull mistral
ollama pull gemma3:4b
```

## Run

### Streamlit Workspace

```bash
streamlit run app.py
```

After launch:

1. Start in `Command Center` for readiness and quick actions.
2. Use `Agent Studio` for authoring tasks and reviewing handoff traces.
3. Use `Speech Lab` for STT, TTS, and optional prompt-audio voice conditioning.
4. Use `Operations and Snapshots` to inspect outputs, logs, and saved evidence.
5. Use sidebar `Run full workspace smoke test` to execute full orchestrator + STT/TTS verification from the UI.

### Programmatic E2E Validation

```bash
python scripts/e2e_validate.py --speech-text "Hello world. This is VoxCPM multilingual speech verification." --language auto
```

## Step-by-Step Walkthrough

Follow each walkthrough below in order. Every step includes a brief note explaining what is happening and a snapshot so you can verify you see the same result.

---

### Walkthrough 1 — Environment Setup and Readiness Check

Before using the workspace you need Ollama models pulled and the codebase validated.

**Step 1: Pull Ollama models and verify the inventory.**

```bash
ollama serve
ollama pull llama3 && ollama pull mistral && ollama pull gemma3:4b
curl http://localhost:11434/api/tags
```

> **What happens:** Ollama downloads each model. The `api/tags` call returns a JSON inventory of all locally available models. The workspace uses `llama3` (researcher and communicator), `mistral` (summarizer), and `gemma3:4b` (planner).

<details>
<summary>Snapshot — Ollama model inventory</summary>

See [docs/snapshots/01_ollama_tags.json](docs/snapshots/01_ollama_tags.json) for the full JSON output listing every pulled model, its size, and digest.
</details>

**Step 2: Compile-check the entire codebase.**

```bash
python -m compileall . -q
```

> **What happens:** Python byte-compiles every `.py` file in the project. A clean run means zero syntax errors across `app.py`, `orchestrator.py`, `speech.py`, `smoke_test.py`, and all agent modules.

<details>
<summary>Snapshot — Compile validation</summary>

See [docs/snapshots/02_compileall.txt](docs/snapshots/02_compileall.txt) for the compile output confirming zero errors.
</details>

**Step 3: Launch the Streamlit workspace.**

```bash
streamlit run app.py
```

> **What happens:** Streamlit starts a local server (default port 8501). The terminal shows the local and network URLs. Open the browser link and you land on the production-style hero banner with four metric cards and four tabs.

<details>
<summary>Snapshot — Streamlit startup log</summary>

See [docs/snapshots/05_streamlit_startup.txt](docs/snapshots/05_streamlit_startup.txt) for the terminal output showing the Streamlit process starting and the available URLs.
</details>

---

### Walkthrough 2 — Command Center: Workspace Overview

The first thing you see after launching is the **Command Center** tab. This is the operational dashboard for the entire workspace.

**Step 1: Review the hero banner.**

> **What you see:** A dark gradient banner at the top shows the active planner model, speech readiness status (TTS/STT ready or partial), and artifact counts (markdown files, audio files, snapshots). These update live as you use the workspace.

**Step 2: Check the four metric cards.**

> **What you see:** Four cards below the banner show: (1) Agent backend — the LLM backend powering orchestration, (2) Run history — count of recent workflow executions, (3) Speech assets — number of generated WAV files, (4) Snapshots — total validation evidence files.

**Step 3: Review the capability matrix (right column).**

> **What you see:** Four status chips showing readiness for Orchestration, TTS, STT, and Smoke Test. Green = ready, amber = blocked or missing a dependency. This tells you at a glance which features will work.

**Step 4: Use the cross-workflow shortcuts (left column).**

> **What they do:** Four shortcut buttons let you move data between tabs without switching manually:
> - *Use transcript as task* — takes STT output and loads it into the Agent Studio task composer.
> - *Send final output to speech* — takes the latest orchestrator markdown and loads it into the Speech Lab text area.
> - *Load latest markdown into task* — reads the most recent saved `.md` file from `outputs/` into the task composer.
> - *Load transcript into speech* — copies a transcript directly into the TTS text area.

**Step 5: View the latest validation snapshot (right column).**

> **What you see:** If you have run a smoke test before, the full JSON result appears here. If not, a blue info box prompts you to run one.

![Command Center — full view](docs/snapshots/10_ui_command_center.png)

---

### Walkthrough 3 — Agent Studio: Multi-Agent Wiki Generation

This is the core content generation flow. Four specialized agents collaborate in a chain to produce a wiki-quality document from a single task prompt.

**Step 1: Navigate to the Agent Studio tab.**

> **What you see:** A two-column layout with the task composer on the left and the delivery panel on the right.

**Step 2: Enter a task (or load a preset).**

Type a task in the text area, for example:

```
Create a wiki page on renewable energy with key technologies and future outlook.
```

Alternatively, use the sidebar **Task Presets** dropdown to load a sample task file, then click *Load selected preset*.

> **Note:** Task presets are plain-text files in the `sample_tasks/` directory. You can add your own `.txt` or `.md` files there.

**Step 3: Click "Run multi-agent workflow".**

> **What happens internally:**
> 1. **Researcher** sends the task to `llama3` and gathers context.
> 2. **Summarizer** receives the researcher's output and condenses it using `mistral`.
> 3. **Planner** structures the condensed output into sections using `gemma3:4b`.
> 4. **Communicator** produces the final wiki-ready markdown using `llama3`.
>
> Each handoff is logged to `outputs/agent_logs.jsonl` with timestamps, model names, and token metadata.

**Step 4: Review the delivery panel (right column).**

> **What you see:**
> - **Metric cards** showing the backend used, message count, word count, and estimated reading time.
> - **Final markdown** rendered in a scrollable container with a download button.
> - **Agent handoff trace** — expand each agent's section to see its raw input/output and the model that produced it.

**Step 5: Inspect the run in the history panel.**

> **What you see:** Below the task composer, a *Run history* selectbox lists recent executions in reverse chronological order. Selecting one shows its full metadata as JSON (task, backend, timestamp, agent chain).

![Agent Studio — task composer and delivery panel](docs/snapshots/11_ui_agent_studio.png)

<details>
<summary>Snapshot — Orchestrator run summary (JSON)</summary>

See [docs/snapshots/03_e2e_run_summary.json](docs/snapshots/03_e2e_run_summary.json) for a full run summary showing backend, message count, word count, and timing.
</details>

<details>
<summary>Snapshot — Output preview (Markdown)</summary>

See [docs/snapshots/04_e2e_output_preview.md](docs/snapshots/04_e2e_output_preview.md) for the raw markdown output generated by the communicator agent.
</details>

<details>
<summary>Snapshot — Agent log sample (JSONL entry)</summary>

See [docs/snapshots/06_agent_log_last_run.json](docs/snapshots/06_agent_log_last_run.json) for a single JSONL log entry showing agent name, model, timestamp, and output excerpt.
</details>

---

### Walkthrough 4 — Speech Lab: Multilingual TTS and STT

The Speech Lab combines text-to-speech (VoxCPM) and speech-to-text (FunASR SenseVoice) with voice presets and optional prompt-audio conditioning.

#### Part A: Speech-to-Text (STT)

**Step 1: Navigate to the Speech Lab tab.**

> **What you see:** Two side-by-side sections — STT on the left and TTS on the right.

**Step 2: Upload an audio file for transcription.**

Click the file uploader and select a `.wav`, `.mp3`, or `.flac` file.

**Step 3: Select the source language.**

Choose from 14 supported languages (auto, en, zh, es, fr, de, hi, ja, ko, ar, ru, pt, it, tr). Select `auto` to let SenseVoice detect the language automatically.

**Step 4: Click "Transcribe".**

> **What happens:** FunASR's SenseVoice model processes the audio and returns a transcript. The transcript appears in the UI and is stored in session state so you can reuse it later via the cross-workflow shortcuts (e.g., *Use transcript as task* from the Command Center).

#### Part B: Text-to-Speech (TTS)

**Step 5: Choose a voice preset.**

Five presets are available:

| Preset | Voice character |
|--------|----------------|
| Studio Neutral | Clear, neutral, production-ready narration |
| Executive Brief | Confident executive presentation voice |
| Customer Success | Warm, reassuring, service-oriented voice |
| Explainer | Energetic explainer with crisp emphasis |
| Custom | Enter your own voice direction text |

> **Note:** The preset fills in the *Voice direction / control instruction* field. You can edit it freely after selecting a preset.

**Step 6: Enter or edit the text to synthesize.**

Type text in the TTS text area, or use the shortcut *Send final output to speech* from the Command Center to auto-populate it with the latest orchestrator output.

**Step 7 (optional): Add prompt-audio conditioning.**

Expand the *Prompt audio conditioning* section.

- Upload a short reference WAV file (the "voice sample").
- Enter the transcript of that reference audio.

> **What happens:** VoxCPM uses the reference audio + transcript to condition its output voice, producing speech that sounds closer to the reference speaker. This is useful for voice cloning or maintaining a consistent narrator voice across outputs.

**Step 8: Click "Generate speech".**

> **What happens:** VoxCPM synthesizes a WAV file at 48kHz. The audio player appears in the UI for immediate playback. The file is saved to `outputs/speech/` and can also be downloaded.

**Step 9: Try "Read latest final output".**

> **What it does:** This button takes the most recent orchestrator output and feeds it directly into VoxCPM TTS — a one-click way to generate a spoken version of any wiki page the agents produced.

![Speech Lab — STT and TTS with voice presets](docs/snapshots/12_ui_speech_lab.png)

---

### Walkthrough 5 — Operations and Snapshots: Artifact Inspection

This tab is the evidence and audit trail for everything the workspace produces.

**Step 1: Navigate to the Operations and Snapshots tab.**

> **What you see:** Four sections — artifact browser, log record inspector, snapshot center, and workspace summary.

**Step 2: Browse generated artifacts.**

- **Markdown outputs:** Select any `.md` file from the dropdown to preview the content inline.
- **Speech outputs:** Select any `.wav` file to play it directly in the browser.

> **Note:** Files are sorted newest-first. Each artifact shows the filename and timestamp.

**Step 3: Inspect run history logs.**

Select a log entry from the dropdown. The full JSONL record is displayed as formatted JSON, including agent name, model, timestamp, input excerpt, output excerpt, and token metadata.

> **Note:** This is the same data shown in the Agent Studio run history, but here you can browse all entries without running a new workflow.

**Step 4: Browse the snapshot center.**

All files in `docs/snapshots/` are listed. Selecting one renders it inline:
- `.png` images are displayed as images.
- `.json` files are displayed as formatted JSON.
- `.md` and `.txt` files are displayed as text.

> **Note:** This is where you can verify every validation artifact referenced in this README without leaving the UI.

**Step 5: Review the workspace summary.**

A JSON block at the bottom shows the current workspace state: counts of markdown outputs, speech outputs, snapshots, and recent history entries.

![Operations and Snapshots — artifact browser and snapshot center](docs/snapshots/13_ui_operations_snapshots.png)

---

### Walkthrough 6 — One-Click Smoke Test and E2E Validation

The smoke test runs the entire pipeline (orchestrator + TTS + STT) in one click and produces a validation artifact that proves all features are working.

#### Option A: UI-triggered smoke test

**Step 1: Click "Run full workspace smoke test" in the sidebar.**

> **What happens under the hood:**
> 1. The orchestrator runs a fixed validation task ("Create a concise wiki page on renewable energy in 5 sections").
> 2. VoxCPM generates speech from a test sentence ("Hello world. This is VoxCPM multilingual speech verification.").
> 3. FunASR transcribes the generated WAV back to text.
> 4. The results (backend used, message count, TTS status, STT status, sample rate, duration, transcript) are saved to `docs/snapshots/09_ui_smoke_test.json`.

**Step 2: View results in the Command Center.**

> **What you see:** The *Latest Validation Snapshot* card in the Command Center right column now shows the full smoke test JSON. The metric cards at the top also update to reflect the new run.

<details>
<summary>Snapshot — UI-triggered smoke test result</summary>

See [docs/snapshots/09_ui_smoke_test.json](docs/snapshots/09_ui_smoke_test.json) for the JSON output produced by clicking the sidebar button.
</details>

#### Option B: Programmatic E2E validation (CLI)

**Step 3 (alternative): Run the validation script from the terminal.**

```bash
python scripts/e2e_validate.py \
  --speech-text "Hello world. This is VoxCPM multilingual speech verification." \
  --language auto
```

> **What happens:** The script runs the same three-phase validation (orchestrate → TTS → STT) and writes the result to `docs/snapshots/`.

<details>
<summary>Snapshot — CLI e2e speech validation</summary>

See [docs/snapshots/08_e2e_speech_validation.json](docs/snapshots/08_e2e_speech_validation.json) for the script-generated validation summary.
</details>

<details>
<summary>Snapshot — Upgraded workspace e2e validation</summary>

See [docs/snapshots/14_e2e_workspace_validation.json](docs/snapshots/14_e2e_workspace_validation.json) for the latest end-to-end validation confirming orchestrator backend `voxcpm`, TTS `ok` (48kHz WAV), and STT `ok`.
</details>

---

### Walkthrough 7 — Sidebar Features

The sidebar is always visible and provides quick access to workspace-wide actions.

| Feature | What it does |
|---------|-------------|
| **Task Presets** | Dropdown to load sample tasks from `sample_tasks/` into the Agent Studio composer. |
| **Workspace Readiness** | Three status chips showing whether VoxCPM, FunASR, and soundfile are installed and importable. |
| **One-Click Validation** | Runs the full smoke test (orchestrator + TTS + STT) and writes the result to `docs/snapshots/09_ui_smoke_test.json`. |

> **Tip:** Always run the smoke test before sharing results or updating the README. It refreshes the validation artifact and confirms all dependencies are working.

---

### Quick Reference: UI at a Glance

| Tab | Purpose | Key features |
|-----|---------|-------------|
| **Command Center** | Operational dashboard | Hero metrics, capability matrix, cross-workflow shortcuts, latest validation JSON |
| **Agent Studio** | Content generation | Task composer, run/reset, agent handoff trace, run history, markdown download |
| **Speech Lab** | TTS and STT | 5 voice presets, prompt-audio conditioning, 14 language support, one-click "read output" |
| **Operations and Snapshots** | Audit and evidence | Artifact browser (MD + WAV), log inspector, snapshot center, workspace summary |

---

### Snapshot Index

All evidence artifacts are stored in `docs/snapshots/`. Each is referenced inline in the walkthrough above.

| # | File | Description |
|---|------|-------------|
| 01 | [01_ollama_tags.json](docs/snapshots/01_ollama_tags.json) | Ollama model inventory |
| 02 | [02_compileall.txt](docs/snapshots/02_compileall.txt) | Python compile validation |
| 03 | [03_e2e_run_summary.json](docs/snapshots/03_e2e_run_summary.json) | Orchestrator run summary |
| 04 | [04_e2e_output_preview.md](docs/snapshots/04_e2e_output_preview.md) | Generated markdown output |
| 05 | [05_streamlit_startup.txt](docs/snapshots/05_streamlit_startup.txt) | Streamlit startup log |
| 06 | [06_agent_log_last_run.json](docs/snapshots/06_agent_log_last_run.json) | Agent log JSONL entry |
| 07 | [07_streamlit_ui.png](docs/snapshots/07_streamlit_ui.png) | Legacy UI (pre-redesign) |
| 08 | [08_e2e_speech_validation.json](docs/snapshots/08_e2e_speech_validation.json) | CLI e2e speech validation |
| 09 | [09_ui_smoke_test.json](docs/snapshots/09_ui_smoke_test.json) | UI-triggered smoke test |
| 10 | [10_ui_command_center.png](docs/snapshots/10_ui_command_center.png) | Command Center tab |
| 11 | [11_ui_agent_studio.png](docs/snapshots/11_ui_agent_studio.png) | Agent Studio tab |
| 12 | [12_ui_speech_lab.png](docs/snapshots/12_ui_speech_lab.png) | Speech Lab tab |
| 13 | [13_ui_operations_snapshots.png](docs/snapshots/13_ui_operations_snapshots.png) | Operations and Snapshots tab |
| 14 | [14_e2e_workspace_validation.json](docs/snapshots/14_e2e_workspace_validation.json) | Latest e2e workspace validation |
| 15 | [15_ui_sidebar.png](docs/snapshots/15_ui_sidebar.png) | Sidebar with workspace readiness and controls |

## Configuration

Main runtime settings are in `config.yaml`.

- `ollama`: local LLM endpoint and timeout
- `agents`: model, temperature, prompts per agent
- `storage`: markdown and log output locations
- `speech`:
  - `voxcpm_model_id`
  - `asr_model_id`
  - `speech_output_dir`
  - `enable_tts`, `enable_stt`
  - synthesis defaults (`tts_cfg_value`, `tts_inference_timesteps`)

## Troubleshooting

### STT fails with ffmpeg error

Install ffmpeg:

```bash
brew install ffmpeg
```

### VoxCPM model download is slow

Set `HF_TOKEN` for faster and higher-limit Hugging Face downloads.

### Backend shows `local-fallback`

Install VoxCPM package and restart run.

```bash
pip install git+https://github.com/OpenBMB/VoxCPM.git
```

### Ollama connection errors

```bash
ollama serve
curl http://localhost:11434/api/tags
```

## Roadmap

1. Parallel agent graph execution
2. Structured evaluation metrics per run
3. Human approval checkpoint before final publish
4. Optional RAG connector for larger corpora

## License

MIT (see [LICENSE](LICENSE)).
