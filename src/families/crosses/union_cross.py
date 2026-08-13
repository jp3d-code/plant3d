"""
Cruz unión Swagelok.
Ver guía en guide/10-cruces/union.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Crosses",
    TooltipShort="Cruz unión",
    TooltipLong="Cruz con cuatro extremos tubo del mismo diámetro",
    LengthUnit="in",
    Ports="4"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Dimensión del centro al extremo")
@param(D=LENGTH, TooltipShort="Diámetro exterior del cuerpo")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def UNION_CROSS(s, A=2.12, D=0.60, E=0.19, **kw):
    Rbody = D / 2
    Rbore = E / 2
    totalLen = A * 2

    main = CYLINDER(s, R=Rbody, H=totalLen)
    main.translate((0, 0, -A))

    branch = CYLINDER(s, R=Rbody, H=totalLen)
    branch.translate((0, 0, -A))
    branch.rotateY(90)
    main.uniteWith(branch)
    branch.erase()

    boreZ = CYLINDER(s, R=Rbore, H=totalLen)
    boreZ.translate((0, 0, -A))
    main.subtractFrom(boreZ)
    boreZ.erase()

    boreX = CYLINDER(s, R=Rbore, H=totalLen)
    boreX.translate((0, 0, -A))
    boreX.rotateY(90)
    main.subtractFrom(boreX)
    boreX.erase()

    s.setPoint((0, 0, -A), (0, 0, -1), 0)
    s.setPoint((0, 0, A), (0, 0, 1), 0)
    s.setPoint((A, 0, 0), (1, 0, 0), 0)
    s.setPoint((-A, 0, 0), (-1, 0, 0), 0)

    return s
