"""
Modèles d'authentification et d'organisation pour Mon Chai.
Invariants techniques respectés :
- User référencé par email (USERNAME_FIELD=email)
- Organization regroupe des utilisateurs via Membership
- Vérification Membership actif obligatoire pour écrans métier
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
import uuid

class User(AbstractUser):
    """
    Utilisateur personnalisé avec email comme identifiant principal.
    Invariant : USERNAME_FIELD = email
    """
    email = models.EmailField(
        'Adresse email',
        unique=True,
        help_text='Adresse email utilisée pour la connexion'
    )
    first_name = models.CharField('Prénom', max_length=150, blank=True)
    last_name = models.CharField('Nom', max_length=150, blank=True)
    
    # Email comme identifiant de connexion (invariant technique)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        db_table = 'accounts_user'
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Nom complet de l'utilisateur"""
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def get_active_membership(self):
        """
        Retourne le Membership actif de l'utilisateur.
        Invariant : toujours vérifier l'existence d'un Membership actif
        """
        return self.memberships.filter(is_active=True).first()
    
    def has_active_membership(self):
        """Vérifie si l'utilisateur a un Membership actif"""
        return self.get_active_membership() is not None


class Organization(models.Model):
    """
    Organisation (Exploitation) regroupant des utilisateurs.
    Invariant : Une Organization regroupe des utilisateurs via Membership
    """
    name = models.CharField(
        'Nom de l\'exploitation',
        max_length=200,
        help_text='Nom commercial de l\'exploitation'
    )
    siret = models.CharField(
        'SIRET',
        max_length=14,
        validators=[RegexValidator(r'^\d{14}$', 'Le SIRET doit contenir 14 chiffres')],
        blank=True,
        null=True,
        unique=True,
        help_text='Numéro SIRET à 14 chiffres (optionnel)'
    )
    tva_number = models.CharField(
        'Numéro de TVA',
        max_length=20,
        blank=True,
        help_text='Numéro de TVA intracommunautaire (optionnel)'
    )
    
    # Champs d'adresse pour la checklist d'onboarding - Roadmap 09
    address = models.CharField(
        'Adresse',
        max_length=255,
        blank=True,
        help_text='Adresse fiscale complète'
    )
    postal_code = models.CharField(
        'Code postal',
        max_length=10,
        blank=True,
        help_text='Code postal'
    )
    city = models.CharField(
        'Ville',
        max_length=100,
        blank=True,
        help_text='Ville'
    )
    country = models.CharField(
        'Pays',
        max_length=100,
        default='France',
        help_text='Pays'
    )
    
    currency = models.CharField(
        'Devise',
        max_length=3,
        default='EUR',
        choices=[
            ('EUR', 'Euro (€)'),
            ('USD', 'Dollar US ($)'),
            ('GBP', 'Livre Sterling (£)'),
        ],
        help_text='Devise principale de l\'exploitation'
    )
    
    # UX Multi-chai
    color = models.CharField(
        'Couleur',
        max_length=7,
        default='#722F37',
        help_text='Couleur distinctive du chai (hex, ex: #722F37)'
    )
    is_test = models.BooleanField(
        'Chai de test',
        default=False,
        help_text='Marque ce chai comme environnement de test'
    )
    
    # Région viticole pour préfiltrer les cépages
    REGION_VITICOLE_CHOICES = [
        ('', '-- Non spécifiée --'),
        ('bordeaux', 'Bordeaux'),
        ('bourgogne', 'Bourgogne'),
        ('alsace', 'Alsace'),
        ('champagne', 'Champagne'),
        ('loire', 'Val de Loire'),
        ('rhone', 'Vallée du Rhône'),
        ('provence', 'Provence'),
        ('languedoc', 'Languedoc-Roussillon'),
        ('sud_ouest', 'Sud-Ouest'),
        ('jura', 'Jura'),
        ('savoie', 'Savoie'),
        ('corse', 'Corse'),
        ('beaujolais', 'Beaujolais'),
    ]
    region_viticole = models.CharField(
        'Région viticole',
        max_length=20,
        choices=REGION_VITICOLE_CHOICES,
        blank=True,
        default='',
        help_text='Région viticole principale pour préfiltrer les cépages'
    )
    
    is_initialized = models.BooleanField(
        'Initialisé',
        default=False,
        help_text='Exploitation initialisée via onboarding'
    )
    created_at = models.DateTimeField('Date de création', auto_now_add=True)
    updated_at = models.DateTimeField('Dernière modification', auto_now=True)
    
    class Meta:
        verbose_name = 'Organisation'
        verbose_name_plural = 'Organisations'
        db_table = 'accounts_organization'
    
    def save(self, *args, **kwargs):
        # Convertir chaîne vide en None pour éviter les conflits unique sur SIRET
        if self.siret == '':
            self.siret = None
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_initials(self):
        """Retourne les initiales du chai (2 lettres max)"""
        words = self.name.split()
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        return self.name[:2].upper() if self.name else '??'
    
    def get_active_members(self):
        """Retourne tous les membres actifs de cette organisation"""
        return Membership.objects.filter(
            organization=self,
            is_active=True
        ).select_related('user')
    
    def get_owners(self):
        """Retourne tous les propriétaires actifs de cette organisation"""
        return Membership.objects.filter(
            organization=self,
            is_active=True, 
            role=Membership.Role.OWNER
        ).select_related('user')
    
    def has_multiple_owners(self):
        """Vérifie s'il y a plusieurs propriétaires (pour éviter la suppression du dernier)"""
        return self.get_owners().count() > 1
    
    def can_remove_owner(self, membership):
        """Vérifie si on peut retirer le rôle owner à ce membership"""
        if membership.role != Membership.Role.OWNER:
            return True
        return self.has_multiple_owners()


