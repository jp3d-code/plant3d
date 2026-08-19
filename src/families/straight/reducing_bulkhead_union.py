"""
Unión reductora pasamuros Swagelok.
Ver guía en guide/01-uniones/union-reductora-pasamuros.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Straight",
    TooltipShort="Unión reductora pasamuros",
    TooltipLong="Unión para atravesar paneles conectando tubos de diferente diámetro",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Dimensión del centro al extremo")
@param(D=LENGTH, TooltipShort="Diámetro exterior en el extremo mayor")
@param(DX=LENGTH, TooltipShort="Diámetro exterior en el extremo menor")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
@param(F=LENGTH, TooltipShort="Ancho entre caras de la tuerca pasamuros")
@param(NL=LENGTH, TooltipShort="Longitud de la tuerca pasamuros")
def REDUCING_BULKHEAD_UNION(s, A=2.17, D=0.60, DX=0.50, E=0.09, F=0.625, NL=0.30, **kw):
    R1 = D / 2
    R2 = DX / 2
    Rnut = F / 2
    Rbore = E / 2

    body = CONE(s, R1=R1, R2=R2, H=A * 2, E=0.0)
    body.translate((0, 0, -A))

    nut = CYLINDER(s, R=Rnut, H=NL)
    nut.translate((0, 0, -NL / 2))
    body.uniteWith(nut)

    bore = CYLINDER(s, R=Rbore, H=A * 2)
    bore.translate((0, 0, -A))
    body.subtractFrom(bore)

    s.setPoint((0, 0, A), (0, 0, 1), 0)
    s.setPoint((0, 0, -A), (0, 0, -1), 0)

    return s
