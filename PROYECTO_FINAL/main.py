import sys
import time
import tkinter as tk
from tkinter import messagebox

try:
    from conexionBD import conexion  # noqa: F401
except ImportError:
    # conexionBD ya mostró el aviso de «Sin conexión»
    sys.exit(1)

from GUI.estilos import (ACTIVO, BLANCO, FUENTE, PRIMARIO, PRIMARIO_HOVER,
                         ROJO, TEXTO_MENU, BotonPildora, ListaTarjetas, centrar,
                         configurar_estilos)
from EMPLEADOS.empleados import EmpleadosSystem
from GUI.pantalla_login import PantallaLogin, PantallaRegistro
from utilidades import horas_texto
from GUI.pantallas_base import MenuSeccion, PantallaBienvenida
from GUI.pantallas_empleados import (ActualizarEmpleado, CambiarContrasena,
                                     ConsultarEmpleado, EliminarEmpleado,
                                     InsertarEmpleado)
from GUI.pantallas_inventario import (ActualizarProducto, ConsultarProducto,
                                      EliminarProducto, InsertarProducto)
from GUI.pantallas_reportes import (BuscarDetalles, ImprimirReporte,
                                    ReporteMensual)
from GUI.pantallas_ventas import (ActualizarVenta, ConsultarVenta,
                                  EliminarVenta, InsertarVenta)

SECCIONES = [("⌂", "Inicio"), ("🛒", "Ventas"), ("▣", "Inventario"),
             ("👥", "Empleados"), ("📊", "Reportes")]

MENUS = {
    "Ventas": [("⊕", "Insertar", InsertarVenta),
               ("🗑", "Eliminar", EliminarVenta),
               ("🔍", "Consultar", ConsultarVenta),
               ("⟳", "Actualizar", ActualizarVenta)],
    "Inventario": [("⊕", "Insertar", InsertarProducto),
                   ("🗑", "Eliminar", EliminarProducto),
                   ("🔍", "Consultar", ConsultarProducto),
                   ("⟳", "Actualizar", ActualizarProducto)],
    "Empleados": [("⊕", "Insertar", InsertarEmpleado),
                  ("🗑", "Eliminar", EliminarEmpleado),
                  ("🔍", "Consultar", ConsultarEmpleado),
                  ("⟳", "Actualizar", ActualizarEmpleado)],
    "Reportes": [("📄", "Reporte", ReporteMensual),
                 ("🔍", "Buscar", BuscarDetalles),
                 ("🖨", "Imprimir Reporte", ImprimirReporte)],
}


# Los empleados que no son gerentes solo pueden consultar sus propios datos.
MENU_EMPLEADOS_BASICO = [("🔍", "Consultar", ConsultarEmpleado)]

