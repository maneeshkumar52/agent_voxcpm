"""Speech services for multilingual STT and TTS.

This module integrates:
- VoxCPM TTS for multilingual text-to-speech generation.
- FunASR (SenseVoice) STT for multilingual audio transcription.

Both integrations are lazy-loaded to keep startup lightweight and to allow
running the app even when speech dependencies are not installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from utils import ensure_directories, slugify, utc_timestamp


class SpeechServiceError(RuntimeError):
    """Raised when speech generation or transcription fails."""


@dataclass
class DependencyStatus:
    """Availability details for optional speech dependencies."""

    voxcpm_available: bool
    funasr_available: bool
    soundfile_available: bool

    @property
    def ready_for_tts(self) -> bool:
        return self.voxcpm_available and self.soundfile_available

    @property
    def ready_for_stt(self) -> bool:
        return self.funasr_available


class VoxSpeechService:
    """Handles optional VoxCPM TTS and FunASR STT capabilities."""

    def __init__(self, config: Dict[str, Any]) -> None:
        speech_config = config.get("speech", {})

        self.enabled = bool(speech_config.get("enabled", True))
        self.tts_enabled = bool(speech_config.get("enable_tts", True))
        self.stt_enabled = bool(speech_config.get("enable_stt", True))

        self.voxcpm_model_id = str(speech_config.get("voxcpm_model_id", "openbmb/VoxCPM2"))
        self.asr_model_id = str(speech_config.get("asr_model_id", "iic/SenseVoiceSmall"))
        self.speech_output_dir = Path(speech_config.get("speech_output_dir", "outputs/speech"))

        self.default_language = str(speech_config.get("default_language", "auto"))
        self.tts_cfg_value = float(speech_config.get("tts_cfg_value", 2.0))
        self.tts_inference_timesteps = int(speech_config.get("tts_inference_timesteps", 10))

        self._voxcpm_model: Any = None
        self._asr_model: Any = None

        ensure_directories([self.speech_output_dir])

    def dependency_status(self) -> DependencyStatus:
        """Return dependency readiness for TTS and STT."""

        voxcpm_available = self._module_available("voxcpm")
        funasr_available = self._module_available("funasr")
        soundfile_available = self._module_available("soundfile")

        return DependencyStatus(
            voxcpm_available=voxcpm_available,
            funasr_available=funasr_available,
            soundfile_available=soundfile_available,
        )

    @staticmethod
    def _module_available(module_name: str) -> bool:
        try:
            __import__(module_name)
            return True
        except Exception:
            return False

    def _get_voxcpm_model(self) -> Any:
        if self._voxcpm_model is not None:
            return self._voxcpm_model

        if not self._module_available("voxcpm"):
            raise SpeechServiceError(
                "VoxCPM is not installed. Install with: pip install git+https://github.com/OpenBMB/VoxCPM.git"
            )

        from voxcpm import VoxCPM  # type: ignore

        try:
            self._voxcpm_model = VoxCPM.from_pretrained(self.voxcpm_model_id, load_denoiser=False)
        except Exception as exc:
            raise SpeechServiceError(
                f"Failed to load VoxCPM model '{self.voxcpm_model_id}'."
            ) from exc

        return self._voxcpm_model

    def _get_asr_model(self) -> Any:
        if self._asr_model is not None:
            return self._asr_model

        if not self._module_available("funasr"):
            raise SpeechServiceError(
                "FunASR is not installed. Install with: pip install funasr"
            )

        try:
            from funasr import AutoModel  # type: ignore

            self._asr_model = AutoModel(
                model=self.asr_model_id,
                disable_update=True,
                log_level="ERROR",
            )
        except Exception as exc:
            raise SpeechServiceError(
                f"Failed to initialize FunASR model '{self.asr_model_id}'."
            ) from exc

        return self._asr_model

    def synthesize(
        self,
        text: str,
        language: str = "auto",
        control_instruction: str = "",
        prompt_wav_path: Optional[str] = None,
        prompt_text: str = "",
    ) -> Dict[str, Any]:
        """Generate speech from text using VoxCPM and return output metadata."""

        if not self.enabled or not self.tts_enabled:
            raise SpeechServiceError("TTS is disabled in config.")

        clean_text = text.strip()
        if not clean_text:
            raise SpeechServiceError("Text input is empty for TTS.")

        model = self._get_voxcpm_model()

        # VoxCPM supports multilingual text directly; language is informational in metadata.
        final_text = clean_text
        control_instruction = control_instruction.strip()
        if control_instruction:
            final_text = f"({control_instruction}){clean_text}"

        prompt_wav_path = prompt_wav_path or None
        clean_prompt_text = prompt_text.strip() or None

        try:
            audio_np = model.generate(
                text=final_text,
                prompt_wav_path=prompt_wav_path,
                prompt_text=clean_prompt_text,
                cfg_value=self.tts_cfg_value,
                inference_timesteps=self.tts_inference_timesteps,
                normalize=False,
                denoise=False,
            )
        except Exception as exc:
            raise SpeechServiceError("VoxCPM TTS generation failed.") from exc

        if not isinstance(audio_np, np.ndarray):
            audio_np = np.array(audio_np, dtype=np.float32)

        try:
            import soundfile as sf  # type: ignore
        except Exception as exc:
            raise SpeechServiceError("soundfile is required to persist generated audio.") from exc

        sample_rate = int(getattr(model.tts_model, "sample_rate", 48000))
        file_name = f"tts-{slugify(clean_text, max_len=50)}-{utc_timestamp()}.wav"
        out_path = self.speech_output_dir / file_name

        sf.write(str(out_path), audio_np, sample_rate)

        duration_seconds = float(len(audio_np) / sample_rate) if sample_rate > 0 else 0.0

        return {
            "audio_path": str(out_path),
            "sample_rate": sample_rate,
            "duration_seconds": duration_seconds,
            "language": language,
            "model": self.voxcpm_model_id,
        }

    def transcribe(self, audio_path: str, language: str = "auto") -> Dict[str, Any]:
        """Transcribe speech audio using FunASR SenseVoice."""

        if not self.enabled or not self.stt_enabled:
            raise SpeechServiceError("STT is disabled in config.")

        path = Path(audio_path)
        if not path.exists():
            raise SpeechServiceError(f"Audio file does not exist: {audio_path}")

        model = self._get_asr_model()
        try:
            result = model.generate(input=str(path), language=language, use_itn=True)
        except Exception as exc:
            raise SpeechServiceError(f"FunASR transcription failed: {exc}") from exc

        transcript = ""
        if isinstance(result, list) and result:
            first = result[0]
            if isinstance(first, dict):
                transcript = str(first.get("text", "")).strip()

        if "|>" in transcript:
            transcript = transcript.split("|>")[-1].strip()

        return {
            "transcript": transcript,
            "language": language,
            "model": self.asr_model_id,
            "raw": result,
        }
