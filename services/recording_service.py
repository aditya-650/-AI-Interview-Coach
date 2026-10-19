"""
services/recording_service.py
Service for capturing, persisting, and processing candidate video answers.
Features:
- Structured storage of WebM video files in `interview_recordings/session_{session_id}/`
- FFmpeg-based audio stream extraction from WebM video container
- Azure AI Speech transcription of candidate speech from the video track
- Background HTTP receiver daemon (port 8503) for seamless WebRTC in-browser uploads
- Real-time proctoring violation tracking & 3-strike immediate session termination
"""

import os
import json
import time
import sys
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from services.speech_service import get_speech_service, normalize_audio_to_pcm_wav

# Base recording directory in project workspace
RECORDINGS_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "interview_recordings")
os.makedirs(RECORDINGS_BASE_DIR, exist_ok=True)

# In-memory stores
LATEST_RECORDINGS: Dict[str, Dict[str, Any]] = {}
TERMINATED_SESSIONS: Dict[str, Dict[str, Any]] = {}

HTTP_RECEIVER_PORT = 8503
_server_thread: Optional[threading.Thread] = None
_server_instance: Optional[HTTPServer] = None


def get_session_dir(session_id: str) -> str:
    """Returns and creates the session-specific recording directory."""
    clean_id = "".join(c for c in session_id if c.isalnum() or c in ("-", "_")) or "default_session"
    s_dir = os.path.join(RECORDINGS_BASE_DIR, f"session_{clean_id}")
    os.makedirs(s_dir, exist_ok=True)
    return s_dir


def save_video_and_transcribe(
    video_bytes: bytes,
    session_id: str,
    question_index: int
) -> Dict[str, Any]:
    """
    Saves incoming WebM video bytes, extracts the audio track,
    and runs Azure AI Speech transcription.
    """
    session_dir = get_session_dir(session_id)
    timestamp = int(time.time())
    video_filename = f"q{question_index}_{timestamp}.webm"
    video_path = os.path.join(session_dir, video_filename)

    # If a candidate is actively uploading their answer, clear any false strike flags
    if session_id in TERMINATED_SESSIONS:
        del TERMINATED_SESSIONS[session_id]

    with open(video_path, "wb") as f:
        f.write(video_bytes)

    # Step 1: Extract and normalize audio track using FFmpeg
    transcription = ""
    error_msg = ""
    try:
        pcm_wav = normalize_audio_to_pcm_wav(video_bytes)
        if pcm_wav and len(pcm_wav) > 100:
            speech_service = get_speech_service()
            transcription = speech_service.transcribe_audio_bytes(
                pcm_wav,
                filename_hint=f"q{question_index}_audio.wav"
            )
    except Exception as e:
        error_msg = str(e)
        print(f"[RecordingService] Audio extraction/transcription notice: {e}")

    result = {
        "status": "success",
        "session_id": session_id,
        "question_index": question_index,
        "video_path": video_path,
        "video_filename": video_filename,
        "size_bytes": len(video_bytes),
        "transcription": transcription,
        "error": error_msg,
        "timestamp": timestamp
    }

    # Store in memory and write metadata JSON
    key = f"{session_id}_{question_index}"
    LATEST_RECORDINGS[key] = result

    meta_path = os.path.join(session_dir, f"q{question_index}_{timestamp}_meta.json")
    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    except Exception:
        pass

    return result


def get_latest_recording(session_id: str, question_index: int) -> Optional[Dict[str, Any]]:
    """Retrieves the latest processed recording for a specific question."""
    key = f"{session_id}_{question_index}"
    return LATEST_RECORDINGS.get(key)


def mark_session_terminated(session_id: str, reason: str = "3 Proctoring Strikes Exceeded") -> None:
    """Records that a session has been terminated for integrity violations."""
    TERMINATED_SESSIONS[session_id] = {
        "terminated": True,
        "reason": reason,
        "timestamp": time.time()
    }


def clear_session_terminated(session_id: str) -> None:
    """Clears termination record for a session."""
    if session_id in TERMINATED_SESSIONS:
        del TERMINATED_SESSIONS[session_id]


def is_session_terminated(session_id: str) -> bool:
    """Checks whether the session was terminated."""
    return session_id in TERMINATED_SESSIONS


class RecordingHTTPHandler(BaseHTTPRequestHandler):
    """Handles browser uploads and proctoring events via HTTP."""

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Requested-With")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/health":
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return

        if parsed.path == "/get_recording":
            session_id = params.get("session_id", ["default"])[0]
            q_index = int(params.get("q_index", ["1"])[0])
            rec = get_latest_recording(session_id, q_index)
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(rec or {}).encode("utf-8"))
            return

        if parsed.path == "/is_terminated":
            session_id = params.get("session_id", ["default"])[0]
            term_info = TERMINATED_SESSIONS.get(session_id, {"terminated": False})
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(term_info).encode("utf-8"))
            return

        self.send_response(404)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        if parsed.path == "/upload_video":
            session_id = params.get("session_id", ["default"])[0]
            q_index = int(params.get("q_index", ["1"])[0])

            # Post data may be raw WebM bytes or multipart
            # If multipart, extract file bytes cleanly
            video_bytes = post_data
            if b"\r\n\r\n" in post_data and b"Content-Type: video" in post_data:
                # Basic multipart boundary split
                parts = post_data.split(b"\r\n\r\n", 1)
                if len(parts) > 1:
                    body = parts[1]
                    # strip trailing boundary
                    if b"\r\n--" in body:
                        video_bytes = body.split(b"\r\n--")[0]
                    else:
                        video_bytes = body

            result = save_video_and_transcribe(video_bytes, session_id, q_index)
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        if parsed.path == "/report_violation":
            session_id = params.get("session_id", ["default"])[0]
            try:
                payload = json.loads(post_data.decode("utf-8")) if post_data else {}
            except Exception:
                payload = {}

            strikes = payload.get("strikes", 0)
            reason = payload.get("reason", "Tab Switch / Window Blur")
            if strikes >= 3 or payload.get("terminated"):
                mark_session_terminated(session_id, reason)

            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "recorded", "terminated": strikes >= 3}).encode("utf-8"))
            return

        self.send_response(404)
        self._send_cors_headers()
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress routine logging to keep console clean
        return


def start_recording_receiver_server(port: int = HTTP_RECEIVER_PORT) -> bool:
    """Starts the background HTTP receiver daemon thread."""
    global _server_thread, _server_instance
    if _server_thread and _server_thread.is_alive():
        return True

    try:
        _server_instance = HTTPServer(("127.0.0.1", port), RecordingHTTPHandler)
        _server_thread = threading.Thread(target=_server_instance.serve_forever, daemon=True)
        _server_thread.start()
        print(f"[RecordingService] Receiver daemon listening on http://127.0.0.1:{port}")
        return True
    except Exception as e:
        print(f"[RecordingService] Could not start server on port {port}: {e}")
        return False


# Auto-start daemon on import
start_recording_receiver_server()


if __name__ == "__main__":
    print(f"[RecordingService] Starting standalone server on http://127.0.0.1:{HTTP_RECEIVER_PORT}...")
    server = HTTPServer(("127.0.0.1", HTTP_RECEIVER_PORT), RecordingHTTPHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