class Membership(models.Model):
    """
    Relation entre User et Organization avec gestion des rôles.
    Invariant : Vérifier l'existence d'un Membership actif avant écrans métier
    """
    
    class Role(models.TextChoices):
        """
        Rôles définis dans la roadmap 04_roles_acces.txt
        - owner/admin : propriétaire/administrateur
        - editor : éditeur
        - read_only : lecture seule
        """
        OWNER = 'owner', 'Propriétaire'
        ADMIN = 'admin', 'Administrateur'  
        EDITOR = 'editor', 'Éditeur'
        READ_ONLY = 'read_only', 'Lecture seule'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Utilisateur'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Organisation'
    )
    role = models.CharField(
        'Rôle',
        max_length=20,
        choices=Role.choices,
        default=Role.READ_ONLY,
        help_text='Rôle de l\'utilisateur dans l\'organisation'
    )
    is_active = models.BooleanField(
        'Actif',
        default=True,
        help_text='Membership actif (invariant : vérifier avant écrans métier)'
    )
    
    # Permissions granulaires (JSONField)
    permissions = models.JSONField(
        'Permissions détaillées',
        default=dict,
        blank=True,
        help_text='Permissions par module: parcelles, cuvees, vendanges, lots, stocks, ventes, factures, stats'
    )
    
    joined_at = models.DateTimeField('Date d\'adhésion', auto_now_add=True)
    updated_at = models.DateTimeField('Dernière modification', auto_now=True)
    
    class Meta:
        verbose_name = 'Adhésion'
        verbose_name_plural = 'Adhésions'
        db_table = 'accounts_membership'
        unique_together = ['user', 'organization']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['organization', 'is_active']),
        ]
    
    def __str__(self):
        return f'{self.user.full_name} - {self.organization.name} ({self.get_role_display()})'
    
    def can_manage_roles(self):
        """Vérifie si ce membership peut gérer les rôles (owner ou admin)"""
        return self.role in [self.Role.OWNER, self.Role.ADMIN]
    
    def can_invite_users(self):
        """Vérifie si ce membership peut inviter des utilisateurs"""
        return self.can_manage_roles()
    
    def can_edit_data(self):
        """Vérifie si ce membership peut modifier les données métier"""
        return self.role in [self.Role.OWNER, self.Role.ADMIN, self.Role.EDITOR]
    
    def can_view_sensitive_data(self):
        """Vérifie si ce membership peut voir les données sensibles (paramètres, facturation)"""
        return self.role in [self.Role.OWNER, self.Role.ADMIN]
    
    def can_access_billing(self):
        """Vérifie si ce membership peut accéder à la facturation et aux ventes"""
        return self.role in [self.Role.OWNER, self.Role.ADMIN]
    
    def is_read_only(self):
        """Vérifie si ce membership est en lecture seule"""
        return self.role == self.Role.READ_ONLY
    
    def get_role_level(self):
        """Retourne le niveau numérique du rôle pour comparaisons"""
        role_levels = {
            self.Role.READ_ONLY: 1,
            self.Role.EDITOR: 2,
            self.Role.ADMIN: 3,
            self.Role.OWNER: 4,
        }
        return role_levels.get(self.role, 0)
    
    def is_owner_or_admin(self):
        """Vérifie si le rôle permet la gestion de l'organisation"""
        return self.role in [self.Role.OWNER, self.Role.ADMIN]
    
    # ===== Permissions granulaires =====
    
    @classmethod
    def get_default_permissions(cls, role='read_only'):
        """Retourne les permissions par defaut selon le role"""
        if role in ['owner', 'admin']:
            # Admins/Owners ont tout par defaut
            return {
                'parcelles': {'view': True, 'edit': True},
                'cuvees': {'view': True, 'edit': True},
                'vendanges': {'view': True, 'edit': True},
                'lots': {'view': True, 'edit': True},
                'stocks': {'view': True, 'edit': True},
                'ventes': {'view': True, 'edit': True},
                'factures': {'view': True, 'edit': True},
                'stats': {'view': True, 'export': True},
                'team': {'view': True, 'manage': True},
            }
        elif role == 'editor':
            # Editeurs peuvent modifier les donnees metier mais pas gerer l'equipe
            return {
                'parcelles': {'view': True, 'edit': True},
                'cuvees': {'view': True, 'edit': True},
                'vendanges': {'view': True, 'edit': True},
                'lots': {'view': True, 'edit': True},
                'stocks': {'view': True, 'edit': True},
                'ventes': {'view': True, 'edit': True},
                'factures': {'view': True, 'edit': False},
                'stats': {'view': True, 'export': False},
                'team': {'view': True, 'manage': False},
            }
        else:
            # read_only: lecture seule
            return {
                'parcelles': {'view': True, 'edit': False},
                'cuvees': {'view': True, 'edit': False},
                'vendanges': {'view': True, 'edit': False},
                'lots': {'view': True, 'edit': False},
                'stocks': {'view': True, 'edit': False},
                'ventes': {'view': False, 'edit': False},
                'factures': {'view': False, 'edit': False},
                'stats': {'view': True, 'export': False},
                'team': {'view': False, 'manage': False},
            }
    
    def get_permissions(self):
        """Retourne les permissions effectives (fusion défaut + custom)"""
        default = self.get_default_permissions(self.role)
        custom = self.permissions or {}
        
        # Owner a toujours tout
        if self.role == self.Role.OWNER:
            return default
        
        # Fusionner les permissions custom
        result = {}
        for module, perms in default.items():
            result[module] = perms.copy()
            if module in custom:
                result[module].update(custom[module])
        
        return result
    
    def has_permission(self, module, action='view'):
        """
        Vérifie si l'utilisateur a une permission spécifique.
        
        Args:
            module: 'parcelles', 'cuvees', 'vendanges', 'lots', 'stocks', 'ventes', 'factures', 'stats', 'team'
            action: 'view', 'edit', 'export', 'manage'
        
        Returns:
            bool
        """
        if not self.is_active:
            return False
        
        # Owner a tout
        if self.role == self.Role.OWNER:
            return True
        
        perms = self.get_permissions()
        module_perms = perms.get(module, {})
        return module_perms.get(action, False)
    
    def can_view(self, module):
        """Raccourci pour vérifier l'accès en lecture"""
        return self.has_permission(module, 'view')
    
    def can_edit(self, module):
        """Raccourci pour vérifier l'accès en écriture"""
        return self.has_permission(module, 'edit')
    
    def set_permission(self, module, action, value):
        """Définir une permission spécifique"""
        if self.permissions is None:
            self.permissions = {}
        
        if module not in self.permissions:
            self.permissions[module] = {}
        
        self.permissions[module][action] = value


