"""
J.A.R.V.I.S. - a local AI assistant with a futuristic HUD.

Run:  python app.py
Open: http://127.0.0.1:5055  (Chrome or Edge recommended for voice)
"""
import datetime
import os
import platform
import re
import shlex
import subprocess
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path

import psutil
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")

USER_NAME = os.getenv("JARVIS_USER_NAME", "sir").strip() or "sir"
MODEL = os.getenv("JARVIS_MODEL", "claude-sonnet-5-5").strip()
API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
PORT = int(os.getenv("JARVIS_PORT", "5055"))
AUTO_OPEN = os.getenv("JARVIS_AUTO_OPEN", "true").lower() == "true"
SYSTEM_OS = platform.system()  # Windows / Darwin / Linux

app = Flask(__name__, static_folder=str(BASE / "static"), static_url_path="/static")

# --------------------------------------------------------------------------
# AI brain (optional): works only if ANTHROPIC_API_KEY is set in .env
# --------------------------------------------------------------------------
client = None
if API_KEY:
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=API_KEY)
    except Exception as exc:  # pragma: no cover
        print(f"[JARVIS] Could not start AI core: {exc}")


def system_prompt() -> str:
    now = datetime.datetime.now().strftime("%A, %d %B %Y, %H:%M")
    return (
        "You are J.A.R.V.I.S., a calm, highly capable AI butler inspired by the "
        "assistant from the Iron Man films. Address the user as "
        f"'{USER_NAME}'. Your replies are spoken aloud, so keep them short "
        "(one to three sentences), plain text only, no markdown, no lists. "
        "Use dry, understated British wit sparingly. Be accurate; if you do not "
        "know something, say so. You can run these local commands on the user's "
        "computer when asked: open websites and apps, search Google, play "
        "YouTube videos, report system status, tell the time. "
        f"Current local time: {now}. Host: {platform.node()} ({SYSTEM_OS})."
    )


def ask_claude(history, message: str) -> str:
    msgs = [
        {"role": m["role"], "content": str(m["content"])}
        for m in (history or [])
        if m.get("role") in ("user", "assistant") and m.get("content")
    ][-10:]
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    msgs.append({"role": "user", "content": message})
    resp = client.messages.create(
        model=MODEL, max_tokens=300, system=system_prompt(), messages=msgs
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


# --------------------------------------------------------------------------
# System telemetry
# --------------------------------------------------------------------------
psutil.cpu_percent(interval=None)  # prime the counter
_last_net = (time.time(), psutil.net_io_counters())


def read_stats() -> dict:
    global _last_net
    now = time.time()
    net = psutil.net_io_counters()
    dt = max(now - _last_net[0], 1e-6)
    down = (net.bytes_recv - _last_net[1].bytes_recv) / dt
    up = (net.bytes_sent - _last_net[1].bytes_sent) / dt
    _last_net = (now, net)

    try:
        disk = psutil.disk_usage(Path.home().anchor or "/").percent
    except Exception:
        disk = 0
    battery = None
    try:
        b = psutil.sensors_battery()
        if b is not None:
            battery = {"percent": round(b.percent), "plugged": bool(b.power_plugged)}
    except Exception:
        pass

    return {
        "cpu": round(psutil.cpu_percent(interval=None)),
        "ram": round(psutil.virtual_memory().percent),
        "disk": round(disk),
        "battery": battery,
        "net_down": down,
        "net_up": up,
        "uptime": int(now - psutil.boot_time()),
        "host": platform.node(),
        "os": f"{SYSTEM_OS} {platform.release()}",
        "ai": client is not None,
    }


def stats_sentence() -> str:
    s = read_stats()
    out = f"CPU at {s['cpu']} percent, memory at {s['ram']} percent, disk at {s['disk']} percent."
    if s["battery"]:
        state = "charging" if s["battery"]["plugged"] else "on battery"
        out += f" Battery is at {s['battery']['percent']} percent and {state}."
    return out


# --------------------------------------------------------------------------
# Local commands (work even without an API key)
# --------------------------------------------------------------------------
SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "stack overflow": "https://stackoverflow.com",
    "stackoverflow": "https://stackoverflow.com",
    "maps": "https://maps.google.com",
    "google maps": "https://maps.google.com",
    "linkedin": "https://www.linkedin.com",
    "whatsapp": "https://web.whatsapp.com",
    "wikipedia": "https://www.wikipedia.org",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "claude": "https://claude.ai",
}

