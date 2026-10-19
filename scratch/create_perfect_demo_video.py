import os
import sys
import wave
import subprocess
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.speech_service import find_ffmpeg_executable

load_dotenv()
ffmpeg_bin = find_ffmpeg_executable()
if not ffmpeg_bin:
    raise RuntimeError("FFmpeg executable not found!")

speech_key = os.getenv("AZURE_SPEECH_KEY")
speech_region = os.getenv("AZURE_SPEECH_REGION")

if not speech_key or not speech_region:
    raise RuntimeError("Azure Speech credentials missing!")

print(f"[DemoBuilder] Using FFmpeg: {ffmpeg_bin}")

# 1. Voiceover Scenes with high-impact scripts
scenes = [
    {
        "id": 1,
        "raw_img": "scratch/screen1_landing.png",
        "badge": "FRONTIER AI COACH • V3.5",
        "title": "Master Tier-1 Technical & Behavioral Interviews with Frontier AI",
        "narration": "Welcome to Interview IQ, the autonomous, multimodal AI interview coach powered by Microsoft Azure."
    },
    {
        "id": 2,
        "raw_img": "scratch/screen2_questions.png",
        "badge": "FEATURE 01 • BENCHMARK TRACKS",
        "title": "Staff ML, Distributed Systems, & High-Scale Infrastructure Tracks",
        "narration": "Explore curated benchmark tracks across distributed systems, staff machine learning, and cloud infrastructure."
    },
    {
        "id": 3,
        "raw_img": "scratch/screen3_setup.png",
        "badge": "FEATURE 02 • RAG GROUNDING",
        "title": "Resume & System Architecture Spec Document Grounding",
        "narration": "Configure your target engineering role, and index your resume into Azure AI Foundry Vector Stores for grounded questions."
    },
    {
        "id": 4,
        "raw_img": "scratch/screen4_interview_text.png",
        "badge": "FEATURE 03 • NEURAL TTS VOICE",
        "title": "AI Principal Interviewer with Live Audio Question Narration",
        "narration": "In the live interview cockpit, questions are spoken aloud naturally using Azure AI Speech neural voice synthesis."
    },
    {
        "id": 5,
        "raw_img": "scratch/screen5_interview_video.png",
        "badge": "FEATURE 04 • PROCTORED VIDEO",
        "title": "On-Demand Candidate Webcam Capture & Exam Integrity Guardian",
        "narration": "Record proctored video answers with automated speech transcription, protected by a real-time exam integrity monitor."
    },
    {
        "id": 6,
        "raw_img": "scratch/screen6_evaluated.png",
        "badge": "FEATURE 05 • RUBRIC TELEMETRY",
        "title": "Foundry Evaluation: Technical Rigor, STAR Delivery & Growth Areas",
        "narration": "Receive instant rubric telemetry across technical rigor, system trade-offs, and STAR methodology delivery."
    },
    {
        "id": 7,
        "raw_img": "scratch/screen7_report.png",
        "badge": "FEATURE 06 • EXECUTIVE REPORT",
        "title": "Executive Hiring Recommendation & Telemetry Dashboard",
        "narration": "Review comprehensive performance synthesis, question-by-question telemetry, and recorded video playback."
    },
    {
        "id": 8,
        "raw_img": "scratch/screen8_copilot.png",
        "badge": "FEATURE 07 • ZERO-HALLUCINATION COPILOT",
        "title": "STAR Coaching & System Design Architecture Frameworks",
        "narration": "Plus, consult the zero-hallucination AI Copilot for structured hints and frameworks. Elevate your interview readiness with Interview IQ."
    }
]

os.makedirs("scratch/audio_48k", exist_ok=True)
os.makedirs("scratch/frames", exist_ok=True)

# 2. Synthesize High-Fidelity 48kHz Studio Voiceovers
print("\n[Step 1] Synthesizing Studio 48kHz Voiceovers via Azure AI Speech...")
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm)

synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

scene_durations = []
audio_paths = []

for sc in scenes:
    idx = sc["id"]
    wav_out = f"scratch/audio_48k/voice_{idx}_48k.wav"
    print(f"  Synthesizing scene {idx}: \"{sc['narration'][:45]}...\"")
    res = synthesizer.speak_text_async(sc["narration"]).get()
    if res.reason != speechsdk.ResultReason.SynthesizingAudioCompleted or not res.audio_data:
        raise RuntimeError(f"Speech synthesis failed for scene {idx}: {res.reason}")
    with open(wav_out, "wb") as f:
        f.write(res.audio_data)

    with wave.open(wav_out, "rb") as w:
        dur = w.getnframes() / float(w.getframerate())
    # Add a gentle 0.3s pause between scenes
    scene_durations.append(dur + 0.3)
    audio_paths.append(wav_out)
    print(f"  -> Generated {wav_out}: duration={dur:.2f}s (allocated {dur+0.3:.2f}s)")

total_duration = sum(scene_durations)
print(f"\n[Total Planned Duration]: {total_duration:.2f} seconds")

# 3. Concatenate all audio files into a single, seamless, continuous Master Audio Track
print("\n[Step 2] Building continuous master audio track with 48kHz Stereo & Volume Boost...")
master_wav_mono = "scratch/audio_48k/master_mono.wav"
master_wav_stereo = "scratch/audio_48k/master_voiceover_final.wav"

# Create master mono WAV with silence padding
output_frames = []
for p in audio_paths:
    with wave.open(p, "rb") as w:
        output_frames.append(w.readframes(w.getnframes()))
    # 0.3 sec silence at 48000 Hz, 16-bit mono = 48000 * 0.3 * 2 bytes = 28800 bytes
    silence_bytes = b"\x00" * int(48000 * 0.3 * 2)
    output_frames.append(silence_bytes)