class Invitation(models.Model):
    """
    Modèle d'invitation selon roadmap 07_invitations_tokens_emails.txt
    L'invitation est un enregistrement + un lien signé.
    """
    
    class Status(models.TextChoices):
        SENT = 'sent', 'Envoyée'
        ACCEPTED = 'accepted', 'Acceptée'
        EXPIRED = 'expired', 'Expirée'
    
    # Contenu minimal de l'invitation (roadmap 07)
    email = models.EmailField(
        'Email destinataire',
        help_text='Adresse email de la personne invitée'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name='Organisation cible'
    )
    role = models.CharField(
        'Rôle proposé',
        max_length=20,
        choices=Membership.Role.choices,
        default=Membership.Role.EDITOR,
        help_text='Rôle à attribuer (editor par défaut)'
    )
    
    # Métadonnées
    token = models.CharField(
        'Token signé',
        max_length=500,
        unique=True,
        help_text='Token signé côté serveur, jamais prédictible'
    )
    invite_code = models.CharField(
        'Code d\'invitation',
        max_length=8,
        unique=True,
        blank=True,
        null=True,
        help_text='Code court à partager (ex: ABC123)'
    )
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=Status.choices,
        default=Status.SENT
    )
    
    # Dates
    created_at = models.DateTimeField(
        'Date de création',
        auto_now_add=True
    )
    expires_at = models.DateTimeField(
        'Date d\'expiration',
        help_text='Expiration (ex: 72h selon roadmap)'
    )
    accepted_at = models.DateTimeField(
        'Date d\'acceptation',
        null=True,
        blank=True,
        help_text='Enregistrer accepted_at pour suivi'
    )
    
    # Traçabilité
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name='Invité par'
    )
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_invitations',
        verbose_name='Accepté par'
    )
    
    class Meta:
        verbose_name = 'Invitation'
        verbose_name_plural = 'Invitations'
        # Interdire une deuxième invitation active identique (email+org)
        unique_together = [['email', 'organization', 'status']]
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['token']),
        ]
    
    def __str__(self):
        return f'Invitation {self.email} → {self.organization.name} ({self.get_status_display()})'
    
    def is_expired(self):
        """Vérifier si l'invitation est expirée"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def can_be_accepted(self):
        """Vérifier si l'invitation peut être acceptée"""
        return self.status == self.Status.SENT and not self.is_expired()
    
    def mark_as_accepted(self, user):
        """Marquer l'invitation comme acceptée"""
        from django.utils import timezone
        self.status = self.Status.ACCEPTED
        self.accepted_at = timezone.now()
        self.accepted_by = user
        self.save()
    
    def mark_as_expired(self):
        """Marquer l'invitation comme expirée"""
        self.status = self.Status.EXPIRED
        self.save()


