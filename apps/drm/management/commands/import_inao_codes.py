from __future__ import annotations
import os
import csv
from datetime import datetime
from typing import Optional, Dict
from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings
from apps.drm.models import INAOCode


def _norm_header(h: str) -> str:
    return (h or "").strip().lower().replace("\n", " ")


def parse_categorie(cat_text: str) -> tuple:
    """Parse la catégorie pour extraire le code, la couleur et la région."""
    cat = cat_text.strip()
    
    # Déterminer le code catégorie
    cat_lower = cat.lower()
    if 'igp' in cat_lower and 'blanc' in cat_lower:
        code = 'igp_blanc'
        color = 'blanc'
    elif 'igp' in cat_lower and ('rouge' in cat_lower or 'rosé' in cat_lower):
        code = 'igp_rouge_rose'
        color = 'rouge/rosé'
    elif 'aop' in cat_lower and 'blanc' in cat_lower:
        code = 'aop_blanc'
        color = 'blanc'
    elif 'aop' in cat_lower and ('rouge' in cat_lower or 'rosé' in cat_lower):
        code = 'aop_rouge_rose'
        color = 'rouge/rosé'
    else:
        code = 'autre'
        color = ''
    
    # Extraire la région
    region = ''
    regions = ['ALSACE', 'BORDEAUX', 'BOURGOGNE', 'CHAMPAGNE', 'LOIRE', 'VAL DE LOIRE',
               'RHÔNE', 'VALLÉE DU RHÔNE', 'PROVENCE', 'LANGUEDOC', 'SUD-OUEST', 'JURA', 
               'SAVOIE', 'CORSE', 'BEAUJOLAIS']
    for r in regions:
        if r in cat.upper():
            region = r.title()
            break
    
    return code, color, region


class Command(BaseCommand):
    help = "Importe les codes INAO/NC depuis un fichier CSV ou Excel."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--path",
            dest="path",
            default=None,
            help="Chemin vers le fichier CSV ou Excel",
        )
        parser.add_argument(
            "--sheet",
            dest="sheet",
            default=0,
            help="Nom ou index de la feuille Excel (par défaut 0)",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Vider la table avant import",
        )

    def handle(self, *args, **options):
        path = options.get("path")
        truncate = options.get("truncate")

        if not path:
            # Cherche le fichier CSV à la racine du projet
            default_csv = "monchai_import_clean_test.csv"
            candidate = os.path.join(settings.BASE_DIR, default_csv)
            if os.path.exists(candidate):
                path = candidate
        
        if not path or not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"Fichier introuvable: {path!r}"))
            return

        if truncate:
            INAOCode.objects.all().delete()
            self.stdout.write(self.style.WARNING("Table INAOCode vidée"))

        records = 0
        errors = 0

        # Détection format (CSV ou Excel)
        if path.endswith('.csv'):
            self.stdout.write(f"Import CSV: {path}")
            records, errors = self._import_csv(path)
        else:
            self.stdout.write(f"Import Excel: {path}")
            records, errors = self._import_excel(path, options.get("sheet", 0))

        self.stdout.write(self.style.SUCCESS(f"Import terminé: {records} lignes, {errors} erreurs"))

    def _import_csv(self, path: str) -> tuple:
        """Import depuis fichier CSV par index de colonnes (plus robuste)."""
        records = 0
        errors = 0
        
        # Colonnes par index (évite les problèmes d'encodage des noms):
        # 0: Libellé FR (appellation)
        # 1: Nomenclature combinée : code NC  <-- IMPORTANT
        # 2: Code vinicole interprofessionnel (code INAO)
        # 3: Date de début de validité
        # 4: Catégorie (mal nommée dans le CSV)
        # 5: Contenance
        
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Skip header row
            self.stdout.write(f"Colonnes détectées: {headers}")
            
            for row in reader:
                try:
                    if len(row) < 6:
                        continue
                    
                    appellation = row[0].strip()
                    code_nc = row[1].strip()      # Colonne B - Nomenclature combinée
                    code_inao = row[2].strip()    # Colonne C - Code vinicole
                    date_str = row[3].strip()
                    categorie = row[4].strip()
                    contenance = row[5].strip() if len(row) > 5 else ''
                    
                    if not code_inao and not code_nc:
                        continue
                    
                    # Parser la date
                    date_validite = None
                    if date_str:
                        try:
                            date_validite = datetime.strptime(date_str, '%d/%m/%Y').date()
                        except ValueError:
                            pass
                    
                    # Parser la catégorie
                    cat_code, color, region = parse_categorie(categorie)
                    
                    # Créer ou mettre à jour (clé unique: code_inao + code_nc)
                    INAOCode.objects.update_or_create(
                        code_inao=code_inao,
                        code_nc=code_nc,
                        defaults={
                            'appellation_label': appellation,
                            'categorie': categorie,
                            'categorie_code': cat_code,
                            'color': color,
                            'region': region,
                            'date_validite': date_validite,
                            'contenance': contenance,
                            'active': True,
                        }
                    )
                    records += 1
                    
                except Exception as e:
                    errors += 1
                    self.stderr.write(self.style.WARNING(f"Ligne ignorée: {e}"))
        
        return records, errors

    def _import_excel(self, path: str, sheet) -> tuple:
        """Import depuis fichier Excel (legacy)."""
        from apps.drm.services import parse_condition_text_to_bounds
        
        records = 0
        errors = 0
        
        try:
            import pandas as pd
            df = pd.read_excel(path, sheet_name=sheet, dtype=str)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erreur lecture Excel: {e}"))
            return 0, 1
        
        for _, row in df.iterrows():
            try:
                code_inao = str(row.get('Code vinicole interprofessionnel', '') or '').strip()
                code_nc = str(row.get('Nomenclature combinée : code NC', '') or '').strip()
                
                if not code_inao and not code_nc:
                    continue
                
                appellation = str(row.get('Libéllé FR', '') or '').strip()
                
                INAOCode.objects.update_or_create(
                    code_inao=code_inao or code_nc,
                    code_nc=code_nc or code_inao,
                    defaults={
                        'appellation_label': appellation,
                        'active': True,
                    }
                )
                records += 1
            except Exception as e:
                errors += 1
                self.stderr.write(self.style.WARNING(f"Ligne ignorée: {e}"))
        
        return records, errors
