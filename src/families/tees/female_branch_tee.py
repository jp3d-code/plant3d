"""
Te con rosca hembra NPT en el ramal (TTF) Swagelok con bloque central de forja.
Ver guía en guide/09-tes/hembra-lateral-ttf.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Tees",
    TooltipShort="Te hembra en ramal TTF",
    TooltipLong="Te con paso recto tubo-tubo y ramal a 90 grados rosca hembra NPT",
    LengthUnit="in",
    Ports="3"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Diámetro exterior del tubo")
@param(L=LENGTH, TooltipShort="Longitud del tramo principal")
@param(H=LENGTH, TooltipShort="Altura de la derivación hembra")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def FEMALE_BRANCH_TEE(s, OD=0.5, L=1.8, H=0.9, E=0.17, **kw):
    R = OD / 2

    # Cuerpo principal en Z
    main = CYLINDER(s, R=R, H=L)
    main.translate((0, 0, -L / 2))

    # Bloque cúbico central de forja
    block_size = OD * 1.3
    center_block = BOX(s, L=block_size, W=block_size, H=block_size)
    center_block.translate((-block_size / 2, -block_size / 2, -block_size / 2))
    main.uniteWith(center_block)

    # Derivación a 90° en X
    branch = CYLINDER(s, R=R, H=H)
    branch.rotateY(90)
    main.uniteWith(branch)

    s.setPoint((0, 0, -L / 2), (0, 0, -1), 0)
    s.setPoint((0, 0, L / 2), (0, 0, 1), 0)
    s.setPoint((H, 0, 0), (1, 0, 0), 0)

    return s
