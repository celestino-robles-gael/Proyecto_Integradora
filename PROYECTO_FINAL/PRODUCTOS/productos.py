from conexionBD import conexion, cursor
from errores import ErrorCampo


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


COLUMNAS = "id, nombre, stock, stockMinimo, precioCompra, precioVenta"


class ProductosSystem:

    def listar(self, filtro=""):
        patron = f"%{filtro.strip()}%"
        return consultar(
            f"""SELECT {COLUMNAS} FROM Productos
                WHERE nombre LIKE %s OR CAST(id AS CHAR) LIKE %s
                ORDER BY nombre""",
            (patron, patron),
        )

    def obtener(self, id_producto):
        return consultar(
            f"SELECT {COLUMNAS} FROM Productos WHERE id = %s",
            (id_producto,), uno=True,
        )

    def agregar(self, nombre, stock, stock_minimo, precio_compra, precio_venta):
        """Registra un producto y devuelve su ID (se asigna solo)."""
        self._validar(nombre, stock, stock_minimo, precio_compra, precio_venta)
        return ejecutar(
            """INSERT INTO Productos
               (nombre, stock, stockMinimo, precioCompra, precioVenta)
               VALUES (%s, %s, %s, %s, %s)""",
            (nombre.strip(), stock, stock_minimo, precio_compra, precio_venta),
        )

    def actualizar(self, id_producto, nombre, stock, stock_minimo,
                   precio_compra, precio_venta):
        if not self.obtener(id_producto):
            raise ErrorCampo("id_producto", "No existe un producto con ese ID.")
        self._validar(nombre, stock, stock_minimo, precio_compra, precio_venta)
        ejecutar(
            """UPDATE Productos
               SET nombre = %s, stock = %s, stockMinimo = %s,
                   precioCompra = %s, precioVenta = %s
               WHERE id = %s""",
            (nombre.strip(), stock, stock_minimo, precio_compra, precio_venta,
             id_producto),
        )

    def eliminar(self, id_producto):
        usado = consultar(
            "SELECT COUNT(*) FROM detalleVenta WHERE idProducto = %s",
            (id_producto,), uno=True,
        )[0]
        if usado:
            raise ValueError(
                "No se puede eliminar: el producto ya tiene ventas registradas.")
        ejecutar("DELETE FROM Productos WHERE id = %s", (id_producto,))

    def stock_bajo(self):
        return consultar(
            """SELECT id, nombre, stock, stockMinimo FROM Productos
               WHERE stock <= stockMinimo ORDER BY stock, nombre"""
        )

    @staticmethod
    def _validar(nombre, stock, stock_minimo, precio_compra, precio_venta):
        if not nombre.strip():
            raise ErrorCampo("nombre", "Escriba el nombre del producto.")
        if len(nombre.strip()) > 100:
            raise ErrorCampo("nombre", "El nombre es demasiado largo (máx. 100).")
        if stock < 0:
            raise ErrorCampo("stock", "El stock no puede ser negativo.")
        if stock_minimo < 0:
            raise ErrorCampo("stock_minimo", "El stock mínimo no puede ser negativo.")
        if precio_compra < 0:
            raise ErrorCampo("precio_compra", "El precio no puede ser negativo.")
        if precio_venta < 0:
            raise ErrorCampo("precio_venta", "El precio no puede ser negativo.")
