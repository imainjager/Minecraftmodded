"""Starts a dev server with only Forged Ascent, waits until it has loaded, optionally runs server
commands over RCON (printing each reply), shows relevant warnings/errors, then shuts it down.
Run from the forgedascent folder:

    python tools/smoke_test.py ["command one" "command two" ...]
"""
import queue
import re
import socket
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "run"
TIMEOUT = 420
RCON_PORT, RCON_PASSWORD = 25575, "forgedascent-test"

RUN.mkdir(parents=True, exist_ok=True)
(RUN / "eula.txt").write_text("eula=true\n")
props_path = RUN / "server.properties"
props = {}
if props_path.exists():
    for line in props_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            props[k] = v
props.update({"online-mode": "false", "level-type": "minecraft\\:flat", "spawn-protection": "0",
              "enable-rcon": "true", "rcon.port": str(RCON_PORT), "rcon.password": RCON_PASSWORD})
props_path.write_text("".join(f"{k}={v}\n" for k, v in props.items()))

proc = subprocess.Popen(["cmd", "/c", str(ROOT / "gradlew.bat"), "runServer", "--console=plain"], cwd=ROOT,
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding="utf-8", errors="replace")
lines = queue.Queue()
threading.Thread(target=lambda: [lines.put(l) for l in proc.stdout], daemon=True).start()

interesting = re.compile(r"forgedascent|Couldn't|Failed to|Exception|ERROR|missing references|Error loading", re.I)
noise = re.compile(r"server\.properties|FMLPaths|LaunchHandler|ModFile|mixin|LOADING|SOMAXCONN|mcassetsroot", re.I)
history = []


def pump(seconds=0.0, until=None):
    start = time.time()
    while True:
        try:
            line = lines.get(timeout=0.5)
        except queue.Empty:
            line = None
        if line:
            history.append(line)
            if interesting.search(line) and not noise.search(line):
                print(line.rstrip()[:400])
            if until and until(line):
                return True
        if until is None and time.time() - start >= seconds:
            return False
        if until is not None and time.time() - start > TIMEOUT:
            return False


class Rcon:
    def __init__(self):
        self.sock = socket.create_connection(("127.0.0.1", RCON_PORT), timeout=10)
        self.send(3, RCON_PASSWORD)

    def send(self, kind, body):
        data = body.encode("utf-8")
        self.sock.sendall(struct.pack("<iii", len(data) + 10, 1, kind) + data + b"\x00\x00")
        size = struct.unpack("<i", self._read(4))[0]
        payload = self._read(size)
        return payload[8:-2].decode("utf-8", "replace")

    def _read(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("RCON closed")
            buf += chunk
        return buf


done = pump(until=lambda l: "Done (" in l and "For help" in l)
print("SERVER STARTED OK" if done else "SERVER DID NOT FINISH STARTING")
if done:
    time.sleep(2)
    rcon = Rcon()
    for command in sys.argv[1:]:
        reply = rcon.send(2, command)
        print(f">>> {command}\n    {reply[:1500]}")
        pump(seconds=0.5)
    rcon.send(2, "stop")
    pump(seconds=5)
try:
    proc.wait(timeout=60)
except Exception:
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
if not done:
    print("".join(history[-60:]))
sys.exit(0 if done else 1)
