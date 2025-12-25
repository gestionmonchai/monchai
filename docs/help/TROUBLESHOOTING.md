# 🔧 Guide de Résolution des Problèmes MonChai

> **Version:** 2.0  
> **Dernière mise à jour:** Décembre 2024

---

## 🔐 Problèmes d'Authentification

### Je ne peux pas me connecter

**Symptômes :**
- Message "Email ou mot de passe incorrect"
- Page de connexion qui se recharge sans erreur

**Solutions :**
1. **Vérifiez votre email** - Assurez-vous qu'il n'y a pas de faute de frappe
2. **Vérifiez les majuscules** - Le mot de passe est sensible à la casse
3. **Réinitialisez votre mot de passe** - Utilisez "Mot de passe oublié"
4. **Vérifiez votre compte** - Votre compte peut être suspendu
5. **Videz le cache** - `Ctrl+Shift+Delete` puis reconnectez-vous

**Si le problème persiste :**
- Contactez l'administrateur de votre organisation
- Envoyez un email à support@monchai.fr

### Je ne reçois pas l'email de réinitialisation

**Solutions :**
1. **Vérifiez les spams/indésirables**
2. **Attendez quelques minutes** - Les emails peuvent prendre du temps
3. **Vérifiez l'adresse email** - Est-ce bien celle de votre compte ?
4. **Réessayez** - Demandez un nouvel email de réinitialisation
5. **Vérifiez votre serveur mail** - Certains filtres bloquent les emails automatiques

### Ma session expire trop vite

**Solutions :**
1. **Cochez "Se souvenir de moi"** à la connexion
2. **Vérifiez les cookies** - Ils doivent être autorisés pour monchai.fr
3. **Vérifiez votre navigateur** - Certains modes de navigation privée suppriment les sessions

---

## 🏢 Problèmes d'Organisation

### Je ne vois pas mon organisation

**Symptômes :**
- Redirection vers la page de sélection d'organisation
- Message "Aucune organisation trouvée"

**Solutions :**
1. **Vérifiez votre email** - Êtes-vous connecté avec le bon compte ?
2. **Acceptez l'invitation** - Vérifiez vos emails pour une invitation en attente
3. **Créez une organisation** - Si vous n'en avez pas, créez-en une nouvelle
4. **Contactez l'admin** - Demandez à être réinvité si nécessaire

### Je ne peux pas accéder à certaines fonctionnalités

**Symptômes :**
- Menu grisé ou absent
- Message "Permission refusée"
- Redirection vers le dashboard

**Solutions :**
1. **Vérifiez votre rôle** - Allez dans Mon profil pour voir vos permissions
2. **Demandez une élévation** - Contactez un Admin ou Owner
3. **Changez d'organisation** - Certaines fonctions sont spécifiques à l'org

**Rôles et accès :**
| Rôle | Accès |
|------|-------|
| Viewer | Lecture seule |
| Member | Création/modification limitée |
| Manager | Gestion complète + invitations |
| Admin | Tout sauf suppression org |
| Owner | Accès complet |

---

## 📊 Problèmes d'Affichage

### La page ne charge pas

**Solutions :**
1. **Rafraîchissez** - `F5` ou `Ctrl+R`
2. **Videz le cache** - `Ctrl+Shift+Delete`
3. **Essayez un autre navigateur**
4. **Vérifiez votre connexion internet**
5. **Attendez quelques minutes** - Le serveur peut être temporairement surchargé

### Les données ne s'affichent pas

**Solutions :**
1. **Vérifiez vos filtres** - Un filtre peut cacher les données
2. **Vérifiez l'organisation** - Êtes-vous dans la bonne org ?
3. **Rafraîchissez la page**
4. **Vérifiez la période** - Certaines vues ont des filtres de date

### L'interface est cassée / mal affichée

**Solutions :**
1. **Videz le cache** - `Ctrl+Shift+Delete`
2. **Désactivez les extensions** - Certaines extensions perturbent l'affichage
3. **Essayez un autre navigateur**
4. **Vérifiez le zoom** - `Ctrl+0` pour remettre à 100%
5. **Mettez à jour votre navigateur**

### Les graphiques ne s'affichent pas

**Solutions :**
1. **Activez JavaScript** - Les graphiques nécessitent JS
2. **Vérifiez les données** - Pas de graphique si pas de données
3. **Attendez le chargement** - Les graphiques peuvent prendre quelques secondes
4. **Essayez un autre navigateur**

