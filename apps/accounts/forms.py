"""
Formulaires d'authentification pour Mon Chai.
Implémentation selon roadmap 02_auth_flow.txt
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

from .models import Organization, Invitation, UserProfile, Membership, OrgBilling, OrgSettings


class LoginForm(AuthenticationForm):
    """
    Formulaire de connexion avec email comme identifiant.
    """
    username = forms.EmailField(
        label='Adresse e-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.fr',
            'autofocus': True,
            'required': True,
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre mot de passe',
            'required': True,
            'autocomplete': 'current-password'
        })
    )
    
    error_messages = {
        'invalid_login': 'Email ou mot de passe incorrect.',
        'inactive': 'Ce compte a été désactivé.',
    }


class SignupForm(UserCreationForm):
    """
    Formulaire d'inscription avec champs optionnels.
    Roadmap : email, first_name, last_name (optionnels), password
    """
    email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.com',
            'required': True
        })
    )
    first_name = forms.CharField(
        label='Prénom',
        max_length=150,
        required=False,
    )
    last_name = forms.CharField(
        label='Nom',
        max_length=150,
        required=False,
    )
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choisissez un mot de passe',
            'minlength': '8',
            'autocomplete': 'new-password'
        })
    )
    password2 = forms.CharField(
        label='Confirmation du mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez votre mot de passe',
            'minlength': '8',
            'autocomplete': 'new-password'
        })
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')
    
    def clean_email(self):
        """Vérifier que l'email n'existe pas déjà"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Un compte avec cette adresse email existe déjà.')
        return email
    
    def save(self, commit=True):
        """Créer l'utilisateur avec email comme username"""
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # email comme username
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class PasswordResetRequestForm(forms.Form):
    """
    Formulaire de demande de réinitialisation de mot de passe.
    """
    email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.com',
            'autofocus': True
        }),
        help_text='Saisissez l\'adresse email de votre compte.'
    )
    
    def clean_email(self):
        """
        Validation de l'email sans révéler si le compte existe.
        Sécurité : ne pas révéler l'existence d'un email.
        """
        email = self.cleaned_data.get('email')
        # On ne vérifie pas ici si l'email existe pour des raisons de sécurité
        # La vérification se fera dans la vue
        return email


class OrganizationCreationForm(forms.ModelForm):
    """
    Formulaire de création d'exploitation pour l'onboarding rapide.
    Roadmap : name (obligatoire), siret (optionnel), tax_id (optionnel), currency
    """
    
    class Meta:
        model = Organization
        fields = ['name', 'siret', 'tva_number', 'currency']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de votre exploitation',
                'autofocus': True
            }),
            'siret': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345678901234 (optionnel)'
            }),
            'tva_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FR12345678901 (optionnel)'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs optionnels sauf le nom
        self.fields['siret'].required = False
        self.fields['tva_number'].required = False
        
        # Messages d'aide
        self.fields['name'].help_text = 'Le nom de votre exploitation (obligatoire)'
        self.fields['siret'].help_text = 'Numéro SIRET à 14 chiffres (optionnel)'
        self.fields['tva_number'].help_text = 'Numéro de TVA intracommunautaire (optionnel)'
        self.fields['currency'].help_text = 'Devise principale pour vos transactions'
    
    def clean_siret(self):
        """Validation du SIRET si fourni"""
        siret = self.cleaned_data.get('siret')
        if siret and siret.strip():
            # Nettoyer les espaces
            siret = siret.replace(' ', '')
            if not siret.isdigit() or len(siret) != 14:
                raise ValidationError('Le SIRET doit contenir exactement 14 chiffres.')
        return siret or ''
    
    def save(self, user, commit=True):
        """
        Créer l'organisation et le membership owner.
        Roadmap : créer Organization; créer Membership(user=current, role=owner); set is_initialized=True
        """
        organization = super().save(commit=False)
        organization.is_initialized = True
        
        if commit:
            organization.save()
            
            # Créer le Membership owner pour l'utilisateur
            from .models import Membership
            Membership.objects.create(
                user=user,
                organization=organization,
                role=Membership.Role.OWNER,
                is_active=True
            )
        
        return organization


