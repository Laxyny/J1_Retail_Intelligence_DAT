#!/bin/bash
set -euo pipefail
python3 -m venv /tmp/retail-j3-venv
/tmp/retail-j3-venv/bin/python -m pip install -r /work/configuration/requirements.lock.txt
