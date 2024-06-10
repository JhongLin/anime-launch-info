#!/usr/bin/env bash

python3.11 -m venv venv
source ./venv/bin/activate
pip list -o | cut -f1 -d' ' | tr " " "\n" | tail -n +3 | xargs pip install --upgrade
pip install pytest-playwright
playwright install && playwright install-deps
