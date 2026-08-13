"""
Tapón para racor Swagelok.
Ver guía en guide/06-tapones/tapon-racor.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Plugs",
    TooltipShort="Tapón para racor",
    TooltipLong="Tapón roscado que se atornilla en el cuerpo de un racor Swagelok",
    LengthUnit="in",
    Ports="1"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total")
@param(D=LENGTH, TooltipShort="Diámetro exterior del cuerpo")
def FITTING_PLUG(s, A=0.75, D=0.50, **kw):
    Rbody = D / 2
    body = CYLINDER(s, R=Rbody, H=A)
    s.setPoint((0, 0, 0), (0, 0, -1), 0)
    return s
