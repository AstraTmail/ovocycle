#!/bin/bash
# ─────────────────────────────────────────────────────────
#  OvoCycle — Script d'installation & démarrage
#  Usage: bash setup.sh
# ─────────────────────────────────────────────────────────

set -e

echo ""
echo "🥚  OvoCycle — Installation"
echo "─────────────────────────────────────────────────────"

# 1. Environnement virtuel
echo ""
echo "📦 Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# 2. Installation des dépendances
echo ""
echo "📦 Installation des dépendances..."
pip install -r requirements.txt --quiet

# 3. Migrations
echo ""
echo "🗄️  Création de la base de données..."
python manage.py makemigrations incubation
python manage.py makemigrations
python manage.py migrate

# 4. Superuser
echo ""
echo "👤 Création du compte administrateur..."
echo "   (laissez vide pour passer)"
python manage.py createsuperuser --noinput \
  --username admin \
  --email admin@ovocycle.local 2>/dev/null || echo "   Compte admin déjà existant."

# 5. Données de démo (optionnel)
echo ""
read -p "📊 Charger des données de démonstration ? (o/N) " load_demo
if [[ "$load_demo" =~ ^[Oo]$ ]]; then
  python manage.py loaddata demo_data.json 2>/dev/null || \
  python manage.py create_demo_data 2>/dev/null || \
  echo "   Pas de données de démo disponibles (normal au premier lancement)."
fi

# 6. Static files
python manage.py collectstatic --noinput --clear -v 0

echo ""
echo "✅  Installation terminée !"
echo ""
echo "─────────────────────────────────────────────────────"
echo "🚀  Lancement du serveur..."
echo "    → http://127.0.0.1:8000"
echo "    → Admin : http://127.0.0.1:8000/admin"
echo "    → Mot de passe admin : à définir via 'python manage.py changepassword admin'"
echo "─────────────────────────────────────────────────────"
echo ""

python manage.py runserver
