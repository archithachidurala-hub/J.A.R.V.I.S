# J.A.R.V.I.S. – personal AI assistant with a HUD interface

Voice + text assistant that runs on your own computer.

- Arc-reactor HUD that reacts when you speak or when Jarvis answers
- Live system telemetry (CPU, memory, disk, battery, network)
- Voice input and spoken replies (Chrome or Edge)
- Commands that work with no API key: open websites and apps, Google search, play YouTube, time and date, system status
- Optional AI conversation through the Anthropic API

## Quick start (about 5 minutes)

Requirements: Python 3.9+ ([python.org](https://www.python.org/downloads/), tick "Add Python to PATH" on Windows) and Chrome or Edge.

1. Unzip the folder and open it in VS Code (File > Open Folder > `jarvis`).
2. Open the terminal in VS Code (Ctrl + `).
3. Run the one-click launcher:
   - Windows: `run.bat`
   - Mac / Linux: `./run.sh`

   The first run creates a virtual environment, installs the packages, and starts the server. Your browser opens at http://127.0.0.1:5055.
4. Click INITIALIZE.

### Manual setup (if you prefer)

```
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env
python app.py
```

## Turn on the AI brain (optional)

1. Create an API key at https://console.anthropic.com
2. Open `.env` and paste it after `ANTHROPIC_API_KEY=`
3. Restart (Ctrl+C in the terminal, then run again).

The "AI core" indicator in the top-right corner changes from offline to online.

## Things to say

- "Open YouTube" / "Open notepad" / "Open VS Code"
- "Search for best laptops 2026"
- "Play Interstellar soundtrack"
- "System status", "What time is it?"
- Anything else goes to the AI core.

## Customise

- Your name: `JARVIS_USER_NAME` in `.env`
- Add websites: edit `SITES` in `app.py`
- Add apps: edit `APPS` in `app.py`
- Colours and layout: `static/index.html` (CSS variables at the top)

## Troubleshooting

- Mic does nothing: use Chrome or Edge, and allow microphone access in the address bar.
- No sound: tick "Voice replies" and check your system volume.
- Port in use: change `JARVIS_PORT` in `.env`.
- `python` not found: reinstall Python with "Add to PATH" ticked, or use `py` on Windows / `python3` on Mac/Linux.
