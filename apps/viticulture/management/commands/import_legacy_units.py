"""
Importe les unités legacy (apps.referentiels.Unite) vers viticulture.UnitOfMeasure
- Mappe nom/symbole/facteur_conversion -> name/code/base_ratio_to_l
- Définit l'unité par défaut (par code) si demandé

Usage:
  python manage.py import_legacy_units [--org-id <uuid>] [--force] [--set-default L]

Comportement:
- Par défaut, merge sans écraser: crée les UoM manquantes; met à jour seulement si --force
- Le default est positionné sur le code donné par --set-default (défaut: L) s'il existe
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Organization
from apps.referentiels.models import Unite as LegacyUnite
from apps.viticulture.models import UnitOfMeasure


class Command(BaseCommand):
    help = "Importe les unités de 'referentiels.Unite' vers 'viticulture.UnitOfMeasure'"

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-id',
            type=str,
            help="ID de l'organisation (optionnel, prend la première si non spécifié)"
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Met à jour les unités existantes avec les valeurs legacy'
        )
        parser.add_argument(
            '--set-default',
            type=str,
            default='L',
            help="Code de l'unité à définir par défaut (défaut: L)"
        )

    def handle(self, *args, **options):
        # Résoudre organisation cible
        organization = None
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

        # Récupérer unités legacy pour l'org
        # Importer uniquement les unités de type volume
        legacy_units = LegacyUnite.objects.filter(organization=organization, type_unite='volume').order_by('nom')
        if not legacy_units.exists():
            self.stdout.write(self.style.WARNING("Aucune unité legacy à importer pour cette organisation."))
            return

        created, updated, skipped = 0, 0, 0

        with transaction.atomic():
            for lu in legacy_units:
                name = (lu.nom or '').strip()[:50]
                symb = (lu.symbole or '').strip()
                code = (symb or name[:10]).upper()[:10] or None

                if not code:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"  Ignoré (code manquant): {name}"))
                    continue

                try:
                    ratio = Decimal(lu.facteur_conversion)
                except Exception:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"  Ignoré (facteur invalid): {name}"))
                    continue

                defaults = {
                    'name': name or code,
                    'base_ratio_to_l': ratio,
                    'is_default': False,
                }

                # Éviter les doublons en recherchant une UoM existante en insensible à la casse
                existing = UnitOfMeasure.objects.filter(
                    organization=organization,
                    code__iexact=code,
                ).first()

                if existing:
                    if options['force']:
                        existing.name = defaults['name']
                        existing.base_ratio_to_l = defaults['base_ratio_to_l']
                        existing.save(update_fields=['name', 'base_ratio_to_l'])
                        updated += 1
                        self.stdout.write(f"  UoM mise à jour: {existing.name} ({existing.code})")
                    else:
                        skipped += 1
                        self.stdout.write(f"  UoM existante conservée: {existing.name} ({existing.code})")
                else:
                    uom = UnitOfMeasure.objects.create(
                        organization=organization,
                        code=code,
                        **defaults,
                    )
                    created += 1
                    self.stdout.write(f"  UoM créée: {uom.name} ({uom.code}) => {uom.base_ratio_to_l} L")

            # Positionner l'unité par défaut si présente
            default_code = (options.get('set_default') or 'L').upper()
            default_uom = UnitOfMeasure.objects.filter(organization=organization, code__iexact=default_code).first()
            if default_uom:
                UnitOfMeasure.objects.filter(organization=organization, is_default=True).exclude(id=default_uom.id).update(is_default=False)
                if not default_uom.is_default:
                    default_uom.is_default = True
                    default_uom.save(update_fields=['is_default'])
                self.stdout.write(self.style.SUCCESS(f"Unité par défaut: {default_uom.name} ({default_uom.code})"))
            else:
                self.stdout.write(self.style.WARNING(f"Aucune unité trouvée pour set-default='{default_code}'."))

            # Optionnel: désactiver les unités non-volume si elles existent côté viticulture (nettoyage)
            # Cela aligne le référentiel viticulture sur les unités strictement volume
            non_volume = LegacyUnite.objects.filter(organization=organization).exclude(type_unite='volume')
            deactivated = 0
            for lu in non_volume:
                name = (lu.nom or '').strip()[:50]
                symb = (lu.symbole or '').strip()
                code = (symb or name[:10]).upper()[:10]
                if not code:
                    continue
                u = UnitOfMeasure.objects.filter(organization=organization, code__iexact=code, is_active=True).first()
                if u:
                    u.is_active = False
                    u.save(update_fields=['is_active'])
                    deactivated += 1
            if deactivated:
                self.stdout.write(self.style.WARNING(f"Unités non-volume désactivées: {deactivated}"))

        # Résumé
        self.stdout.write(self.style.SUCCESS(f"Import terminé. Créées: {created}, Mises à jour: {updated}, Ignorées: {skipped}"))