class OrgSetupChecklist(models.Model):
    """
    Checklist d'onboarding par organisation - Roadmap 09
    Persiste l'état des 4 tâches initiales après création d'exploitation
    """
    
    class TaskStatus(models.TextChoices):
        TODO = 'todo', 'À faire'
        DOING = 'doing', 'En cours'
        DONE = 'done', 'Terminé'
    
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='setup_checklist',
        verbose_name='Organisation'
    )
    
    state = models.JSONField(
        'État des tâches',
        default=dict,
        help_text='État des 4 tâches: company_info, taxes, currency_format, terms'
    )
    
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    
    class Meta:
        verbose_name = 'Checklist d\'onboarding'
        verbose_name_plural = 'Checklists d\'onboarding'
        db_table = 'accounts_org_setup_checklist'
    
    def __str__(self):
        return f'Checklist {self.organization.name} ({self.get_progress()}%)'
    
    @classmethod
    def get_default_state(cls):
        """État initial par défaut selon roadmap 09"""
        return {
            'company_info': cls.TaskStatus.TODO,
            'taxes': cls.TaskStatus.TODO,
            'currency_format': cls.TaskStatus.TODO,
            'terms': cls.TaskStatus.TODO
        }
    
    def save(self, *args, **kwargs):
        """Initialiser l'état par défaut si vide"""
        if not self.state:
            self.state = self.get_default_state()
        super().save(*args, **kwargs)
    
    def get_progress(self):
        """Calculer le pourcentage d'avancement (0-100)"""
        if not self.state:
            return 0
        
        completed_count = sum(
            1 for status in self.state.values() 
            if status == self.TaskStatus.DONE
        )
        total_tasks = 4
        return int((completed_count / total_tasks) * 100)
    
    def get_completed_count(self):
        """Nombre de tâches terminées"""
        if not self.state:
            return 0
        return sum(
            1 for status in self.state.values() 
            if status == self.TaskStatus.DONE
        )
    
    def is_completed(self):
        """Vérifier si toutes les tâches sont terminées"""
        return self.get_completed_count() == 4
    
    def update_task(self, task_key, status):
        """Mettre à jour l'état d'une tâche spécifique"""
        if task_key not in ['company_info', 'taxes', 'currency_format', 'terms']:
            raise ValueError(f"Clé de tâche invalide: {task_key}")
        
        if status not in [choice[0] for choice in self.TaskStatus.choices]:
            raise ValueError(f"Statut invalide: {status}")
        
        if not self.state:
            self.state = self.get_default_state()
        
        self.state[task_key] = status
        self.save()
    
    def get_task_info(self):
        """Obtenir les informations détaillées des tâches pour l'affichage"""
        tasks = [
            {
                'key': 'company_info',
                'title': 'Informations de l\'exploitation',
                'description': 'Nom, adresse fiscale et informations légales',
                'status': self.state.get('company_info', self.TaskStatus.TODO),
                'url': '/settings/billing/',
                'icon': 'bi-building'
            },
            {
                'key': 'taxes',
                'title': 'TVA et taxes',
                'description': 'Configuration du régime fiscal et TVA',
                'status': self.state.get('taxes', self.TaskStatus.TODO),
                'url': '/settings/billing/',
                'icon': 'bi-receipt'
            },
            {
                'key': 'currency_format',
                'title': 'Devise et formats',
                'description': 'Devise, formats de date et de nombres',
                'status': self.state.get('currency_format', self.TaskStatus.TODO),
                'url': '/settings/general/',
                'icon': 'bi-currency-euro'
            },
            {
                'key': 'terms',
                'title': 'Conditions générales',
                'description': 'CGV, mentions légales et documents',
                'status': self.state.get('terms', self.TaskStatus.TODO),
                'url': '/settings/general/',
                'icon': 'bi-file-text'
            }
        ]
        return tasks


