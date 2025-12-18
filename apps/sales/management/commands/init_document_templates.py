"""
Commande pour initialiser les templates de documents par défaut
Usage: python manage.py init_document_templates
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import Organization
from apps.sales.models_documents import DocumentTemplate
from apps.sales.default_templates import DEFAULT_TEMPLATES


class Command(BaseCommand):
    help = 'Crée les templates de documents par défaut pour toutes les organisations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--org',
            type=str,
            help='Slug de l\'organisation (optionnel, sinon toutes)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recréer même si les templates existent déjà',
        )
    
    def handle(self, *args, **options):
        org_slug = options.get('org')
        force = options.get('force', False)
        
        if org_slug:
            orgs = Organization.objects.filter(slug=org_slug)
            if not orgs.exists():
                self.stderr.write(self.style.ERROR(f'Organisation "{org_slug}" non trouvée'))
                return
        else:
            orgs = Organization.objects.all()
        
        for org in orgs:
            self.stdout.write(f'Organisation: {org.name}')
            created_count = 0
            skipped_count = 0
            
            for doc_type, preset in DEFAULT_TEMPLATES.items():
                # Vérifier si un template par défaut existe déjà
                existing = DocumentTemplate.objects.filter(
                    organization=org,
                    document_type=doc_type,
                    is_default=True
                ).first()
                
                if existing and not force:
                    self.stdout.write(f'  - {doc_type}: déjà existant (skipped)')
                    skipped_count += 1
                    continue
                
                if existing and force:
                    existing.delete()
                
                # Créer le template
                template = DocumentTemplate.objects.create(
                    organization=org,
                    name=preset['name'],
                    document_type=doc_type,
                    description=preset.get('description', ''),
                    is_default=True,
                    is_active=True,
                    paper_size='A4',
                    orientation='portrait',
                    html_header=preset.get('header', ''),
                    html_body=preset.get('body', ''),
                    html_footer=preset.get('footer', ''),
                    custom_css=preset.get('css', ''),
                )
                
                self.stdout.write(self.style.SUCCESS(f'  - {doc_type}: créé ({template.name})'))
                created_count += 1
            
            self.stdout.write(f'  Total: {created_count} créés, {skipped_count} ignorés\n')
        
        self.stdout.write(self.style.SUCCESS('Terminé!'))
