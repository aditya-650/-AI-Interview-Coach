import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.speech_service import get_speech_service

speech_service = get_speech_service()

narration_scenes = [
    (1, "Welcome to Interview IQ, the frontier autonomous AI interview coach powered by Microsoft Azure."),
    (2, "Choose from curated benchmark tracks across distributed systems, staff machine learning, and cloud infrastructure."),
    (3, "Configure your target engineering role, and index your resume into Azure AI Foundry Vector Stores for grounded questions."),
    (4, "In the live interview cockpit, questions are spoken aloud naturally using Azure AI Speech neural text-to-speech."),
    (5, "Record proctored video answers with automated speech transcription, protected by a real-time browser integrity monitor."),
    (6, "Receive instant rubric telemetry across technical rigor, system trade-offs, and STAR methodology delivery."),
    (7, "Review comprehensive performance synthesis, question-by-question telemetry, and recorded video playback."),
    (8, "Plus, consult the AI Copilot for structured hints and frameworks. Elevate your interview readiness with Interview IQ.")
]

os.makedirs("scratch/audio", exist_ok=True)

print("Synthesizing voiceovers with Azure AI Speech...")
for idx, text in narration_scenes:
    out_file = f"scratch/audio/voice_{idx}.wav"
    print(f"Generating scene {idx} audio...")
    wav_bytes = speech_service.synthesize_speech_to_wav(text)
    if wav_bytes:
        with open(out_file, "wb") as f:
            f.write(wav_bytes)
        print(f"Saved {out_file} ({len(wav_bytes)} bytes)")
    else:
        print(f"Failed to generate audio for scene {idx}")

print("All voiceover tracks successfully generated!")
