import os
import tempfile
from datetime import datetime
from html import escape

from utilidades import dinero, fecha_corta, nombre_mes, rango_mes

ESTILO = """
body{font-family:Segoe UI,Arial,sans-serif;color:#111;margin:32px}
h1{color:#43478C;margin:0}
h2{color:#43478C;border-bottom:2px solid #43478C;padding-bottom:4px;margin-top:36px}
h3{margin:18px 0 6px}
.sub{color:#666;margin:2px 0 18px}
.resumen{display:flex;gap:16px;margin:10px 0}
.caja{background:#EAEAEA;border-radius:10px;padding:10px 18px}
.caja b{display:block;font-size:20px;color:#43478C}
table{border-collapse:collapse;width:100%;font-size:14px}
th{background:#43478C;color:#fff;text-align:left;padding:6px 8px}
td{padding:6px 8px;border-bottom:1px solid #ddd}
.num{text-align:right}
section{page-break-inside:avoid}
@media print{body{margin:12mm}}
"""


def _tabla(encabezados, filas, numericas=()):
    cab = "".join(f"<th>{escape(h)}</th>" for h in encabezados)
    cuerpo = ""
    for fila in filas:
        celdas = "".join(
            f'<td class="{"num" if i in numericas else ""}">{escape(str(c))}</td>'
            for i, c in enumerate(fila))
        cuerpo += f"<tr>{celdas}</tr>"
    if not filas:
        cuerpo = f'<tr><td colspan="{len(encabezados)}">Sin registros</td></tr>'
    return f"<table><tr>{cab}</tr>{cuerpo}</table>"


def generar_html(meses, ventas, ruta=None):
    """meses: lista de (año, mes). Devuelve la ruta del archivo HTML creado."""
    secciones = []
    for anio, mes in sorted(meses):
        desde, hasta = rango_mes(anio, mes)
        lista = ventas.ventas_por_fecha(desde, hasta)
        total = sum(float(v[3]) for v in lista)
        top = ventas.mas_vendidos(desde, hasta)
        emp = ventas.por_empleado(desde, hasta)

        secciones.append(f"""
<section>
<h2>{nombre_mes(mes).capitalize()} {anio}</h2>
<div class="resumen">
  <div class="caja">Ventas<b>{len(lista)}</b></div>
  <div class="caja">Total vendido<b>{dinero(total)}</b></div>
</div>
<h3>Ventas del mes</h3>
{_tabla(["# Venta", "Fecha", "Empleado", "Total"],
        [(i, fecha_corta(f), e, dinero(t)) for i, f, e, t in lista], numericas=(3,))}
<h3>Productos más vendidos</h3>
{_tabla(["Producto", "Unidades", "Ingresos"],
        [(n, int(c), dinero(i)) for n, c, i in top], numericas=(1, 2))}
<h3>Ventas por empleado</h3>
{_tabla(["Empleado", "Ventas", "Total vendido"],
        [(n, c, dinero(t)) for n, c, t in emp], numericas=(1, 2))}
</section>""")

    pagina = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Reporte de ventas - El Baratero</title><style>{ESTILO}</style></head>
<body onload="window.print()">
<h1>EL BARATERO Minisúper</h1>
<p class="sub">Reporte de ventas · generado el {datetime.now():%d/%m/%Y %H:%M}</p>
{''.join(secciones)}
</body></html>"""

    if ruta is None:
        ruta = os.path.join(tempfile.gettempdir(), "reporte_ventas_el_baratero.html")
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(pagina)
    return ruta
