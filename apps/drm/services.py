from __future__ import annotations
import re
from decimal import Decimal
from typing import Optional, Tuple
from django.db.models import Q, QuerySet
from .models import INAOCode



def _to_decimal(val: Optional[str]) -> Optional[Decimal]:
    if val is None:
        return None
    try:
        s = str(val).strip().replace(',', '.')
        if not s:
            return None
        return Decimal(s)
    except Exception:
        return None


def parse_condition_text_to_bounds(text: Optional[str]) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
    """
    Parse French regulatory condition text to extract packaging (L) and ABV (%) bounds.
    Supports patterns like:
    - "n'excédant pas 2 L" → max L = 2
    - "au plus 1,5 litre" → max L = 1.5
    - "au moins 0,2 L" → min L = 0.2
    - "compris entre 0,2 L et 2 L" → min L = 0.2, max L = 2
    - "≤ 2 L" / "< 2 L" / ">= 0,2 L"
    - "n'excédant pas 15 degrés" → max % = 15
    - "titre alcoométrique volumique > 14,5 %" → min % = 14.5
    Returns: (packaging_min_l, packaging_max_l, abv_min_pct, abv_max_pct)
    """
    if not text:
        return None, None, None, None
    t = text.lower()
    t = t.replace("litres", "l").replace("litre", "l").replace("degrés", "%").replace("degre", "%").replace("degré", "%")

    pmin = pmax = amin = amax = None

    # between patterns: "compris entre X et Y", "entre X et Y"
    m = re.search(r"(compris\s+)?entre\s*(\d+[\.,]?\d*)\s*l?\s*et\s*(\d+[\.,]?\d*)\s*l", t)
    if m:
        pmin = _to_decimal(m.group(2))
        pmax = _to_decimal(m.group(3))

    m = re.search(r"(compris\s+)?entre\s*(\d+[\.,]?\d*)\s*%\s*et\s*(\d+[\.,]?\d*)\s*%", t)
    if m:
        amin = _to_decimal(m.group(2))
        amax = _to_decimal(m.group(3))

    # max patterns for packaging
    for pat in [
        r"n['’]exc[ée]d(?:ant|e)?\s*pas\s*(\d+[\.,]?\d*)\s*l",
        r"au\s+plus\s*(\d+[\.,]?\d*)\s*l",
        r"(?:<=|≤)\s*(\d+[\.,]?\d*)\s*l",
        r"inf[ée]rieur\s*(?:ou\s*égal\s*)?\s*à\s*(\d+[\.,]?\d*)\s*l",
    ]:
        m = re.search(pat, t)
        if m:
            pmax = _to_decimal(m.group(1))
            break

    # min patterns for packaging
    for pat in [
        r"au\s+moins\s*(\d+[\.,]?\d*)\s*l",
        r"(?:>=|≥)\s*(\d+[\.,]?\d*)\s*l",
        r"sup[ée]rieur\s*(?:ou\s*égal\s*)?\s*à\s*(\d+[\.,]?\d*)\s*l",
    ]:
        m = re.search(pat, t)
        if m:
            pmin = _to_decimal(m.group(1))
            break

    # max patterns for ABV
    for pat in [
        r"n['’]exc[ée]d(?:ant|e)?\s*pas\s*(\d+[\.,]?\d*)\s*%",
        r"au\s+plus\s*(\d+[\.,]?\d*)\s*%",
        r"(?:<=|≤)\s*(\d+[\.,]?\d*)\s*%",
        r"inf[ée]rieur\s*(?:ou\s*égal\s*)?\s*à\s*(\d+[\.,]?\d*)\s*%",
    ]:
        m = re.search(pat, t)
        if m:
            amax = _to_decimal(m.group(1))
            break

    # min patterns for ABV
    for pat in [
        r"au\s+moins\s*(\d+[\.,]?\d*)\s*%",
        r"(?:>=|≥)\s*(\d+[\.,]?\d*)\s*%",
        r"sup[ée]rieur\s*(?:ou\s*égal\s*)?\s*à\s*(\d+[\.,]?\d*)\s*%",
        r"titre\s+alcoom[ée]trique\s+volumique\s*(?:>\s*|sup[ée]rieur\s*à\s*)(\d+[\.,]?\d*)\s*%",
    ]:
        m = re.search(pat, t)
        if m:
            amin = _to_decimal(m.group(1))
            break

    return pmin, pmax, amin, amax


def select_inao_codes(*, appellation: Optional[str] = None, color: Optional[str] = None,
                      volume_l: Optional[Decimal] = None, abv_pct: Optional[Decimal] = None,
                      q: Optional[str] = None, limit: int = 50) -> QuerySet:
    qs = INAOCode.objects.filter(active=True)
    if q:
        qnorm = q.strip()
        if qnorm:
            qs = qs.filter(
                Q(code_inao__icontains=qnorm) |
                Q(code_nc__icontains=qnorm) |
                Q(appellation_label__icontains=qnorm) |
                Q(condition_text__icontains=qnorm)
            )
    if appellation:
        qs = qs.filter(appellation_label__icontains=appellation.strip())
    if color:
        qs = qs.filter(color__iexact=color.strip())
    # Apply numeric filters conservatively: only include rows whose bounds admit the given value
    if volume_l is not None:
        qs = qs.filter(
            Q(packaging_min_l__isnull=True) | Q(packaging_min_l__lte=volume_l),
        ).filter(
            Q(packaging_max_l__isnull=True) | Q(packaging_max_l__gte=volume_l),
        )
    if abv_pct is not None:
        qs = qs.filter(
            Q(abv_min_pct__isnull=True) | Q(abv_min_pct__lte=abv_pct),
        ).filter(
            Q(abv_max_pct__isnull=True) | Q(abv_max_pct__gte=abv_pct),
        )
    return qs.order_by('code_inao', 'code_nc')[:limit]
