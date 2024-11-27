#!/usr/bin/env bash
# exit on error
#!/bin/bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

set -o errexit
python -m pip install --upgrade pip

python -m pip install -r requirements.txt
python -m pip install --force-reinstall -U setuptools

python manage.py collectstatic --no-input
python manage.py makemigrations
python manage.py migrate