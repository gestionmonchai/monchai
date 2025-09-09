from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    """Manager personnalisé pour le modèle User"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Crée et sauvegarde un utilisateur avec l'email et le mot de passe"""
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Crée et sauvegarde un superutilisateur"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superutilisateur doit avoir is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superutilisateur doit avoir is_superuser=True")
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Modèle d'utilisateur personnalisé avec email comme identifiant"""
    
    username = None  # Supprime le champ username
    email = models.EmailField("Adresse email", unique=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.email


class Domaine(models.Model):
    """Modèle pour un domaine viticole (tenant)"""
    
    nom = models.CharField("Nom du domaine", max_length=100)
    siret = models.CharField("SIRET", max_length=14, blank=True)
    adresse = models.TextField("Adresse", blank=True)
    code_postal = models.CharField("Code postal", max_length=10, blank=True)
    ville = models.CharField("Ville", max_length=100, blank=True)
    pays = models.CharField("Pays", max_length=100, default="France")
    telephone = models.CharField("Téléphone", max_length=20, blank=True)
    email_contact = models.EmailField("Email de contact", blank=True)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Domaine"
        verbose_name_plural = "Domaines"
    
    def __str__(self):
        return self.nom


class Profile(models.Model):
    """Profil utilisateur avec rôle"""
    
    ROLE_CHOICES = [
        ("admin_domaine", "Administrateur domaine"),
        ("oenologue", "Œnologue"),
        ("operateur_chai", "Opérateur chai"),
        ("compta", "Comptabilité"),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    domaine = models.ForeignKey(Domaine, on_delete=models.CASCADE, related_name="profiles")
    role = models.CharField("Rôle", max_length=20, choices=ROLE_CHOICES, default="operateur_chai")
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de mise à jour", auto_now=True)
    
    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"
    
    def __str__(self):
        return f"{self.user.email} - {self.get_role_display()} ({self.domaine.nom})"
