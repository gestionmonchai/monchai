# Déploiement sur PythonAnywhere

## Étape 1 : Créer un compte

1. Allez sur https://www.pythonanywhere.com
2. Créez un compte gratuit (ex: `monchai`)
3. Votre site sera accessible sur `monchai.pythonanywhere.com`

## Étape 2 : Uploader le code

### Option A : Via GitHub (recommandé)
Dans la console Bash de PythonAnywhere :
```bash
cd ~
git clone https://github.com/gestionmonchai/mon-chai.git
```

### Option B : Upload ZIP
1. Compressez le dossier en ZIP
2. Files → Upload dans PythonAnywhere
3. Bash → `unzip mon-chai.zip`

## Étape 3 : Créer l'environnement virtuel

Dans la console Bash :
```bash
cd ~/mon-chai
mkvirtualenv --python=/usr/bin/python3.10 monchai-env
pip install -r requirements.txt
```

## Étape 4 : Configurer le settings

Éditez `monchai/settings_prod.py` :
```python
ALLOWED_HOSTS = [
    'VOTREUSERNAME.pythonanywhere.com',  # Remplacez VOTREUSERNAME
    ...
]
```

## Étape 5 : Initialiser la base de données

```bash
cd ~/mon-chai
python manage.py migrate --settings=monchai.settings_prod
python manage.py collectstatic --settings=monchai.settings_prod --noinput
python manage.py createsuperuser --settings=monchai.settings_prod
```

## Étape 6 : Configurer l'application Web

1. Onglet **Web** → Add a new web app
2. Choisir **Manual configuration** → **Python 3.10**
3. Configurer :

### Source code
```
/home/VOTREUSERNAME/mon-chai
```

### Virtualenv
```
/home/VOTREUSERNAME/.virtualenvs/monchai-env
```

### WSGI file
Cliquez sur le lien du fichier WSGI et remplacez tout par :

```python
import os
import sys

# Chemin vers votre projet
path = '/home/VOTREUSERNAME/mon-chai'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'monchai.settings_prod'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Static files
Ajoutez ces mappings :

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/VOTREUSERNAME/mon-chai/staticfiles` |
| `/media/` | `/home/VOTREUSERNAME/mon-chai/media` |

## Étape 7 : Reload

Cliquez sur le gros bouton vert **Reload**

Votre site est maintenant accessible sur `https://VOTREUSERNAME.pythonanywhere.com`

---

## Mise à jour du site

Quand vous modifiez le code en local :

```bash
# En local
git add .
git commit -m "Description des changements"
git push

# Sur PythonAnywhere (console Bash)
cd ~/mon-chai
git pull
python manage.py migrate --settings=monchai.settings_prod
python manage.py collectstatic --settings=monchai.settings_prod --noinput
```

Puis **Reload** dans l'onglet Web.

---

## Dépannage

### Erreur 500
- Vérifiez les logs : Web → Error log
- Vérifiez que `ALLOWED_HOSTS` contient votre domaine

### Fichiers statiques manquants
```bash
python manage.py collectstatic --settings=monchai.settings_prod --noinput
```

### Base de données
La version gratuite utilise SQLite. Pour PostgreSQL, il faut un compte payant.
