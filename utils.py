"""
Funciones utilitarias comunes para scripts de Plant3D.
"""

# Constantes de unidad
LENGTH = "LENGTH"
ANGLE = "ANGLE"
BOOLEAN = "BOOLEAN"


def validate_positive(value, name="value"):
    """Valida que un valor sea mayor que 0."""
    if value <= 0:
        raise ValueError(f"{name} debe ser mayor que 0, recibido: {value}")
    return value


def validate_non_negative(value, name="value"):
    """Valida que un valor sea mayor o igual que 0."""
    if value < 0:
        raise ValueError(f"{name} debe ser mayor o igual que 0, recibido: {value}")
    return value


def calculate_wall_thickness(od, thickness, min_factor=0.05):
    """Calcula el espesor de pared con valor por defecto."""
    if thickness <= 0:
        return od * min_factor
    return thickness


def inches_to_mm(inches):
    """Convierte pulgadas a milimetros."""
    return inches * 25.4


def mm_to_inches(mm):
    """Convierte milimetros a pulgadas."""
    return mm / 25.4
