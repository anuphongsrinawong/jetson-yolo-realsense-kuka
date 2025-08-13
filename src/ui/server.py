from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, render_template, request

PROJECT_ROOT = Path("/home/god/jetson-yolo-realsense-kuka").resolve()
VENV_PY = PROJECT_ROOT / ".venv" / "bin" / "python"
MAIN_PY = PROJECT_ROOT / "src" / "main.py"
CONFIG_YAML = PROJECT_ROOT / "config" / "config.yaml"
RUN_LOG = PROJECT_ROOT / "run.log"

# Mirror env from scripts/run.sh to see system dist-packages (pyrealsense2/opencv)
PYTHONPATH_EXTRA = ":".join([
    "/usr/lib/python3/dist-packages",
    "/usr/local/lib/python3.10/dist-packages",
    "/usr/local/lib/python3/dist-packages",
    str(PROJECT_ROOT / "src"),
])


class AppProcessManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._proc: Optional[subprocess.Popen] = None

    def is_running(self) -> bool:
        with self._lock:
            return self._proc is not None and self._proc.poll() is None

    def start_realtime(self) -> dict:
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                return {"ok": True, "message": "Already running", "pid": self._proc.pid}

            env = os.environ.copy()
            env["PYTHONPATH"] = f"{PYTHONPATH_EXTRA}:{env.get('PYTHONPATH','')}"
            cmd = [str(VENV_PY), str(MAIN_PY), "--config", str(CONFIG_YAML)]
            # Start detached; inherit stdout/stderr so logs go to file via app's logger
            self._proc = subprocess.Popen(cmd, env=env, cwd=str(PROJECT_ROOT))
            return {"ok": True, "message": "Started", "pid": self._proc.pid}

    def stop(self) -> dict:
        with self._lock:
            if self._proc is None or self._proc.poll() is not None:
                self._proc = None
                return {"ok": True, "message": "Not running"}
            try:
                self._proc.send_signal(signal.SIGINT)
            except Exception:
                try:
                    self._proc.terminate()
                except Exception:
                    pass
            return {"ok": True, "message": "Stopping"}

    def run_single_shot(self, timeout_s: float = 30.0) -> dict:
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{PYTHONPATH_EXTRA}:{env.get('PYTHONPATH','')}"
        cmd = [str(VENV_PY), str(MAIN_PY), "--config", str(CONFIG_YAML), "--mode", "single"]
        try:
            out = subprocess.check_output(cmd, env=env, cwd=str(PROJECT_ROOT), timeout=timeout_s)
            text = out.decode("utf-8", errors="ignore").strip()
            # Extract last JSON line if noise exists
            json_line = None
            for line in reversed(text.splitlines()):
                if line.startswith("{") and line.endswith("}"):
                    json_line = line
                    break
            if json_line is None:
                return {"ok": False, "error": "No JSON payload captured", "raw": text[-1000:]}
            payload = json.loads(json_line)
            return {"ok": True, "payload": payload}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Single-shot timed out"}
        except Exception as e:
            return {"ok": False, "error": str(e)}


app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "src" / "ui" / "templates"),
    static_folder=str(PROJECT_ROOT / "src" / "ui" / "static"),
)
manager = AppProcessManager()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/status")
def status():
    return jsonify({
        "running": manager.is_running(),
    })


@app.post("/start")
def start():
    res = manager.start_realtime()
    return jsonify(res)


@app.post("/stop")
def stop():
    res = manager.stop()
    return jsonify(res)


@app.post("/single")
def single():
    res = manager.run_single_shot()
    return jsonify(res)


@app.get("/log")
def log_tail():
    n = int(request.args.get("n", 200))
    try:
        with open(RUN_LOG, "r") as f:
            lines = f.readlines()
        tail = "".join(lines[-n:])
    except Exception:
        tail = ""
    return jsonify({"log": tail})


if __name__ == "__main__":
    host = os.environ.get("UI_HOST", "0.0.0.0")
    port = int(os.environ.get("UI_PORT", "8080"))
    app.run(host=host, port=port, debug=False)
