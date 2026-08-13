"""
Unión reductora Swagelok.
Ver guía en guide/01-uniones/union-reductora.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Straight",
    TooltipShort="Unión reductora",
    TooltipLong="Conecta dos tubos de diferente diámetro en línea recta",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Dimensión del centro al extremo")
@param(D=LENGTH, TooltipShort="Diámetro exterior en el extremo mayor")
@param(DX=LENGTH, TooltipShort="Diámetro exterior en el extremo menor")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def REDUCING_UNION(s, A=1.52, D=0.60, DX=0.50, E=0.09, **kw):
    R1 = D / 2
    R2 = DX / 2
    Rbore = E / 2

    body = CONE(s, R1=R1, R2=R2, H=A * 2, E=0.0)
    body.translate((0, 0, -A))

    bore = CYLINDER(s, R=Rbore, H=A * 2)
    bore.translate((0, 0, -A))
    body.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, A), (0, 0, 1), 0)
    s.setPoint((0, 0, -A), (0, 0, -1), 0)

    return s
