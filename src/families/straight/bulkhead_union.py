"""
Unión pasamuros Swagelok.
Ver guía en guide/01-uniones/union-pasamuros.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Straight",
    TooltipShort="Unión pasamuros",
    TooltipLong="Unión para atravesar paneles con tuerca pasamuros",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Dimensión del centro al extremo")
@param(D=LENGTH, TooltipShort="Diámetro exterior del cuerpo")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
@param(F=LENGTH, TooltipShort="Ancho entre caras de la tuerca pasamuros")
@param(NL=LENGTH, TooltipShort="Longitud de la tuerca pasamuros")
def BULKHEAD_UNION(s, A=2.27, D=0.60, E=0.19, F=0.625, NL=0.30, **kw):
    Rbody = D / 2
    Rnut = F / 2
    Rbore = E / 2
    totalLen = A * 2

    body = CYLINDER(s, R=Rbody, H=totalLen)
    body.translate((0, 0, -A))

    nut = CYLINDER(s, R=Rnut, H=NL)
    nut.translate((0, 0, -NL / 2))
    body.uniteWith(nut)

    bore = CYLINDER(s, R=Rbore, H=totalLen)
    bore.translate((0, 0, -A))
    body.subtractFrom(bore)

    s.setPoint((0, 0, -A), (0, 0, -1), 0)
    s.setPoint((0, 0, A), (0, 0, 1), 0)

    return s
