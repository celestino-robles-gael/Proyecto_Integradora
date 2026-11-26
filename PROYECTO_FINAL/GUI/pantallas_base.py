import tkinter as tk
from tkinter import messagebox

from errores import ErrorCampo
from utilidades import horas_texto
from GUI.estilos import (BLANCO, FUENTE, GRIS_CAJA, GRIS_TEXTO, PRIMARIO, BotonPildora,
                         Campo, CampoRedondeado, CajaInstrucciones,
                         ListaTarjetas, Tarjeta, titulo_pantalla)


# ---------- Conversión de campos de texto ----------
def entero(datos, clave, opcional=False):
    texto = datos[clave]
    if texto == "":
        if opcional:
            return None
        raise ErrorCampo(clave, "Este campo es obligatorio.")
    try:
        return int(texto)
    except ValueError:
        raise ErrorCampo(clave, "Escriba un número entero válido.")


def decimal(datos, clave):
    texto = datos[clave].replace(",", "")
    if texto == "":
        raise ErrorCampo(clave, "Este campo es obligatorio.")
    try:
        return float(texto)
    except ValueError:
        raise ErrorCampo(clave, "Escriba un monto válido (ej. 12.50).")


# ---------- Pantalla base ----------
class PantallaBase(tk.Frame):
    SECCION = ""

    def __init__(self, master, app):
        super().__init__(master, bg=BLANCO)
        self.app = app

    @property
    def ventana(self):
        return self.winfo_toplevel()

    def regresar(self):
        self.app.mostrar(self.SECCION)


# ---------- Bienvenida ----------
class PantallaBienvenida(PantallaBase):
    SECCION = "Inicio"

    def __init__(self, master, app):
        super().__init__(master, app)
        self._job = None
        centro = tk.Frame(self, bg=BLANCO)
        centro.place(relx=0.5, rely=0.45, anchor="center")
        tk.Label(centro, text="🏪", bg=BLANCO, fg=PRIMARIO,
                 font=("Segoe UI Symbol", 54)).pack()
        tk.Label(centro, text="BIENVENIDO", bg=BLANCO, fg="#111111",
                 font=(FUENTE, 22, "bold")).pack(pady=(6, 0))
        tk.Label(centro, text=app.usuario[1], bg=BLANCO, fg=PRIMARIO,
                 font=(FUENTE, 15, "bold")).pack(pady=(0, 4))
        tk.Label(centro, justify="center", bg=BLANCO, fg="#333333",
                 font=(FUENTE, 11),
                 text="Sistema de gestión de ventas destinado para la miscelánea.\n"
                      "Seleccione una opción del menú para comenzar.").pack()

        caja = tk.Frame(centro, bg=GRIS_CAJA, padx=26, pady=12)
        caja.pack(pady=(18, 0))
        tk.Label(caja, text="⏱  TUS HORAS TRABAJADAS", bg=GRIS_CAJA, fg=PRIMARIO,
                 font=(FUENTE, 10, "bold")).pack()
        self.lbl_hoy = tk.Label(caja, bg=GRIS_CAJA, fg="#111111",
                                font=(FUENTE, 12))
        self.lbl_hoy.pack(pady=(6, 0))
        self.lbl_total = tk.Label(caja, bg=GRIS_CAJA, fg="#111111",
                                  font=(FUENTE, 12))
        self.lbl_total.pack()
        self._refrescar()

    def _refrescar(self):
        if not self.winfo_exists():
            return
        try:
            self.app.latido()
            hoy, total = self.app.empleados.segundos_trabajados(self.app.usuario[0])
            self.lbl_hoy.config(text=f"Hoy: {horas_texto(hoy)}")
            self.lbl_total.config(text=f"Total acumulado: {horas_texto(total)}")
        except Exception:
            self.lbl_hoy.config(text="No se pudieron leer las horas.")
        self._job = self.after(30000, self._refrescar)

    def destroy(self):
        if self._job is not None:
            self.after_cancel(self._job)
        super().destroy()