# Control de horas por inactividad (sin tocar ratón ni teclado):
#  - a los MINUTOS_AVISO aparece un recordatorio «¿Sigues trabajando?»;
#  - si nadie responde, a los MINUTOS_INACTIVIDAD se pausa el conteo de horas.
# Si el empleado responde (o mueve el ratón) antes de la pausa, ese rato SÍ cuenta.
MINUTOS_AVISO = 10
MINUTOS_INACTIVIDAD = 15


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("El Baratero Minisúper")
        self.configure(bg=BLANCO)
        centrar(self, 1100, 690)
        self.minsize(1100, 690)
        configurar_estilos()

        self.empleados = EmpleadosSystem()
        self.usuario = None       # (id, nombre, puesto) del empleado en sesión
        self.turno = None         # id de la sesión de trabajo (control de horas)
        self._job_turno = None
        self._ultima_actividad = time.time()
        self._inactivo = False
        self._aviso = None          # ventana «¿Sigues trabajando?»
        self._aviso_desde = 0
        self.protocol("WM_DELETE_WINDOW", self.salir)
        self.pantalla = None
        self.seccion_activa = None
        self.items = {}

        # Rueda del ratón para las listas con desplazamiento
        self.bind_all("<MouseWheel>", self._rueda)
        self.bind_all("<Button-4>", self._rueda)
        self.bind_all("<Button-5>", self._rueda)
        # Actividad del usuario (para no contar horas con el equipo inactivo)
        for evento in ("<Motion>", "<Key>", "<ButtonPress>"):
            self.bind_all(evento, self._actividad, add="+")

        self.mostrar_login()

    # ---------- Sesión ----------
    def _vaciar(self):
        for hijo in self.winfo_children():
            hijo.destroy()
        self.pantalla = None
        self.items = {}

    def mostrar_login(self, usuario=""):
        self._vaciar()
        self.usuario = None
        PantallaLogin(self, self, usuario).pack(fill="both", expand=True)

    def mostrar_registro(self):
        self._vaciar()
        PantallaRegistro(self, self).pack(fill="both", expand=True)

    @property
    def es_gerente(self):
        return bool(self.usuario) and self.usuario[2].strip().lower() == "gerente"

    def iniciar_sesion(self, usuario):
        self.usuario = usuario
        self._ultima_actividad = time.time()
        self._inactivo = False
        try:
            self.turno = self.empleados.iniciar_turno(usuario[0])
            self._job_turno = self.after(30000, self._latido_periodico)
        except Exception as error:
            messagebox.showwarning("Horas", f"No se pudo iniciar el registro de horas:\n{error}")
        self._vaciar()
        self._encabezado()
        self._cuerpo()
        self.mostrar("Inicio")

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar la sesión?"):
            self._terminar_turno()
            self.mostrar_login()

    def salir(self):
        if self.usuario is not None and not messagebox.askyesno(
                "Cerrar el programa",
                "¿Seguro que quieres cerrar el programa?\n"
                "Se cerrará tu sesión y el conteo de horas."):
            return
        self._terminar_turno()
        self.destroy()

    # ---------- Control de horas ----------
    def _actividad(self, _evento=None):
        # Justo al aparecer el aviso se ignoran eventos sueltos del sistema, para
        # que no se cierre solo ni reinicie el reloj de inactividad.
        if self._aviso is not None and time.time() - self._aviso_desde < 2:
            return
        self._ultima_actividad = time.time()
        self._cerrar_aviso()
        if self._inactivo and self.usuario is not None:
            self._reanudar()

    def _mostrar_aviso(self):
        if self._aviso is not None:
            return
        ventana = tk.Toplevel(self)
        ventana.title("¿Sigues trabajando?")
        ventana.configure(bg=BLANCO)
        ventana.resizable(False, False)
        ventana.attributes("-topmost", True)
        tk.Label(ventana, text="¿Sigues trabajando?", bg=BLANCO, fg="#111111",
                 font=(FUENTE, 15, "bold")).pack(padx=34, pady=(22, 6))
        tk.Label(ventana, bg=BLANCO, fg="#333333", font=(FUENTE, 10),
                 justify="center",
                 text=f"Llevas {MINUTOS_AVISO} minutos sin actividad.\n"
                      f"Si no respondes, en {MINUTOS_INACTIVIDAD - MINUTOS_AVISO} minutos "
                      "se pausará\nel conteo de tus horas.\n\n"
                      "Mueve el ratón o pulsa el botón para continuar."
                 ).pack(padx=34)
        BotonPildora(ventana, "Sigo trabajando", lambda: self._actividad(),
                     w=240, h=38).pack(pady=(14, 22))
        ventana.protocol("WM_DELETE_WINDOW", lambda: self._actividad())
        centrar(ventana, 440, 260)
        ventana.lift()
        self._aviso = ventana
        self._aviso_desde = time.time()

    def _cerrar_aviso(self):
        if self._aviso is not None:
            try:
                self._aviso.destroy()
            except tk.TclError:
                pass
            self._aviso = None

    def _reanudar(self):
        """El empleado volvió tras estar inactivo: se abre un periodo nuevo."""
        try:
            if self.turno is not None:
                self.empleados.cerrar_turno(self.turno, contar=False)
            self.turno = self.empleados.iniciar_turno(self.usuario[0])
            self._inactivo = False
        except Exception:
            pass

    def latido(self):
        """Avisa que el programa sigue abierto y guarda la última actividad real.
        Si el equipo estuvo inactivo o suspendido, ese tiempo no se cuenta."""
        if self.turno is None:
            return
        inactivo = int(time.time() - self._ultima_actividad)
        if inactivo >= MINUTOS_INACTIVIDAD * 60:
            self._inactivo = True
            self._cerrar_aviso()
        elif inactivo >= MINUTOS_AVISO * 60 and self._aviso is None:
            self._mostrar_aviso()
        try:
            if self._inactivo:
                self.empleados.latido(self.turno, contar=False)
            else:
                self.empleados.latido(self.turno, inactivo)
        except Exception:
            pass

    def _latido_periodico(self):
        self.latido()
        self._job_turno = self.after(30000, self._latido_periodico)

    def _terminar_turno(self):
        self._cerrar_aviso()
        if self._job_turno is not None:
            self.after_cancel(self._job_turno)
            self._job_turno = None
        if self.turno is not None:
            try:
                self.empleados.cerrar_turno(
                    self.turno, int(time.time() - self._ultima_actividad),
                    contar=not self._inactivo)
            except Exception:
                pass
        self.turno = None
        self._inactivo = False

    def eliminar_mi_usuario(self):
        if not messagebox.askyesno(
                "Eliminar mi usuario",
                "¿Seguro que quieres eliminar tu usuario?\n\n"
                "Se borrarán tu cuenta y tus horas. No se puede deshacer.",
                icon="warning"):
            return
        try:
            self.empleados.eliminar(self.usuario[0], self.usuario[0])
        except Exception as error:
            messagebox.showerror("No se pudo eliminar", str(error))
            return
        self._terminar_turno()
        self.mostrar_login()
        messagebox.showinfo("Usuario eliminado", "Tu usuario fue eliminado.")

    # ---------- Estructura ----------
    def _encabezado(self):
        barra = tk.Frame(self, bg=PRIMARIO, height=78)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        logo = tk.Frame(barra, bg=PRIMARIO)
        logo.pack(side="left", padx=26)
        tk.Label(logo, text="EL BARATERO", bg=PRIMARIO, fg=BLANCO,
                 font=(FUENTE, 24, "bold")).pack(anchor="w", pady=(10, 0))
        tk.Label(logo, text="—— M I N I S Ú P E R ——", bg=PRIMARIO,
                 fg=TEXTO_MENU, font=(FUENTE, 7)).pack(anchor="w")

        icono = tk.Canvas(barra, width=48, height=48, bg=PRIMARIO,
                          highlightthickness=0, cursor="hand2")
        icono.create_oval(3, 3, 45, 45, outline=BLANCO, width=2)
        icono.create_text(24, 25, text="👤", fill=BLANCO,
                          font=("Segoe UI Emoji", 16))
        icono.bind("<Button-1>", lambda e: self._info_sesion())
        icono.pack(side="right", padx=30)

    def _info_sesion(self):
        self.latido()
        hoy, total = self.empleados.segundos_trabajados(self.usuario[0])
        messagebox.showinfo(
            "Sesión activa",
            f"{self.usuario[1]}\nPuesto: {self.usuario[2]}\n\n"
            f"Horas hoy: {horas_texto(hoy)}\nHoras en total: {horas_texto(total)}")

    def _cuerpo(self):
        cuerpo = tk.Frame(self, bg=BLANCO)
        cuerpo.pack(fill="both", expand=True)

        menu = tk.Frame(cuerpo, bg=PRIMARIO, width=280)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)
        tk.Label(menu, text="MENÚ PRINCIPAL", bg=PRIMARIO, fg=TEXTO_MENU,
                 font=(FUENTE, 12)).pack(anchor="w", padx=22, pady=(24, 10))
        for icono, nombre in SECCIONES:
            self._item_menu(menu, icono, nombre)

        salir = tk.Label(menu, text="⇦  Cerrar Sesión", bg=PRIMARIO, fg=ROJO,
                         font=(FUENTE, 9, "bold"), cursor="hand2")
        salir.pack(side="bottom", anchor="w", padx=22, pady=(4, 16))
        salir.bind("<Button-1>", lambda e: self.cerrar_sesion())
        borrar = tk.Label(menu, text="🗑  Eliminar mi usuario", bg=PRIMARIO,
                          fg=ROJO, font=(FUENTE, 9, "bold"), cursor="hand2")
        borrar.pack(side="bottom", anchor="w", padx=22, pady=(0, 4))
        borrar.bind("<Button-1>", lambda e: self.eliminar_mi_usuario())
        clave = tk.Label(menu, text="🔑  Cambiar mi contraseña", bg=PRIMARIO,
                         fg=BLANCO, font=(FUENTE, 9, "bold"), cursor="hand2")
        clave.pack(side="bottom", anchor="w", padx=22, pady=(0, 4))
        clave.bind("<Button-1>", lambda e: self.abrir(CambiarContrasena))

        self.contenido = tk.Frame(cuerpo, bg=BLANCO)
        self.contenido.pack(side="right", fill="both", expand=True)

    def _item_menu(self, master, icono, nombre):
        item = tk.Label(master, text=f"{icono}   {nombre}", bg=PRIMARIO,
                        fg=BLANCO, font=(FUENTE, 13, "bold"), anchor="w",
                        padx=22, pady=8, cursor="hand2")
        item.pack(fill="x")
        item.bind("<Enter>", lambda e: item.config(
            bg=ACTIVO if nombre == self.seccion_activa else PRIMARIO_HOVER))
        item.bind("<Leave>", lambda e: item.config(
            bg=ACTIVO if nombre == self.seccion_activa else PRIMARIO))
        item.bind("<Button-1>", lambda e: self.mostrar(nombre))
        self.items[nombre] = item

    # ---------- Navegación ----------
    def _cambiar(self, fabrica, seccion):
        try:
            nueva = fabrica()
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo abrir la pantalla:\n{error}")
            return
        if self.pantalla is not None:
            self.pantalla.destroy()
        self.pantalla = nueva
        nueva.pack(fill="both", expand=True)
        self.seccion_activa = seccion
        for nombre, item in self.items.items():
            item.config(bg=ACTIVO if nombre == seccion else PRIMARIO)

    def mostrar(self, seccion):
        """Muestra la pantalla principal de una sección del menú."""
        if seccion == "Inicio":
            self._cambiar(lambda: PantallaBienvenida(self.contenido, self), "Inicio")
        else:
            tarjetas = MENUS[seccion]
            if seccion == "Empleados" and not self.es_gerente:
                tarjetas = MENU_EMPLEADOS_BASICO
            self._cambiar(lambda: MenuSeccion(
                self.contenido, self, seccion, tarjetas), seccion)

    def abrir(self, clase):
        """Abre una pantalla de acción (insertar, consultar, etc.)."""
        self._cambiar(lambda: clase(self.contenido, self), clase.SECCION)

    # ---------- Rueda del ratón ----------
    def _rueda(self, evento):
        try:
            widget = self.winfo_containing(evento.x_root, evento.y_root)
        except (tk.TclError, KeyError):
            return
        while widget is not None:
            if isinstance(widget, ListaTarjetas):
                if getattr(evento, "num", 0) == 4:
                    pasos = -1
                elif getattr(evento, "num", 0) == 5:
                    pasos = 1
                else:
                    pasos = -1 if evento.delta > 0 else 1
                widget.desplazar(pasos)
                return
            widget = getattr(widget, "master", None)


if __name__ == "__main__":
    App().mainloop()
