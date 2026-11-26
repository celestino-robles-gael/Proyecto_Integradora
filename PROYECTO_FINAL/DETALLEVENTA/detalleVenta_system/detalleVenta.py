from conexionBD import conexion, cursor


class DetalleVenta:
    def __init__(self, id=None, id_venta=None, id_producto=None,
                 precio_unitario=None, cantidad=None):
        self.id = id
        self.id_venta = id_venta
        self.id_producto = id_producto
        self.precio_unitario = precio_unitario
        self.cantidad = cantidad


class DetalleVentaSystem:

    # ---------- CREAR ----------
    def agregar(self, id_venta, id_producto, cantidad):
        """Agrega un producto a una venta, descuenta stock y recalcula el total."""
        try:
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a 0.")

            cursor.execute(
                "SELECT precioVenta, stock FROM Productos WHERE id = %s",
                (id_producto,),
            )
            fila = cursor.fetchone()
            if fila is None:
                raise ValueError("El producto no existe.")

            precio, stock = fila
            if stock < cantidad:
                raise ValueError(f"Stock insuficiente (disponible: {stock}).")

            cursor.execute(
                """INSERT INTO detalleVenta
                   (idVenta, idProducto, precioUnitario, cantidad)
                   VALUES (%s, %s, %s, %s)""",
                (id_venta, id_producto, precio, cantidad),
            )
            id_nuevo = cursor.lastrowid

            cursor.execute(
                "UPDATE Productos SET stock = stock - %s WHERE id = %s",
                (cantidad, id_producto),
            )
            self._recalcular_total(id_venta)

            conexion.commit()
            return id_nuevo
        except Exception:
            conexion.rollback()
            raise

    # ---------- LEER ----------
    def listar_por_venta(self, id_venta):
        cursor.execute(
            """SELECT d.id, d.idVenta, d.idProducto, p.nombre,
                      d.precioUnitario, d.cantidad,
                      d.precioUnitario * d.cantidad AS subtotal
               FROM detalleVenta d
               JOIN Productos p ON p.id = d.idProducto
               WHERE d.idVenta = %s""",
            (id_venta,),
        )
        filas = cursor.fetchall()
        conexion.commit()
        return filas

    def obtener(self, id_detalle):
        cursor.execute(
            """SELECT id, idVenta, idProducto, precioUnitario, cantidad
               FROM detalleVenta WHERE id = %s""",
            (id_detalle,),
        )
        fila = cursor.fetchone()
        conexion.commit()
        return DetalleVenta(*fila) if fila else None

    # ---------- ACTUALIZAR ----------
    def actualizar_cantidad(self, id_detalle, nueva_cantidad):
        try:
            if nueva_cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a 0.")

            cursor.execute(
                "SELECT idVenta, idProducto, cantidad FROM detalleVenta WHERE id = %s",
                (id_detalle,),
            )
            fila = cursor.fetchone()
            if fila is None:
                raise ValueError("El detalle no existe.")

            id_venta, id_producto, cantidad_actual = fila
            diferencia = nueva_cantidad - cantidad_actual

            if diferencia > 0:
                cursor.execute("SELECT stock FROM Productos WHERE id = %s",
                               (id_producto,))
                (stock,) = cursor.fetchone()
                if stock < diferencia:
                    raise ValueError(f"Stock insuficiente (disponible: {stock}).")

            cursor.execute(
                "UPDATE detalleVenta SET cantidad = %s WHERE id = %s",
                (nueva_cantidad, id_detalle),
            )
            cursor.execute(
                "UPDATE Productos SET stock = stock - %s WHERE id = %s",
                (diferencia, id_producto),
            )
            self._recalcular_total(id_venta)

            conexion.commit()
        except Exception:
            conexion.rollback()
            raise

    # ---------- ELIMINAR ----------
    def eliminar(self, id_detalle):
        """Elimina el detalle, regresa el stock y recalcula el total."""
        try:
            cursor.execute(
                "SELECT idVenta, idProducto, cantidad FROM detalleVenta WHERE id = %s",
                (id_detalle,),
            )
            fila = cursor.fetchone()
            if fila is None:
                raise ValueError("El detalle no existe.")

            id_venta, id_producto, cantidad = fila

            cursor.execute("DELETE FROM detalleVenta WHERE id = %s", (id_detalle,))
            cursor.execute(
                "UPDATE Productos SET stock = stock + %s WHERE id = %s",
                (cantidad, id_producto),
            )
            self._recalcular_total(id_venta)

            conexion.commit()
        except Exception:
            conexion.rollback()
            raise

    # ---------- AUXILIAR ----------
    @staticmethod
    def _recalcular_total(id_venta):
        cursor.execute(
            """UPDATE Venta
               SET total = COALESCE(
                   (SELECT SUM(precioUnitario * cantidad)
                    FROM detalleVenta WHERE idVenta = %s), 0)
               WHERE id = %s""",
            (id_venta, id_venta),
        )
