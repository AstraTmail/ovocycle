# 🥚 OvoCycle — Application Django de gestion de couveuse

Application web complète pour analyser les cycles d'incubation et améliorer les taux d'éclosion.

---

## 🚀 Installation rapide (3 étapes)

### Étape 1 — Prérequis

- Python 3.10 ou supérieur
- pip

Vérifiez : `python3 --version`

---

### Étape 2 — Installation

```bash
# Cloner ou extraire le projet
cd ovocycle

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate          # Linux/Mac
# ou: venv\Scripts\activate       # Windows

# Installer les dépendances
pip install -r requirements.txt

# Créer la base de données
python manage.py makemigrations incubation
python manage.py makemigrations
python manage.py migrate

# Créer le superutilisateur admin
python manage.py createsuperuser

# (Optionnel) Charger des données de démonstration
python manage.py create_demo_data
```

---

### Étape 3 — Lancement

```bash
python manage.py runserver
```

Ouvrez votre navigateur sur : **http://127.0.0.1:8000**

Interface admin : **http://127.0.0.1:8000/admin**

---

## 📁 Structure du projet

```
ovocycle/
├── manage.py
├── requirements.txt
├── setup.sh                   ← Script d'installation automatique
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── incubation/            ← App principale
│   │   ├── models.py          ← IncubationBatch, Egg, EggObservation, IncubatorLog
│   │   ├── views.py           ← Vues CBV + endpoints HTMX
│   │   ├── forms.py           ← Formulaires
│   │   ├── urls.py            ← Routes
│   │   ├── admin.py           ← Interface admin
│   │   └── management/commands/create_demo_data.py
│   │
│   ├── analytics/             ← Tableau de bord analytique
│   │   ├── views.py
│   │   └── urls.py
│   │
│   └── core/                  ← Utilitaires partagés
│       ├── context_processors.py
│       └── templatetags/ovo_tags.py
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── batches/               ← Lots d'incubation
│   ├── eggs/                  ← Œufs & observations
│   ├── analytics/             ← Graphiques & stats
│   └── components/            ← Composants réutilisables
│
└── static/
    └── css/custom.css
```

---

## ⚡ Fonctionnalités principales

| Fonctionnalité | Description |
|---|---|
| **Dashboard** | Lots actifs, KPI, alertes du jour, prochains événements |
| **Gestion des lots** | Créer, suivre, terminer un cycle d'incubation |
| **Timeline visuelle** | Entrée → Mirage 1 → Mirage 2 → Mirage 3 → Éclosion |
| **Dates automatiques** | Mirages et éclosion calculés selon l'espèce |
| **Suivi individuel** | Statut par œuf, observations, historique |
| **Heatmap grille** | Visualisation positionnelle de tous les œufs |
| **Observations mirages** | Enregistrement fertile/clair/mort pour chaque mirage |
| **Journal couveuse** | Log température, humidité, événements |
| **Alertes HTMX** | Bannière auto-rafraîchie : mirages, lockdown, éclosion |
| **Analytique** | Graphiques taux d'éclosion, causes d'échec, par espèce |
| **Admin Django** | Interface complète pour toutes les données |

---

## 🐣 Espèces supportées

| Espèce | Durée |
|--------|-------|
| Poulet | 21 jours |
| Caille | 17 jours |
| Canard | 28 jours |
| Dinde  | 28 jours |
| Oie    | 30 jours |
| Faisan | 24 jours |

---

## 🛠️ Stack technique

- **Backend** : Django 5.x + SQLite
- **Frontend** : TailwindCSS + DaisyUI (via CDN)
- **Interactions** : HTMX (pas de rechargement de page)
- **UI légère** : AlpineJS
- **Graphiques** : Chart.js

---

## 📝 Notes de développement

### Passer à PostgreSQL
```python
# Dans config/settings.py, remplacer DATABASES par :
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ovocycle',
        'USER': 'postgres',
        'PASSWORD': 'votre_mot_de_passe',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Variables d'environnement (production)
```bash
export SECRET_KEY="votre-cle-secrete-longue"
export DEBUG="False"
export ALLOWED_HOSTS="votre-domaine.com"
```

### Identifiants du superutilisateur
| Paramètre | Valeur    |
|-----------|-----------|
| Username  | AstraCode |
| Password  | Oumar2007 |

| Espèce | Durée |
|--------|-------|
| Poulet | 21 jours |
| Caille | 17 jours |
| Canard | 28 jours |
| Dinde  | 28 jours |
| Oie    | 30 jours |
| Faisan | 24 jours |
