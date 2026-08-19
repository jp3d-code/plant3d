"""
Conector hembra NPT Swagelok.
Ver guía en guide/03-conectores-hembra/npt.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="FemaleConnectors",
    TooltipShort="Conector hembra NPT",
    TooltipLong="Conector recto tubo Swagelok a rosca hembra NPT",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total centro a extremo")
@param(D=LENGTH, TooltipShort="Diámetro exterior del cuerpo")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
@param(F=LENGTH, TooltipShort="Ancho entre caras del hexágono")
def FEMALE_CONNECTOR(s, A=1.50, D=0.60, E=0.19, F=0.75, **kw):
    Rbody = D / 2
    Rhex = F / 2
    Rbore = E / 2
    halfA = A / 2

    body = CYLINDER(s, R=Rbody, H=A)
    body.translate((0, 0, -halfA))

    hex_head = CYLINDER(s, R=Rhex, H=A / 2)
    hex_head.translate((0, 0, -halfA))
    body.uniteWith(hex_head)

    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
