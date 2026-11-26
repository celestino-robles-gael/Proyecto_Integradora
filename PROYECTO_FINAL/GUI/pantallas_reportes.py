import tkinter as tk
import webbrowser
from datetime import date
from pathlib import Path
from tkinter import messagebox

from GUI.estilos import (BLANCO, FUENTE, PRIMARIO, ROJO_ERROR, BotonPildora,
                         TarjetaDato, dinero, titulo_pantalla)
from GUI.pantallas_base import PantallaBase, PantallaLista
from utilidades import nombre_mes
from VENTAS.reporte_html import generar_html
from VENTAS.ventas import VentasSystem

ventas = VentasSystem()


# ---------------- Reporte mensual (MES / VENTA / CRECIMIENTO) ----------------
class ReporteMensual(PantallaBase):
    SECCION = "Reportes"

    def __init__(self, master, app):
        super().__init__(master, app)
        hoy = date.today()
        self.anio, self.mes = hoy.year, hoy.month
        titulo_pantalla(self, "REPORTE DE VENTAS")

        barra = tk.Frame(self, bg=BLANCO)
        barra.pack(side="bottom", fill="x", padx=44, pady=(0, 20))
        BotonPildora(barra, "Regresar", self.regresar, relleno=False).pack(
            side="right")

        nav = tk.Frame(self, bg=BLANCO)
        nav.pack(anchor="w", padx=44, pady=(0, 14))
        self._flecha(nav, "◀", -1).pack(side="left")
        self.lbl_mes = tk.Label(nav, text="", bg=BLANCO, fg=PRIMARIO, width=20,
                                font=(FUENTE, 13, "bold"))
        self.lbl_mes.pack(side="left")
        self._flecha(nav, "▶", 1).pack(side="left")

        self.tarjetas = tk.Frame(self, bg=BLANCO)
        self.tarjetas.pack(anchor="w", padx=44, pady=(8, 0))
        self.dibujar()

    def _flecha(self, padre, simbolo, paso):
        boton = tk.Label(padre, text=simbolo, bg=BLANCO, fg=PRIMARIO,
                         font=("Segoe UI Symbol", 14), cursor="hand2", padx=8)
        boton.bind("<Button-1>", lambda e: self.mover(paso))
        return boton

    def mover(self, paso):
        self.mes += paso
        if self.mes == 0:
            self.mes, self.anio = 12, self.anio - 1
        elif self.mes == 13:
            self.mes, self.anio = 1, self.anio + 1
        self.dibujar()

    def dibujar(self):
        for hijo in self.tarjetas.winfo_children():
            hijo.destroy()
        self.lbl_mes.config(text=f"{nombre_mes(self.mes).capitalize()} {self.anio}")

        n, total = ventas.resumen_mes(self.anio, self.mes)
        ant_anio, ant_mes = ((self.anio - 1, 12) if self.mes == 1
                             else (self.anio, self.mes - 1))
        _, total_ant = ventas.resumen_mes(ant_anio, ant_mes)

        if float(total_ant) > 0:
            pct = (float(total) - float(total_ant)) / float(total_ant) * 100
            crecimiento = f"{pct:+.0f}%"
            detalle = f"frente a {nombre_mes(ant_mes)} {ant_anio}"
            color = ROJO_ERROR if pct < 0 else "#111111"
        else:
            crecimiento, color = "—", "#111111"
            detalle = "sin ventas en el mes anterior"

        TarjetaDato(self.tarjetas, "MES", nombre_mes(self.mes).capitalize(),
                    str(self.anio)).grid(row=0, column=0, padx=(0, 14))
        TarjetaDato(self.tarjetas, "VENTA", dinero(total),
                    f"{n} ventas registradas").grid(row=0, column=1, padx=(0, 14))
        TarjetaDato(self.tarjetas, "CRECIMIENTO", crecimiento, detalle,
                    color_valor=color).grid(row=0, column=2)


# ---------------- Buscar detalles de ventas ----------------
class BuscarDetalles(PantallaLista):
    SECCION = "Reportes"
    TITULO = "BUSCAR DETALLES DE VENTAS"
    ETIQUETA = "Puede buscar o escribir"
    PLACEHOLDER = "Buscar por ID de venta, ID de producto o nombre..."

    def buscar(self, texto):
        return ventas.detalles(texto)

    def datos_fila(self, fila):
        id_d, id_venta, id_prod, producto, cantidad, subtotal = fila
        return dict(
            clave=id_d, izq=f"ID: {id_d}",
            centro=(f"ID PRODUCTO: {id_prod}  ·  {producto.upper()}",
                    f"ID VENTA: {id_venta}"),
            der=(f"CANTIDAD: {cantidad}", f"SUBTOTAL: {dinero(subtotal)}"))


# ---------------- Imprimir reporte ----------------
class ImprimirReporte(PantallaLista):
    SECCION = "Reportes"
    TITULO = "IMPRIMIR REPORTE"
    ETIQUETA = "Seleccione los reportes que desea imprimir"
    PLACEHOLDER = "Filtrar por mes o año (ej. octubre, 2026)..."
    MODO = "imprimir"

    def antes_de_cargar(self):
        pass

    def __init__(self, master, app):
        self.seleccion = set()
        super().__init__(master, app)

    def crear_botones(self, barra):
        BotonPildora(barra, "Imprimir reporte", self.imprimir).pack(side="left")
        BotonPildora(barra, "Regresar", self.regresar, relleno=False).pack(
            side="right")

    def buscar(self, texto):
        meses = [(i + 1, *m) for i, m in enumerate(ventas.meses_con_ventas())]
        texto = texto.lower()
        return [m for m in meses
                if texto in f"{nombre_mes(m[2])} {m[1]}".lower()]

    def datos_fila(self, fila):
        orden, anio, mes, n, total = fila
        return dict(
            clave=(anio, mes), izq=f"ID: {orden}",
            centro=(f"FECHA: {nombre_mes(mes).upper()} {anio}",
                    f"{n} ventas  ·  TOTAL: {dinero(total)}"))

    def crear_casilla(self, clave):
        variable = tk.BooleanVar(value=clave in self.seleccion)

        def alternar():
            if variable.get():
                self.seleccion.add(clave)
            else:
                self.seleccion.discard(clave)
        return variable, alternar

    def imprimir(self):
        if not self.seleccion:
            messagebox.showwarning("Sin selección",
                                   "Marque al menos un reporte para imprimir.",
                                   parent=self.ventana)
            return
        try:
            ruta = generar_html(sorted(self.seleccion), ventas)
            webbrowser.open(Path(ruta).as_uri())
        except Exception as error:
            messagebox.showerror("No se pudo generar el reporte", str(error),
                                 parent=self.ventana)
            return
        messagebox.showinfo(
            "Reporte listo",
            "El reporte se abrió en su navegador.\n"
            "Elija su impresora en la ventana de impresión (o «Guardar como PDF»).",
            parent=self.ventana)
