"""
Union simple para tubo con puertos.
Conecta dos tubos del mismo diametro en linea recta.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *

@activate(
    Group="Straight",
    TooltipShort="Simple Union",
    TooltipLong="Connects two tubes of the same diameter in a straight line",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Outside diameter of tube")
@param(L=LENGTH, TooltipShort="Total length of fitting")
@param(T=LENGTH, TooltipShort="Wall thickness")
def SIMPLE_UNION(s, OD=1, L=2, T=0.1, **kw):
    R = OD / 2

    union = CYLINDER(s, R=R, H=L)

    # Puerto 1 (Entrada)
    s.setPoint((0, 0, 0), (0, 0, -1), 0)

    # Puerto 2 (Salida)
    s.setPoint((0, 0, L), (0, 0, 1), 0)

    return s