class InviteUserForm(forms.Form):
    """
    Formulaire d'invitation d'un utilisateur à rejoindre une organisation.
    Roadmap 04 : email + rôle, visible seulement owner/admin
    """
    email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemple.fr'
        }),
        help_text='Adresse email de la personne à inviter'
    )
    
    role = forms.ChoiceField(
        label='Rôle',
        choices=Membership.Role.choices,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text='Rôle à attribuer à cette personne'
    )
    
    def __init__(self, *args, current_user_role=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Limiter les rôles selon le rôle de l'utilisateur actuel
        if current_user_role == Membership.Role.ADMIN:
            # Un admin ne peut pas créer d'owner
            available_roles = [
                (Membership.Role.READ_ONLY, 'Lecture seule'),
                (Membership.Role.EDITOR, 'Éditeur'),
                (Membership.Role.ADMIN, 'Administrateur'),
            ]
            self.fields['role'].choices = available_roles
            self.fields['role'].initial = Membership.Role.EDITOR
        else:
            # Un owner peut créer tous les rôles
            self.fields['role'].initial = Membership.Role.EDITOR
    
    def clean_email(self):
        """Validation de l'email d'invitation"""
        email = self.cleaned_data.get('email')
        
        # Vérifier que l'email est valide (Django le fait déjà)
        # On pourrait ajouter d'autres validations ici si nécessaire
        
        return email


class ChangeRoleForm(forms.Form):
    """
    Formulaire pour changer le rôle d'un membre existant.
    Roadmap 04 : Change role avec protection anti-suppression du dernier owner
    """
    role = forms.ChoiceField(
        label='Nouveau rôle',
        choices=Membership.Role.choices,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, membership=None, current_user_role=None, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.membership = membership
        self.organization = organization
        
        # Définir le rôle actuel
        if membership:
            self.fields['role'].initial = membership.role
        
        # Limiter les rôles selon le rôle de l'utilisateur actuel
        if current_user_role == Membership.Role.ADMIN:
            # Un admin ne peut pas créer d'owner
            available_roles = [
                (Membership.Role.READ_ONLY, 'Lecture seule'),
                (Membership.Role.EDITOR, 'Éditeur'),
                (Membership.Role.ADMIN, 'Administrateur'),
            ]
            self.fields['role'].choices = available_roles
    
    def clean_role(self):
        """Validation du changement de rôle"""
        new_role = self.cleaned_data.get('role')
        
        if not self.membership or not self.organization:
            return new_role
        
        # Vérifier qu'on ne supprime pas le dernier owner
        if (self.membership.role == Membership.Role.OWNER and 
            new_role != Membership.Role.OWNER and 
            not self.organization.has_multiple_owners()):
            raise ValidationError(
                'Impossible de retirer le rôle propriétaire au dernier propriétaire de l\'organisation.'
            )
        
        return new_role


class InvitationForm(forms.Form):
    """
    Formulaire d'invitation selon roadmap 07.
    Simplifié par rapport à InviteUserForm pour la nouvelle logique.
    """
    email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemple.fr',
            'required': True
        }),
        help_text='Adresse email de la personne à inviter'
    )
    
    role = forms.ChoiceField(
        label='Rôle',
        choices=Membership.Role.choices,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        help_text='Rôle à attribuer à cette personne'
    )
    
    def __init__(self, *args, current_user_role=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Limiter les rôles selon le rôle de l'utilisateur actuel (roadmap 07)
        if current_user_role == Membership.Role.ADMIN:
            # Un admin ne peut pas créer d'owner
            available_roles = [
                (Membership.Role.READ_ONLY, 'Lecture seule'),
                (Membership.Role.EDITOR, 'Éditeur'),
                (Membership.Role.ADMIN, 'Administrateur'),
            ]
            self.fields['role'].choices = available_roles
            self.fields['role'].initial = Membership.Role.EDITOR
        else:
            # Un owner peut créer tous les rôles
            self.fields['role'].initial = Membership.Role.EDITOR
    
    def clean_email(self):
        """Validation de l'email d'invitation selon roadmap 07"""
        email = self.cleaned_data.get('email')
        
        # Normaliser l'email
        if email:
            email = email.lower().strip()
        
        return email


class OrganizationBillingForm(forms.ModelForm):
    """
    Formulaire pour les paramètres de facturation - Roadmap 09
    Champs: nom, adresse fiscale, TVA
    """
    
    class Meta:
        model = Organization
        fields = [
            'name', 'address', 'postal_code', 'city', 'country',
            'siret', 'tva_number'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de votre exploitation'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse complète'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Code postal'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ville'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'France'
            }),
            'siret': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro SIRET (optionnel)'
            }),
            'tva_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de TVA intracommunautaire (optionnel)'
            }),
        }
        labels = {
            'name': 'Nom de l\'exploitation',
            'address': 'Adresse fiscale',
            'postal_code': 'Code postal',
            'city': 'Ville',
            'country': 'Pays',
            'siret': 'Numéro SIRET',
            'tva_number': 'Numéro de TVA',
        }
    
    def clean_name(self):
        """Validation du nom d'exploitation"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError('Le nom doit contenir au moins 2 caractères.')
        return name


class OrganizationGeneralForm(forms.ModelForm):
    """
    Formulaire pour les paramètres généraux de l'organisation
    Champs: couleur (pour le header)
    """
    
    class Meta:
        model = Organization
        fields = ['color']
        widgets = {
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color',
                'title': 'Choisir une couleur pour le header'
            }),
        }
        labels = {
            'color': 'Couleur distinctive',
        }
        help_texts = {
            'color': 'Cette couleur sera utilisée pour le header et les éléments distinctifs de ce chai.',
        }


class UserProfileForm(forms.ModelForm):
    """
    Formulaire pour le profil utilisateur - Roadmap 10
    Champs: display_name, locale, timezone, avatar
    """
    
    class Meta:
        model = UserProfile
        fields = ['display_name', 'locale', 'timezone', 'avatar']
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom d\'affichage (optionnel)'
            }),
            'locale': forms.Select(attrs={
                'class': 'form-select'
            }),
            'timezone': forms.Select(attrs={
                'class': 'form-select'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png'
            }),
        }
        labels = {
            'display_name': 'Nom d\'affichage',
            'locale': 'Langue',
            'timezone': 'Fuseau horaire',
            'avatar': 'Photo de profil',
        }
        help_texts = {
            'display_name': 'Nom affiché dans l\'interface (laissez vide pour utiliser votre email)',
            'locale': 'Langue de l\'interface utilisateur',
            'timezone': 'Fuseau horaire pour l\'affichage des dates et heures',
            'avatar': 'Image JPG ou PNG, maximum 2 Mo, format carré recommandé',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ajouter les choix de fuseau horaire depuis le modèle
        self.fields['timezone'].choices = UserProfile.get_timezone_choices()
        
        # Rendre locale et timezone requis selon roadmap 10
        self.fields['locale'].required = True
        self.fields['timezone'].required = True
    
    def clean_avatar(self):
        """Validation de l'avatar selon roadmap 10"""
        avatar = self.cleaned_data.get('avatar')
        
        if avatar:
            # Vérifier la taille (max 2 Mo)
            if avatar.size > 2 * 1024 * 1024:  # 2 Mo en bytes
                raise forms.ValidationError('La taille de l\'image ne peut pas dépasser 2 Mo.')
            
            # Vérifier le format
            if not avatar.content_type in ['image/jpeg', 'image/png']:
                raise forms.ValidationError('Seuls les formats JPG et PNG sont acceptés.')
            
            # Vérifier l'extension
            import os
            ext = os.path.splitext(avatar.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png']:
                raise forms.ValidationError('Seuls les fichiers .jpg, .jpeg et .png sont acceptés.')
        
        return avatar
    
    def clean_display_name(self):
        """Validation du nom d'affichage"""
        display_name = self.cleaned_data.get('display_name')
        
        if display_name:
            display_name = display_name.strip()
            if len(display_name) > 100:
                raise forms.ValidationError('Le nom d\'affichage ne peut pas dépasser 100 caractères.')
        
        return display_name


class OrgBillingForm(forms.ModelForm):
    """
    Formulaire pour les informations de facturation - Roadmap 11
    Gestion des informations légales, fiscales et de facturation
    """
    
    class Meta:
        model = OrgBilling
        fields = [
            'legal_name', 
            'billing_address_line1', 'billing_address_line2', 
            'billing_postal_code', 'billing_city', 'billing_country',
            'siret', 'vat_status', 'vat_number',
            'billing_contact_name', 'billing_contact_email', 'billing_contact_phone'
        ]
        widgets = {
            'legal_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Raison sociale officielle'
            }),
            'billing_address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro et nom de rue'
            }),
            'billing_address_line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Complément d\'adresse (optionnel)'
            }),
            'billing_postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Code postal'
            }),
            'billing_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ville'
            }),
            'billing_country': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'France'
            }),
            'siret': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '14 chiffres (optionnel)',
                'maxlength': '14'
            }),
            'vat_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'vat_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FR + 11 chiffres'
            }),
            'billing_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du contact (optionnel)'
            }),
            'billing_contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemple.com'
            }),
            'billing_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+33 1 23 45 67 89'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Rendre certains champs requis selon roadmap 11
        self.fields['legal_name'].required = True
        self.fields['billing_address_line1'].required = True
        self.fields['billing_postal_code'].required = True
        self.fields['billing_city'].required = True
        self.fields['vat_status'].required = True
        
        # Ajouter des classes CSS pour les champs requis
        for field_name in ['legal_name', 'billing_address_line1', 'billing_postal_code', 'billing_city', 'vat_status']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'required': True})
    
    def clean_siret(self):
        """Validation du SIRET selon roadmap 11"""
        siret = self.cleaned_data.get('siret')
        
        if siret:
            # Supprimer les espaces et caractères non numériques
            siret = ''.join(filter(str.isdigit, siret))
            
            # Vérifier que c'est exactement 14 chiffres
            if len(siret) != 14:
                raise forms.ValidationError('Le SIRET doit contenir exactement 14 chiffres.')
            
            # Vérifier que ce sont bien tous des chiffres
            if not siret.isdigit():
                raise forms.ValidationError('Le SIRET ne peut contenir que des chiffres.')
        
        return siret
    
    def clean_vat_number(self):
        """Validation du numéro de TVA selon roadmap 11"""
        vat_number = self.cleaned_data.get('vat_number')
        vat_status = self.cleaned_data.get('vat_status')
        
        if vat_status == 'subject_to_vat':
            if not vat_number:
                raise forms.ValidationError('Le numéro de TVA est requis si vous êtes assujetti à la TVA.')
            
            # Validation simple du format français FR + 11 chiffres
            vat_number = vat_number.upper().replace(' ', '')
            if not vat_number.startswith('FR'):
                raise forms.ValidationError('Le numéro de TVA français doit commencer par "FR".')
            
            # Vérifier qu'il y a bien 11 chiffres après FR
            vat_digits = vat_number[2:]
            if len(vat_digits) != 11 or not vat_digits.isdigit():
                raise forms.ValidationError('Le numéro de TVA français doit être au format FR + 11 chiffres.')
        
        elif vat_status == 'not_subject_to_vat' and vat_number:
            # Si non assujetti mais numéro fourni, vider le champ
            vat_number = ''
        
        return vat_number
    
    def clean_billing_contact_email(self):
        """Validation de l'email de contact"""
        email = self.cleaned_data.get('billing_contact_email')
        
        if email:
            # Django EmailField fait déjà la validation de base
            # On peut ajouter des validations supplémentaires si nécessaire
            pass
        
        return email
    
    def clean_billing_contact_phone(self):
        """Validation du téléphone de contact"""
        phone = self.cleaned_data.get('billing_contact_phone')
        
        if phone:
            # Validation simple : supprimer les espaces et vérifier la longueur
            phone_digits = ''.join(filter(str.isdigit, phone.replace('+', '')))
            if len(phone_digits) < 10:
                raise forms.ValidationError('Le numéro de téléphone doit contenir au moins 10 chiffres.')
        
        return phone
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        vat_status = cleaned_data.get('vat_status')
        vat_number = cleaned_data.get('vat_number')
        
        # Validation croisée TVA
        if vat_status == 'subject_to_vat' and not vat_number:
            self.add_error('vat_number', 'Le numéro de TVA est requis si vous êtes assujetti à la TVA.')
        
        return cleaned_data


