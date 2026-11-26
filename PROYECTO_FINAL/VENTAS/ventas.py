from conexionBD import conexion, cursor
from DETALLEVENTA.detalleVenta_system.detalleVenta import DetalleVentaSystem
from errores import ErrorCampo
from utilidades import rango_mes


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


class VentasSystem:

    def __init__(self):
        self.detalle = DetalleVentaSystem()

    # ---------- Consultas ----------
    def listar(self):
        return self.buscar("")

    def buscar(self, filtro=""):
        patron = f"%{filtro.strip()}%"
        return consultar(
            """SELECT v.id, v.fecha, COALESCE(e.nombre, '(empleado eliminado)'), v.total
               FROM Venta v LEFT JOIN Empleado e ON e.id = v.idEmpleado
               WHERE CAST(v.id AS CHAR) LIKE %s OR COALESCE(e.nombre, '(empleado eliminado)') LIKE %s
               ORDER BY v.id DESC""",
            (patron, patron),
        )

    def obtener(self, id_venta):
        return consultar(
            """SELECT v.id, v.fecha, v.total, COALESCE(e.nombre, '(empleado eliminado)')
               FROM Venta v LEFT JOIN Empleado e ON e.id = v.idEmpleado
               WHERE v.id = %s""",
            (id_venta,), uno=True,
        )

    def detalles(self, filtro=""):
        """(id detalle, id venta, id producto, producto, cantidad, subtotal)"""
        patron = f"%{filtro.strip()}%"
        return consultar(
            """SELECT d.id, d.idVenta, d.idProducto, p.nombre, d.cantidad,
                      d.precioUnitario * d.cantidad
               FROM detalleVenta d JOIN Productos p ON p.id = d.idProducto
               WHERE CAST(d.idVenta AS CHAR) LIKE %s
                  OR CAST(d.idProducto AS CHAR) LIKE %s
                  OR p.nombre LIKE %s
               ORDER BY d.idVenta DESC, d.id""",
            (patron, patron, patron),
        )

    # ---------- Altas, cambios y bajas ----------
    def crear(self, id_empleado, fecha=None):
        if fecha is None:
            return ejecutar(
                "INSERT INTO Venta (fecha, total, idEmpleado) VALUES (NOW(), 0, %s)",
                (id_empleado,),
            )
        return ejecutar(
            "INSERT INTO Venta (fecha, total, idEmpleado) VALUES (%s, 0, %s)",
            (fecha.strftime("%Y-%m-%d %H:%M:%S"), id_empleado),
        )

    def guardar_venta(self, id_empleado, items, fecha=None):
        """items: lista de (id_producto, cantidad).
        Si algo falla a la mitad, deshace todo y vuelve a lanzar el error."""
        if not items:
            raise ValueError("La venta no tiene productos.")
        id_venta = self.crear(id_empleado, fecha)
        agregados = []
        try:
            for id_producto, cantidad in items:
                agregados.append(
                    self.detalle.agregar(id_venta, id_producto, cantidad))
        except Exception:
            for id_detalle in agregados:
                self.detalle.eliminar(id_detalle)
            ejecutar("DELETE FROM Venta WHERE id = %s", (id_venta,))
            raise
        return id_venta

    def actualizar(self, id_venta, fecha=None, id_producto=None, cantidad=None):
        """Cambia la fecha y/o la cantidad de un producto de la venta."""
        if not self.obtener(id_venta):
            raise ErrorCampo("id_venta", "No existe una venta con ese ID.")
        if (id_producto is None) != (cantidad is None):
            clave = "cantidad" if cantidad is None else "id_producto"
            raise ErrorCampo(clave, "Indique el producto y la nueva cantidad.")
        if fecha is None and id_producto is None:
            raise ErrorCampo("fecha", "No hay nada que actualizar.")

        if id_producto is not None:
            fila = consultar(
                "SELECT id FROM detalleVenta WHERE idVenta = %s AND idProducto = %s",
                (id_venta, id_producto), uno=True,
            )
            if not fila:
                raise ErrorCampo("id_producto", "Ese producto no está en la venta.")
            self.detalle.actualizar_cantidad(fila[0], cantidad)
        if fecha is not None:
            ejecutar("UPDATE Venta SET fecha = %s WHERE id = %s",
                     (fecha.strftime("%Y-%m-%d %H:%M:%S"), id_venta))

    def eliminar(self, id_venta):
        """Borra la venta y regresa el stock de sus productos."""
        for fila in self.detalle.listar_por_venta(id_venta):
            self.detalle.eliminar(fila[0])
        ejecutar("DELETE FROM Venta WHERE id = %s", (id_venta,))

    # ---------- Resúmenes ----------
    def resumen_hoy(self):
        n, total = consultar(
            """SELECT COUNT(*), COALESCE(SUM(total), 0) FROM Venta
               WHERE DATE(fecha) = CURDATE()""",
            uno=True,
        )
        return n, total

    def resumen_mes(self, anio, mes):
        desde, hasta = rango_mes(anio, mes)
        n, total = consultar(
            """SELECT COUNT(*), COALESCE(SUM(total), 0) FROM Venta
               WHERE DATE(fecha) BETWEEN %s AND %s""",
            (str(desde), str(hasta)), uno=True,
        )
        return n, total

    def meses_con_ventas(self):
        """(año, mes, número de ventas, total) del más reciente al más antiguo."""
        return consultar(
            """SELECT YEAR(fecha), MONTH(fecha), COUNT(*), COALESCE(SUM(total), 0)
               FROM Venta
               GROUP BY YEAR(fecha), MONTH(fecha)
               ORDER BY YEAR(fecha) DESC, MONTH(fecha) DESC"""
        )

    def ventas_por_fecha(self, desde, hasta):
        return consultar(
            """SELECT v.id, v.fecha, COALESCE(e.nombre, '(empleado eliminado)'), v.total
               FROM Venta v LEFT JOIN Empleado e ON e.id = v.idEmpleado
               WHERE DATE(v.fecha) BETWEEN %s AND %s
               ORDER BY v.fecha""",
            (str(desde), str(hasta)),
        )

    def mas_vendidos(self, desde, hasta):
        return consultar(
            """SELECT p.nombre, SUM(d.cantidad),
                      SUM(d.cantidad * d.precioUnitario)
               FROM detalleVenta d
               JOIN Venta v ON v.id = d.idVenta
               JOIN Productos p ON p.id = d.idProducto
               WHERE DATE(v.fecha) BETWEEN %s AND %s
               GROUP BY p.id, p.nombre
               ORDER BY SUM(d.cantidad) DESC""",
            (str(desde), str(hasta)),
        )

    def por_empleado(self, desde, hasta):
        return consultar(
            """SELECT COALESCE(e.nombre, '(empleado eliminado)'), COUNT(v.id), SUM(v.total)
               FROM Venta v LEFT JOIN Empleado e ON e.id = v.idEmpleado
               WHERE DATE(v.fecha) BETWEEN %s AND %s
               GROUP BY e.id, e.nombre
               ORDER BY SUM(v.total) DESC""",
            (str(desde), str(hasta)),
        )
