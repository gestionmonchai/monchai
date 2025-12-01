"""
Utilitaires pour Mon Chai.
Implémentation selon roadmap 04_roles_acces.txt
"""

import json
from datetime import datetime, timedelta
from django.core.signing import Signer, BadSignature, SignatureExpired
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import Membership


class InvitationManager:
    """
    Gestionnaire des invitations avec tokens signés.
    Roadmap 07 : L'invitation est un enregistrement (Invitation) + un lien signé.
    Deux cas d'usage: invité non connecté → signup + session; invité connecté → membership direct
    """
    
    def __init__(self):
        self.signer = Signer(salt='accounts.invite')  # Salt spécifique roadmap 07
        self.expiry_hours = 72  # Expiration 72h selon roadmap 07
    
    def generate_invite_code(self):
        """Générer un code d'invitation court et unique (6 caractères alphanumériques)"""
        import random
        import string
        from .models import Invitation
        
        chars = string.ascii_uppercase + string.digits
        # Éviter les caractères ambigus (0, O, I, l, 1)
        chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
        
        for _ in range(10):  # 10 tentatives max
            code = ''.join(random.choices(chars, k=6))
            if not Invitation.objects.filter(invite_code=code).exists():
                return code
        
        # Fallback: code plus long si collision
        return ''.join(random.choices(chars, k=8))
    
    def create_invitation_token(self, email, organization_id, role):
        """
        Créer un token d'invitation signé.
        
        Args:
            email (str): Email de la personne invitée
            organization_id (int): ID de l'organisation
            role (str): Rôle à attribuer
            
        Returns:
            str: Token signé
        """
        expiry = timezone.now() + timedelta(hours=self.expiry_hours)
        
        payload = {
            'email': email,
            'org_id': organization_id,
            'role': role,
            'exp': expiry.isoformat(),
            'created': timezone.now().isoformat()
        }
        
        # Encoder le payload en JSON puis le signer
        payload_json = json.dumps(payload)
        return self.signer.sign(payload_json)
    
    def verify_invitation_token(self, token):
        """
        Vérifier et décoder un token d'invitation.
        
        Args:
            token (str): Token à vérifier
            
        Returns:
            dict: Payload décodé ou None si invalide
        """
        try:
            # Décoder le token
            payload_json = self.signer.unsign(token)
            payload = json.loads(payload_json)
            
            # Vérifier l'expiration
            expiry = datetime.fromisoformat(payload['exp'])
            if timezone.now() > expiry.replace(tzinfo=timezone.get_current_timezone()):
                return None  # Token expiré
            
            return payload
            
        except (BadSignature, SignatureExpired, json.JSONDecodeError, KeyError):
            return None  # Token invalide
    
    def send_invitation_email(self, email, organization_name, role, token, inviter_name, request):
        """
        Envoyer l'email d'invitation avec templates HTML et texte.
        
        Args:
            email (str): Email du destinataire
            organization_name (str): Nom de l'organisation
            role (str): Rôle à attribuer
            token (str): Token d'invitation
            inviter_name (str): Nom de la personne qui invite
            request: Objet request Django
            
        Returns:
            bool: True si envoi réussi, False sinon
        """
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        
        # Construire l'URL d'acceptation
        accept_url = request.build_absolute_uri(
            reverse('auth:accept_invitation', kwargs={'token': token})
        )
        
        # Mapper le rôle vers un affichage lisible
        role_display_map = {
            'read_only': 'Lecture seule',
            'editor': 'Éditeur',
            'admin': 'Administrateur',
            'owner': 'Propriétaire'
        }
        role_display = role_display_map.get(role, role)
        
        # Contexte pour les templates
        context = {
            'organization_name': organization_name,
            'role_display': role_display,
            'inviter_name': inviter_name,
            'accept_url': accept_url,
            'email': email
        }
        
        # Rendu des templates
        subject = f'Invitation à rejoindre {organization_name} - Mon Chai'
        text_content = render_to_string('emails/invitation_email.txt', context)
        html_content = render_to_string('emails/invitation_email.html', context)
        
        try:
            # Créer l'email avec version HTML et texte
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            return True
        except Exception as e:
            print(f"Erreur envoi email: {e}")
            return False
    
    def get_invitation_info(self, token):
        """
        Obtenir les informations d'une invitation sans la valider complètement.
        Utile pour l'affichage avant acceptation.
        """
        payload = self.verify_invitation_token(token)
        if not payload:
            return None
        
        from .models import Organization
        
        try:
            organization = Organization.objects.get(id=payload['org_id'])
            role_display = dict(Membership.Role.choices).get(payload['role'], payload['role'])
            
            return {
                'email': payload['email'],
                'organization': organization,
                'role': payload['role'],
                'role_display': role_display,
                'expiry': datetime.fromisoformat(payload['exp']),
                'created': datetime.fromisoformat(payload['created'])
            }
        except Organization.DoesNotExist:
            return None
    
    def create_invitation(self, email, organization, role, invited_by, request):
        """
        Créer une invitation complète selon roadmap 07.
        L'invitation est un enregistrement (Invitation) + un lien signé.
        
        Args:
            email (str): Email de la personne invitée
            organization: Instance Organization
            role (str): Rôle à attribuer
            invited_by: Instance User qui invite
            request: Objet request Django
            
        Returns:
            Invitation: Instance créée ou None si erreur
        """
        from .models import Invitation, Organization
        
        # Vérifier qu'il n'y a pas déjà une invitation active (roadmap 07)
        existing = Invitation.objects.filter(
            email=email,
            organization=organization,
            status=Invitation.Status.SENT
        ).first()
        
        if existing and not existing.is_expired():
            # Interdire une deuxième invitation active identique (roadmap 07)
            return None
        
        # Marquer l'ancienne comme expirée si elle existe
        if existing:
            existing.mark_as_expired()
        
        # Créer le token signé
        token = self.create_invitation_token(email, organization.id, role)
        
        # Générer le code d'invitation court
        invite_code = self.generate_invite_code()
        
        # Calculer l'expiration
        expires_at = timezone.now() + timedelta(hours=self.expiry_hours)
        
        # Créer l'enregistrement Invitation
        invitation = Invitation.objects.create(
            email=email,
            organization=organization,
            role=role,
            token=token,
            invite_code=invite_code,
            expires_at=expires_at,
            invited_by=invited_by
        )
        
        # Envoyer l'email (console en dev selon roadmap 07)
        success = self.send_invitation_email(
            email=email,
            organization_name=organization.name,
            role=role,
            token=token,
            inviter_name=invited_by.full_name,
            request=request
        )
        
        if not success:
            print(f"Erreur envoi email pour invitation {invitation.id}")
        
        return invitation
    
    def accept_invitation(self, token, user=None):
        """
        Accepter une invitation selon roadmap 07.
        Deux cas d'usage:
        1) Invité non connecté → stocker payload en session, rediriger /auth/signup/
        2) Invité déjà connecté → créer immédiatement le Membership
        
        Args:
            token (str): Token d'invitation
            user: Instance User si connecté, None sinon
            
        Returns:
            dict: Résultat avec 'success', 'action', 'payload', 'membership'
        """
        from .models import Invitation, Membership
        
        # Vérifier le token
        payload = self.verify_invitation_token(token)
        if not payload:
            return {
                'success': False,
                'error': 'Token invalide ou expiré',
                'action': 'error'
            }
        
        # Récupérer l'invitation
        try:
            invitation = Invitation.objects.get(token=token)
        except Invitation.DoesNotExist:
            return {
                'success': False,
                'error': 'Invitation introuvable',
                'action': 'error'
            }
        
        # Vérifier que l'invitation peut être acceptée
        if not invitation.can_be_accepted():
            return {
                'success': False,
                'error': 'Invitation expirée ou déjà acceptée',
                'action': 'error'
            }
        
        # Cas 2: Utilisateur connecté → créer immédiatement le Membership
        if user and user.is_authenticated:
            # Vérifier que l'email correspond
            if user.email != invitation.email:
                return {
                    'success': False,
                    'error': 'Cette invitation n\'est pas pour votre compte',
                    'action': 'error'
                }
            
            # Créer ou récupérer le membership
            membership, created = Membership.objects.get_or_create(
                user=user,
                organization=invitation.organization,
                defaults={
                    'role': invitation.role,
                    'is_active': True
                }
            )
            
            if not created:
                # Mettre à jour le rôle si membership existant
                membership.role = invitation.role
                membership.is_active = True
                membership.save()
            
            # Marquer l'invitation comme acceptée
            invitation.mark_as_accepted(user)
            
            return {
                'success': True,
                'action': 'membership_created',
                'membership': membership,
                'payload': payload
            }
        
        # Cas 1: Utilisateur non connecté → payload en session
        else:
            return {
                'success': True,
                'action': 'store_in_session',
                'payload': {
                    'email': invitation.email,
                    'organization_id': invitation.organization.id,
                    'organization_name': invitation.organization.name,
                    'role': invitation.role,
                    'role_display': invitation.get_role_display(),
                    'token': token,
                    'invitation_id': invitation.id
                }
            }
    
    def accept_by_code(self, code, user):
        """
        Accepter une invitation par code court.
        L'utilisateur doit être connecté.
        
        Args:
            code (str): Code d'invitation (6 caractères)
            user: Instance User connecté
            
        Returns:
            dict: Résultat avec 'success', 'error', 'membership', 'organization'
        """
        from .models import Invitation, Membership
        
        code = code.strip().upper()
        
        # Chercher l'invitation
        try:
            invitation = Invitation.objects.select_related('organization').get(
                invite_code=code,
                status=Invitation.Status.SENT
            )
        except Invitation.DoesNotExist:
            return {
                'success': False,
                'error': 'Code d\'invitation invalide ou expiré.'
            }
        
        # Vérifier expiration
        if invitation.is_expired():
            invitation.mark_as_expired()
            return {
                'success': False,
                'error': 'Cette invitation a expiré.'
            }
        
        # Vérifier si déjà membre
        if Membership.objects.filter(user=user, organization=invitation.organization, is_active=True).exists():
            return {
                'success': False,
                'error': f'Vous êtes déjà membre de {invitation.organization.name}.'
            }
        
        # Créer le membership
        membership = Membership.objects.create(
            user=user,
            organization=invitation.organization,
            role=invitation.role,
            is_active=True
        )
        
        # Marquer l'invitation comme acceptée
        invitation.mark_as_accepted(user)
        
        return {
            'success': True,
            'membership': membership,
            'organization': invitation.organization,
            'role_display': membership.get_role_display()
        }


