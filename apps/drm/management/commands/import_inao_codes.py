from __future__ import annotations
import os
from typing import Optional, Dict
from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings
from apps.drm.models import INAOCode
from apps.drm.services import parse_condition_text_to_bounds


def _norm_header(h: str) -> str:
    return (h or "").strip().lower().replace("\n", " ")


class Command(BaseCommand):
    help = "Importe les codes INAO/NC depuis un fichier Excel et parse les conditions (packaging/ABV)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--path",
            dest="path",
            default=None,
            help="Chemin vers le fichier Excel (par défaut: 'codes vinicoles interprofessionnels 2022 V3.xls' à la racine)",
        )
        parser.add_argument(
            "--sheet",
            dest="sheet",
            default=0,
            help="Nom ou index de la feuille (par défaut 0)",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Vider la table avant import",
        )

    def handle(self, *args, **options):
        path = options.get("path")
        sheet = options.get("sheet")
        truncate = options.get("truncate")

        if not path:
            # Cherche le fichier à la racine du projet
            default_name = "codes vinicoles interprofessionnels 2022 V3.xls"
            candidate = os.path.join(settings.BASE_DIR, default_name)
            if os.path.exists(candidate):
                path = candidate
            else:
                # Essaye aussi .xlsx
                candidate_x = os.path.join(settings.BASE_DIR, default_name + "x")
                if os.path.exists(candidate_x):
                    path = candidate_x
        if not path or not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"Fichier introuvable: {path!r}"))
            return

        if truncate:
            INAOCode.objects.all().delete()
            self.stdout.write(self.style.WARNING("Table INAOCode vidée"))

        # Lecture Excel via pandas si disponible, sinon xlrd/openpyxl
        df = None
        read_err: Optional[Exception] = None
        try:
            import pandas as pd  # type: ignore
            try:
                df = pd.read_excel(path, sheet_name=sheet, dtype=str)
            except Exception:
                # Try specifying engine explicitly
                df = pd.read_excel(path, sheet_name=sheet, dtype=str, engine="xlrd")
        except Exception as e:
            read_err = e
        if df is None:
            try:
                # Fallback très basique via xlrd (pour .xls)
                import xlrd  # type: ignore
                book = xlrd.open_workbook(path)
                sh = book.sheet_by_index(int(sheet) if isinstance(sheet, int) or str(sheet).isdigit() else 0)
                headers = [_norm_header(sh.cell_value(0, c)) for c in range(sh.ncols)]
                rows = []
                for r in range(1, sh.nrows):
                    row = {}
                    for c in range(sh.ncols):
                        row[headers[c]] = str(sh.cell_value(r, c))
                    rows.append(row)
                df = rows  # type: ignore
            except Exception as e2:
                self.stderr.write(self.style.ERROR(f"Impossible de lire le fichier Excel: {read_err or e2}"))
                return

        # Normalisation headers + itération
        records = 0
        errors = 0

        def get_cols_map(columns) -> Dict[str, Optional[str]]:
            cols = { _norm_header(c): c for c in columns }
            def find(*cands: str) -> Optional[str]:
                for k, v in cols.items():
                    for cand in cands:
                        if cand in k:
                            return v
                return None
            return {
                'code_inao': find('inao'),
                'code_nc': find('nc'),
                'appellation': find('appell', 'denomin', 'designation', 'libelle'),
                'color': find('couleur', 'color'),
                'conditions': find('condition', 'observ', 'comment', 'note', 'texte'),
            }

        if hasattr(df, 'columns'):
            # pandas DataFrame
            colmap = get_cols_map(df.columns)
            for _, row in df.iterrows():
                try:
                    code_inao = (row.get(colmap['code_inao']) or '').strip()
                    code_nc = (row.get(colmap['code_nc']) or '').strip()
                    if not code_inao and not code_nc:
                        continue
                    appellation = (row.get(colmap['appellation']) or '').strip()
                    color = (row.get(colmap['color']) or '').strip()
                    cond_text = (row.get(colmap['conditions']) or '').strip()
                    pmin, pmax, amin, amax = parse_condition_text_to_bounds(cond_text)
                    INAOCode.objects.update_or_create(
                        code_inao=code_inao or code_nc,
                        code_nc=code_nc or code_inao,
                        defaults={
                            'appellation_label': appellation,
                            'color': color,
                            'condition_text': cond_text,
                            'packaging_min_l': pmin,
                            'packaging_max_l': pmax,
                            'abv_min_pct': amin,
                            'abv_max_pct': amax,
                            'active': True,
                        }
                    )
                    records += 1
                except Exception as e:
                    errors += 1
                    self.stderr.write(self.style.WARNING(f"Ligne ignorée: {e}"))
        else:
            # list[dict] fallback
            colmap = get_cols_map(list(df[0].keys()) if df else [])
            for row in (df or []):
                try:
                    code_inao = (row.get(colmap['code_inao']) or '').strip()
                    code_nc = (row.get(colmap['code_nc']) or '').strip()
                    if not code_inao and not code_nc:
                        continue
                    appellation = (row.get(colmap['appellation']) or '').strip()
                    color = (row.get(colmap['color']) or '').strip()
                    cond_text = (row.get(colmap['conditions']) or '').strip()
                    pmin, pmax, amin, amax = parse_condition_text_to_bounds(cond_text)
                    INAOCode.objects.update_or_create(
                        code_inao=code_inao or code_nc,
                        code_nc=code_nc or code_inao,
                        defaults={
                            'appellation_label': appellation,
                            'color': color,
                            'condition_text': cond_text,
                            'packaging_min_l': pmin,
                            'packaging_max_l': pmax,
                            'abv_min_pct': amin,
                            'abv_max_pct': amax,
                            'active': True,
                        }
                    )
                    records += 1
                except Exception as e:
                    errors += 1
                    self.stderr.write(self.style.WARNING(f"Ligne ignorée: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Import terminé: {records} lignes, {errors} erreurs"))