class OrgBilling(models.Model):
    """
    Informations de facturation et légales de l'organisation - Roadmap 11
    Coordonnées fiscales, SIRET, TVA pour la facturation
    """
    
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='billing',
        verbose_name='Organisation'
    )
    
    # Identité légale
    legal_name = models.CharField(
        'Raison sociale',
        max_length=200,
        help_text='Dénomination sociale officielle de votre organisation'
    )
    
    # Adresse de facturation
    billing_address_line1 = models.CharField(
        'Adresse ligne 1',
        max_length=100,
        help_text='Numéro et nom de rue'
    )
    
    billing_address_line2 = models.CharField(
        'Adresse ligne 2',
        max_length=100,
        blank=True,
        help_text='Complément d\'adresse (optionnel)'
    )
    
    billing_postal_code = models.CharField(
        'Code postal',
        max_length=10,
        help_text='Code postal de facturation'
    )
    
    billing_city = models.CharField(
        'Ville',
        max_length=100,
        help_text='Ville de facturation'
    )
    
    billing_country = models.CharField(
        'Pays',
        max_length=100,
        default='France',
        help_text='Pays de facturation'
    )
    
    # Informations fiscales
    siret = models.CharField(
        'SIRET',
        max_length=14,
        blank=True,
        help_text='Numéro SIRET (14 chiffres, si pertinent)'
    )
    
    VAT_STATUS_CHOICES = [
        ('subject_to_vat', 'Assujetti à la TVA'),
        ('not_subject_to_vat', 'Non assujetti à la TVA'),
    ]
    
    vat_status = models.CharField(
        'Statut TVA',
        max_length=20,
        choices=VAT_STATUS_CHOICES,
        help_text='Statut fiscal pour la TVA'
    )
    
    vat_number = models.CharField(
        'Numéro de TVA intracommunautaire',
        max_length=20,
        blank=True,
        help_text='Format FR + 11 chiffres (si assujetti à la TVA)'
    )
    
    # Contact de facturation (optionnel)
    billing_contact_name = models.CharField(
        'Nom du contact facturation',
        max_length=100,
        blank=True,
        help_text='Personne responsable de la facturation (optionnel)'
    )
    
    billing_contact_email = models.EmailField(
        'Email du contact facturation',
        blank=True,
        help_text='Email pour les questions de facturation (optionnel)'
    )
    
    billing_contact_phone = models.CharField(
        'Téléphone du contact facturation',
        max_length=20,
        blank=True,
        help_text='Numéro de téléphone du contact (optionnel)'
    )
    
    # Métadonnées
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    
    class Meta:
        verbose_name = 'Informations de facturation'
        verbose_name_plural = 'Informations de facturation'
        db_table = 'accounts_org_billing'
    
    def __str__(self):
        return f'Facturation {self.organization.name}'
    
    def get_full_billing_address(self):
        """Adresse de facturation complète formatée"""
        address_parts = [self.billing_address_line1]
        if self.billing_address_line2:
            address_parts.append(self.billing_address_line2)
        address_parts.extend([
            f"{self.billing_postal_code} {self.billing_city}",
            self.billing_country
        ])
        return '\n'.join(address_parts)
    
    def is_vat_subject(self):
        """Vérifie si l'organisation est assujettie à la TVA"""
        return self.vat_status == 'subject_to_vat'
    
    def has_complete_company_info(self):
        """Vérifie si les informations société sont complètes pour la checklist"""
        return bool(
            self.legal_name and 
            self.billing_address_line1 and 
            self.billing_postal_code and 
            self.billing_city
        )
    
    def has_complete_tax_info(self):
        """Vérifie si les informations fiscales sont complètes pour la checklist"""
        if self.vat_status == 'not_subject_to_vat':
            return True
        elif self.vat_status == 'subject_to_vat':
            return bool(self.vat_number)
        return False


