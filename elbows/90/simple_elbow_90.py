"""
Codo de 90 grados simple.
Conecta dos tubos en angulo de 90 grados.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *

@activate(
    Group="Elbows",
    TooltipShort="Simple 90 Elbow",
    TooltipLong="Connects two tubes at 90 degree angle",
    LengthUnit="in"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Outside diameter of tube")
@param(L=LENGTH, TooltipShort="Center to end dimension")
@param(T=LENGTH, TooltipShort="Wall thickness")
def SIMPLE_ELBOW_90(s, OD=1, L=2, T=0.1, **kw):
    R = OD / 2
    
    s = CYLINDER(s, R=R, H=L)
    
    return s
