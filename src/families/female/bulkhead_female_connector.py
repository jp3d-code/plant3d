"""
Conector hembra NPT pasamuros Swagelok.
Ver guía en guide/03-conectores-hembra/npt-pasamuros.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="FemaleConnectors",
    TooltipShort="Conector hembra NPT pasamuros",
    TooltipLong="Conector hembra NPT para atravesar paneles con tuerca pasamuros",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total centro a extremo")
@param(D=LENGTH, TooltipShort="Diámetro exterior del cuerpo")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
@param(F=LENGTH, TooltipShort="Ancho entre caras del hexágono")
@param(NL=LENGTH, TooltipShort="Longitud de la tuerca pasamuros")
def BULKHEAD_FEMALE_CONNECTOR(s, A=2.20, D=0.60, E=0.19, F=0.75, NL=0.30, **kw):
    Rbody = D / 2
    Rnut = F / 2
    Rbore = E / 2
    halfA = A / 2

    body = CYLINDER(s, R=Rbody, H=A)
    body.translate((0, 0, -halfA))

    nut = CYLINDER(s, R=Rnut, H=NL)
    nut.translate((0, 0, -NL / 2))
    body.uniteWith(nut)

    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
