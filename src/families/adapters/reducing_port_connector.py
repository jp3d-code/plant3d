"""
Conector manguito reductor de puerto Swagelok con anillo de tope central.
Ver guía en guide/05-tubos-manguito/tubo-manguito-conector-reductor.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Adapters",
    TooltipShort="Conector de puerto reductor",
    TooltipLong="Manguito conector reductor con anillo de tope central entre dos diámetros",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total")
@param(D=LENGTH, TooltipShort="Diámetro exterior del extremo mayor")
@param(DX=LENGTH, TooltipShort="Diámetro exterior del extremo menor")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def REDUCING_PORT_CONNECTOR(s, A=1.35, D=0.50, DX=0.375, E=0.17, **kw):
    R1 = D / 2
    R2 = DX / 2
    Rbore = E / 2
    halfA = A / 2

    # Cuerpo cónico reductor
    body = CONE(s, R1=R1, R2=R2, H=A, E=0.0)
    body.translate((0, 0, -halfA))

    # Anillo de tope central
    ring_height = A * 0.10
    ring = CYLINDER(s, R=R1 + 0.05, H=ring_height)
    ring.translate((0, 0, -ring_height / 2))
    body.uniteWith(ring)
    ring.erase()

    # Perforación interna pasante
    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
