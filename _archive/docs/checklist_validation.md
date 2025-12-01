# Check-list Validation - Refactoring Clients

## Date : 2025-09-25

## 🎯 10 Clics de Validation

### Préparation
- **Serveur** : `python manage.py runserver 127.0.0.1:8000`
- **Navigateur** : Mode navigation privée (pas de cache)
- **URLs de test** : Notez les résultats dans chaque case ☐

---

## 🔒 Test 1 : Hors Connexion

### 1.1 Accès direct `/clients/`
```
☐ Aller sur: http://127.0.0.1:8000/clients/
☐ Résultat attendu: Redirection vers /auth/login/?next=/clients/
☐ Résultat obtenu: _______________
```

### 1.2 Ancienne URL admin
```
☐ Aller sur: http://127.0.0.1:8000/admin/sales/customer/
☐ Résultat attendu: Redirection 301 vers /clients/ puis login
☐ Résultat obtenu: _______________
```

---

## 👤 Test 2 : Employé (editeur@vignoble.fr)

### 2.1 Connexion
```
☐ Aller sur: http://127.0.0.1:8000/auth/login/
☐ Email: editeur@vignoble.fr
☐ Mot de passe: [demander à l'admin]
☐ Résultat attendu: Connexion réussie
☐ Résultat obtenu: _______________
```

### 2.2 Navigation menu
```
☐ Cliquer sur: Menu "Clients" dans la barre de navigation
☐ Résultat attendu: Dropdown avec "Liste des clients" et "Nouveau client"
☐ Résultat obtenu: _______________
```

### 2.3 Liste des clients
```
☐ Cliquer sur: "Liste des clients"
☐ URL attendue: /clients/
☐ Résultat attendu: Page avec liste des clients de son organisation
☐ Résultat obtenu: _______________
```

### 2.4 Nouveau client
```
☐ Cliquer sur: "Nouveau client" (depuis le menu ou bouton)
☐ URL attendue: /clients/nouveau/
☐ Résultat attendu: Formulaire de création client
☐ Résultat obtenu: _______________
```

### 2.5 Test ancienne URL
```
☐ Taper dans la barre d'adresse: /admin/sales/customer/
☐ Résultat attendu: Redirection automatique vers /clients/
☐ Résultat obtenu: _______________
```

---

## 👨‍💼 Test 3 : Admin Organisation (proprietaire@vignoble.fr)

### 3.1 Connexion admin
```
☐ Se déconnecter puis se reconnecter avec: proprietaire@vignoble.fr
☐ Résultat attendu: Connexion réussie avec plus de droits
☐ Résultat obtenu: _______________
```

### 3.2 Export clients (admin seulement)
```
☐ Aller sur: /clients/
☐ Chercher: Bouton ou lien "Export" 
☐ Résultat attendu: Bouton visible pour admin, pas pour employé
☐ Résultat obtenu: _______________
```

---

## 🔧 Test 4 : SuperAdmin (demo@monchai.fr)

### 4.1 Connexion superadmin
```
☐ Se connecter avec: demo@monchai.fr
☐ Résultat attendu: Accès complet
☐ Résultat obtenu: _______________
```

### 4.2 Admin Django technique
```
☐ Aller sur: /admin/
☐ Résultat attendu: Interface admin Django accessible
☐ Chercher: Section "Sales" → "Clients" 
☐ Résultat attendu: Soit absent, soit avec permissions restreintes
☐ Résultat obtenu: _______________
```

---

## 🔍 Test 5 : Vérifications Techniques

### 5.1 Recherche liens cassés
```
☐ Ouvrir: Outils développeur (F12)
☐ Onglet: Console
☐ Naviguer sur: /clients/ et sous-pages
☐ Résultat attendu: Aucune erreur 404 dans la console
☐ Résultat obtenu: _______________
```

### 5.2 Test responsive
```
☐ Ouvrir: Outils développeur → Mode responsive
☐ Tester: /clients/ sur mobile (375px)
☐ Résultat attendu: Interface adaptée mobile
☐ Résultat obtenu: _______________
```

---

## 📊 Résultats Attendus

### ✅ Succès Total
- **10/10 tests** passent
- **Aucun lien** vers `/admin/sales/customer/` dans la navigation
- **Redirections 301** fonctionnent
- **Permissions** respectées par rôle

### ⚠️ Problèmes Possibles
- **Erreur 500** → Problème de configuration
- **Erreur 403** → Problème de permissions  
- **Erreur 404** → URL mal configurée
- **Pas de redirection** → Middleware non actif

### 🚨 Échec Critique
- **Admin encore accessible** pour utilisateurs normaux
- **Liens cassés** dans la navigation
- **Données cross-organisation** visibles

---

## 📝 Rapport de Test

```
Date: _______________
Testeur: _______________

Résultats:
☐ Test 1 (Hors connexion): ___/2
☐ Test 2 (Employé): ___/5  
☐ Test 3 (Admin Org): ___/2
☐ Test 4 (SuperAdmin): ___/2
☐ Test 5 (Technique): ___/2

Total: ___/13

Problèmes identifiés:
_________________________________
_________________________________
_________________________________

Recommandations:
_________________________________
_________________________________
_________________________________
```

---

**Validation manuelle : Prêt pour les tests !** 🧪
