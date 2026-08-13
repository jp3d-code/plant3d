"""
Tapón para tubo Swagelok.
Ver guía en guide/06-tapones/tapon-tubo.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Plugs",
    TooltipShort="Tapón para tubo",
    TooltipLong="Tapa el extremo de un tubo con conexión de férula Swagelok",
    LengthUnit="in",
    Ports="1"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total")
@param(D=LENGTH, TooltipShort="Diámetro exterior del cuerpo")
def TUBE_CAP(s, A=0.92, D=0.60, **kw):
    Rbody = D / 2
    body = CYLINDER(s, R=Rbody, H=A)
    s.setPoint((0, 0, 0), (0, 0, -1), 0)
    return s
