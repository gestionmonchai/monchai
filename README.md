# Monchai - Mono-repo

## Vision

Ce mono-repo regroupe deux applications complémentaires pour la plateforme Monchai :
- **backend/** : API et logique métier en Django (Python)
- **mobile/** : Application mobile en Expo (React Native)

## Présentation

Mon Chai est un SaaS viticole conçu pour suivre le flux chai : *vendanges → cuves/lots → assemblages/soutirages → mise en bouteille → ventes → exports DRM*.

### Différenciant
- Ergonomie intuitive
- Mouvements automatiques (débits/crédits)
- Verrouillage par événements
- Exports DRM prêts à déposer (région pilote)

### Public cible
- Domaines indépendants (1–20 ha)
- Caves particulières
- Petites coopératives

## Structure du projet

```
monchai/
  backend/          # API Django + Django REST Framework
  mobile/           # Application Expo (React Native)
  docs/             # Documentation
```

## Guide de développement

Consulter le [Dev Book](./MonChai_DevBook_v1.md) pour les détails sur l'architecture, les modèles de données, et le planning de développement.
