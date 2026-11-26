import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from errores import ErrorCampo
from GUI.estilos import (BLANCO, FUENTE, PRIMARIO, BotonPildora, Campo,
                         CajaInstrucciones, crear_tabla, dinero, titulo_pantalla)
from GUI.pantallas_base import (PantallaBase, PantallaFormulario, PantallaLista,
                                entero)
from PRODUCTOS.productos import ProductosSystem
from utilidades import fecha_corta, fecha_larga, hora, parse_fecha
from VENTAS.ventas import VentasSystem

ventas = VentasSystem()
productos = ProductosSystem()


# ---------------- Insertar venta ----------------
class InsertarVenta(PantallaBase):
    SECCION = "Ventas"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.carrito = []  # (id_producto, nombre, precio, cantidad)
        titulo_pantalla(self, "INSERTAR VENTA")

        barra = tk.Frame(self, bg=BLANCO)
        barra.pack(side="bottom", fill="x", padx=44, pady=(0, 20))
        BotonPildora(barra, "Guardar", self.guardar).pack(side="left")
        BotonPildora(barra, "Regresar", self.regresar, relleno=False).pack(
            side="right")

        self.f_fecha = Campo(self, "Fecha de venta", "AAAA-MM-DD HH:MM")
        self.f_fecha.pack(fill="x", padx=44)
        self.f_fecha.set(datetime.now().strftime("%Y-%m-%d %H:%M"))

        fila = tk.Frame(self, bg=BLANCO)
        fila.pack(fill="x", padx=44)
        fila.grid_columnconfigure(0, weight=3)
        fila.grid_columnconfigure(1, weight=1)
        self.f_producto = Campo(fila, "Producto (ID o nombre)",
                                "Escriba el ID o el nombre del producto...")
        self.f_producto.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.f_cantidad = Campo(fila, "Cantidad", "1")
        self.f_cantidad.grid(row=0, column=1, sticky="ew")
        self.f_cantidad.set("1")
        self.f_producto.enlazar("<Return>", lambda e: self.agregar())
        self.f_cantidad.enlazar("<Return>", lambda e: self.agregar())

        acciones = tk.Frame(self, bg=BLANCO)
        acciones.pack(fill="x", padx=44, pady=(0, 6))
        BotonPildora(acciones, "Agregar", self.agregar, w=180, h=32).pack(
            side="left")
        BotonPildora(acciones, "Quitar seleccionado", self.quitar, w=200, h=32,
                     relleno=False).pack(side="left", padx=10)

        inferior = tk.Frame(self, bg=BLANCO)
        inferior.pack(fill="both", expand=True, padx=44)
        marco, self.tabla = crear_tabla(inferior, [
            ("producto", "Producto", 200), ("precio", "Precio", 80),
            ("cantidad", "Cant.", 50), ("subtotal", "Subtotal", 90)], altura=4)
        marco.pack(side="left", fill="both", expand=True)
        derecha = tk.Frame(inferior, bg=BLANCO)
        derecha.pack(side="right", padx=(16, 0), anchor="n")
        CajaInstrucciones(derecha, [
            "Escriba el ID o nombre del producto.",
            "Indique la cantidad y pulse Agregar.",
            "Repita para cada producto.",
            "Pulse Guardar para registrar la venta.",
        ]).pack()
        self.lbl_total = tk.Label(derecha, text="Total de venta: $0.00",
                                  bg=BLANCO, fg=PRIMARIO,
                                  font=(FUENTE, 13, "bold"))
        self.lbl_total.pack(pady=(10, 0), anchor="w")

    def refrescar(self):
        self.tabla.delete(*self.tabla.get_children())
        total = 0
        for n, (_, nombre, precio, cant) in enumerate(self.carrito):
            sub = float(precio) * cant
            total += sub
            self.tabla.insert("", "end", iid=str(n), values=(
                nombre, dinero(precio), cant, dinero(sub)))
        self.lbl_total.config(text=f"Total de venta: {dinero(total)}")

    def _resolver_producto(self, texto):
        if not texto:
            raise ErrorCampo("producto", "Escriba el ID o el nombre del producto.")
        if texto.isdigit():
            fila = productos.obtener(int(texto))
            if fila:
                return fila
        coincidencias = productos.listar(texto)
        if len(coincidencias) == 1:
            return coincidencias[0]
        if not coincidencias:
            raise ErrorCampo("producto", "No se encontró ese producto.")
        raise ErrorCampo("producto",
                         "Hay varios productos parecidos; escriba el ID.")

    def agregar(self):
        self.f_producto.sin_error()
        self.f_cantidad.sin_error()
        try:
            fila = self._resolver_producto(self.f_producto.valor())
            cantidad = entero({"cantidad": self.f_cantidad.valor()}, "cantidad")
            if cantidad <= 0:
                raise ErrorCampo("cantidad", "Debe ser mayor a 0.")
            id_prod, nombre, stock, _, _, precio = fila
            en_carrito = sum(c for p, _, _, c in self.carrito if p == id_prod)
            if en_carrito + cantidad > stock:
                raise ErrorCampo("cantidad", f"Solo hay {stock} en inventario.")
        except ErrorCampo as error:
            destino = self.f_cantidad if error.clave == "cantidad" else self.f_producto
            destino.error(error.mensaje)
            return
        self.carrito.append((id_prod, nombre, precio, cantidad))
        self.refrescar()
        self.f_producto.set("")
        self.f_cantidad.set("1")
        self.f_producto.foco()

    def quitar(self):
        seleccion = self.tabla.selection()
        if seleccion:
            self.carrito.pop(int(seleccion[0]))
            self.refrescar()

    def guardar(self):
        self.f_fecha.sin_error()
        try:
            fecha = parse_fecha(self.f_fecha.valor())
        except ValueError as error:
            self.f_fecha.error(str(error))
            return
        if not self.carrito:
            self.f_producto.error("Agregue al menos un producto a la venta.")
            return
        items = [(p, c) for p, _, _, c in self.carrito]
        try:
            id_venta = ventas.guardar_venta(self.app.usuario[0], items, fecha)
        except Exception as error:
            messagebox.showerror("No se pudo guardar", str(error),
                                 parent=self.ventana)
            return
        messagebox.showinfo("Listo", f"Venta #{id_venta} guardada.",
                            parent=self.ventana)
        self.carrito.clear()
        self.refrescar()
        self.f_fecha.set(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.f_producto.sin_error()


# ---------------- Actualizar venta ----------------
class ActualizarVenta(PantallaFormulario):
    SECCION = "Ventas"
    TITULO = "ACTUALIZAR VENTA"
    CAMPOS = [
        ("id_venta", "ID de la venta", "Escriba el ID de la venta..."),
        ("fecha", "Nueva fecha de venta", "AAAA-MM-DD HH:MM"),
        ("id_producto", "ID del producto a modificar (opcional)",
         "Escriba el ID del producto..."),
        ("cantidad", "Nueva cantidad (opcional)", "Escriba la nueva cantidad..."),
    ]
    INSTRUCCIONES = [
        "Escriba el ID de la venta; se mostrará su fecha actual.",
        "Cambie la fecha si lo desea.",
        "Para corregir un producto, indique su ID y la nueva cantidad.",
        "Pulse Guardar. El total y el inventario se ajustan solos.",
    ]

    def al_construir(self):
        self.campos["id_venta"].enlazar("<FocusOut>", lambda e: self.cargar())

    def cargar(self):
        texto = self.campos["id_venta"].valor()
        if not texto.isdigit():
            return
        fila = ventas.obtener(int(texto))
        if not fila:
            self.campos["id_venta"].error("No existe una venta con ese ID.")
            return
        self.campos["id_venta"].sin_error()
        self.campos["fecha"].set(fecha_corta(fila[1]))

    def procesar(self, d):
        id_venta = entero(d, "id_venta")
        try:
            fecha = parse_fecha(d["fecha"]) if d["fecha"] else None
        except ValueError as error:
            raise ErrorCampo("fecha", str(error))
        id_producto = entero(d, "id_producto", opcional=True)
        cantidad = entero(d, "cantidad", opcional=True)
        if cantidad is not None and cantidad <= 0:
            raise ErrorCampo("cantidad", "Debe ser mayor a 0.")
        ventas.actualizar(id_venta, fecha, id_producto, cantidad)
        return f"La venta #{id_venta} se actualizó correctamente."


# ---------------- Consultar y eliminar ----------------
class ConsultarVenta(PantallaLista):
    SECCION = "Ventas"
    TITULO = "BUSCAR VENTA"
    ETIQUETA = "Si desea, escriba aquí"
    PLACEHOLDER = "Buscar por ID de venta o nombre del empleado..."

    def buscar(self, texto):
        return ventas.buscar(texto)

    def datos_fila(self, fila):
        id_v, fecha, empleado, total = fila
        return dict(
            clave=id_v, izq=f"ID: {id_v}",
            centro=(f"FECHA: {fecha_larga(fecha)}",
                    f"HORA: {hora(fecha)}  ·  EMPLEADO: {empleado}  ·  "
                    f"TOTAL: {dinero(total)}"))


class EliminarVenta(ConsultarVenta):
    TITULO = "ELIMINAR VENTA"
    ETIQUETA = "Buscar por ID de venta"
    MODO = "eliminar"
    CONFIRMAR = ("¿Eliminar esta venta?\n"
                 "El stock de sus productos se regresará al inventario.")

    def eliminar_registro(self, clave):
        ventas.eliminar(clave)
