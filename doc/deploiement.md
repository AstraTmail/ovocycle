# 🚀 Déploiement OvoCycle — Railway (100% gratuit)

## Pourquoi Railway ?

| Plateforme | Gratuit | SQLite persistant | Facilité |
|------------|---------|-------------------|----------|
| **Railway** | ✅ 5$/mois de crédits offerts | ✅ Volume possible | ⭐⭐⭐⭐⭐ |
| Render | ✅ mais dort après 15min | ❌ | ⭐⭐⭐⭐ |
| Fly.io | ✅ limité | ✅ | ⭐⭐⭐ |
| Heroku | ❌ payant | ❌ | ⭐⭐⭐ |

Railway offre **5$ de crédits/mois gratuits**, ce qui couvre largement un petit projet perso.

---

## Étape 1 — Préparer le dépôt Git

Dans ton dossier `ovocycle/`, ouvre un terminal :

```bash
git init
git add .
git commit -m "Initial commit — OvoCycle"
```

Puis pousse sur GitHub :

```bash
# Sur github.com → New repository → Nom: ovocycle → Create
git remote add origin https://github.com/TON_USERNAME/ovocycle.git
git branch -M main
git push -u origin main
```

---

## Étape 2 — Créer un compte Railway

1. Va sur [railway.app](https://railway.app)
2. Clique **"Start a New Project"**
3. **"Login with GitHub"** (recommandé pour le déploiement automatique)

---

## Étape 3 — Créer le projet

1. Dans Railway → **"New Project"**
2. Choisis **"Deploy from GitHub repo"**
3. Sélectionne ton repo `ovocycle`
4. Railway détecte automatiquement Python/Django ✅

---

## Étape 4 — Variables d'environnement

Dans Railway → ton service → onglet **"Variables"**, ajoute :

| Variable | Valeur |
|----------|--------|
| `SECRET_KEY` | Une clé longue et aléatoire (voir ci-dessous) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `*.up.railway.app` (ou ton domaine) |
| `CSRF_TRUSTED_ORIGINS` | `https://TON-APP.up.railway.app` |
| `DB_PATH` | `/data/db.sqlite3` |

**Générer une SECRET_KEY :**
```python
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## Étape 5 — Ajouter un volume persistant (IMPORTANT pour SQLite)

Sans volume, la base de données est **effacée à chaque déploiement**.

1. Dans Railway → ton projet → **"+ New"** → **"Volume"**
2. Nom : `ovocycle-data`
3. Mount path : `/data`
4. Clique **"Add Volume"**

Railway rattache le volume à ton service automatiquement.

---

## Étape 6 — Domaine public

1. Dans Railway → ton service → onglet **"Settings"**
2. Section **"Networking"** → **"Generate Domain"**
3. Tu obtiens une URL type `ovocycle-production.up.railway.app`

Mets à jour ta variable `CSRF_TRUSTED_ORIGINS` avec cette URL exacte :
```
https://ovocycle-production.up.railway.app
```

---

## Étape 7 — Créer le superuser

Après le premier déploiement réussi :

1. Dans Railway → ton service → onglet **"Settings"**
2. Section **"Deploy"** → champ **"Start Command"** 
3. **Temporairement** remplace par :
   ```
   python manage.py createsuperuser --noinput
   ```
4. Ajoute les variables :
   - `DJANGO_SUPERUSER_USERNAME` = `admin`
   - `DJANGO_SUPERUSER_EMAIL` = `ton@email.com`
   - `DJANGO_SUPERUSER_PASSWORD` = `MotDePasseSecret123!`
5. Redéploie → l'utilisateur est créé
6. **Remets** le start command original : `bash railway_start.sh`
7. Supprime les 3 variables `DJANGO_SUPERUSER_*`

---

## Vérification du déploiement

Dans Railway → ton service → onglet **"Deployments"** → clique sur le dernier déploiement pour voir les logs.

Tu dois voir :
```
==> Migrations...
Operations to perform: ...
==> Collectstatic...
==> Démarrage gunicorn...
[INFO] Listening at: http://0.0.0.0:XXXX
```

---

## Mises à jour futures

Chaque `git push` sur `main` redéploie automatiquement :

```bash
# Modifier du code, puis :
git add .
git commit -m "Mise à jour feature X"
git push
# Railway redéploie automatiquement ✅
```

---

## Limites du plan gratuit Railway

- **5$/mois** de crédits (≈ 500h de compute/mois)
- Pour un usage perso léger (quelques utilisateurs) : largement suffisant
- Monitoring disponible dans le dashboard Railway
- Pas de mise en veille (contrairement à Render gratuit) ✅

---

## Sauvegarde de la base de données

SQLite sur volume Railway est persistant, mais pense à faire des sauvegardes manuelles :

```bash
# Depuis Railway CLI (optionnel) :
railway run python manage.py dumpdata > backup_$(date +%Y%m%d).json
```

Ou via l'admin Django (`/admin/`) → exporter les données.

---

## En cas de problème

| Symptôme | Solution |
|----------|----------|
| `DisallowedHost` | Vérifier `ALLOWED_HOSTS` dans les variables |
| Erreur CSRF | Vérifier `CSRF_TRUSTED_ORIGINS` avec le bon domaine HTTPS |
| DB vide à chaque déploiement | Le volume `/data` n'est pas monté → refaire étape 5 |
| Static files 404 | Vérifier que `collectstatic` tourne dans les logs |
| App ne démarre pas | Regarder les logs dans Railway → onglet Deployments |