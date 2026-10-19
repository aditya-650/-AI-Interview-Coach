import os
import sys
import wave
import subprocess
from PIL import Image, ImageDraw, ImageFont

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.speech_service import find_ffmpeg_executable

ffmpeg_bin = find_ffmpeg_executable()
if not ffmpeg_bin:
    raise RuntimeError("FFmpeg executable not found!")

print(f"Using FFmpeg: {ffmpeg_bin}")

scenes_data = [
    {
        "id": 1,
        "raw_img": "scratch/screen1_landing.png",
        "audio": "scratch/audio/voice_1.wav",
        "badge": "FRONTIER AI INTERVIEW COACH • V3.5",
        "title": "Master Tier-1 Technical & Behavioral Interviews with Frontier AI",
        "caption": "Welcome to Interview IQ, the frontier autonomous AI interview coach powered by Microsoft Azure."
    },
    {
        "id": 2,
        "raw_img": "scratch/screen2_questions.png",
        "audio": "scratch/audio/voice_2.wav",
        "badge": "FEATURE 01 • CURATED BENCHMARK PROMPTS",
        "title": "Staff ML, Distributed Systems, & High-Scale Infrastructure Tracks",
        "caption": "Choose from curated benchmark tracks across distributed systems, staff machine learning, and cloud infrastructure."
    },
    {
        "id": 3,
        "raw_img": "scratch/screen3_setup.png",
        "audio": "scratch/audio/voice_3.wav",
        "badge": "FEATURE 02 • RAG VECTOR STORE GROUNDING",
        "title": "Resume & System Architecture Spec Document Grounding",
        "caption": "Configure your target engineering role, and index your resume into Azure AI Foundry Vector Stores for grounded questions."
    },
    {
        "id": 4,
        "raw_img": "scratch/screen4_interview_text.png",
        "audio": "scratch/audio/voice_4.wav",
        "badge": "FEATURE 03 • NEURAL VOICE NARRATION",
        "title": "AI Principal Interviewer with Live Audio Question Narration",
        "caption": "In the live interview cockpit, questions are spoken aloud naturally using Azure AI Speech neural text-to-speech."
    },
    {
        "id": 5,
        "raw_img": "scratch/screen5_interview_video.png",
        "audio": "scratch/audio/voice_5.wav",
        "badge": "FEATURE 04 • PROCTORED VIDEO ANSWERS",
        "title": "On-Demand Candidate Webcam Capture & Exam Integrity Guardian",
        "caption": "Record proctored video answers with automated speech transcription, protected by a real-time browser integrity monitor."
    },
    {
        "id": 6,
        "raw_img": "scratch/screen6_evaluated.png",
        "audio": "scratch/audio/voice_6.wav",
        "badge": "FEATURE 05 • INSTANT RUBRIC TELEMETRY",
        "title": "Foundry Evaluation: Technical Rigor, STAR Delivery & Growth Areas",
        "caption": "Receive instant rubric telemetry across technical rigor, system trade-offs, and STAR methodology delivery."
    },
    {
        "id": 7,
        "raw_img": "scratch/screen7_report.png",
        "audio": "scratch/audio/voice_7.wav",
        "badge": "FEATURE 06 • EXECUTIVE PERFORMANCE SYNTHESIS",
        "title": "Executive Hiring Recommendation & Telemetry Dashboard",
        "caption": "Review comprehensive performance synthesis, question-by-question telemetry, and recorded video playback."
    },
    {
        "id": 8,
        "raw_img": "scratch/screen8_copilot.png",
        "audio": "scratch/audio/voice_8.wav",
        "badge": "FEATURE 07 • ZERO-HALLUCINATION AI COPILOT",
        "title": "STAR Coaching & System Design Architecture Frameworks",
        "caption": "Plus, consult the AI Copilot for structured hints and frameworks. Elevate your interview readiness with Interview IQ."
    }
]

os.makedirs("scratch/frames", exist_ok=True)
os.makedirs("scratch/clips", exist_ok=True)

