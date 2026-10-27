import time
import subprocess
import os
from playwright.sync_api import sync_playwright

def capture_streamlit_nav():
    cmd = ["python", "-m", "streamlit", "run", "app/Home.py", "--server.port=8599", "--server.headless=true"]
    proc = subprocess.Popen(cmd, cwd=r"C:\Users\jyoti\OneDrive\Desktop\FreightIQ")
    time.sleep(5)  # wait for streamlit to initialize

    artifact_dir = r"C:\Users\jyoti\.gemini\antigravity\brain\9ffd82a2-ef8e-4505-bd8e-9ca19a99587a"
    screenshot_path = os.path.join(artifact_dir, "nav_header_verification.png")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto("http://localhost:8599", timeout=30000)
            page.wait_for_timeout(3000)
            page.screenshot(path=screenshot_path, full_page=False)
            print(f"Screenshot saved to: {screenshot_path}")
            browser.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    capture_streamlit_nav()
