"""
Reductor Swagelok.
Ver guía en guide/04-reductores/reductor.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Straight",
    TooltipShort="Reductor",
    TooltipLong="Conecta dos tubos de diferente diámetro en línea recta con férulas preensambladas",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total")
@param(D=LENGTH, TooltipShort="Diámetro exterior en el extremo mayor")
@param(DX=LENGTH, TooltipShort="Diámetro exterior en el extremo menor")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def REDUCER(s, A=1.54, D=0.60, DX=0.50, E=0.17, **kw):
    R1 = D / 2
    R2 = DX / 2
    Rbore = E / 2
    halfA = A / 2

    upper = CYLINDER(s, R=R1, H=halfA)

    lower = CYLINDER(s, R=R2, H=halfA)
    lower.translate((0, 0, -halfA))
    upper.uniteWith(lower)
    lower.erase()

    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    upper.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
