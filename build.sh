#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "--- Installing Python dependencies ---"
pip install -r requirements.txt

echo "--- Collecting static assets with WhiteNoise ---"
python manage.py collectstatic --no-input

echo "--- Applying database migrations ---"
python manage.py migrate

echo "--- Seeding default demo data if database is empty ---"
python manage.py seed_demo_data || true

echo "--- Build complete! ---"
