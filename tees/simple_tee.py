"""
T simple.
Conecta tres tubos en configuracion de T.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *

@activate(
    Group="Tees",
    TooltipShort="Simple Tee",
    TooltipLong="Connects three tubes in T configuration",
    LengthUnit="in"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Outside diameter of tube")
@param(L=LENGTH, TooltipShort="Center to end dimension")
@param(T=LENGTH, TooltipShort="Wall thickness")
def SIMPLE_TEE(s, OD=1, L=2, T=0.1, **kw):
    R = OD / 2
    
    s = CYLINDER(s, R=R, H=L)
    
    return s
