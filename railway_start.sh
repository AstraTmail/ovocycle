#!/bin/bash
set -e

echo "==> Migrations..."
python manage.py migrate --noinput

echo "==> Créer superuser si inexistant..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='AstraCode').exists():
    User.objects.create_superuser('AstraCode', 'ton@email.com', 'Oumar2007')
    print('Superuser créé')
else:
    print('Superuser existe déjà')
"

echo "==> Collectstatic..."
python manage.py collectstatic --noinput

echo "==> Démarrage gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --threads 2 \
  --timeout 60 \
  --log-level info