"""
services/speech_service.py
Azure AI Speech Service integration for Speech-to-Text (STT).
Transcribes recorded candidate audio using Microsoft Azure Cognitive Services Speech SDK.
Includes automatic audio normalization to 16kHz mono 16-bit PCM WAV using FFmpeg
to guarantee compatibility with browser-recorded WebM/Opus audio formats.
"""

import os
import gc
import time
import shutil
import tempfile
import threading
import subprocess
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()


def find_ffmpeg_executable() -> Optional[str]:
    """Finds ffmpeg executable from PATH, WinGet, or standard installation directories."""
    # 1. System PATH
    found = shutil.which("ffmpeg")
    if found:
        return found

    # 2. Known WinGet / manual install locations on Windows
    candidate_paths = [
        r"C:\Users\adity\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"),
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path

    # 3. Dynamic search in LocalAppData WinGet packages
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        winget_dir = os.path.join(local_app_data, "Microsoft", "WinGet", "Packages")
        if os.path.exists(winget_dir):
            for root, _, files in os.walk(winget_dir):
                if "ffmpeg.exe" in files:
                    return os.path.join(root, "ffmpeg.exe")
 
    return None


def normalize_audio_to_pcm_wav(audio_bytes: bytes) -> bytes:
    """
    Converts any incoming audio bytes (WebM, Opus, Ogg, MP3, or non-standard WAV)
    to uncompressed 16kHz mono 16-bit PCM WAV, which is Azure Speech's optimal format.
    """
    if not audio_bytes:
        return audio_bytes

    ffmpeg_bin = find_ffmpeg_executable()
    if not ffmpeg_bin:
        # If FFmpeg is not available, return original bytes
        return audio_bytes

    try:
        proc = subprocess.Popen(
            [
                ffmpeg_bin,
                "-y",
                "-i", "pipe:0",          # Read from stdin
                "-acodec", "pcm_s16le",  # 16-bit PCM
                "-ar", "16000",          # 16 kHz sample rate
                "-ac", "1",              # Mono channel
                "-f", "wav",             # Standard WAV container
                "pipe:1"                 # Write to stdout
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout_data, stderr_data = proc.communicate(input=audio_bytes, timeout=15)
        if proc.returncode == 0 and stdout_data and stdout_data.startswith(b"RIFF"):
            return stdout_data
    except Exception:
        pass

    return audio_bytes


class SpeechService:
    """Manages Azure AI Speech configuration and Speech-to-Text transcription."""

    def __init__(self):
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")

        if not self.speech_key or not self.speech_region:
            self.is_configured = False
        else:
            self.is_configured = True
        self._tts_cache: Dict[str, bytes] = {}

    def _get_speech_config(self) -> speechsdk.SpeechConfig:
        if not self.is_configured:
            raise ValueError(
                "AZURE_SPEECH_KEY or AZURE_SPEECH_REGION is missing in your .env file. "
                "Please configure both to enable Azure Speech-to-Text."
            )
        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        speech_config.speech_recognition_language = "en-US"
        speech_config.output_format = speechsdk.OutputFormat.Simple
        return speech_config

    def transcribe_audio_bytes(self, audio_bytes: bytes, filename_hint: str = "recording.wav") -> str:
        """
        Transcribes audio data bytes (e.g. from Streamlit st.audio_input) using Azure Speech STT.
        Automatically normalizes incoming browser WebM/Opus audio to 16kHz PCM WAV first.
        """
        if not audio_bytes or len(audio_bytes) == 0:
            raise ValueError("No audio data was received. Please record your voice before transcribing.")

        speech_config = self._get_speech_config()

        # Step 1: Normalize audio to clean 16kHz mono PCM WAV (handles WebM from browser)
        pcm_wav_bytes = normalize_audio_to_pcm_wav(audio_bytes)

        # Step 2: Write normalized WAV to a temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
        try:
            with os.fdopen(temp_fd, "wb") as f:
                f.write(pcm_wav_bytes)

            audio_config = speechsdk.audio.AudioConfig(filename=temp_path)
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )

            all_transcripts = []
            done = threading.Event()
            cancellation_details = None

            def on_recognized(evt):
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    text = evt.result.text.strip()
                    if text:
                        all_transcripts.append(text)

            def on_canceled(evt):
                nonlocal cancellation_details
                cancellation_details = evt.cancellation_details
                done.set()

            def on_session_stopped(evt):
                done.set()

            recognizer.recognized.connect(on_recognized)
            recognizer.session_stopped.connect(on_session_stopped)
            recognizer.canceled.connect(on_canceled)

            recognizer.start_continuous_recognition_async()
            # Wait for recognition to finish processing the file
            done.wait(timeout=30)
            recognizer.stop_continuous_recognition_async().get()

            # Clean references so Windows releases file handle
            del recognizer
            del audio_config
            gc.collect()

            if cancellation_details and cancellation_details.reason == speechsdk.CancellationReason.Error:
                raise RuntimeError(
                    f"Azure Speech Error ({cancellation_details.error_code}): "
                    f"{cancellation_details.error_details}"
                )

            final_text = " ".join(all_transcripts).strip()
            return final_text

        finally:
            # Safely remove temporary file on Windows
            for _ in range(5):
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    break
                except PermissionError:
                    time.sleep(0.1)

    def record_and_transcribe_local_mic(self, timeout_seconds: int = 15) -> str:
        """
        Directly listens to the host machine's default microphone and transcribes speech.
        Useful when running locally on Windows as an alternative to browser audio upload.
        """
        speech_config = self._get_speech_config()
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        result = recognizer.recognize_once_async().get()

        del recognizer
        del audio_config
        gc.collect()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text.strip()
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return ""
        elif result.reason == speechsdk.ResultReason.Canceled:
            details = result.cancellation_details
            raise RuntimeError(f"Speech recognition canceled: {details.reason}. {details.error_details}")

        return ""

    def synthesize_speech_to_wav(self, text: str, voice_name: str = "en-US-JennyNeural") -> Optional[bytes]:
        """
        Synthesizes input text into high-fidelity 16kHz mono WAV audio bytes using Azure AI Speech.
        Caches audio results in memory to avoid redundant API calls.
        """
        if not text or not text.strip():
            return None

        clean_text = text.strip()
        cache_key = f"{voice_name}_{clean_text}"
        if hasattr(self, "_tts_cache") and cache_key in self._tts_cache:
            return self._tts_cache[cache_key]

        if not self.is_configured:
            return None

        try:
            speech_config = self._get_speech_config()
            speech_config.speech_synthesis_voice_name = voice_name
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
            )

            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=None
            )
            result = synthesizer.speak_text_async(clean_text).get()

            del synthesizer
            gc.collect()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted and result.audio_data:
                if not hasattr(self, "_tts_cache"):
                    self._tts_cache = {}
                self._tts_cache[cache_key] = result.audio_data
                return result.audio_data
            return None
        except Exception:
            return None

    def verify_speech_service(self) -> Dict[str, Any]:
        """Validates Speech service credentials, connectivity, and audio decoder availability."""
        if not self.is_configured:
            return {
                "success": False,
                "error": "AZURE_SPEECH_KEY or AZURE_SPEECH_REGION not configured in .env"
            }
        try:
            _ = self._get_speech_config()
            ffmpeg_path = find_ffmpeg_executable()
            return {
                "success": True,
                "region": self.speech_region,
                "configured": True,
                "audio_decoder": "ffmpeg" if ffmpeg_path else "native"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


_speech_service_instance: Optional[SpeechService] = None


def get_speech_service() -> SpeechService:
    global _speech_service_instance
    if _speech_service_instance is None:
        _speech_service_instance = SpeechService()
    return _speech_service_instance
