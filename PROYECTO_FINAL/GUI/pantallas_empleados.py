from errores import ErrorCampo
from EMPLEADOS.empleados import EmpleadosSystem
from GUI.pantallas_base import PantallaFormulario, PantallaLista, entero
from utilidades import horas_texto

empleados = EmpleadosSystem()


class InsertarEmpleado(PantallaFormulario):
    SECCION = "Empleados"
    TITULO = "INSERTAR EMPLEADO"
    CAMPOS = [
        ("nombre", "Nombre completo", "Escriba el nombre completo..."),
        ("puesto", "Puesto del empleado", "Escriba: empleado o gerente..."),
        ("usuario", "Usuario de acceso", "Escriba el nombre de usuario..."),
    ]
    INSTRUCCIONES = [
        "Escriba el nombre completo y el puesto.",
        "Defina el usuario con el que iniciará sesión (la contraseña es «admin»).",
        "Pulse Guardar para registrar al empleado.",
    ]

    def procesar(self, d):
        id_e = empleados.agregar(self.app.usuario[0], d["nombre"], d["puesto"],
                                 d["usuario"])
        return f"Empleado registrado con el ID {id_e}."


class ActualizarEmpleado(PantallaFormulario):
    SECCION = "Empleados"
    TITULO = "ACTUALIZAR EMPLEADO"
    CAMPOS = [
        ("id_empleado", "ID del empleado", "Escriba el ID del empleado..."),
        ("nombre", "Nuevo nombre completo", "Escriba el nuevo nombre..."),
        ("puesto", "Nuevo puesto del empleado", "Escriba: empleado o gerente..."),
        ("usuario", "Nuevo usuario de acceso", "Escriba el nuevo usuario..."),
        ("restablecer", "¿Restablecer su contraseña a «admin»? (opcional)",
         "Escriba «si» para restablecerla..."),
    ]

    def al_construir(self):
        self.campos["id_empleado"].enlazar("<FocusOut>", lambda e: self.cargar())

    def cargar(self):
        texto = self.campos["id_empleado"].valor()
        if not texto.isdigit():
            return
        fila = empleados.obtener(int(texto))
        if not fila:
            self.campos["id_empleado"].error("No existe un empleado con ese ID.")
            return
        self.campos["id_empleado"].sin_error()
        for clave, valor in zip(("nombre", "puesto", "usuario"), fila[1:]):
            self.campos[clave].set(valor)

    def procesar(self, d):
        id_e = entero(d, "id_empleado")
        restablecer = d["restablecer"].strip().lower() in ("si", "sí", "s")
        empleados.actualizar(self.app.usuario[0], id_e, d["nombre"], d["puesto"],
                             d["usuario"], restablecer)
        return f"El empleado {id_e} se actualizó correctamente."


class ConsultarEmpleado(PantallaLista):
    SECCION = "Empleados"
    TITULO = "BUSCAR EMPLEADO"
    ETIQUETA = "Si desea, escriba aquí"
    PLACEHOLDER = "Buscar por ID, nombre o puesto..."

    def buscar(self, texto):
        # El gerente ve a todos; los demás solo se ven a sí mismos.
        solo = None if self.app.es_gerente else self.app.usuario[0]
        return empleados.listar(texto, solo_id=solo)

    def datos_fila(self, fila):
        id_e, nombre, puesto, segundos = fila
        return dict(clave=id_e, izq=f"ID: {id_e}",
                    centro=(nombre.upper(), f"PUESTO: {puesto.upper()}"),
                    der=("HORAS TRABAJADAS", horas_texto(segundos)))


class EliminarEmpleado(ConsultarEmpleado):
    TITULO = "ELIMINAR EMPLEADO"
    ETIQUETA = "Buscar por ID o nombre del empleado"
    MODO = "eliminar"
    CONFIRMAR = "¿Eliminar este empleado?"

    def eliminar_registro(self, clave):
        if clave == self.app.usuario[0]:
            raise ValueError("Para borrar tu propio usuario usa «Eliminar mi usuario» "
                             "en el menú de la izquierda.")
        empleados.eliminar(self.app.usuario[0], clave)


class CambiarContrasena(PantallaFormulario):
    """Disponible para todos desde el menú lateral."""
    SECCION = "Inicio"
    TITULO = "CAMBIAR MI CONTRASEÑA"
    CAMPOS = [
        ("contrasena_actual", "Contraseña actual", "Escriba su contraseña actual..."),
        ("contrasena_nueva", "Contraseña nueva", "Mínimo 4 caracteres..."),
        ("contrasena_confirmar", "Repita la contraseña nueva", "Escríbala otra vez..."),
    ]
    INSTRUCCIONES = [
        "Todos empiezan con la contraseña «admin»; cámbiela para proteger su cuenta.",
        "Si la olvida, el gerente puede restablecerla desde Empleados → Actualizar.",
    ]

    def procesar(self, d):
        if d["contrasena_nueva"] != d["contrasena_confirmar"]:
            raise ErrorCampo("contrasena_confirmar", "Las contraseñas no coinciden.")
        empleados.cambiar_contrasena(self.app.usuario[0], d["contrasena_actual"],
                                     d["contrasena_nueva"])
        return "Tu contraseña se actualizó correctamente."