with wave.open(master_wav_mono, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(48000)
    wf.writeframes(b"".join(output_frames))

print(f"  Saved {master_wav_mono}")

# Convert mono master to rich Stereo 48kHz with volume normalization (+6dB / loudnorm) using FFmpeg
print("  Normalizing volume and converting to loud, clear Stereo 48kHz...")
norm_cmd = [
    ffmpeg_bin,
    "-y",
    "-i", master_wav_mono,
    "-af", "volume=2.8,aresample=48000,pan=stereo|c0=c0|c1=c0",
    "-ar", "48000",
    "-ac", "2",
    master_wav_stereo
]
subprocess.run(norm_cmd, check=True)
print(f"  Master voiceover ready: {master_wav_stereo}")

# 4. Render Composite 1080p Image Frames with Glassmorphic Lower-Thirds
print("\n[Step 3] Rendering 1080p Glassmorphic Video Frames...")
font_badge = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 22)
font_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 34)
font_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 26)
top_font = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 20)

frame_paths = []
for sc in scenes:
    idx = sc["id"]
    base_im = Image.open(sc["raw_img"]).convert("RGBA")
    overlay = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Top brand bar
    draw.rectangle([(0, 0), (1920, 48)], fill=(15, 23, 42, 225))
    draw.ellipse([(30, 16), (46, 32)], fill=(56, 189, 248, 255))
    draw.text((58, 12), "INTERVIEW IQ  •  FRONTIER AI MULTIMODAL INTERVIEW COACH  •  POWERED BY AZURE AI", fill=(226, 232, 240, 255), font=top_font)

    # Bottom Glassmorphic Card
    card_x1, card_y1 = 80, 890
    card_x2, card_y2 = 1840, 1035
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=18, fill=(15, 23, 42, 235), outline=(56, 189, 248, 180), width=2)

    # Badge Pill
    badge_w = 460
    draw.rounded_rectangle([(card_x1 + 30, card_y1 + 18), (card_x1 + 30 + badge_w, card_y1 + 52)], radius=8, fill=(56, 189, 248, 45), outline=(56, 189, 248, 200), width=1)
    draw.text((card_x1 + 44, card_y1 + 22), sc["badge"], fill=(56, 189, 248, 255), font=font_badge)

    # Title
    draw.text((card_x1 + 30 + badge_w + 24, card_y1 + 18), sc["title"], fill=(255, 255, 255, 255), font=font_title)

    # Subtitle Caption
    draw.text((card_x1 + 34, card_y1 + 76), f"🗣️  \"{sc['narration']}\"", fill=(203, 213, 225, 255), font=font_sub)

    comp = Image.alpha_composite(base_im, overlay).convert("RGB")
    out_f = f"scratch/frames/frame_{idx}.png"
    comp.save(out_f, "PNG")
    frame_paths.append(out_f)
    print(f"  Rendered {out_f}")

# 5. Build Silent Video Stream matching scene durations
print("\n[Step 4] Encoding video clips for each scene...")
os.makedirs("scratch/video_clips", exist_ok=True)
video_clip_files = []

for sc, dur, fpath in zip(scenes, scene_durations, frame_paths):
    idx = sc["id"]
    clip_p = os.path.abspath(f"scratch/video_clips/clip_{idx}.mp4")
    enc_cmd = [
        ffmpeg_bin,
        "-y",
        "-loop", "1",
        "-i", os.path.abspath(fpath),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-t", f"{dur:.3f}",
        clip_p
    ]
    subprocess.run(enc_cmd, check=True)
    video_clip_files.append(clip_p)
    print(f"  Encoded video clip {idx} ({dur:.2f}s)")

# Concat video clips
concat_v_txt = os.path.abspath("scratch/concat_video.txt")
with open(concat_v_txt, "w", encoding="utf-8") as f:
    for c in video_clip_files:
        escaped = c.replace("\\", "/")
        f.write(f"file '{escaped}'\n")

raw_video_mp4 = os.path.abspath("scratch/raw_video_stream.mp4")
subprocess.run([
    ffmpeg_bin,
    "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_v_txt,
    "-c", "copy",
    raw_video_mp4
], check=True)
print(f"  Concatenated video stream ready: {raw_video_mp4}")

# 6. Mux Video + Master Audio Track into Final Production MP4
final_mp4 = os.path.abspath("interview_iq_demo_showcase.mp4")
print("\n[Step 5] Muxing video and 48kHz stereo master audio into final showcase MP4...")

mux_cmd = [
    ffmpeg_bin,
    "-y",
    "-i", raw_video_mp4,
    "-i", os.path.abspath(master_wav_stereo),
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "256k",
    "-ar", "48000",
    "-ac", "2",
    "-shortest",
    final_mp4
]
subprocess.run(mux_cmd, check=True)

# Copy to artifact directory
artifact_mp4 = r"C:\Users\adity\.gemini\antigravity\brain\bd169516-0a39-42d7-aaae-271617718f27\interview_iq_demo_showcase.mp4"
try:
    import shutil
    shutil.copyfile(final_mp4, artifact_mp4)
    print(f"  Copied to artifact directory: {artifact_mp4}")
except Exception as e:
    print(f"  Notice copying to artifact: {e}")

file_size_mb = os.path.getsize(final_mp4) / (1024 * 1024)
print("\n[SUCCESS] DEMO VIDEO GENERATION COMPLETE!")
print(f"  File: {final_mp4}")
print(f"  Size: {file_size_mb:.2f} MB")
print(f"  Audio Track: Studio 48,000 Hz, 2-Channel Stereo AAC (Loud & Crystal-Clear)")
