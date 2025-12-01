"""
Commande pour mettre à jour les permissions des utilisateurs selon leurs rôles
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from apps.accounts.models import User, Membership


class Command(BaseCommand):
    help = 'Met à jour les permissions Django des utilisateurs selon leurs rôles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les changements sans les appliquer',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Mode dry-run activé - aucun changement ne sera appliqué'))
        
        updated_count = 0
        
        # Traiter tous les utilisateurs avec un membership actif
        for user in User.objects.filter(memberships__is_active=True).distinct():
            membership = user.get_active_membership()
            if not membership:
                continue
                
            old_is_staff = user.is_staff
            old_permissions_count = user.user_permissions.count()
            
            # Déterminer les nouveaux droits
            should_be_staff = membership.can_access_billing()
            
            changes = []
            
            if old_is_staff != should_be_staff:
                changes.append(f"is_staff: {old_is_staff} -> {should_be_staff}")
            
            if not dry_run:
                # Appliquer les changements
                user.is_staff = should_be_staff
                
                if should_be_staff:
                    # Donner les permissions pour sales et billing
                    try:
                        sales_permissions = Permission.objects.filter(
                            content_type__app_label='sales'
                        )
                        billing_permissions = Permission.objects.filter(
                            content_type__app_label='billing'
                        )
                        
                        user.user_permissions.set(sales_permissions)
                        user.user_permissions.add(*billing_permissions)
                        
                        new_permissions_count = user.user_permissions.count()
                        if old_permissions_count != new_permissions_count:
                            changes.append(f"permissions: {old_permissions_count} -> {new_permissions_count}")
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Erreur permissions pour {user.email}: {e}')
                        )
                        continue
                else:
                    # Retirer les permissions
                    user.user_permissions.clear()
                    if old_permissions_count > 0:
                        changes.append(f"permissions: {old_permissions_count} -> 0")
                
                user.save()
            
            if changes:
                updated_count += 1
                role_display = membership.get_role_display()
                changes_str = ', '.join(changes)
                self.stdout.write(
                    f'  {user.email} ({role_display}): {changes_str}'
                )
        
        if updated_count > 0:
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'{updated_count} utilisateur(s) seraient mis à jour')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'{updated_count} utilisateur(s) mis à jour avec succès')
                )
        else:
            self.stdout.write('Aucun utilisateur à mettre à jour')
