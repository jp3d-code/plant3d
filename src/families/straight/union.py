"""
Unión simple Swagelok.
Ver guía en guide/01-uniones/union.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Straight",
    TooltipShort="Unión simple",
    TooltipLong="Conecta dos tubos del mismo diámetro en línea recta",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Diámetro exterior del tubo")
@param(L=LENGTH, TooltipShort="Longitud total")
@param(T=LENGTH, TooltipShort="Espesor de pared")
def SIMPLE_UNION(s, OD=1, L=2, T=0.1, **kw):
    R = OD / 2
    union = CYLINDER(s, R=R, H=L)
    s.setPoint((0, 0, 0), (0, 0, -1), 0)
    s.setPoint((0, 0, L), (0, 0, 1), 0)
    return s
