# Guide d'accès à l'Import CSV - Mon Chai V1

## 🎯 Où trouver la fonction d'import CSV ?

### 1. **Accès direct par URL**
```
http://127.0.0.1:8000/ref/import/
```

### 2. **Navigation dans l'interface**
1. Connectez-vous avec un compte **administrateur**
2. Allez sur la page **Référentiels** : `http://127.0.0.1:8000/ref/`
3. Scrollez vers le bas jusqu'à la section "Prochaines étapes"
4. Cliquez sur le bouton **"Import CSV en masse"**

### 3. **Comptes administrateurs disponibles**
Voici les comptes avec droits admin que vous pouvez utiliser :

- **demo@monchai.fr** (Domaine des Vignes d'Or - owner)
- **proprietaire@vignoble.fr** (Vignoble des Coteaux - owner)  
- **moutier.norbert37@gmail.com** (Domaine du Moutier - owner)
- **test@audit.com** (Test Org - admin)

### 4. **Pourquoi vous ne voyez peut-être pas le lien ?**

#### ❌ **Causes possibles :**
- Vous n'êtes pas connecté
- Votre compte n'a pas les droits admin/owner
- Vous regardez la mauvaise page

#### ✅ **Solution :**
1. **Vérifiez votre rôle** : Seuls les admin+ voient le bouton d'import
2. **Connectez-vous avec un compte admin** (voir liste ci-dessus)
3. **Allez sur /ref/** (page d'accueil des référentiels)
4. **Cherchez en bas de page** la section "Prochaines étapes"

## 🚀 Fonctionnalités d'import disponibles

### **Types de référentiels supportés :**
- ✅ **Cépages** (nom, couleur, code, notes)
- ✅ **Parcelles** (nom, surface_ha, notes)
- ✅ **Unités** (nom, code, notes)
- ✅ **Cuvées** (nom, notes)
- ✅ **Entrepôts** (nom, notes)

### **Formats supportés :**
- ✅ **CSV** avec délimiteurs : `;` `,` `\t`
- ✅ **Encodages** : UTF-8, UTF-8-BOM, Latin-1
- ✅ **Taille max** : 10MB, 10 000 lignes

### **Workflow d'import :**
1. **Sélection** : Choisir le type + uploader le fichier
2. **Prévisualisation** : Mapper les colonnes + voir les erreurs
3. **Import** : Exécution avec rapport détaillé

## 🔧 Test rapide

### **Créer un fichier CSV de test :**
```csv
nom,couleur,notes
Cabernet Sauvignon,rouge,Cépage noble de Bordeaux
Chardonnay,blanc,Cépage bourguignon
Pinot Noir,rouge,Cépage de Bourgogne
```

### **Étapes de test :**
1. Sauvegardez le contenu ci-dessus dans `test_cepages.csv`
2. Connectez-vous avec un compte admin
3. Allez sur `http://127.0.0.1:8000/ref/import/`
4. Sélectionnez "Cépages" et uploadez le fichier
5. Suivez le workflow de prévisualisation et import

## 🆘 Dépannage

### **Si la page ne charge pas :**
```bash
# Vérifier que le serveur fonctionne
python manage.py runserver

# Tester l'URL directement
curl -I http://127.0.0.1:8000/ref/import/
```

### **Si vous n'avez pas de compte admin :**
```bash
# Créer un superuser
python manage.py createsuperuser

# Ou utiliser un compte existant (voir liste ci-dessus)
```

### **Si le bouton n'apparaît pas :**
- Vérifiez que vous êtes sur `/ref/` (pas `/ref/cepages/`)
- Vérifiez votre rôle dans l'organisation
- Scrollez jusqu'en bas de la page

---

**URL de test direct :** http://127.0.0.1:8000/ref/import/
**Page référentiels :** http://127.0.0.1:8000/ref/
