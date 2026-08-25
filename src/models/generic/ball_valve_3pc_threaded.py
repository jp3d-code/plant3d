"""
Válvula de bola roscada / SW de 3 piezas paramétrica genérica para AutoCAD Plant 3D.
"""
from varmain.primitiv import *
from varmain.var_basic import *
from varmain.custom import *
from math import *


@activate(
    Group="Valves",
    TooltipShort="Válvula de bola 3-Piezas roscada",
    TooltipLong="Válvula de bola de 3 piezas roscada/SW paramétrica genérica",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(L=LENGTH, TooltipShort="Longitud total cara a cara")
@param(H=LENGTH, TooltipShort="Altura del centro a la palanca")
@param(L1=LENGTH, TooltipShort="Longitud de la palanca de accionamiento")
@param(OD=LENGTH, TooltipShort="Diámetro nominal de paso de tubería")
def BALL_VALVE_3PC_THREADED(s, L=2.80, H=2.50, L1=4.50, OD=0.50, **kw):
    halfL = float(L) / 2.0
    Rbore = float(OD) / 2.0

    Rbody = max(float(OD) * 1.5, 0.75)
    body = CYLINDER(s, R=Rbody, H=float(L))
    body.translate((0, 0, -halfL))

    # Bloque hexagonal/octogonal central de 3 piezas
    block_size = Rbody * 2.1
    center_block = BOX(s, L=block_size, W=block_size, H=float(L) * 0.5)
    center_block.translate((-block_size / 2.0, -block_size / 2.0, -float(L) * 0.25))
    body.uniteWith(center_block)

    Rstem = max(float(OD) * 0.35, 0.25)
    stem_h = max(0.5, float(H))
    stem = CYLINDER(s, R=Rstem, H=stem_h)
    stem.rotateY(90)
    body.uniteWith(stem)

    if float(L1) > 0:
        arm_len = float(L1)
        arm_w = max(0.25, float(OD) * 0.20)
        arm_th = 0.15
        lever = BOX(s, L=arm_th, W=arm_len, H=arm_w)
        lever.translate((stem_h, 0.0, -arm_len / 2.0))
        body.uniteWith(lever)

    bore = CYLINDER(s, R=Rbore, H=float(L) + 0.1)
    bore.translate((0, 0, -halfL - 0.05))
    body.subtractFrom(bore)

    s.setPoint((0, 0, halfL), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfL), (0, 0, -1), 0)

    return s
