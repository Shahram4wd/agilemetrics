#!/usr/bin/env bash
# exit on error
set -o errexit  

# Activate the virtual environment (Render typically does this)
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Collect static files, apply migrations
python manage.py collectstatic --no-input
python manage.py migrate
