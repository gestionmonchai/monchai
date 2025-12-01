def norm_insee(s):
    s = str(s or "").strip()
    assert len(s) == 5 and s.isdigit(), "INSEE invalide"
    return s


def norm_section(s):
    return str(s or "").strip().upper()[:3]


def norm_numero(s):
    return str(s or "").strip().zfill(4)


def build_parcelle_id(insee, section, numero):
    # Convention idpar = INSEE(5) + '000' + SECTION(2) + NUM(4)
    # Si section 3 char, garder 2 premiers pour idpar (MVP)
    return f"{insee}000{section[:2]}{numero}"


def split_parcelle_id(pid):
    pid = str(pid)
    insee = pid[:5]
    section = pid[8:10]
    numero = pid[-4:]
    return insee, section, numero