APPS = {
    "Windows": {
        "notepad": "notepad",
        "calculator": "calc",
        "file explorer": "explorer",
        "explorer": "explorer",
        "terminal": "start cmd",
        "command prompt": "start cmd",
        "vs code": "code",
        "visual studio code": "code",
        "paint": "mspaint",
        "task manager": "taskmgr",
    },
    "Darwin": {
        "notepad": "open -a TextEdit",
        "calculator": "open -a Calculator",
        "finder": "open -a Finder",
        "file explorer": "open -a Finder",
        "terminal": "open -a Terminal",
        "vs code": "open -a 'Visual Studio Code'",
        "visual studio code": "open -a 'Visual Studio Code'",
    },
    "Linux": {
        "notepad": "gedit",
        "calculator": "gnome-calculator",
        "file explorer": "xdg-open .",
        "terminal": "x-terminal-emulator",
        "vs code": "code",
        "visual studio code": "code",
    },
}


def launch_app(name: str) -> bool:
    cmd = APPS.get(SYSTEM_OS, {}).get(name)
    if not cmd:
        return False
    try:
        if SYSTEM_OS == "Windows":
            subprocess.Popen(cmd, shell=True)
        else:
            subprocess.Popen(shlex.split(cmd))
        return True
    except Exception:
        return False


def greeting() -> str:
    h = datetime.datetime.now().hour
    return "Good morning" if h < 12 else "Good afternoon" if h < 18 else "Good evening"


def handle_local(text: str):
    t = text.lower().strip(" .!?")
    t = re.sub(r"^(hey |ok |okay )?jarvis[, ]*", "", t).strip()
    t = re.sub(r"^(please |can you |could you |would you )+", "", t).strip()
    if not t:
        return f"At your service, {USER_NAME}."

    if re.search(r"\b(what('?s| is) the time|current time|time is it|tell me the time)\b", t):
        return datetime.datetime.now().strftime("It is %I:%M %p, ") + USER_NAME + "."
    if re.search(r"\b(today'?s date|what('?s| is) the date|what day is it|which day)\b", t):
        return datetime.datetime.now().strftime("Today is %A, %d %B %Y.")

    m = re.match(r"(?:search|google|look up)(?: for)?\s+(.+)", t)
    if m:
        q = m.group(1)
        webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote_plus(q))
        return f"Searching the web for {q}."

    m = re.match(r"play\s+(.+)", t)
    if m:
        q = re.sub(r"\s+on youtube$", "", m.group(1))
        webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(q))
        return f"Pulling up {q} on YouTube."

    m = re.match(r"(?:open|launch|start)\s+(.+)", t)
    if m:
        target = re.sub(r"^(the|my)\s+", "", m.group(1)).strip()
        if launch_app(target):
            return f"Opening {target}."
        if target in SITES:
            webbrowser.open(SITES[target])
            return f"Opening {target}."
        if re.match(r"^[\w-]+(\.[\w-]+)+$", target):
            webbrowser.open("https://" + target)
            return f"Opening {target}."
        return f"I don't have {target} in my launch list yet, {USER_NAME}. You can add it in app.py."

    if re.search(r"\b(system (status|report|check)|status report|cpu|memory|ram|battery|disk)\b", t):
        return stats_sentence()
    if re.match(r"^(hello|hi|hey|good (morning|afternoon|evening))\b", t):
        return f"{greeting()}, {USER_NAME}. How may I assist you?"
    if re.search(r"\b(thank you|thanks)\b", t):
        return "Always a pleasure."
    if re.search(r"\b(what can you do|help|commands)\b", t):
        return (
            "I can open websites and apps, search the web, play YouTube, tell the time, "
            "report system status, and hold a conversation when my AI core is connected."
        )
    return None


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/stats")
def api_stats():
    return jsonify(read_stats())


@app.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return jsonify({"reply": "I didn't catch that."})

    local = handle_local(message)
    if local:
        return jsonify({"reply": local, "source": "local"})

    if client is None:
        return jsonify(
            {
                "reply": (
                    f"My conversation core is offline, {USER_NAME}. Add your "
                    "ANTHROPIC_API_KEY to the .env file and restart me. Meanwhile, "
                    "try 'open YouTube' or 'system status'."
                ),
                "source": "offline",
            }
        )
    try:
        return jsonify({"reply": ask_claude(data.get("history"), message), "source": "ai"})
    except Exception as exc:
        print(f"[JARVIS] AI error: {exc}")
        return jsonify(
            {"reply": f"I'm having trouble reaching my AI core, {USER_NAME}. Check the terminal for details."}
        )


if __name__ == "__main__":
    url = f"http://127.0.0.1:{PORT}"
    print("\n  J.A.R.V.I.S. online ->", url)
    print("  AI core:", "connected" if client else "offline (add ANTHROPIC_API_KEY to .env)", "\n")
    if AUTO_OPEN:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=PORT, debug=False)