# ---------- Menú de una sección (tarjetas) ----------
class MenuSeccion(PantallaBase):
    def __init__(self, master, app, seccion, tarjetas):
        super().__init__(master, app)
        self.SECCION = seccion
        titulo_pantalla(self, seccion.upper())
        rejilla = tk.Frame(self, bg=BLANCO)
        rejilla.pack(anchor="w", padx=44)
        for n, (icono, texto, clase) in enumerate(tarjetas):
            es_ultima_sola = (n == len(tarjetas) - 1 and len(tarjetas) % 2 == 1)
            if es_ultima_sola:
                tarjeta = Tarjeta(rejilla, icono, texto,
                                  lambda c=clase: app.abrir(c), w=518)
                tarjeta.grid(row=n // 2, column=0, columnspan=2, pady=(0, 14))
            else:
                tarjeta = Tarjeta(rejilla, icono, texto,
                                  lambda c=clase: app.abrir(c))
                tarjeta.grid(row=n // 2, column=n % 2, padx=(0, 18), pady=(0, 14))


# ---------- Formulario genérico ----------
class PantallaFormulario(PantallaBase):
    TITULO = ""
    CAMPOS = []            # (clave, etiqueta, texto de ayuda)
    INSTRUCCIONES = None   # lista de líneas o None

    def __init__(self, master, app):
        super().__init__(master, app)
        titulo_pantalla(self, self.TITULO)

        barra = tk.Frame(self, bg=BLANCO)
        barra.pack(side="bottom", fill="x", padx=44, pady=(0, 20))
        BotonPildora(barra, "Guardar", self.guardar).pack(side="left")
        BotonPildora(barra, "Regresar", self.regresar, relleno=False).pack(
            side="right")

        self.campos = {}
        for clave, etiqueta, ayuda in self.CAMPOS:
            campo = Campo(self, etiqueta, ayuda, oculto=clave.startswith("contrasena"))
            campo.pack(fill="x", padx=44)
            campo.enlazar("<Return>", lambda e: self.guardar())
            self.campos[clave] = campo

        if self.INSTRUCCIONES:
            CajaInstrucciones(self, self.INSTRUCCIONES).pack(pady=(8, 0))
        self.al_construir()

    def al_construir(self):
        pass

    def procesar(self, datos):
        """Guarda los datos y devuelve el mensaje de éxito.
        Puede lanzar ErrorCampo para marcar un campo en rojo."""
        raise NotImplementedError

    def guardar(self):
        for campo in self.campos.values():
            campo.sin_error()
        datos = {k: c.valor() for k, c in self.campos.items()}
        try:
            mensaje = self.procesar(datos)
        except ErrorCampo as error:
            campo = self.campos.get(error.clave)
            if campo is None:
                messagebox.showerror("No se pudo guardar", error.mensaje,
                                     parent=self.ventana)
            else:
                campo.error(error.mensaje)
                campo.foco()
            return
        except Exception as error:
            messagebox.showerror("No se pudo guardar", str(error),
                                 parent=self.ventana)
            return
        messagebox.showinfo("Listo", mensaje, parent=self.ventana)
        self.limpiar()

    def limpiar(self):
        for campo in self.campos.values():
            campo.limpiar()
        self.al_limpiar()

    def al_limpiar(self):
        pass


# ---------- Lista con buscador (consultar / eliminar / imprimir) ----------
class PantallaLista(PantallaBase):
    TITULO = ""
    ETIQUETA = ""
    PLACEHOLDER = ""
    MODO = "consultar"     # consultar | eliminar | imprimir
    CONFIRMAR = "¿Eliminar este registro?"

    def __init__(self, master, app):
        super().__init__(master, app)
        titulo_pantalla(self, self.TITULO)

        barra = tk.Frame(self, bg=BLANCO)
        barra.pack(side="bottom", fill="x", padx=44, pady=(8, 20))
        self.crear_botones(barra)

        tk.Label(self, text=self.ETIQUETA, bg=BLANCO, fg="#222222",
                 font=(FUENTE, 10), anchor="w").pack(fill="x", padx=44)
        self.busqueda = CampoRedondeado(self, self.PLACEHOLDER, icono="🔍")
        self.busqueda.pack(fill="x", padx=44, pady=(2, 10))
        self.busqueda.enlazar("<KeyRelease>", lambda e: self.cargar())

        tk.Label(self, text="Resultados de la búsqueda", bg=BLANCO,
                 fg=GRIS_TEXTO, font=(FUENTE, 9), anchor="w").pack(
            fill="x", padx=44)
        self.lista = ListaTarjetas(self)
        self.lista.pack(fill="both", expand=True, padx=44, pady=(4, 0))
        self.antes_de_cargar()
        self.cargar()

    def crear_botones(self, barra):
        BotonPildora(barra, "Regresar", self.regresar, relleno=False).pack(
            side="right")

    def antes_de_cargar(self):
        pass

    # -- A implementar en cada pantalla --
    def buscar(self, texto):
        raise NotImplementedError

    def datos_fila(self, fila):
        """Devuelve dict(clave=..., izq=..., centro=(a, b), der=(a, b) opcional)."""
        raise NotImplementedError

    def eliminar_registro(self, clave):
        raise NotImplementedError

    # -- Comportamiento común --
    def cargar(self):
        self.lista.limpiar()
        try:
            filas = self.buscar(self.busqueda.get().strip())
        except Exception as error:
            messagebox.showerror("Error", str(error), parent=self.ventana)
            return
        if not filas:
            self.lista.vacio("No se encontraron resultados.")
            return
        for fila in filas:
            self.agregar_fila(self.datos_fila(fila))

    def agregar_fila(self, datos):
        clave = datos["clave"]
        extra = {}
        if self.MODO == "eliminar":
            extra = dict(icono="🗑", accion=lambda c=clave: self.pedir_eliminar(c))
        elif self.MODO == "imprimir":
            extra = dict(casilla=self.crear_casilla(clave))
        self.lista.agregar(datos["izq"], datos["centro"], datos.get("der"), **extra)

    def crear_casilla(self, clave):
        raise NotImplementedError

    def pedir_eliminar(self, clave):
        if not messagebox.askyesno("Confirmar", self.CONFIRMAR, parent=self.ventana):
            return
        try:
            self.eliminar_registro(clave)
        except Exception as error:
            messagebox.showerror("No se pudo eliminar", str(error),
                                 parent=self.ventana)
            return
        self.cargar()
