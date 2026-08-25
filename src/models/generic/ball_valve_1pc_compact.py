"""
Válvula de bola compacta roscada de 1 pieza paramétrica genérica para AutoCAD Plant 3D.
"""
from varmain.primitiv import *
from varmain.var_basic import *
from varmain.custom import *
from math import *


@activate(
    Group="Valves",
    TooltipShort="Válvula de bola 1-Pieza compacta",
    TooltipLong="Válvula de bola monolítica de 1 pieza compacta roscada",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(L=LENGTH, TooltipShort="Longitud total cara a cara")
@param(H=LENGTH, TooltipShort="Altura del centro a la palanca")
@param(L1=LENGTH, TooltipShort="Longitud de la palanca de accionamiento")
@param(OD=LENGTH, TooltipShort="Diámetro nominal de paso de tubería")
def BALL_VALVE_1PC_COMPACT(s, L=2.20, H=2.20, L1=4.00, OD=0.50, **kw):
    halfL = float(L) / 2.0
    Rbore = float(OD) / 2.0

    Rbody = max(float(OD) * 1.4, 0.65)
    body = CYLINDER(s, R=Rbody, H=float(L))
    body.translate((0, 0, -halfL))

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