class UserProfile(models.Model):
    """
    Profil utilisateur personnel - Roadmap 10
    Préférences individuelles indépendantes de l'organisation
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Utilisateur'
    )
    
    display_name = models.CharField(
        'Nom d\'affichage',
        max_length=100,
        blank=True,
        help_text='Nom affiché dans l\'interface (optionnel)'
    )
    
    locale = models.CharField(
        'Langue',
        max_length=10,
        default='fr',
        choices=[
            ('fr', 'Français'),
            ('en', 'English'),
        ],
        help_text='Langue de l\'interface'
    )
    
    timezone = models.CharField(
        'Fuseau horaire',
        max_length=50,
        default='Europe/Paris',
        help_text='Fuseau horaire pour l\'affichage des dates'
    )
    
    avatar = models.ImageField(
        'Photo de profil',
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        help_text='Photo de profil (max 2 Mo, formats JPG/PNG)'
    )
    
    # Preferences multi-chai (UX points 13, 17)
    default_org = models.ForeignKey(
        'Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_users',
        verbose_name='Chai par defaut',
        help_text='Chai a ouvrir automatiquement a la connexion'
    )
    last_org = models.ForeignKey(
        'Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_used_by_users',
        verbose_name='Dernier chai utilise'
    )
    org_preference = models.CharField(
        'Preference de chai',
        max_length=20,
        default='last_used',
        choices=[
            ('last_used', 'Dernier chai utilise'),
            ('always_ask', 'Toujours demander'),
            ('default', 'Toujours ouvrir le chai par defaut'),
        ]
    )
    
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    
    class Meta:
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateur'
        db_table = 'accounts_user_profile'
    
    def __str__(self):
        return f'Profil de {self.get_display_name()}'
    
    def get_display_name(self):
        """
        Nom d'affichage avec fallback selon roadmap 10:
        1. display_name si défini
        2. first_name + last_name si définis
        3. email sinon
        """
        if self.display_name:
            return self.display_name
        
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        
        if self.user.first_name:
            return self.user.first_name
        
        return self.user.email
    
    def get_avatar_url(self):
        """URL de l'avatar ou avatar par défaut"""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return None
    
    @classmethod
    def get_timezone_choices(cls):
        """Liste des fuseaux horaires supportés - shortlist selon roadmap 10"""
        return [
            ('Europe/Paris', 'Paris (Europe/Paris)'),
            ('Europe/London', 'Londres (Europe/London)'),
            ('Europe/Berlin', 'Berlin (Europe/Berlin)'),
            ('Europe/Madrid', 'Madrid (Europe/Madrid)'),
            ('Europe/Rome', 'Rome (Europe/Rome)'),
            ('America/New_York', 'New York (America/New_York)'),
            ('America/Los_Angeles', 'Los Angeles (America/Los_Angeles)'),
            ('America/Montreal', 'Montréal (America/Montreal)'),
            ('Asia/Tokyo', 'Tokyo (Asia/Tokyo)'),
            ('Australia/Sydney', 'Sydney (Australia/Sydney)'),
        ]


def validate_pdf_size(value):
    """Valide que le fichier PDF ne dépasse pas 5 Mo"""
    if value.size > 5 * 1024 * 1024:  # 5 Mo
        raise ValidationError('Le fichier PDF ne peut pas dépasser 5 Mo.')


