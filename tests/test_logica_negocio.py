import pytest


def calcular_subtotal(precio: float, cantidad: int) -> float:
    """Calcula el subtotal de una línea de producto."""
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a cero")
    return round(precio * cantidad, 2)


def validar_stock(stock_actual: int, cantidad_solicitada: int) -> bool:
    """Verifica si existe inventario suficiente para cubrir la venta."""
    return 0 < cantidad_solicitada <= stock_actual


def calcular_total_con_iva(subtotal: float, tasa_iva: float = 0.16) -> float:
    """Calcula el total neto aplicando el porcentaje de IVA."""
    return round(subtotal * (1 + tasa_iva), 2)


def test_pu01_calculo_subtotal():
    """PU-01: Verifica el cálculo exacto de precio por cantidad."""
    assert calcular_subtotal(25.50, 4) == 102.00


def test_pu02_validacion_stock_insuficiente():
    """PU-02: Verifica que rechace ventas mayores al inventario disponible."""
    assert validar_stock(stock_actual=5, cantidad_solicitada=8) is False
    assert validar_stock(stock_actual=5, cantidad_solicitada=3) is True


def test_pu03_total_venta_con_iva():
    """PU-03: Verifica el cálculo final de la venta con 16% de IVA."""
    assert calcular_total_con_iva(200.00) == 232.00