#!/usr/bin/env bash
# Exit on error
set -o errexit

# Create and activate a virtual environment
python -m venv /opt/render/project/.venv
source /opt/render/project/.venv/bin/activate

# Upgrade pip to the latest version
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate