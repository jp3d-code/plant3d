"""
Válvula de bola bridada accionada por volante/rueda giratoria para AutoCAD Plant 3D.
Gobernada por L y D (altura y volante proporcionales).
"""
from varmain.primitiv import *
from varmain.var_basic import *
from varmain.custom import *
from math import *


@activate(
    Group="Valves",
    TooltipShort="Válvula con volante giratorio",
    TooltipLong="Válvula de bola/globo bridada accionada por volante giratorio",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(L=LENGTH, TooltipShort="Longitud cara a cara")
@param(D=LENGTH, TooltipShort="Diámetro exterior de la brida")
@param(OD=LENGTH, TooltipShort="Diámetro nominal de paso de tubería")
def BALL_VALVE_HANDWHEEL(s, L=4.25, D=3.50, OD=0.50, **kw):
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
    main_cyl.erase()

    flange1 = CYLINDER(s, R=Rflange, H=flange_th)
    flange1.translate((0, 0, -halfL))
    body.uniteWith(flange1)
    flange1.erase()

    flange2 = CYLINDER(s, R=Rflange, H=flange_th)
    flange2.translate((0, 0, halfL - flange_th))
    body.uniteWith(flange2)
    flange2.erase()

    # Altura del vástago y diámetro del volante derivados proporcionalmente de D y OD
    Rstem = max(float(OD) * 0.30, 0.25)
    stem_h = max(float(D) * 0.85, float(OD) * 2.0, 2.0)
    stem = CYLINDER(s, R=Rstem, H=stem_h)
    stem.rotateY(90)
    body.uniteWith(stem)
    stem.erase()

    # Volante giratorio proporcional
    Rwheel = max(float(D) * 0.5, float(OD) * 1.5, 1.8)
    wheel_th = max(0.18, float(OD) * 0.12)
    wheel = TORUS(s, R1=Rwheel, R2=wheel_th)
    wheel.rotateY(90)
    wheel.translate((stem_h, 0, 0))
    body.uniteWith(wheel)
    wheel.erase()

    # Hub central del volante
    hub = CYLINDER(s, R=Rwheel * 0.25, H=0.3)
    hub.rotateY(90)
    hub.translate((stem_h, 0, 0))
    body.uniteWith(hub)
    hub.erase()

    bore = CYLINDER(s, R=Rbore, H=float(L) + 0.1)
    bore.translate((0, 0, -halfL - 0.05))
    body.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, halfL), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfL), (0, 0, -1), 0)

    return s
