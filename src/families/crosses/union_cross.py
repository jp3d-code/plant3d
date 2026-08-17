"""
Cruz unión Swagelok con bloque central de forja.
Ver guía en guide/10-cruces/union.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Crosses",
    TooltipShort="Cruz unión",
    TooltipLong="Cruz con cuatro extremos tubo del mismo diámetro y bloque central de forja",
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

    # Tramo principal en Z
    main = CYLINDER(s, R=Rbody, H=totalLen)
    main.translate((0, 0, -A))

    # Bloque cúbico central de forja
    block_size = D * 1.3
    center_block = BOX(s, L=block_size, W=block_size, H=block_size)
    center_block.translate((-block_size / 2, -block_size / 2, -block_size / 2))
    main.uniteWith(center_block)
    center_block.erase()

    # Tramo transversal en X
    branch = CYLINDER(s, R=Rbody, H=totalLen)
    branch.translate((0, 0, -A))
    branch.rotateY(90)
    main.uniteWith(branch)
    branch.erase()

    # Perforaciones internas pasantes
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
