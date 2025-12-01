from __future__ import annotations
import re
import csv
import hashlib
from decimal import Decimal
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from apps.drm.models import INAOCode


# ============ Normalization helpers ============

def _norm_color(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s2 = str(s).strip().lower()
    if "rouge" in s2:
        return "rouge"
    if "blanc" in s2:
        return "blanc"
    if "rose" in s2 or "rosé" in s2 or "ros" in s2:
        return "rosé"
    return None


def _parse_degre_field(s: Optional[str]) -> Tuple[Optional[Decimal], Optional[Decimal]]:
    if not s:
        return (None, None)
    txt = str(s).strip().replace(",", ".")
    nums = re.findall(r"\d+(?:\.\d+)?", txt)
    if not nums:
        return (None, None)
    vals = [Decimal(x) for x in nums]
    if not vals:
        return (None, None)
    if len(vals) == 1:
        return (vals[0], None)
    return (min(vals), max(vals))


ess = re.compile(r"(\d+(?:\.\d+)?)\s*(l|litre|litres)\b", re.I)
es_cl = re.compile(r"(\d+(?:\.\d+)?)\s*cl\b", re.I)
es_ml = re.compile(r"(\d+)\s*ml\b", re.I)

def _parse_contenance(s: Optional[str]) -> Optional[Decimal]:
    if not s:
        return None
    txt = str(s).strip().lower().replace(",", ".")
    m = ess.search(txt)
    if m:
        try:
            return Decimal(m.group(1))
        except Exception:
            return None
    m = es_cl.search(txt)
    if m:
        try:
            return (Decimal(m.group(1)) / Decimal(100)).quantize(Decimal("0.001"))
        except Exception:
            return None
    m = es_ml.search(txt)
    if m:
        try:
            return (Decimal(m.group(1)) / Decimal(1000)).quantize(Decimal("0.001"))
        except Exception:
            return None
    # sometimes just a bare number like "0.75"
    try:
        v = Decimal(txt)
        if Decimal("0") < v < Decimal("10"):
            return v.quantize(Decimal("0.001"))
    except Exception:
        pass
    return None


def _q_dec(v: Optional[Decimal], q: str) -> Optional[Decimal]:
    if v is None:
        return None
    try:
        return v.quantize(Decimal(q))
    except Exception:
        return v


def _norm_header(h: str) -> str:
    return (h or "").strip().lower().replace("\n", " ")


# Deterministic short key when no INAO/NC code exists
# Use a short hash to stay within CharField(32)

def _build_det_code(appellation: Optional[str], couleur: Optional[str], type_vin: Optional[str],
                    contenance_l: Optional[Decimal], code_interpro: Optional[str]) -> str:
    # Build a stable short code excluding degrees (to keep idempotence if degrees change)
    base = {
        'app': (appellation or '').strip().lower(),
        'couleur': (couleur or '').strip().lower(),
        'type': (type_vin or '').strip().lower(),
        'cont': str(contenance_l or ''),
        'cip': (code_interpro or '').strip().lower(),
    }
    raw = "|".join([f"{k}={v}" for k, v in base.items()])
    h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"CVI-{h}"  # <= 14 chars


class Command(BaseCommand):
    help = "Importe des 'codes vinicoles' (CSV/XLSX) vers INAOCode en mappant appellation, couleur, degrés, contenance, code_interpro (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--path", required=True, help="Chemin vers le fichier .csv ou .xlsx")
        parser.add_argument("--dry-run", action="store_true", help="Ne rien écrire en base, seulement un rapport")
        parser.add_argument("--encoding", default="utf-8", help="Encodage CSV (par défaut: utf-8)")
        parser.add_argument("--sheet", default=0, help="Feuille Excel (index ou nom), par défaut 0")

    def handle(self, *args, **opts):
        path = Path(opts["path"]) if opts.get("path") else None
        dry = bool(opts.get("dry_run"))
        encoding = opts.get("encoding") or "utf-8"
        sheet = opts.get("sheet") or 0

        if not path or not path.exists():
            raise CommandError(f"Fichier introuvable: {path}")

        rows: List[Dict[str, Any]] = []

        # ---- Read input
        if path.suffix.lower() == ".csv":
            try:
                # Try pandas for robustness
                import pandas as pd  # type: ignore
                df = pd.read_csv(path, dtype=str, encoding=encoding, na_filter=False)
                rows = [dict(r._asdict()) if hasattr(r, "_asdict") else {k: (str(v) if v is not None else '') for k, v in r.items()} for _, r in df.iterrows()]  # type: ignore
            except Exception:
                # Fallback to csv
                with path.open("r", encoding=encoding, newline="") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        rows.append({k: (v or '') for k, v in r.items()})
        else:
            # XLSX via pandas
            try:
                import pandas as pd  # type: ignore
                df = pd.read_excel(path, dtype=str, sheet_name=sheet)
                rows = [ {k: (str(v) if v is not None else '') for k, v in rec.items()} for _, rec in df.iterrows() ]  # type: ignore
            except Exception as e:
                raise CommandError(f"Impossible de lire {path.name}: {e}")

        if not rows:
            self.stdout.write(self.style.WARNING("Aucune ligne à importer"))
            return

        # ---- Column mapping
        def pick(_row: Dict[str, Any], *names: str) -> Optional[str]:
            keys = { _norm_header(k): k for k in _row.keys() }
            for n in names:
                if n in keys:
                    return keys[n]
            # fuzzy contains
            for n in names:
                for lk, kk in keys.items():
                    if n in lk:
                        return kk
            return None

        created = 0
        updated = 0
        skipped = 0

        # Probe first row for header mapping
        hdr_row = rows[0]
        c_app = pick(hdr_row, "appellation", "denomination", "dénomination", "libell")
        c_reg = pick(hdr_row, "region", "région")
        c_cou = pick(hdr_row, "couleur", "color")
        c_type = pick(hdr_row, "type_vin", "type", "style")
        c_deg = pick(hdr_row, "degre", "degré", "degree", "titrage", "alcool")
        c_deg_min = pick(hdr_row, "degre_min", "degré_min")
        c_deg_max = pick(hdr_row, "degre_max", "degré_max")
        c_cont = pick(hdr_row, "contenance_l", "contenance", "volume", "recipient", "récipient", "bouteille", "litres")
        c_code = pick(hdr_row, "code_interpro", "code")
        c_comm = pick(hdr_row, "commentaire", "comment", "notes", "remarque")

        for r in rows:
            try:
                appellation = (r.get(c_app) or '').strip() if c_app else ''
                if not appellation:
                    skipped += 1
                    continue
                region = (r.get(c_reg) or '').strip() if c_reg else ''
                couleur = _norm_color((r.get(c_cou) or '').strip()) if c_cou else None
                type_vin = (r.get(c_type) or '').strip() if c_type else ''

                # Degrés
                degmin: Optional[Decimal] = None
                degmax: Optional[Decimal] = None
                if c_deg_min and (r.get(c_deg_min) or '').strip():
                    try: degmin = Decimal(str(r.get(c_deg_min)).replace(',', '.'))
                    except Exception: degmin = None
                if c_deg_max and (r.get(c_deg_max) or '').strip():
                    try: degmax = Decimal(str(r.get(c_deg_max)).replace(',', '.'))
                    except Exception: degmax = None
                if degmin is None and degmax is None and c_deg and (r.get(c_deg) or '').strip():
                    dmin, dmax = _parse_degre_field(r.get(c_deg))
                    degmin, degmax = dmin, dmax
                degmin = _q_dec(degmin, '0.01')
                degmax = _q_dec(degmax, '0.01')

                # Contenance
                cont_l = _parse_contenance(r.get(c_cont)) if c_cont else None
                cont_l = _q_dec(cont_l, '0.001')

                code_interpro = (r.get(c_code) or '').strip() if c_code else ''
                commentaire = (r.get(c_comm) or '').strip() if c_comm else ''

                # Deterministic short code as key (exclude degrees for stability)
                det_code = _build_det_code(appellation, couleur, type_vin, cont_l, code_interpro)

                # Build condition text amalgamating extra info (region, type, commentaire)
                cond_parts: List[str] = []
                if region:
                    cond_parts.append(f"Région: {region}")
                if type_vin:
                    cond_parts.append(f"Type: {type_vin}")
                if cont_l is not None:
                    cond_parts.append(f"Contenance: {cont_l} L")
                if degmin is not None or degmax is not None:
                    if degmin is not None and degmax is not None:
                        cond_parts.append(f"Degré: {degmin}–{degmax}%")
                    elif degmin is not None:
                        cond_parts.append(f"Degré min: {degmin}%")
                    elif degmax is not None:
                        cond_parts.append(f"Degré max: {degmax}%")
                if code_interpro:
                    cond_parts.append(f"Code interpro: {code_interpro}")
                if commentaire:
                    cond_parts.append(commentaire)
                cond_text = " | ".join(cond_parts)

                # Map into INAOCode fields
                defaults = {
                    'appellation_label': appellation,
                    'color': couleur or '',
                    'condition_text': cond_text,
                    'packaging_min_l': cont_l,
                    'packaging_max_l': cont_l,
                    'abv_min_pct': degmin,
                    'abv_max_pct': degmax,
                    'active': True,
                }

                if dry:
                    skipped += 1
                    continue

                obj, created_flag = INAOCode.objects.update_or_create(
                    code_inao=det_code,
                    code_nc=det_code,
                    defaults=defaults,
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                skipped += 1
                self.stderr.write(self.style.WARNING(f"Ligne ignorée: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"Terminé. Créés: {created} | Mis à jour: {updated} | Ignorés: {skipped}"
        ))
