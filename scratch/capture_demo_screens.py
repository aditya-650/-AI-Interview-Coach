import time
import os
from playwright.sync_api import sync_playwright

os.makedirs("scratch", exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        permissions=["camera", "microphone"]
    )
    page = context.new_page()

    views = [
        ("landing", "scratch/screen1_landing.png", 3000),
        ("questions", "scratch/screen2_questions.png", 2500),
        ("setup", "scratch/screen3_setup.png", 2500),
        ("interviewing", "scratch/screen4_interview_text.png", 3000),
        ("evaluated", "scratch/screen6_evaluated.png", 2500),
        ("report", "scratch/screen7_report.png", 2500),
        ("copilot", "scratch/screen8_copilot.png", 2500),
    ]

    for view_name, out_path, wait_ms in views:
        url = f"http://localhost:8501/?view={view_name}"
        print(f"Capturing view={view_name} -> {out_path}...")
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(wait_ms)
        page.screenshot(path=out_path)
        print(f"Saved {out_path}")

    # Capture Video mode inside interviewing
    print("Capturing interviewing with Video mode active...")
    page.goto("http://localhost:8501/?view=interviewing", wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    video_opt = page.get_by_text("Record Video Answer")
    if video_opt.count() > 0:
        video_opt.first.click(force=True)
        page.wait_for_timeout(3000)
        page.screenshot(path="scratch/screen5_interview_video.png")
        print("Saved scratch/screen5_interview_video.png")

    browser.close()
    print("ALL 8 DEMO SCREENS CAPTURED SUCCESSFULLY!")