---

## 📝 Problèmes de Saisie

### Je ne peux pas enregistrer un formulaire

**Symptômes :**
- Bouton "Enregistrer" grisé
- Message d'erreur de validation
- Formulaire qui se vide après soumission

**Solutions :**
1. **Vérifiez les champs obligatoires** - Marqués par un astérisque *
2. **Vérifiez le format des données** - Email, téléphone, dates...
3. **Vérifiez les doublons** - Certains champs doivent être uniques
4. **Vérifiez votre connexion** - Une déconnexion peut empêcher la sauvegarde

### Les données saisies disparaissent

**Solutions :**
1. **Sauvegardez régulièrement** - Ne comptez pas sur la sauvegarde automatique
2. **Vérifiez les erreurs** - Un message d'erreur peut avoir annulé la saisie
3. **Évitez les onglets multiples** - Deux onglets sur le même formulaire peuvent créer des conflits

### La recherche ne trouve rien

**Solutions :**
1. **Vérifiez l'orthographe**
2. **Essayez des termes plus courts** - "cab" au lieu de "cabernet franc"
3. **Vérifiez les filtres actifs** - Ils limitent les résultats
4. **Élargissez la recherche** - Enlevez des critères

---

## 📦 Problèmes de Stock

### Le stock affiché est incorrect

**Solutions :**
1. **Rafraîchissez la page**
2. **Vérifiez les mouvements récents** - Un mouvement non validé peut fausser le stock
3. **Lancez un inventaire** - Pour corriger les écarts
4. **Vérifiez les transferts en cours**

### Les alertes de stock ne fonctionnent pas

**Solutions :**
1. **Vérifiez les seuils** - Sont-ils configurés dans Stocks → Seuils ?
2. **Vérifiez les notifications** - Sont-elles activées dans votre profil ?
3. **Rafraîchissez le dashboard**
4. **Vérifiez l'email de notification** - Il peut être en spam

### Je ne peux pas faire de mouvement de stock

**Solutions :**
1. **Vérifiez le stock disponible** - Vous ne pouvez pas sortir plus que disponible
2. **Vérifiez la capacité** - Vous ne pouvez pas dépasser la capacité d'un contenant
3. **Vérifiez vos permissions**
4. **Vérifiez si le lot n'est pas verrouillé**

---

## 💰 Problèmes de Ventes

### Je ne peux pas créer de devis/facture

**Solutions :**
1. **Vérifiez vos permissions** - Rôle Member minimum requis
2. **Sélectionnez un client** - Obligatoire pour créer un document
3. **Ajoutez au moins une ligne** - Un document vide n'est pas valide
4. **Vérifiez le catalogue** - Les produits doivent être configurés

### Le PDF ne se génère pas

**Solutions :**
1. **Vérifiez que le document est validé** - Les brouillons n'ont pas de PDF
2. **Attendez quelques secondes** - La génération peut prendre du temps
3. **Rafraîchissez la page**
4. **Vérifiez votre navigateur** - Autorisez les pop-ups pour monchai.fr

### L'envoi d'email échoue

**Solutions :**
1. **Vérifiez l'email du client** - Est-il correct ?
2. **Vérifiez votre serveur mail** - Configuration SMTP correcte ?
3. **Réessayez plus tard** - Problème temporaire possible
4. **Téléchargez le PDF** - Et envoyez manuellement si urgent

---

## 📊 Problèmes de DRM

### Les données DRM sont incomplètes

**Solutions :**
1. **Vérifiez les mouvements du mois** - Tout est-il saisi ?
2. **Vérifiez les codes INAO** - Tous les produits en ont-ils un ?
3. **Régénérez le brouillon** - Bouton "Recalculer"
4. **Complétez manuellement** - Si certaines données manquent

### L'export DRM échoue

**Solutions :**
1. **Vérifiez le format** - CSV ou PDF selon votre besoin
2. **Validez le brouillon** - L'export nécessite une validation
3. **Vérifiez les erreurs** - Des incohérences peuvent bloquer l'export
4. **Essayez période par période**

### Les codes INAO ne sont pas reconnus

**Solutions :**
1. **Vérifiez l'orthographe** du code
2. **Cherchez par nom d'appellation** dans DRM → Codes INAO
3. **Mettez à jour le référentiel** si le code est récent
4. **Contactez le support** pour ajout d'un code manquant