# Load Segoe UI fonts
font_badge = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 22)
font_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 34)
font_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 26)

print("Rendering enhanced 1080p composite frames...")

for item in scenes_data:
    idx = item["id"]
    base_im = Image.open(item["raw_img"]).convert("RGBA")
    
    # Overlay layer for glassmorphism
    overlay = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Top brand bar
    draw.rectangle([(0, 0), (1920, 48)], fill=(15, 23, 42, 220))
    # Top brand indicator
    draw.ellipse([(30, 16), (46, 32)], fill=(56, 189, 248, 255))
    top_font = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 20)
    draw.text((58, 12), "INTERVIEW IQ  •  FRONTIER AI MULTIMODAL INTERVIEW COACH  •  POWERED BY AZURE AI", fill=(226, 232, 240, 255), font=top_font)

    # Bottom Glassmorphic Card
    card_x1, card_y1 = 80, 890
    card_x2, card_y2 = 1840, 1035

    # Card background with deep blur effect
    draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=18, fill=(15, 23, 42, 235), outline=(56, 189, 248, 180), width=2)

    # Badge Pill
    badge_w = 460
    draw.rounded_rectangle([(card_x1 + 30, card_y1 + 18), (card_x1 + 30 + badge_w, card_y1 + 52)], radius=8, fill=(56, 189, 248, 45), outline=(56, 189, 248, 200), width=1)
    draw.text((card_x1 + 44, card_y1 + 22), item["badge"], fill=(56, 189, 248, 255), font=font_badge)

    # Title
    draw.text((card_x1 + 30 + badge_w + 24, card_y1 + 18), item["title"], fill=(255, 255, 255, 255), font=font_title)

    # Spoken Subtitle Caption
    draw.text((card_x1 + 34, card_y1 + 76), f"🗣️  \"{item['caption']}\"", fill=(203, 213, 225, 255), font=font_sub)

    # Composite & save
    comp = Image.alpha_composite(base_im, overlay).convert("RGB")
    out_frame = f"scratch/frames/frame_{idx}.png"
    comp.save(out_frame, "PNG")
    print(f"Rendered composite: {out_frame}")

print("\nEncoding scene clips with FFmpeg...")
clip_files = []

for item in scenes_data:
    idx = item["id"]
    frame_path = os.path.abspath(f"scratch/frames/frame_{idx}.png")
    audio_path = os.path.abspath(item["audio"])
    clip_path = os.path.abspath(f"scratch/clips/scene_{idx}.mp4")

    # Get exact duration of audio
    with wave.open(audio_path, "rb") as w:
        dur = w.getnframes() / float(w.getframerate())

    # Add a 0.3s padding so audio doesn't cut abruptly
    clip_dur = dur + 0.3

    cmd = [
        ffmpeg_bin,
        "-y",
        "-loop", "1",
        "-i", frame_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", f"{clip_dur:.3f}",
        clip_path
    ]
    
    print(f"Encoding Scene {idx} ({clip_dur:.2f}s)...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Error encoding scene {idx}:", res.stderr[-300:])
        raise RuntimeError(f"FFmpeg scene {idx} failed")
    clip_files.append(clip_path)

print("\nConcatenating full demo video...")
concat_txt_path = os.path.abspath("scratch/concat_list.txt")
with open(concat_txt_path, "w", encoding="utf-8") as f:
    for c in clip_files:
        escaped = c.replace("\\", "/")
        f.write(f"file '{escaped}'\n")

final_output_path = os.path.abspath("interview_iq_demo_showcase.mp4")

cmd_concat = [
    ffmpeg_bin,
    "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_txt_path,
    "-c", "copy",
    final_output_path
]

res = subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
if res.returncode != 0:
    print("Error in concat:", res.stderr[-400:])
    raise RuntimeError("FFmpeg concat failed")

file_size = os.path.getsize(final_output_path)
print(f"\n🎉 DEMO VIDEO CREATED SUCCESSFULLY!")
print(f"Output File: {final_output_path}")
print(f"File Size: {file_size / (1024*1024):.2f} MB")
