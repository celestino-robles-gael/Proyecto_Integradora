from GUI.estilos import dinero
from GUI.pantallas_base import (PantallaFormulario, PantallaLista, decimal,
                                entero)
from PRODUCTOS.productos import ProductosSystem

productos = ProductosSystem()

CAMPOS_PRODUCTO = [
    ("nombre", "Nombre del producto", "Escriba el nombre del producto..."),
    ("stock", "Stock", "Escriba la cantidad disponible..."),
    ("stock_minimo", "Stock mínimo", "Escriba el stock mínimo antes de reponer..."),
    ("precio_compra", "Precio de compra", "Ej. 15.00"),
    ("precio_venta", "Precio de venta", "Ej. 35.00"),
]


class InsertarProducto(PantallaFormulario):
    SECCION = "Inventario"
    TITULO = "INSERTAR PRODUCTO"
    CAMPOS = CAMPOS_PRODUCTO

    def procesar(self, d):
        id_p = productos.agregar(
            d["nombre"], entero(d, "stock"), entero(d, "stock_minimo"),
            decimal(d, "precio_compra"), decimal(d, "precio_venta"))
        return f"Producto registrado con el ID {id_p}."


class ActualizarProducto(PantallaFormulario):
    SECCION = "Inventario"
    TITULO = "ACTUALIZAR PRODUCTO"
    CAMPOS = [("id_producto", "ID del producto", "Escriba el ID del producto...")] + [
        (c, e.replace("Nombre del producto", "Nuevo nombre del producto")
            .replace("Stock mínimo", "Nuevo stock mínimo")
            .replace("Stock", "Nuevo stock")
            .replace("Precio de", "Nuevo precio de"), a)
        for c, e, a in CAMPOS_PRODUCTO]

    def al_construir(self):
        self.campos["id_producto"].enlazar("<FocusOut>", lambda e: self.cargar())

    def cargar(self):
        texto = self.campos["id_producto"].valor()
        if not texto.isdigit():
            return
        fila = productos.obtener(int(texto))
        if not fila:
            self.campos["id_producto"].error("No existe un producto con ese ID.")
            return
        self.campos["id_producto"].sin_error()
        for clave, valor in zip(("nombre", "stock", "stock_minimo",
                                 "precio_compra", "precio_venta"), fila[1:]):
            self.campos[clave].set(str(valor))

    def procesar(self, d):
        id_p = entero(d, "id_producto")
        productos.actualizar(
            id_p, d["nombre"], entero(d, "stock"), entero(d, "stock_minimo"),
            decimal(d, "precio_compra"), decimal(d, "precio_venta"))
        return f"El producto {id_p} se actualizó correctamente."


class ConsultarProducto(PantallaLista):
    SECCION = "Inventario"
    TITULO = "BUSCAR PRODUCTO"
    ETIQUETA = "Si desea, escriba aquí"
    PLACEHOLDER = "Buscar por ID o nombre del producto..."

    def buscar(self, texto):
        return productos.listar(texto)

    def datos_fila(self, fila):
        id_p, nombre, stock, minimo, compra, venta = fila
        aviso = "   ⚠ STOCK BAJO" if stock <= minimo else ""
        return dict(
            clave=id_p, izq=f"ID: {id_p}",
            centro=(nombre.upper(),
                    f"STOCK: {stock}  ·  MÍNIMO: {minimo}{aviso}"),
            der=(f"VENTA: {dinero(venta)}", f"COMPRA: {dinero(compra)}"))


class EliminarProducto(ConsultarProducto):
    TITULO = "ELIMINAR PRODUCTO"
    ETIQUETA = "Buscar por ID o nombre del producto"
    MODO = "eliminar"
    CONFIRMAR = "¿Eliminar este producto?"

    def eliminar_registro(self, clave):
        productos.eliminar(clave)
