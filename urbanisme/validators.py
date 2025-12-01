import re

__all__ = [
    "normalize_insee",
    "normalize_section",
    "normalize_numero",
]

_digit_re = re.compile(r"\D+")
_alnum_re = re.compile(r"[^A-Z0-9]+")


def normalize_insee(s: str) -> str:
    s = (s or "").strip()
    s = _digit_re.sub("", s)
    if len(s) != 5:
        raise ValueError("INSEE invalide (5 chiffres)")
    return s


def normalize_section(s: str) -> str:
    s = (s or "").strip().upper()
    s = _alnum_re.sub("", s)
    if len(s) != 2:
        raise ValueError("Section invalide (2 caractères alphanum)")
    return s


def normalize_numero(s: str) -> str:
    s = (s or "").strip()
    s = _digit_re.sub("", s)
    if not s:
        raise ValueError("Numéro invalide (chiffres)")
    if len(s) > 4:
        # garder 4 derniers (usage local, les services attendent en général 4)
        s = s[-4:]
    return s.zfill(4)
