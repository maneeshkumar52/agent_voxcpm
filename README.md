# VoxCPM + Ollama Multi-Agent Wiki Orchestrator

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-black.svg)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#license)

Production-ready multi-agent system that runs locally with Ollama models and orchestrates specialized agents through a VoxCPM-compatible orchestration layer.

## Table of Contents

- [Overview](#overview)
- [Business Use Case](#business-use-case)
- [Core Capabilities](#core-capabilities)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quickstart](#quickstart)
- [Functional Flows (Post Setup)](#functional-flows-post-setup)
- [Execution Snapshots](#execution-snapshots)
- [Configuration](#configuration)
- [Operational Notes](#operational-notes)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [License](#license)

## Overview

This solution demonstrates a practical AI collaboration workflow where four specialized agents cooperate to produce high-quality wiki content from a single user prompt.

Agents and responsibilities:

- Researcher: collects and structures evidence from local docs and optional API context.
- Summarizer: compresses research into concise, high-signal synthesis.
- Planner: converts synthesis into an actionable content structure.
- Communicator: composes polished final markdown output for delivery.

The implementation is designed for local-first execution, reproducibility, and production-readiness:

- Config-driven behavior (models, temperatures, storage paths)
- Deterministic orchestration handoffs
- Durable run logs and output artifacts
- Dockerized deployment path

## Business Use Case

Enable knowledge teams, architects, and analysts to turn raw prompts into structured wiki artifacts with transparent multi-agent traceability.

Example prompt:

Create a wiki page on renewable energy with key technologies, grid challenges, policy trends, and future outlook.

## Core Capabilities

- Local LLM execution with Ollama (`llama3`, `mistral`, `gemma3:4b`)
- VoxCPM-compatible orchestration with local fallback
- Streamlit UI for interactive orchestration and trace visualization
- Timestamped markdown output generation
- JSONL audit logs for every run
- Sample tasks for quick demo and onboarding

## Architecture

```text
User Input (Streamlit)
        |
        v
VoxCPM Orchestrator (or local fallback)
        |
        +--> Researcher --> Summarizer --> Planner --> Communicator
                                                      |
                                                      +--> Final Wiki Markdown
                                                              |
                                                              +--> outputs/*.md
                                                              +--> outputs/agent_logs.jsonl
        |
        v
Ollama Local Models (llama3 / mistral / gemma3:4b)
```

## Project Structure

```text
agent_voxcpm/
├── app.py
├── orchestrator.py
├── ollama_client.py
├── utils.py
├── config.yaml
├── requirements.txt
├── Dockerfile
├── README.md
├── agents/
│   ├── researcher.py
│   ├── summarizer.py
│   ├── planner.py
│   └── communicator.py
├── sample_tasks/
│   ├── renewable_energy.txt
│   └── company_strategy.md
├── outputs/
└── docs/
    └── snapshots/
```

## Quickstart

### Prerequisites

1. Python 3.11+
2. Ollama installed locally
3. Models available locally (`llama3`, `mistral`, `gemma3:4b`)
4. Optional VoxCPM installation from source

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install git+https://github.com/OpenBMB/VoxCPM.git
ollama serve
ollama pull llama3
ollama pull mistral
ollama pull gemma3:4b
streamlit run app.py
```

### Programmatic Run

```bash
python - <<'PY'
from orchestrator import VoxCPMOrchestrator

task = "Create a professional wiki page on renewable energy covering technologies, grid challenges, policy trends, and outlook to 2035."
result = VoxCPMOrchestrator("config.yaml").run(task)
print("BACKEND:", result.backend)
print("OUTPUT:", result.output_file)
print("MESSAGES:", len(result.messages))
PY
```

## Functional Flows (Post Setup)

### Flow A: Interactive Streamlit Flow

1. User enters task in UI.
2. Orchestrator forwards prompt to Researcher.
3. Researcher sends notes to Summarizer.
4. Summarizer sends synthesis to Planner.
5. Planner sends structured plan to Communicator.
6. Communicator returns final wiki markdown.
7. UI renders full trace and output.
8. System persists markdown and JSONL log.

### Flow B: Headless Orchestrator Flow

1. Instantiate orchestrator from `config.yaml`.
2. Resolve backend mode (`voxcpm` or `local-fallback`).
3. Execute deterministic handoff chain.
4. Save timestamped markdown to `outputs/`.
5. Append full run trace to `outputs/agent_logs.jsonl`.

## Execution Snapshots

The following artifacts were captured from live execution on April 18, 2026.

### Snapshot Index

- Ollama model inventory: [docs/snapshots/01_ollama_tags.json](docs/snapshots/01_ollama_tags.json)
- Python compile validation: [docs/snapshots/02_compileall.txt](docs/snapshots/02_compileall.txt)
- E2E run summary: [docs/snapshots/03_e2e_run_summary.json](docs/snapshots/03_e2e_run_summary.json)
- Final output preview: [docs/snapshots/04_e2e_output_preview.md](docs/snapshots/04_e2e_output_preview.md)
- Streamlit startup snapshot: [docs/snapshots/05_streamlit_startup.txt](docs/snapshots/05_streamlit_startup.txt)
- Latest agent log record: [docs/snapshots/06_agent_log_last_run.json](docs/snapshots/06_agent_log_last_run.json)
- Streamlit UI screenshot: [docs/snapshots/07_streamlit_ui.png](docs/snapshots/07_streamlit_ui.png)

### UI Snapshot

![Streamlit Multi-Agent UI](docs/snapshots/07_streamlit_ui.png)

### Validation Checklist

1. `curl http://localhost:11434/api/tags` returns installed models.
2. `python -m compileall .` completes without syntax errors.
3. `streamlit run app.py` starts and exposes local URL.
4. One task run generates markdown output and JSONL run log.
5. Agent trace order appears as User -> Researcher -> Summarizer -> Planner -> Communicator -> User.

## Configuration

All runtime controls are centralized in `config.yaml`:

- Ollama endpoint and timeout
- Per-agent model assignment
- Per-agent temperature and system prompt
- Output and logging storage paths

## Operational Notes

### Reliability

- VoxCPM package is auto-detected at runtime.
- If unavailable, execution falls back to local orchestration.
- Every run is auditable through JSONL logs.

### Docker

```bash
docker build -t voxcpm-multi-agent .
docker run --rm -p 8501:8501 -v "$(pwd)/outputs:/app/outputs" voxcpm-multi-agent
```

Note: Ensure Ollama is reachable from container networking.

### Security

- Keep local deployment in trusted network boundaries.
- Avoid passing secrets in prompts or local source docs.
- Add authentication before public exposure of Streamlit.

## Troubleshooting

### Ollama Unreachable

- Start service with `ollama serve`
- Verify endpoint in `config.yaml`
- Check tags endpoint with `curl http://localhost:11434/api/tags`

### Missing Models

- Pull required models via `ollama pull <model>`
- Ensure names match `config.yaml`

### VoxCPM Missing

- Install from source: `pip install git+https://github.com/OpenBMB/VoxCPM.git`
- Confirm backend mode in run metadata

## Roadmap

1. Parallel branch orchestration for higher throughput
2. Evaluation metrics and quality scoring per run
3. Human approval gates before final publish
4. Optional vector retrieval for larger corpora

## License

MIT
