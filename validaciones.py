"""
Módulo de validaciones de entrada para el Sistema Punto de Venta (POS).
Autor: Evelyn Gurrola / Gael Celestino
Sprint 1 - Proyecto Integrador
"""


def validar_texto_no_vacio(texto: str, nombre_campo: str = "Campo") -> str:
    """
    Verifica que una cadena de texto no esté vacía ni contenga solo espacios.

    Args:
        texto (str): Cadena ingresada por el usuario en la interfaz.
        nombre_campo (str): Nombre descriptivo del campo para mensajes de error.

    Returns:
        str: Texto limpio sin espacios al inicio o al final.

    Raises:
        ValueError: Si el texto es None o queda vacío tras aplicar strip().
    """
    if texto is None or not str(texto).strip():
        raise ValueError(f"El campo '{nombre_campo}' es obligatorio.")
    return str(texto).strip()


def validar_precio_positivo(valor) -> float:
    """
    Valida que el precio ingresado sea un número mayor a cero.

    Args:
        valor (int | float | str): Precio unitario del producto.

    Returns:
        float: Precio convertido y redondeado a 2 decimales.

    Raises:
        ValueError: Si el valor no es numérico o es menor o igual a 0.
    """
    try:
        precio = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError("El precio debe ser un valor numérico válido.") from exc

    if precio <= 0:
        raise ValueError("El precio debe ser mayor a cero.")
    return round(precio, 2)


def validar_stock_entero(cantidad) -> int:
    """
    Verifica que el stock o cantidad ingresada sea un entero no negativo.

    Args:
        cantidad (int | str): Cantidad de unidades en inventario.

    Returns:
        int: Cantidad validada como entero.

    Raises:
        ValueError: Si la cantidad no es un entero válido o es negativa.
    """
    try:
        stock = int(cantidad)
    except (TypeError, ValueError) as exc:
        raise ValueError("La cantidad debe ser un número entero.") from exc

    if stock < 0:
        raise ValueError("La cantidad no puede ser negativa.")
    return stock