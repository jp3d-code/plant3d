"""
Union simple para tubo.
Conecta dos tubos del mismo diametro en linea recta.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *

@activate(
    Group="Straight",
    TooltipShort="Simple Union",
    TooltipLong="Connects two tubes of the same diameter in a straight line",
    LengthUnit="in"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Outside diameter of tube")
@param(L=LENGTH, TooltipShort="Total length of fitting")
@param(T=LENGTH, TooltipShort="Wall thickness")
def SIMPLE_UNION(s, OD=1, L=2, T=0.1, **kw):
    R = OD / 2
    
    s = CYLINDER(s, R=R, H=L)
    
    return s
