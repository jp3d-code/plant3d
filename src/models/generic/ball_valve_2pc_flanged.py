"""
Válvula de bola bridada de 2 piezas paramétrica genérica para AutoCAD Plant 3D.
"""
from varmain.primitiv import *
from varmain.var_basic import *
from varmain.custom import *
from math import *


@activate(
    Group="Valves",
    TooltipShort="Válvula de bola bridada 2-Piezas",
    TooltipLong="Válvula de bola bridada de 2 piezas paramétrica genérica",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(L=LENGTH, TooltipShort="Longitud cara a cara")
@param(D=LENGTH, TooltipShort="Diámetro exterior de la brida")
@param(H=LENGTH, TooltipShort="Altura del centro a la palanca")
@param(L1=LENGTH, TooltipShort="Longitud de la palanca de accionamiento")
@param(E=LENGTH, TooltipShort="Altura del centro al bonete ISO 5211")
@param(OD=LENGTH, TooltipShort="Diámetro nominal de paso de tubería")
def BALL_VALVE_2PC_FLANGED(s, L=4.25, D=3.50, H=3.74, L1=6.30, E=1.55, OD=0.50, **kw):
    halfL = float(L) / 2.0
    Rflange = float(D) / 2.0
    Rbore = float(OD) / 2.0

    flange_th = max(0.375, float(D) * 0.11)
    Rbody = max(float(D) * 0.32, float(OD) * 1.2)
    body = SPHERE(s, R=Rbody)

    Rneck = max(Rbody * 0.85, float(OD) * 0.9)
    cyl_len = max(0.1, float(L) - (2.0 * flange_th))
    main_cyl = CYLINDER(s, R=Rneck, H=cyl_len)
    main_cyl.translate((0, 0, -halfL + flange_th))
    body.uniteWith(main_cyl)

    flange1 = CYLINDER(s, R=Rflange, H=flange_th)
    flange1.translate((0, 0, -halfL))
    body.uniteWith(flange1)

    flange2 = CYLINDER(s, R=Rflange, H=flange_th)
    flange2.translate((0, 0, halfL - flange_th))
    body.uniteWith(flange2)

    Rstem = max(float(OD) * 0.35, 0.30)
    stem_h = max(0.5, float(H))
    stem = CYLINDER(s, R=Rstem, H=stem_h)
    stem.rotateY(90)
    body.uniteWith(stem)

    if float(L1) > 0:
        arm_len = float(L1)
        arm_w = max(0.30, float(OD) * 0.22)
        arm_th = 0.18
        lever = BOX(s, L=arm_th, W=arm_len, H=arm_w)
        lever.translate((stem_h, 0.0, -arm_len / 2.0))
        body.uniteWith(lever)

    bore = CYLINDER(s, R=Rbore, H=float(L) + 0.1)
    bore.translate((0, 0, -halfL - 0.05))
    body.subtractFrom(bore)


    s.setPoint((0, 0, halfL), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfL), (0, 0, -1), 0)

    return s
