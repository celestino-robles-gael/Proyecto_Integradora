import calendar
from datetime import date, datetime

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def dinero(valor):
    return f"${float(valor):,.2f}"


def nombre_mes(mes):
    return MESES[mes - 1]


def parse_fecha(texto):
    """Acepta AAAA-MM-DD, AAAA-MM-DD HH:MM y AAAA-MM-DD HH:MM:SS."""
    texto = texto.strip()
    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    raise ValueError("Use el formato AAAA-MM-DD HH:MM (ej. 2026-10-24 10:30).")


def a_datetime(f):
    if isinstance(f, datetime):
        return f
    if isinstance(f, date):
        return datetime(f.year, f.month, f.day)
    try:
        return parse_fecha(str(f))
    except ValueError:
        return None


def fecha_larga(f):
    d = a_datetime(f)
    if d is None:
        return str(f)
    return f"{d.day:02d} {MESES[d.month - 1].upper()} {d.year}"


def hora(f):
    d = a_datetime(f)
    return d.strftime("%H:%M") if d else ""


def fecha_corta(f):
    d = a_datetime(f)
    return d.strftime("%Y-%m-%d %H:%M") if d else str(f)


def rango_mes(anio, mes):
    return date(anio, mes, 1), date(anio, mes, calendar.monthrange(anio, mes)[1])


def horas_texto(segundos):
    """Segundos -> «3 h 05 min»."""
    segundos = int(segundos or 0)
    return f"{segundos // 3600} h {(segundos % 3600) // 60:02d} min"
