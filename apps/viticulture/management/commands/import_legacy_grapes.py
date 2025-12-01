"""
Importe les cépages legacy (apps.referentiels.Cepage) vers viticulture.GrapeVariety
- Mappe nom/couleur -> name/color
- Merge par name_norm (insensible à la casse et accents)

Usage:
  python manage.py import_legacy_grapes [--org-id <uuid>] [--force]

Comportement:
- Par défaut, merge sans écraser: crée les cépages manquants; met à jour seulement si --force
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Organization
from apps.referentiels.models import Cepage as LegacyCepage
from apps.viticulture.models import GrapeVariety


class Command(BaseCommand):
    help = "Importe les cépages de 'referentiels.Cepage' vers 'viticulture.GrapeVariety'"

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-id',
            type=str,
            help="ID de l'organisation (optionnel, prend la première si non spécifié)"
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Met à jour les cépages existants avec les valeurs legacy'
        )

    def handle(self, *args, **options):
        # Résoudre organisation cible
        if options['org_id']:
            try:
                organization = Organization.objects.get(id=options['org_id'])
            except Organization.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Organisation {options['org_id']} non trouvée"))
                return
        else:
            organization = Organization.objects.first()
            if not organization:
                self.stdout.write(self.style.ERROR("Aucune organisation trouvée."))
                return

        self.stdout.write(f"Organisation: {organization.name}")

        # Récupérer cépages legacy
        legacy_cepages = LegacyCepage.objects.filter(organization=organization, is_active=True).order_by('nom')
        if not legacy_cepages.exists():
            self.stdout.write(self.style.WARNING("Aucun cépage legacy à importer pour cette organisation."))
            return

        created, updated, skipped = 0, 0, 0
        color_map = {
            'rouge': 'rouge',
            'blanc': 'blanc',
            'rose': 'rose',
        }

        with transaction.atomic():
            for lc in legacy_cepages:
                name = (lc.nom or '').strip()
                if not name:
                    skipped += 1
                    continue
                color = color_map.get((lc.couleur or '').strip().lower(), 'rouge')
                name_norm = (name or '').lower().strip()

                existing = GrapeVariety.objects.filter(organization=organization, name_norm=name_norm).first()
                if existing:
                    if options['force']:
                        existing.name = name
                        existing.color = color
                        existing.save(update_fields=['name', 'color'])
                        updated += 1
                        self.stdout.write(f"  Cépage mis à jour: {existing.name} ({existing.get_color_display()})")
                    else:
                        skipped += 1
                        self.stdout.write(f"  Cépage existant conservé: {existing.name}")
                else:
                    gv = GrapeVariety.objects.create(
                        organization=organization,
                        name=name,
                        color=color,
                    )
                    created += 1
                    self.stdout.write(f"  Cépage créé: {gv.name} ({gv.get_color_display()})")

        self.stdout.write(self.style.SUCCESS(f"Import cépages terminé. Créés: {created}, Mises à jour: {updated}, Ignorés: {skipped}"))
