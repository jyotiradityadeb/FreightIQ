import time
import subprocess
import os
from playwright.sync_api import sync_playwright

def verify_robustness_flow():
    cmd = ["python", "-m", "streamlit", "run", "app/Home.py", "--server.port=8597", "--server.headless=true"]
    proc = subprocess.Popen(cmd, cwd=r"C:\Users\jyoti\OneDrive\Desktop\FreightIQ")
    time.sleep(6)

    artifact_dir = r"C:\Users\jyoti\.gemini\antigravity\brain\9ffd82a2-ef8e-4505-bd8e-9ca19a99587a"
    overview_img = os.path.join(artifact_dir, "overview_robustness_verification.png")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            
            # 1. Open Overview
            page.goto("http://localhost:8597", timeout=45000)
            page.wait_for_selector("text=DECISION ROBUSTNESS", timeout=30000)
            page.wait_for_timeout(2000)
            
            overview_text = page.inner_text("body")
            print("--- OVERVIEW CONTENT CHECK ---")
            for line in overview_text.splitlines():
                if "DECISION ROBUSTNESS" in line or "/ 100" in line or "simulated futures" in line:
                    print("OVERVIEW:", line)

            page.screenshot(path=overview_img)
            print(f"Overview screenshot saved to: {overview_img}")

            # 2. Open Decision Twin page
            page.goto("http://localhost:8597/Decision_Twin", timeout=45000)
            page.wait_for_selector("text=DECISION ROBUSTNESS", timeout=30000)
            page.wait_for_timeout(2000)
            twin_text = page.inner_text("body")
            print("\n--- DECISION TWIN CONTENT CHECK ---")
            for line in twin_text.splitlines():
                if "DECISION ROBUSTNESS" in line or "/ 100" in line:
                    print("DECISION TWIN:", line)

            browser.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    verify_robustness_flow()
