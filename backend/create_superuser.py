import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from monchai.apps.accounts.models import User, Domaine, Profile

# Créer un domaine
domaine = Domaine.objects.create(
    nom="Domaine de Test",
    siret="12345678901234",
    adresse="1 Rue des Vignes",
    code_postal="44000",
    ville="Nantes",
    pays="France"
)

# Créer un superutilisateur
superuser = User.objects.create_superuser(
    email="admin@monchai.fr",
    password="Admin123!",
    first_name="Admin",
    last_name="MonChai"
)

# Créer un profil pour l'utilisateur
Profile.objects.create(
    user=superuser,
    domaine=domaine,
    role="admin_domaine"
)

print("Superutilisateur créé avec succès :")
print(f"Email: admin@monchai.fr")
print(f"Mot de passe: Admin123!")
print(f"Domaine: {domaine.nom}")
