"""
Válvula de bola compacta roscada de 1 pieza paramétrica genérica para AutoCAD Plant 3D.
Gobernada por L y D (altura y palanca proporcionales).
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
@param(D=LENGTH, TooltipShort="Diámetro exterior del cuerpo")
@param(OD=LENGTH, TooltipShort="Diámetro nominal de paso de tubería")
def BALL_VALVE_1PC_COMPACT(s, L=2.20, D=1.50, OD=0.50, **kw):
    halfL = float(L) / 2.0
    Rbore = float(OD) / 2.0
    Rbody = max(float(D) / 2.0, float(OD) * 1.2) if float(D) > 0 else float(OD) * 1.4

    body = CYLINDER(s, R=Rbody, H=float(L))
    body.translate((0, 0, -halfL))

    # Altura del cuello y largo de palanca derivados proporcionalmente de D y OD
    Rstem = max(float(OD) * 0.35, 0.25)
    stem_h = max(float(D) * 0.8, float(OD) * 1.8, 1.5)
    stem = CYLINDER(s, R=Rstem, H=stem_h)
    stem.rotateY(90)
    body.uniteWith(stem)
    stem.erase()

    arm_len = max(float(L) * 1.2, float(OD) * 3.5, 3.0)
    arm_w = max(0.25, float(OD) * 0.20)
    arm_th = 0.15
    lever = BOX(s, L=arm_th, W=arm_len, H=arm_w)
    lever.translate((stem_h, 0.0, -arm_len / 2.0))
    body.uniteWith(lever)
    lever.erase()

    bore = CYLINDER(s, R=Rbore, H=float(L) + 0.1)
    bore.translate((0, 0, -halfL - 0.05))
    body.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, halfL), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfL), (0, 0, -1), 0)

    return s
