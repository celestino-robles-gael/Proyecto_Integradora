import hashlib


def consultar(sql, params=(), uno=False):
    """SELECT: devuelve todas las filas, o solo la primera si uno=True."""
    cursor.execute(sql, params)
    filas = cursor.fetchone() if uno else cursor.fetchall()
    conexion.commit()  # cierra la lectura para ver siempre datos actualizados
    return filas


def ejecutar(sql, params=()):
    """INSERT / UPDATE / DELETE: guarda los cambios y devuelve el último id."""
    try:
        cursor.execute(sql, params)
        conexion.commit()
        return cursor.lastrowid
    except Exception:
        conexion.rollback()
        raise


from conexionBD import conexion, cursor
from errores import ErrorCampo

# Todos los empleados usan esta contraseña.
CONTRASENA_GENERAL = "admin"   # contraseña inicial de todos
PUESTOS = ("empleado", "gerente")
SEGUNDOS_SESION_VIVA = 90      # sin «latido» en este tiempo, la sesión se da por muerta


def _hash(contrasena):
    # Mismo resultado que SHA2('texto', 256) de MySQL
    return hashlib.sha256(contrasena.encode("utf-8")).hexdigest()


class EmpleadosSystem:

    def autenticar(self, usuario, contrasena):
        """Devuelve (id, nombre, puesto) si las credenciales son correctas."""
        return consultar(
            """SELECT id, nombre, puesto FROM Empleado
               WHERE usuario = %s AND contrasena = %s""",
            (usuario.strip(), _hash(contrasena)), uno=True,
        )

    # ---------- Permisos ----------
    def es_gerente(self, id_empleado):
        fila = self.obtener(id_empleado) if id_empleado is not None else None
        return bool(fila) and fila[2].strip().lower() == "gerente"

    def _exigir_gerente(self, id_actor):
        if not self.es_gerente(id_actor):
            raise PermissionError("Solo el gerente puede hacer esta acción.")

    def _gerentes(self):
        return consultar(
            "SELECT COUNT(*) FROM Empleado WHERE LOWER(puesto) = 'gerente'",
            uno=True)[0]

    # ---------- Consultas ----------
    def listar(self, filtro="", solo_id=None):
        """(id, nombre, puesto, segundos trabajados en total).
        Con `solo_id` devuelve únicamente a ese empleado."""
        patron = f"%{filtro.strip()}%"
        sql = """SELECT e.id, e.nombre, e.puesto,
                        COALESCE(SUM(TIMESTAMPDIFF(SECOND, a.entrada, a.salida)), 0)
                 FROM Empleado e LEFT JOIN Asistencia a ON a.idEmpleado = e.id
                 WHERE (e.nombre LIKE %s OR e.puesto LIKE %s
                        OR CAST(e.id AS CHAR) LIKE %s)"""
        params = [patron, patron, patron]
        if solo_id is not None:
            sql += " AND e.id = %s"
            params.append(solo_id)
        sql += " GROUP BY e.id, e.nombre, e.puesto ORDER BY e.nombre"
        return consultar(sql, tuple(params))

    def obtener(self, id_empleado):
        """(id, nombre, puesto, usuario)"""
        return consultar(
            "SELECT id, nombre, puesto, usuario FROM Empleado WHERE id = %s",
            (id_empleado,), uno=True,
        )

    # ---------- Altas y cambios ----------
    def registrar(self, nombre, usuario):
        """Auto-registro: siempre puesto «empleado» y contraseña inicial general."""
        self._validar(nombre, "empleado", usuario)
        self._usuario_libre(usuario)
        return self._insertar(nombre, "empleado", usuario)

    def agregar(self, id_actor, nombre, puesto, usuario):
        self._exigir_gerente(id_actor)
        self._validar(nombre, puesto, usuario)
        self._usuario_libre(usuario)
        return self._insertar(nombre, puesto, usuario)

    def _insertar(self, nombre, puesto, usuario):
        return ejecutar(
            """INSERT INTO Empleado (nombre, puesto, usuario, contrasena)
               VALUES (%s, %s, %s, %s)""",
            (nombre.strip(), puesto.strip().lower(), usuario.strip(),
             _hash(CONTRASENA_GENERAL)),
        )

    def actualizar(self, id_actor, id_empleado, nombre, puesto, usuario,
                   restablecer=False):
        """`restablecer=True` devuelve la contraseña a la general («admin»)."""
        self._exigir_gerente(id_actor)
        fila = self.obtener(id_empleado)
        if not fila:
            raise ErrorCampo("id_empleado", "No existe un empleado con ese ID.")
        self._validar(nombre, puesto, usuario)
        self._usuario_libre(usuario, ignorar_id=id_empleado)
        puesto = puesto.strip().lower()
        if fila[3].lower() == "admin" and usuario.strip().lower() != "admin":
            raise ErrorCampo("usuario", "El usuario «admin» no se puede renombrar.")
        if (fila[2].strip().lower() == "gerente" and puesto != "gerente"
                and self._gerentes() <= 1):
            raise ErrorCampo("puesto", "Debe quedar al menos un gerente.")
        if restablecer:
            ejecutar(
                """UPDATE Empleado SET nombre=%s, puesto=%s, usuario=%s,
                          contrasena=%s WHERE id=%s""",
                (nombre.strip(), puesto, usuario.strip(),
                 _hash(CONTRASENA_GENERAL), id_empleado))
        else:
            ejecutar(
                "UPDATE Empleado SET nombre=%s, puesto=%s, usuario=%s WHERE id=%s",
                (nombre.strip(), puesto, usuario.strip(), id_empleado))

    def cambiar_contrasena(self, id_empleado, actual, nueva):
        ok = consultar("SELECT id FROM Empleado WHERE id = %s AND contrasena = %s",
                       (id_empleado, _hash(actual)), uno=True)
        if not ok:
            raise ErrorCampo("contrasena_actual", "La contraseña actual no es correcta.")
        if len(nueva) < 4:
            raise ErrorCampo("contrasena_nueva", "Use al menos 4 caracteres.")
        if nueva == actual:
            raise ErrorCampo("contrasena_nueva", "Debe ser distinta de la actual.")
        ejecutar("UPDATE Empleado SET contrasena = %s WHERE id = %s",
                 (_hash(nueva), id_empleado))

    # ---------- Baja ----------
    def eliminar(self, id_actor, id_empleado):
        """Cada quien puede borrar su propio usuario; para borrar el de otro
        hay que ser gerente. Las ventas se conservan; las horas se borran."""
        fila = self.obtener(id_empleado)
        if not fila:
            raise ValueError("Ese empleado ya no existe.")
        if id_actor != id_empleado:
            self._exigir_gerente(id_actor)
        if fila[3].lower() == "admin":
            raise ValueError("El usuario «admin» no se puede eliminar.")
        if fila[2].strip().lower() == "gerente" and self._gerentes() <= 1:
            raise ValueError("No se puede eliminar al único gerente.")
        ejecutar("DELETE FROM Empleado WHERE id = %s", (id_empleado,))

    # ---------- Horas trabajadas ----------
    def iniciar_turno(self, id_empleado):
        """Abre un periodo de trabajo y devuelve su id."""
        return ejecutar(
            """INSERT INTO Asistencia (idEmpleado, entrada, salida, latido, abierta)
               VALUES (%s, NOW(), NOW(), NOW(), 1)""", (id_empleado,))

    def latido(self, id_turno, segundos_inactivo=0, contar=True):
        """Avisa que el programa sigue abierto. Si `contar`, la salida se fija en la
        última actividad real (ahora menos los segundos de inactividad)."""
        self._actualizar_turno(id_turno, segundos_inactivo, contar, cerrar=False)

    def cerrar_turno(self, id_turno, segundos_inactivo=0, contar=True):
        self._actualizar_turno(id_turno, segundos_inactivo, contar, cerrar=True)

    @staticmethod
    def _actualizar_turno(id_turno, segundos_inactivo, contar, cerrar):
        sets = ["latido = NOW()"]
        params = []
        if contar:
            sets.append("salida = GREATEST(entrada, "
                        "DATE_SUB(NOW(), INTERVAL %s SECOND))")
            params.append(max(int(segundos_inactivo), 0))
        if cerrar:
            sets.append("abierta = 0")
        params.append(id_turno)
        ejecutar(f"UPDATE Asistencia SET {', '.join(sets)} WHERE id = %s",
                 tuple(params))

    def sesion_activa(self, id_empleado):
        """True si ese usuario ya tiene el programa abierto en otra ventana."""
        return consultar(
            """SELECT COUNT(*) FROM Asistencia
               WHERE idEmpleado = %s AND abierta = 1
                     AND latido > DATE_SUB(NOW(), INTERVAL %s SECOND)""",
            (id_empleado, SEGUNDOS_SESION_VIVA), uno=True)[0] > 0

    def segundos_trabajados(self, id_empleado):
        """(segundos de hoy, segundos en total)"""
        hoy, total = consultar(
            """SELECT COALESCE(SUM(CASE WHEN DATE(entrada) = CURDATE()
                      THEN TIMESTAMPDIFF(SECOND, entrada, salida) ELSE 0 END), 0),
                      COALESCE(SUM(TIMESTAMPDIFF(SECOND, entrada, salida)), 0)
               FROM Asistencia WHERE idEmpleado = %s""",
            (id_empleado,), uno=True,
        )
        return int(hoy), int(total)

    # ---------- Validaciones ----------
    def _usuario_libre(self, usuario, ignorar_id=None):
        fila = consultar("SELECT id FROM Empleado WHERE usuario = %s",
                         (usuario.strip(),), uno=True)
        if fila and fila[0] != ignorar_id:
            raise ErrorCampo("usuario", "Ese nombre de usuario ya está en uso.")

    @staticmethod
    def _validar(nombre, puesto, usuario):
        if not nombre.strip():
            raise ErrorCampo("nombre", "Escriba el nombre completo.")
        if puesto.strip().lower() not in PUESTOS:
            raise ErrorCampo("puesto", "El puesto debe ser «empleado» o «gerente».")
        if len(usuario.strip()) < 3:
            raise ErrorCampo("usuario", "El usuario debe tener al menos 3 caracteres.")
