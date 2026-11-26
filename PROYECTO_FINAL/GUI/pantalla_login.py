import os
import tkinter as tk
from tkinter import messagebox

from EMPLEADOS.empleados import EmpleadosSystem
from errores import ErrorCampo
from GUI.estilos import (BLANCO, FUENTE, PRIMARIO, ROJO_ERROR, BotonPildora,
                         Campo)

LOGO = os.path.join(os.path.dirname(__file__), "logo.png")


class PantallaLogin(tk.Frame):
    """Pantalla de inicio de sesión. Si existe GUI/logo.png se usa como logo."""

    def __init__(self, master, app, usuario=""):
        super().__init__(master, bg=BLANCO)
        self.app = app
        self.empleados = EmpleadosSystem()

        centro = tk.Frame(self, bg=BLANCO)
        centro.place(relx=0.5, rely=0.5, anchor="center")

        self._logo(centro)
        tk.Label(centro, text="EL BARATERO", bg=BLANCO, fg="#111111",
                 font=(FUENTE, 34, "bold")).pack()
        tk.Label(centro, text="——  Sistema de abarrotes  ——", bg=BLANCO,
                 fg="#222222", font=("Georgia", 14, "italic")).pack(pady=(0, 14))
        tk.Label(centro, text="INICIO DE SESIÓN", bg=BLANCO, fg="#111111",
                 font=(FUENTE, 12, "bold")).pack(pady=(4, 12))

        formulario = tk.Frame(centro, bg=BLANCO, width=520)
        formulario.pack()
        self.usuario = Campo(formulario, "Usuario",
                             "Escriba su nombre de usuario...")
        self.usuario.pack(fill="x", ipadx=230)
        self.contrasena = Campo(formulario, "Contraseña",
                                "Escriba su contraseña...", oculto=True)
        self.contrasena.pack(fill="x")
        self.usuario.enlazar("<Return>", lambda e: self.contrasena.foco())
        self.contrasena.enlazar("<Return>", lambda e: self.entrar())

        self.mensaje = tk.Label(centro, text="", bg=BLANCO, fg=ROJO_ERROR,
                                font=(FUENTE, 9))
        self.mensaje.pack(pady=(0, 4))
        BotonPildora(centro, "INICIAR SESIÓN", self.entrar, w=520, h=38).pack()

        registro = tk.Label(centro, text="¿Eres empleado nuevo? Regístrate aquí",
                            bg=BLANCO, fg=PRIMARIO, cursor="hand2",
                            font=(FUENTE, 10, "underline"))
        registro.pack(pady=(14, 0))
        registro.bind("<Button-1>", lambda e: self.app.mostrar_registro())

        if usuario:
            self.usuario.set(usuario)
            self.contrasena.foco()
        else:
            self.usuario.foco()

    def _logo(self, padre):
        try:
            imagen = tk.PhotoImage(file=LOGO)
            while imagen.height() > 150:
                imagen = imagen.subsample(2)
            self._imagen = imagen
            tk.Label(padre, image=imagen, bg=BLANCO).pack()
        except (tk.TclError, OSError):
            tk.Label(padre, text="🐓", bg=BLANCO, fg="#111111",
                     font=("Segoe UI Symbol", 56)).pack()

    def entrar(self):
        self.usuario.sin_error()
        self.contrasena.sin_error()
        usuario = self.usuario.valor()
        contrasena = self.contrasena.valor()
        if not usuario:
            self.usuario.error("Escriba su usuario.")
            return
        if not contrasena:
            self.contrasena.error("Escriba su contraseña.")
            return
        try:
            fila = self.empleados.autenticar(usuario, contrasena)
        except Exception as error:
            self.mensaje.config(text=f"Error de base de datos: {error}")
            return
        if fila is None:
            self.mensaje.config(text="Usuario o contraseña incorrectos.")
            return
        try:
            abierta = self.empleados.sesion_activa(fila[0])
        except Exception as error:
            self.mensaje.config(text=f"Error de base de datos: {error}")
            return
        if abierta:
            self.mensaje.config(
                text="Este usuario ya tiene una sesión abierta en otra ventana.\n"
                     "Si el programa se cerró mal, espere un minuto e intente de nuevo.")
            return
        self.app.iniciar_sesion(fila)


class PantallaRegistro(tk.Frame):
    """Auto-registro de empleados. La contraseña de todos es «admin»."""

    def __init__(self, master, app):
        super().__init__(master, bg=BLANCO)
        self.app = app
        self.empleados = EmpleadosSystem()

        centro = tk.Frame(self, bg=BLANCO)
        centro.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(centro, text="EL BARATERO", bg=BLANCO, fg="#111111",
                 font=(FUENTE, 34, "bold")).pack()
        tk.Label(centro, text="REGISTRO DE EMPLEADO", bg=BLANCO, fg="#111111",
                 font=(FUENTE, 12, "bold")).pack(pady=(6, 12))

        formulario = tk.Frame(centro, bg=BLANCO, width=520)
        formulario.pack()
        self.nombre = Campo(formulario, "Nombre completo",
                            "Escriba su nombre completo...")
        self.nombre.pack(fill="x", ipadx=230)
        self.usuario = Campo(formulario, "Usuario",
                             "Elija su nombre de usuario...")
        self.usuario.pack(fill="x")
        self.nombre.enlazar("<Return>", lambda e: self.usuario.foco())
        self.usuario.enlazar("<Return>", lambda e: self.registrar())

        tk.Label(centro, text="Su contraseña será: admin", bg=BLANCO,
                 fg="#555555", font=(FUENTE, 9)).pack(pady=(0, 8))
        BotonPildora(centro, "REGISTRARME", self.registrar, w=520, h=38).pack()
        volver = tk.Label(centro, text="← Volver al inicio de sesión", bg=BLANCO,
                          fg=PRIMARIO, cursor="hand2",
                          font=(FUENTE, 10, "underline"))
        volver.pack(pady=(14, 0))
        volver.bind("<Button-1>", lambda e: self.app.mostrar_login())
        self.nombre.foco()

    def registrar(self):
        self.nombre.sin_error()
        self.usuario.sin_error()
        try:
            self.empleados.registrar(self.nombre.valor(), self.usuario.valor())
        except ErrorCampo as error:
            campo = self.nombre if error.clave == "nombre" else self.usuario
            campo.error(error.mensaje)
            campo.foco()
            return
        except Exception as error:
            messagebox.showerror("No se pudo registrar", str(error))
            return
        usuario = self.usuario.valor()
        messagebox.showinfo("¡Registro exitoso!",
                            f"Ya puedes entrar con el usuario «{usuario}» "
                            "y la contraseña «admin».")
        self.app.mostrar_login(usuario)
