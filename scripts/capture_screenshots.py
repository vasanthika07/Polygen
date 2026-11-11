import os
import shutil
import subprocess
import time

CHROME_BIN = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TEMP_DIR = os.environ.get("TEMP", r"C:\Users\windows\AppData\Local\Temp")
ARTIFACT_DIR = r"C:\Users\windows\.gemini\antigravity\brain\64ef4193-7a70-417d-9b27-f29f773d54c4"

PAGES = [
    ("dashboard.png", "http://127.0.0.1:8000/dashboard"),
    ("workspace.png", "http://127.0.0.1:8000/workspace"),
    ("viewer.png", "http://127.0.0.1:8000/viewer"),
    ("library.png", "http://127.0.0.1:8000/library"),
    ("history.png", "http://127.0.0.1:8000/history"),
    ("settings.png", "http://127.0.0.1:8000/settings"),
    ("landing.png", "http://127.0.0.1:8000/landing"),
]

def capture_all():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    for filename, url in PAGES:
        temp_dest = os.path.join(TEMP_DIR, filename)
        final_dest = os.path.join(ARTIFACT_DIR, filename)

        if os.path.exists(temp_dest):
            try:
                os.remove(temp_dest)
            except Exception:
                pass

        cmd = [
            CHROME_BIN,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--window-size=1440,900",
            "--virtual-time-budget=4000",
            f"--screenshot={temp_dest}",
            url
        ]

        print(f"Capturing {filename} from {url}...")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        
        if os.path.exists(temp_dest):
            shutil.copyfile(temp_dest, final_dest)
            size = os.path.getsize(final_dest)
            print(f"✓ Saved {filename} ({size:,} bytes) to artifacts")
        else:
            print(f"✗ Failed to capture {filename}. Stderr: {res.stderr.decode('utf-8', errors='ignore')[:200]}")

if __name__ == "__main__":
    capture_all()

