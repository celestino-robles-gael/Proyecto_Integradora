import tkinter as tk
from tkinter import ttk

from utilidades import dinero  # noqa: F401  (se reexporta para las pantallas)

# ---------------- Colores y fuentes ----------------
PRIMARIO = "#43478C"
PRIMARIO_HOVER = "#565BA6"
ACTIVO = "#5A5FB0"
BLANCO = "#FFFFFF"
GRIS = "#EAEAEA"
GRIS_HOVER = "#DADAEC"
GRIS_CAMPO = "#EDEDED"
GRIS_CAJA = "#D9D9D9"
GRIS_TEXTO = "#9A9A9A"
TEXTO_MENU = "#C9CBE6"
ROJO = "#FF5A5F"
ROJO_ERROR = "#E53935"

FUENTE = "Segoe UI"


# ---------------- Ventanas y dibujo ----------------
def centrar(ventana, ancho, alto):
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() - ancho) // 2
    y = (ventana.winfo_screenheight() - alto) // 2
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


def rect_redondeado(canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def configurar_estilos():
    st = ttk.Style()
    st.theme_use("clam")
    st.configure("Treeview", font=(FUENTE, 10), rowheight=26,
                 background=BLANCO, fieldbackground=BLANCO)
    st.configure("Treeview.Heading", font=(FUENTE, 10, "bold"),
                 background=PRIMARIO, foreground=BLANCO, relief="flat")
    st.map("Treeview.Heading", background=[("active", PRIMARIO_HOVER)])
    st.map("Treeview", background=[("selected", "#C9CBE6")],
           foreground=[("selected", "#111111")])


def titulo_pantalla(master, texto):
    tk.Label(master, text=texto, bg=BLANCO, fg="#111111",
             font=(FUENTE, 30, "bold")).pack(anchor="w", padx=44, pady=(26, 12))


# ---------------- Botón en forma de píldora ----------------
class BotonPildora(tk.Canvas):
    """relleno=True: morado con letras blancas. relleno=False: contorno morado."""

    def __init__(self, master, texto, comando, w=300, h=40, relleno=True,
                 fondo=BLANCO):
        super().__init__(master, width=w, height=h, bg=fondo,
                         highlightthickness=0, cursor="hand2")
        self.comando = comando
        self.relleno = relleno
        radio = (h - 4) // 2
        self.forma = rect_redondeado(
            self, 2, 2, w - 2, h - 2, radio,
            fill=PRIMARIO if relleno else BLANCO, outline=PRIMARIO, width=2)
        self.create_text(w / 2, h / 2, text=texto,
                         fill=BLANCO if relleno else PRIMARIO,
                         font=(FUENTE, 11, "bold"))
        self.bind("<Enter>", lambda e: self.itemconfig(
            self.forma, fill=PRIMARIO_HOVER if self.relleno else GRIS_HOVER))
        self.bind("<Leave>", lambda e: self.itemconfig(
            self.forma, fill=PRIMARIO if self.relleno else BLANCO))
        self.bind("<Button-1>", lambda e: self.comando())


# ---------------- Campo de texto redondeado ----------------
class CampoRedondeado(tk.Frame):
    def __init__(self, master, placeholder="", oculto=False, icono=None,
                 h=34, fondo=BLANCO):
        super().__init__(master, bg=fondo)
        self.h = h
        self.placeholder = placeholder
        self.oculto = oculto
        self.icono = icono
        self._ph = False
        self._forma = None
        self._icono_id = None

        self.canvas = tk.Canvas(self, height=h, bg=fondo, highlightthickness=0)
        self.canvas.pack(fill="x")
        self.entry = tk.Entry(self.canvas, relief="flat", bd=0, bg=GRIS_CAMPO,
                              fg="#111111", font=(FUENTE, 10),
                              insertbackground="#111111", highlightthickness=0)
        self._ventana = self.canvas.create_window(
            14, h // 2, window=self.entry, anchor="w")
        self.canvas.bind("<Configure>", self._redibujar)
        self.canvas.bind("<Button-1>", lambda e: self.entry.focus_set())
        self.entry.bind("<FocusIn>", self._quitar_ph)
        self.entry.bind("<FocusOut>", self._poner_ph)
        self._poner_ph()

    def _redibujar(self, evento):
        ancho = evento.width
        if self._forma is not None:
            self.canvas.delete(self._forma)
        self._forma = rect_redondeado(self.canvas, 1, 1, ancho - 1, self.h - 1,
                                      15, fill=GRIS_CAMPO, outline=GRIS_CAMPO)
        self.canvas.tag_lower(self._forma)
        margen = 44 if self.icono else 14
        self.canvas.itemconfigure(self._ventana, width=max(ancho - 14 - margen, 20))
        if self.icono:
            if self._icono_id is None:
                self._icono_id = self.canvas.create_text(
                    ancho - 24, self.h // 2, text=self.icono, fill=PRIMARIO,
                    font=("Segoe UI Symbol", 11))
            else:
                self.canvas.coords(self._icono_id, ancho - 24, self.h // 2)

    def _quitar_ph(self, _e=None):
        if self._ph:
            self.entry.delete(0, "end")
            self.entry.config(fg="#111111", show="•" if self.oculto else "")
            self._ph = False

    def _poner_ph(self, _e=None):
        if self._ph or self.entry.get() or not self.placeholder:
            return
        self.entry.config(fg=GRIS_TEXTO, show="")
        self.entry.insert(0, self.placeholder)
        self._ph = True

    def get(self):
        return "" if self._ph else self.entry.get()

    def set(self, texto):
        self.entry.delete(0, "end")
        self._ph = False
        self.entry.config(fg="#111111", show="•" if self.oculto else "")
        if texto != "":
            self.entry.insert(0, texto)
        else:
            self._poner_ph()

    def foco(self):
        self.entry.focus_set()

    def enlazar(self, evento, funcion):
        self.entry.bind(evento, funcion, add="+")


class Campo(tk.Frame):
    """Etiqueta + campo redondeado + línea roja para mensajes de error."""

    def __init__(self, master, etiqueta, placeholder="", oculto=False):
        super().__init__(master, bg=BLANCO)
        tk.Label(self, text=etiqueta, bg=BLANCO, fg="#222222",
                 font=(FUENTE, 10), anchor="w").pack(fill="x")
        self.campo = CampoRedondeado(self, placeholder, oculto)
        self.campo.pack(fill="x", pady=(2, 0))
        self.hint = tk.Label(self, text="", bg=BLANCO, fg=ROJO_ERROR,
                             font=(FUENTE, 8), anchor="w")
        self.hint.pack(fill="x")
        self.oculto = oculto

    def valor(self):
        texto = self.campo.get()
        return texto if self.oculto else texto.strip()

    def set(self, texto):
        self.campo.set(texto)

    def limpiar(self):
        self.campo.set("")
        self.sin_error()

    def error(self, mensaje):
        self.hint.config(text="* " + mensaje)

    def sin_error(self):
        self.hint.config(text="")

    def foco(self):
        self.campo.foco()

    def enlazar(self, evento, funcion):
        self.campo.enlazar(evento, funcion)


# ---------------- Caja gris de instrucciones ----------------
class CajaInstrucciones(tk.Frame):
    def __init__(self, master, lineas, titulo="Instrucciones de uso"):
        super().__init__(master, bg=GRIS_CAJA, padx=16, pady=10)
        tk.Label(self, text=titulo, bg=GRIS_CAJA, fg=PRIMARIO,
                 font=(FUENTE, 9, "bold"), anchor="w").pack(fill="x")
        for n, linea in enumerate(lineas, start=1):
            tk.Label(self, text=f"{n}. {linea}", bg=GRIS_CAJA, fg="#333333",
                     font=(FUENTE, 9), anchor="w", justify="left").pack(fill="x")


# ---------------- Lista de tarjetas con desplazamiento ----------------
class ListaTarjetas(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BLANCO)
        self.canvas = tk.Canvas(self, bg=BLANCO, highlightthickness=0)
        self.barra = ttk.Scrollbar(self, orient="vertical",
                                   command=self.canvas.yview)
        self.interior = tk.Frame(self.canvas, bg=BLANCO)
        self._ventana = self.canvas.create_window(
            (0, 0), window=self.interior, anchor="nw")
        self.canvas.configure(yscrollcommand=self.barra.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.barra.pack(side="right", fill="y")
        self.interior.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self._ventana, width=e.width))

    def desplazar(self, unidades):
        if self.interior.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(unidades, "units")

    def limpiar(self):
        for hijo in self.interior.winfo_children():
            hijo.destroy()
        self.canvas.yview_moveto(0)

    def vacio(self, texto):
        tk.Label(self.interior, text=texto, bg=BLANCO, fg=GRIS_TEXTO,
                 font=(FUENTE, 11)).pack(pady=30)

    def agregar(self, izq, centro, der=None, icono=None, accion=None,
                casilla=None):
        """izq: texto grande (ej. «ID: 1»). centro/der: (línea en negrita, línea gris).
        icono+accion: botón a la derecha. casilla: (BooleanVar, comando)."""
        fila = tk.Frame(self.interior, bg=GRIS)
        fila.pack(fill="x", pady=(0, 3))
        fila.grid_columnconfigure(1, weight=1)

        tk.Label(fila, text=izq, bg=GRIS, fg="#111111", font=(FUENTE, 15),
                 width=9, anchor="w").grid(row=0, column=0, padx=(16, 10), pady=12)

        bloque = tk.Frame(fila, bg=GRIS)
        bloque.grid(row=0, column=1, sticky="w", pady=8)
        tk.Label(bloque, text=centro[0], bg=GRIS, fg="#111111",
                 font=(FUENTE, 10, "bold"), anchor="w").pack(anchor="w")
        if len(centro) > 1 and centro[1]:
            tk.Label(bloque, text=centro[1], bg=GRIS, fg="#555555",
                     font=(FUENTE, 9), anchor="w").pack(anchor="w")

        if der:
            bloque_der = tk.Frame(fila, bg=GRIS)
            bloque_der.grid(row=0, column=2, padx=14, sticky="e")
            tk.Label(bloque_der, text=der[0], bg=GRIS, fg="#111111",
                     font=(FUENTE, 10, "bold"), anchor="e").pack(anchor="e")
            if len(der) > 1 and der[1]:
                tk.Label(bloque_der, text=der[1], bg=GRIS, fg="#555555",
                         font=(FUENTE, 9), anchor="e").pack(anchor="e")

        if icono and accion:
            boton = tk.Label(fila, text=icono, bg=GRIS, fg=PRIMARIO,
                             font=("Segoe UI Symbol", 15), cursor="hand2")
            boton.grid(row=0, column=3, padx=(6, 20))
            boton.bind("<Button-1>", lambda e: accion())
        if casilla is not None:
            variable, comando = casilla
            tk.Checkbutton(fila, variable=variable, command=comando, bg=GRIS,
                           activebackground=GRIS, selectcolor=BLANCO,
                           cursor="hand2").grid(row=0, column=3, padx=(6, 20))


# ---------------- Tarjetas del menú ----------------
class Tarjeta(tk.Canvas):
    """Botón grande redondeado con icono y texto."""

    def __init__(self, master, icono, texto, comando, w=250, h=170):
        super().__init__(master, width=w, height=h, bg=BLANCO,
                         highlightthickness=0, cursor="hand2")
        self.comando = comando
        self.rect = rect_redondeado(self, 2, 2, w - 2, h - 2, 28,
                                    fill=GRIS, outline=GRIS)
        self.create_text(w / 2, 52, text=icono, fill=PRIMARIO,
                         font=("Segoe UI Symbol", 30))
        self.create_text(w / 2, 118, text=texto, fill="#111111",
                         font=(FUENTE, 20))
        self.bind("<Enter>", lambda e: self.itemconfig(
            self.rect, fill=GRIS_HOVER, outline=GRIS_HOVER))
        self.bind("<Leave>", lambda e: self.itemconfig(
            self.rect, fill=GRIS, outline=GRIS))
        self.bind("<Button-1>", lambda e: self.comando())


class TarjetaDato(tk.Canvas):
    """Tarjeta del reporte: título morado, valor grande y detalle."""

    def __init__(self, master, titulo, valor, detalle="", color_valor="#111111",
                 w=230, h=210):
        super().__init__(master, width=w, height=h, bg=BLANCO,
                         highlightthickness=0)
        rect_redondeado(self, 2, 2, w - 2, h - 2, 26, fill=GRIS, outline=GRIS)
        self.create_text(w / 2, 40, text=titulo, fill=PRIMARIO,
                         font=(FUENTE, 15, "bold"))
        tamano = 26 if len(valor) <= 8 else 20
        self.create_text(w / 2, 105, text=valor, fill=color_valor,
                         font=(FUENTE, tamano, "bold"))
        self.create_text(w / 2, 160, text=detalle, fill="#555555",
                         font=(FUENTE, 9), justify="center", width=w - 30)


# ---------------- Tabla (Treeview) ----------------
def configurar_columnas(tabla, columnas):
    """columnas: lista de (id, titulo, ancho)"""
    tabla["columns"] = [c[0] for c in columnas]
    for cid, titulo, ancho in columnas:
        tabla.heading(cid, text=titulo)
        tabla.column(cid, width=ancho, anchor="center")


def crear_tabla(master, columnas, altura=6):
    frame = tk.Frame(master, bg=BLANCO)
    tabla = ttk.Treeview(frame, show="headings", height=altura,
                         selectmode="browse")
    configurar_columnas(tabla, columnas)
    barra = ttk.Scrollbar(frame, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=barra.set)
    tabla.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")
    return frame, tabla