class OrgSettings(models.Model):
    """Paramètres généraux de l'organisation (devise, formats, CGV)"""
    
    CURRENCY_CHOICES = [
        ('EUR', 'Euro (€)'),
        ('USD', 'Dollar US ($)'),
        ('GBP', 'Livre Sterling (£)'),
        ('CHF', 'Franc Suisse (CHF)'),
    ]
    
    DATE_FORMAT_CHOICES = [
        ('DD/MM/YYYY', 'DD/MM/YYYY (31/12/2025)'),
        ('MM/DD/YYYY', 'MM/DD/YYYY (12/31/2025)'),
        ('YYYY-MM-DD', 'YYYY-MM-DD (2025-12-31)'),
    ]
    
    NUMBER_FORMAT_CHOICES = [
        ('FR', '1 234,56 (français)'),
        ('EN', '1,234.56 (anglais)'),
    ]
    
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='EUR',
        verbose_name='Devise'
    )
    date_format = models.CharField(
        max_length=10,
        choices=DATE_FORMAT_CHOICES,
        default='DD/MM/YYYY',
        verbose_name='Format de date'
    )
    number_format = models.CharField(
        max_length=2,
        choices=NUMBER_FORMAT_CHOICES,
        default='FR',
        verbose_name='Format des nombres'
    )
    terms_url = models.URLField(
        blank=True,
        verbose_name='URL des CGV'
    )
    terms_file = models.FileField(
        upload_to='terms/%Y/%m/',
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_pdf_size
        ],
        verbose_name='Fichier CGV (PDF)'
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Paramètres organisation'
        verbose_name_plural = 'Paramètres organisations'
    
    def __str__(self):
        return f"Paramètres {self.organization.name}"
    
    def has_terms(self):
        """Retourne True si des CGV sont définies (URL ou fichier)"""
        return bool(self.terms_url or self.terms_file)
    
    def get_terms_display(self):
        """Retourne l'affichage des CGV (priorité au fichier)"""
        if self.terms_file:
            return f"Fichier: {self.terms_file.name}"
        elif self.terms_url:
            return f"URL: {self.terms_url}"
        return "Non définies"
    
    def clean(self):
        """Validation: priorité au fichier si URL et fichier fournis"""
        if self.terms_url and self.terms_file:
            # Priorité au fichier selon roadmap
            self.terms_url = ''
    
    def get_format_preview(self):
        """Retourne un aperçu du format choisi"""
        from datetime import date
        sample_date = date(2025, 12, 31)
        
        # Format date
        if self.date_format == 'DD/MM/YYYY':
            date_str = sample_date.strftime('%d/%m/%Y')
        elif self.date_format == 'MM/DD/YYYY':
            date_str = sample_date.strftime('%m/%d/%Y')
        else:  # YYYY-MM-DD
            date_str = sample_date.strftime('%Y-%m-%d')
        
        # Format nombre avec devise
        if self.number_format == 'FR':
            number_str = f"1 234,56 {self.get_currency_display()}"
        else:  # EN
            number_str = f"1,234.56 {self.get_currency_display()}"
        
        return f"{number_str} — {date_str}"


# Signal pour création automatique des paramètres
@receiver(post_save, sender=Organization)
def create_org_settings(sender, instance, created, **kwargs):
    """Crée automatiquement les paramètres pour une nouvelle organisation"""
    if created:
        OrgSettings.objects.create(organization=instance)


# Signal pour gérer les permissions Django selon le rôle
@receiver(post_save, sender=Membership)
def update_user_permissions(sender, instance, created, **kwargs):
    """Met à jour les permissions Django de l'utilisateur selon son rôle"""
    user = instance.user
    
    # Réinitialiser les permissions staff pour ce user
    user.is_staff = False
    
    # Si l'utilisateur a un membership actif avec des droits élevés
    active_membership = user.get_active_membership()
    if active_membership and active_membership.can_access_billing():
        # Donner accès à l'admin Django
        user.is_staff = True
        
        # Donner les permissions pour les apps sales et billing
        try:
            # Permissions pour l'app sales
            sales_permissions = Permission.objects.filter(
                content_type__app_label='sales'
            )
            user.user_permissions.set(sales_permissions)
            
            # Permissions pour l'app billing  
            billing_permissions = Permission.objects.filter(
                content_type__app_label='billing'
            )
            user.user_permissions.add(*billing_permissions)
            
        except Exception:
            # Ignorer les erreurs si les apps ne sont pas encore migrées
            pass
    else:
        # Retirer les permissions si plus de droits
        user.user_permissions.clear()
    
    user.save()


# ============================================================================
# DASHBOARD PERSONNALISABLE
# ============================================================================

