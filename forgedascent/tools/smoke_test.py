"""Starts a dev server with only Forged Ascent, waits until it has loaded, prints relevant
warnings/errors from the log, then shuts it down. Run from the forgedascent folder:

    python tools/smoke_test.py
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "runs/server"
TIMEOUT = 420

RUN.mkdir(parents=True, exist_ok=True)
(RUN / "eula.txt").write_text("eula=true\n")
props = RUN / "server.properties"
if not props.exists():
    props.write_text("online-mode=false\nlevel-type=minecraft\\:flat\nspawn-protection=0\n")

proc = subprocess.Popen(["cmd", "/c", str(ROOT / "gradlew.bat"), "runServer", "--console=plain"], cwd=ROOT,
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding="utf-8", errors="replace")
interesting = re.compile(r"forgedascent|Couldn't|Failed to|Exception|ERROR|missing references|Error loading", re.I)
done = False
start = time.time()
lines = []
for line in proc.stdout:
    lines.append(line)
    if interesting.search(line) and "REGISTRIES" not in line:
        print(line.rstrip()[:400])
    if "Done (" in line and "For help" in line:
        done = True
        break
    if time.time() - start > TIMEOUT:
        break

print("SERVER STARTED OK" if done else "SERVER DID NOT FINISH STARTING")
try:
    proc.stdin.write("stop\n")
    proc.stdin.flush()
    proc.wait(timeout=60)
except Exception:
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
if not done:
    print("".join(lines[-60:]))
sys.exit(0 if done else 1)
