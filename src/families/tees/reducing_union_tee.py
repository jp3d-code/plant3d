"""
Te reductora tubo-tubo-tubo Swagelok con bloque central de forja.
Ver guía en guide/09-tes/tes-adaptadoras.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Tees",
    TooltipShort="Te reductora",
    TooltipLong="Conecta tubos de diferente diámetro en configuración de Te con cuerpo central de forja",
    LengthUnit="in",
    Ports="3"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Diámetro exterior del tubo principal")
@param(DX=LENGTH, TooltipShort="Diámetro exterior del tubo en la derivación")
@param(L=LENGTH, TooltipShort="Longitud del tramo principal")
@param(H=LENGTH, TooltipShort="Altura de la derivación")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def REDUCING_UNION_TEE(s, OD=0.5, DX=0.375, L=1.8, H=0.9, E=0.17, **kw):
    Rmain = OD / 2
    Rbranch = DX / 2

    # Cuerpo principal en Z
    main = CYLINDER(s, R=Rmain, H=L)
    main.translate((0, 0, -L / 2))

    # Bloque cúbico central de forja
    block_size = max(OD, DX) * 1.3
    center_block = BOX(s, L=block_size, W=block_size, H=block_size)
    center_block.translate((-block_size / 2, -block_size / 2, -block_size / 2))
    main.uniteWith(center_block)
    center_block.erase()

    # Derivación a 90° en X
    branch = CYLINDER(s, R=Rbranch, H=H)
    branch.rotateY(90)
    main.uniteWith(branch)
    branch.erase()

    s.setPoint((0, 0, -L / 2), (0, 0, -1), 0)
    s.setPoint((0, 0, L / 2), (0, 0, 1), 0)
    s.setPoint((H, 0, 0), (1, 0, 0), 0)

    return s
