#!/bin/bash
set -e

mkdir -p /data 2>/dev/null || true

echo "==> Install deps..."
pip install -r requirements.txt --quiet

echo "==> Migrations..."
python manage.py migrate --noinput

echo "==> Collectstatic..."
python manage.py collectstatic --noinput

echo "==> Démarrage gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --threads 2 \
  --timeout 60 \
  --log-level info