# Instance globale du gestionnaire d'invitations
invitation_manager = InvitationManager()


class ChecklistService:
    """
    Service de gestion de la checklist d'onboarding - Roadmap 09
    Utilitaires pour get_or_create_checklist et checklist_update
    """
    
    def get_or_create_checklist(self, organization):
        """
        Obtenir ou créer la checklist pour une organisation
        Initialise avec état 'todo' partout selon roadmap 09
        """
        from .models import OrgSetupChecklist
        
        checklist, created = OrgSetupChecklist.objects.get_or_create(
            organization=organization,
            defaults={
                'state': OrgSetupChecklist.get_default_state()
            }
        )
        return checklist
    
    def checklist_update(self, organization, task_key, is_done):
        """
        Mettre à jour l'état d'une tâche de la checklist
        
        Args:
            organization: Instance Organization
            task_key: str - 'company_info', 'taxes', 'currency_format', 'terms'
            is_done: bool - True pour marquer comme 'done', False pour 'todo'
        """
        from .models import OrgSetupChecklist
        
        checklist = self.get_or_create_checklist(organization)
        
        new_status = OrgSetupChecklist.TaskStatus.DONE if is_done else OrgSetupChecklist.TaskStatus.TODO
        checklist.update_task(task_key, new_status)
        
        return checklist
    
    def check_company_info_completion(self, organization):
        """
        Vérifier si les infos exploitation sont complètes
        Selon roadmap 09: nom d'exploitation ET adresse fiscale présents
        """
        # Vérifier nom et adresse fiscale
        has_name = bool(organization.name and organization.name.strip())
        has_address = bool(
            organization.address and organization.address.strip() and
            organization.postal_code and organization.postal_code.strip() and
            organization.city and organization.city.strip()
        )
        
        return has_name and has_address
    
    def check_taxes_completion(self, organization):
        """
        Vérifier si la configuration TVA/taxes est complète
        Selon roadmap 09: TVA ou statut "non assujetti" choisi
        """
        # Vérifier si numéro TVA présent (même vide mais défini)
        # ou si un statut fiscal est configuré
        has_tva_config = (
            hasattr(organization, 'tva_number') or  # Champ TVA existe
            hasattr(organization, 'tax_status')     # Ou statut fiscal défini
        )
        
        return has_tva_config
    
    def check_currency_format_completion(self, organization):
        """
        Vérifier si devise et formats sont définis
        Selon roadmap 12: devise, date_format et number_format définis dans OrgSettings
        """
        try:
            settings = organization.settings
            return bool(settings.currency and settings.date_format and settings.number_format)
        except:
            return False
    
    def check_terms_completion(self, organization):
        """
        Vérifier si les CGV sont configurées
        Selon roadmap 12: CGV URL ou fichier PDF défini dans OrgSettings
        """
        try:
            settings = organization.settings
            return settings.has_terms()
        except:
            return False
    
    def auto_update_from_organization(self, organization):
        """
        Mise à jour automatique de la checklist basée sur l'état de l'organisation
        Appelé après modification des paramètres
        """
        checklist = self.get_or_create_checklist(organization)
        
        # Vérifier chaque tâche
        tasks_status = {
            'company_info': self.check_company_info_completion(organization),
            'taxes': self.check_taxes_completion(organization),
            'currency_format': self.check_currency_format_completion(organization),
            'terms': self.check_terms_completion(organization)
        }
        
        # Mettre à jour chaque tâche
        for task_key, is_complete in tasks_status.items():
            current_status = checklist.state.get(task_key, checklist.TaskStatus.TODO)
            
            # Ne pas régresser une tâche marquée manuellement comme 'done'
            if current_status != checklist.TaskStatus.DONE:
                new_status = checklist.TaskStatus.DONE if is_complete else checklist.TaskStatus.TODO
                if current_status != new_status:
                    checklist.update_task(task_key, new_status)
        
        return checklist


# Instance globale du service de checklist
checklist_service = ChecklistService()


def get_display_name(user):
    """
    Utilitaire pour obtenir le nom d'affichage d'un utilisateur - Roadmap 10
    Fallback selon roadmap 10: display_name > first_name last_name > email
    
    Args:
        user: Instance User
        
    Returns:
        str: Nom d'affichage approprié
    """
    try:
        # Essayer d'utiliser le profil utilisateur
        profile = user.profile
        return profile.get_display_name()
    except:
        # Fallback si pas de profil (ne devrait pas arriver avec le signal)
        if user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name}"
        
        if user.first_name:
            return user.first_name
        
        return user.email
