"""
Conector manguito de puerto Swagelok con anillo de tope central.
Ver guía en guide/05-tubos-manguito/tubo-manguito-conector.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Adapters",
    TooltipShort="Conector de puerto",
    TooltipLong="Manguito conector con anillo de tope central para unir dos racores Swagelok",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total")
@param(D=LENGTH, TooltipShort="Diámetro exterior del manguito")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def PORT_CONNECTOR(s, A=1.15, D=0.375, E=0.17, **kw):
    Rbody = D / 2
    Rbore = E / 2
    halfA = A / 2

    # Cuerpo principal
    body = CYLINDER(s, R=Rbody, H=A)
    body.translate((0, 0, -halfA))

    # Anillo de tope central (Stop Ring)
    ring_height = A * 0.12
    ring = CYLINDER(s, R=Rbody + 0.05, H=ring_height)
    ring.translate((0, 0, -ring_height / 2))
    body.uniteWith(ring)

    # Perforación interna pasante
    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