---

## 🖥️ Problèmes Techniques

### "Erreur 500" ou page blanche

**Symptômes :**
- Page blanche
- Message "Erreur serveur"
- Code 500

**Solutions :**
1. **Rafraîchissez** - Erreur temporaire possible
2. **Attendez quelques minutes** - Le serveur peut être en maintenance
3. **Videz le cache**
4. **Contactez le support** avec l'heure exacte de l'erreur

### "Erreur 404" - Page non trouvée

**Symptômes :**
- Message "Page introuvable"
- URL incorrecte

**Solutions :**
1. **Vérifiez l'URL** - Avez-vous tapé l'adresse correctement ?
2. **Utilisez le menu** - Naviguez depuis le menu principal
3. **L'élément a peut-être été supprimé**
4. **Vérifiez vos permissions** - Certaines pages sont restreintes

### "Erreur 403" - Accès refusé

**Symptômes :**
- Message "Accès interdit"
- Redirection vers login

**Solutions :**
1. **Reconnectez-vous** - Votre session a peut-être expiré
2. **Vérifiez vos permissions**
3. **Changez d'organisation** si nécessaire
4. **Contactez un Admin**

### La page charge lentement

**Solutions :**
1. **Vérifiez votre connexion internet**
2. **Réduisez les filtres** - Moins de données = plus rapide
3. **Fermez les autres onglets**
4. **Essayez à une autre heure** - Moins de charge serveur
5. **Videz le cache du navigateur**

---

## 📱 Problèmes Mobile

### L'interface mobile est difficile à utiliser

**Solutions :**
1. **Utilisez le mode paysage** pour les tableaux
2. **Zoomez** avec deux doigts si nécessaire
3. **Utilisez les boutons rapides** (ex: +100, +250 kg pour vendanges)
4. **Préférez l'interface terrain** pour la saisie

### La géolocalisation ne fonctionne pas

**Solutions :**
1. **Autorisez la localisation** dans les paramètres du navigateur
2. **Vérifiez le GPS** - Il doit être activé sur votre appareil
3. **Sortez des bâtiments** - Le signal GPS est meilleur en extérieur

### L'application est lente sur mobile

**Solutions :**
1. **Utilisez le WiFi** plutôt que la 4G si possible
2. **Fermez les autres applications**
3. **Videz le cache du navigateur mobile**
4. **Utilisez un navigateur récent** (Chrome, Safari, Firefox)

---

## 🔄 Problèmes d'Import/Export

### L'import CSV échoue

**Solutions :**
1. **Vérifiez le format** - UTF-8 avec séparateur point-virgule ou virgule
2. **Vérifiez les colonnes** - Les noms doivent correspondre au modèle
3. **Vérifiez les données** - Pas de caractères spéciaux non supportés
4. **Testez avec moins de lignes** pour identifier le problème
5. **Téléchargez le modèle** et utilisez-le comme base

### L'export ne fonctionne pas

**Solutions :**
1. **Réduisez la sélection** - Trop de données peut bloquer l'export
2. **Autorisez les téléchargements** dans votre navigateur
3. **Vérifiez l'espace disque** disponible
4. **Essayez un autre format** (CSV au lieu d'Excel)

---

## 📞 Contacter le Support

Si aucune solution ne fonctionne :

1. **Préparez les informations suivantes :**
   - Description précise du problème
   - Étapes pour reproduire
   - Message d'erreur exact
   - Capture d'écran
   - Navigateur et version
   - Heure du problème

2. **Envoyez à :** support@monchai.fr

3. **Temps de réponse :**
   - Urgence critique : < 4h
   - Problème bloquant : < 24h
   - Question générale : < 48h

---

## 🔍 Diagnostic Rapide

```
Problème de connexion ?
└─> Réinitialisez le mot de passe

Problème d'affichage ?
└─> Videz le cache (Ctrl+Shift+Delete)

Problème de données ?
└─> Vérifiez les filtres et l'organisation

Problème de permissions ?
└─> Contactez votre Admin

Erreur 500 ?
└─> Attendez 5 min, puis contactez le support

Erreur 404 ?
└─> Utilisez le menu de navigation

Lenteur ?
└─> Réduisez les données affichées
```

---

*Guide de troubleshooting MonChai v2.0 - Pour toute aide supplémentaire : support@monchai.fr*
