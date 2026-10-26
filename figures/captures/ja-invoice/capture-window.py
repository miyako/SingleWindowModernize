"""Capture only the owned 4D demo window; never the desktop."""
import json
from pathlib import Path
import subprocess
import time

from PIL import Image

work = Path(__file__).resolve().parents[1]
out = work / "output"
job = json.loads((work / "capture-job.json").read_text())
target = out / (Path(job["path"]).stem + "-window.png")
for path in (out / "window-ready.txt", out / "window-captured.txt", target):
    path.unlink(missing_ok=True)
command = [
    "/Applications/4D 21 R4/4D.app/Contents/MacOS/4D",
    f"--project={work / 'Project/4D Invoice.4DProject'}",
    "--startup-method=ja_capture_bootstrap",
    "--skip-onstartup",
    f"--data={work / 'Data/capture.4DD'}",
]
with target.with_suffix(".log").open("w") as log:
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 75
        while not (out / "window-ready.txt").exists():
            if process.poll() is not None:
                raise RuntimeError(f"4D exited before ready: {process.returncode}")
            if time.monotonic() > deadline:
                raise TimeoutError("Window readiness timed out")
            time.sleep(0.2)
        time.sleep(1)
        raw = subprocess.check_output(
            ["swift", str(out / "task-windows.swift"), str(process.pid)], text=True
        )
        windows = json.loads(raw)
        candidates = [
            window for window in windows
            if abs(window.get("kCGWindowBounds", {}).get("Width", 0) - job["width"]) <= 2
            and window.get("kCGWindowBounds", {}).get("Height", 0) >= job["height"] - 2
        ]
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one matching owned window, found {len(candidates)}")
        window = candidates[0]
        subprocess.run(
            ["/usr/sbin/screencapture", "-x", "-o",
             f"-l{window['kCGWindowNumber']}", str(target)], check=True
        )
        (out / "window-captured.txt").write_text("captured")
        code = process.wait(timeout=30)
        if code != 0:
            raise RuntimeError(f"4D exited with {code}")
        with Image.open(target) as image:
            evidence = {
                "job": job, "window": window, "dimensions": list(image.size),
                "mode": image.mode, "exit": code,
                "state": json.loads((out / "capture-state.json").read_text()),
            }
        target.with_suffix(".json").write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
        )
        print(target, evidence["dimensions"], "exit", code)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