class DashboardWidget(models.Model):
    """
    Widget disponible pour le dashboard
    """
    WIDGET_TYPES = [
        ('metric', 'Métrique'),
        ('chart', 'Graphique'),
        ('list', 'Liste'),
        ('shortcut', 'Raccourci'),
        ('alert', 'Alerte'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, help_text="Code unique du widget")
    name = models.CharField(max_length=100, help_text="Nom du widget")
    description = models.TextField(blank=True, help_text="Description du widget")
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES, default='metric')
    icon = models.CharField(max_length=50, default='bi-graph-up', help_text="Icône Bootstrap")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Widget Dashboard"
        verbose_name_plural = "Widgets Dashboard"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserDashboardConfig(models.Model):
    """
    Configuration personnalisée du dashboard par utilisateur
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_configs')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    
    # Widgets actifs (JSON array de widget codes)
    active_widgets = models.JSONField(
        default=list,
        help_text="Liste des codes de widgets actifs dans l'ordre d'affichage"
    )
    
    # Raccourcis personnalisés (JSON array)
    custom_shortcuts = models.JSONField(
        default=list,
        help_text="Raccourcis personnalisés [{name, url, icon, color}]"
    )

    # Paramètres d'affichage
    layout = models.CharField(
        max_length=20,
        default='grid',
        choices=[('grid', 'Grille'), ('list', 'Liste')]
    )
    columns = models.IntegerField(default=3, help_text="Nombre de colonnes (1-4)")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration Dashboard"
        verbose_name_plural = "Configurations Dashboard"
        unique_together = [['user', 'organization']]
    
    def __str__(self):
        return f"Dashboard {self.user.email} - {self.organization.name}"
    
    def get_active_widgets_objects(self):
        """Retourne les objets Widget dans l'ordre configuré"""
        if not self.active_widgets:
            return DashboardWidget.objects.filter(is_active=True)[:6]
        
        widgets = []
        for code in self.active_widgets:
            try:
                widget = DashboardWidget.objects.get(code=code, is_active=True)
                widgets.append(widget)
            except DashboardWidget.DoesNotExist:
                pass
        return widgets


class UserShortcut(models.Model):
    """
    Raccourcis personnalisés pour l'utilisateur.
    Accessibles via le menu '+' du header.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shortcuts')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='shortcuts')
    
    title = models.CharField('Titre', max_length=100)
    url = models.CharField('URL', max_length=255)
    icon = models.CharField('Icône', max_length=50, default='bi-star-fill')
    color = models.CharField('Couleur', max_length=20, default='text-warning')
    order = models.IntegerField('Ordre', default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Raccourci utilisateur'
        verbose_name_plural = 'Raccourcis utilisateur'
        ordering = ['order', 'created_at']
        
    def __str__(self):
        return f"{self.title} ({self.user})"

# ============================================================================
# FACTURATION & ABONNEMENT (Roadmap 11)
# ============================================================================

class Subscription(models.Model):
    """
    Abonnement de l'organisation - Roadmap 11
    Gère le plan actuel, le renouvellement et le statut
    """
    PLAN_CHOICES = [
        ('discovery', 'Découverte (Gratuit)'),
        ('vigneron', 'Vigneron (Jusqu\'à 20ha)'),
        ('domain', 'Domaine (Illimité)'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('past_due', 'En retard de paiement'),
        ('canceled', 'Annulé'),
    ]

    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='Organisation'
    )
    
    plan_name = models.CharField(
        'Nom du plan',
        max_length=50,
        choices=PLAN_CHOICES,
        default='discovery'
    )
    
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    amount = models.DecimalField(
        'Montant mensuel (HT)',
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    renewal_date = models.DateField(
        'Date de renouvellement',
        null=True,
        blank=True
    )
    
    payment_method_summary = models.CharField(
        'Moyen de paiement',
        max_length=100,
        blank=True,
        help_text='Ex: Visa terminaison 4242'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Abonnement'
        verbose_name_plural = 'Abonnements'
        db_table = 'accounts_subscription'

    def __str__(self):
        return f"{self.get_plan_name_display()} - {self.organization.name}"


class Invoice(models.Model):
    """
    Facture de l'organisation - Roadmap 11
    Historique des factures générées
    """
    STATUS_CHOICES = [
        ('paid', 'Payée'),
        ('pending', 'En attente'),
        ('failed', 'Échouée'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name='Organisation'
    )
    
    number = models.CharField(
        'Numéro de facture',
        max_length=50,
        unique=True
    )
    
    date = models.DateField('Date de facturation')
    
    amount_ht = models.DecimalField(
        'Montant HT',
        max_digits=10,
        decimal_places=2
    )
    
    amount_ttc = models.DecimalField(
        'Montant TTC',
        max_digits=10,
        decimal_places=2
    )
    
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    pdf_file = models.FileField(
        'Facture PDF',
        upload_to='invoices/%Y/%m/',
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'
        ordering = ['-date', '-created_at']
        db_table = 'accounts_invoice'

    def __str__(self):
        return f"Facture {self.number} ({self.organization.name})"