class OrgSettingsForm(forms.ModelForm):
    """Formulaire de paramètres généraux de l'organisation"""
    
    class Meta:
        model = OrgSettings
        fields = ['currency', 'date_format', 'number_format', 'terms_url', 'terms_file']
        widgets = {
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'date_format': forms.RadioSelect(),
            'number_format': forms.RadioSelect(),
            'terms_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://exemple.com/cgv'
            }),
            'terms_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['terms_url'].required = False
        self.fields['terms_file'].required = False
        
        # Aide contextuelle
        self.fields['currency'].help_text = "Devise utilisée pour l'affichage des prix"
        self.fields['date_format'].help_text = "Format d'affichage des dates"
        self.fields['number_format'].help_text = "Format d'affichage des nombres et montants"
        self.fields['terms_url'].help_text = "URL vers vos conditions générales de vente"
        self.fields['terms_file'].help_text = "Ou téléchargez un fichier PDF (max 5 Mo)"
    
    def clean(self):
        cleaned_data = super().clean()
        terms_url = cleaned_data.get('terms_url')
        terms_file = cleaned_data.get('terms_file')
        
        # Si les deux sont fournis, priorité au fichier (vider l'URL)
        if terms_url and terms_file:
            cleaned_data['terms_url'] = ''
        
        return cleaned_data
