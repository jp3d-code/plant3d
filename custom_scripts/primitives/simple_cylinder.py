"""
Cilindro simple para Plant3D.
Dibuja un cilindro solido con radio y altura configurables.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *

@activate(
    Group="Primitives",
    TooltipShort="Simple Cylinder",
    TooltipLong="A solid cylinder with configurable radius and height",
    LengthUnit="in"
)
@group("MainDimensions")
@param(R=LENGTH, TooltipShort="Radius of the cylinder")
@param(H=LENGTH, TooltipShort="Height of the cylinder")
def SIMPLE_CYLINDER(s, R=2, H=4, **kw):
    s = CYLINDER(s, R=R, H=H)
    return s
