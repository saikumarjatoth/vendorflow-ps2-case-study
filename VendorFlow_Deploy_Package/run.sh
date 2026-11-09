#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
python -m pip install -r requirements.txt
exec streamlit run app.py --server.address 127.0.0.1 --server.port 8501
