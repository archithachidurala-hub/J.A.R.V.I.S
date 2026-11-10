#!/usr/bin/env bash
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Setting up J.A.R.V.I.S. for the first time..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip -q
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi
[ -f .env ] || cp .env.example .env
python app.py
