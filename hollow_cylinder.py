"""
Cilindro hueco (tubo) para Plant3D.
Dibuja un cilindro hueco con radio exterior, interior y altura.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *

@activate(
    Group="Primitives",
    TooltipShort="Hollow Cylinder",
    TooltipLong="A hollow cylinder (tube) with outer radius, inner radius and height",
    LengthUnit="in"
)
@group("MainDimensions")
@param(RO=LENGTH, TooltipShort="Outer radius")
@param(RI=LENGTH, TooltipShort="Inner radius")
@param(H=LENGTH, TooltipShort="Height")
def HOLLOW_CYLINDER(s, RO=3, RI=2, H=4, **kw):
    if RI >= RO:
        raise ValueError("Inner radius must be less than outer radius")
    
    s = CYLINDER(s, R=RO, H=H)
    hole = CYLINDER(s, R=RI, H=H)
    s.cut(hole)
    hole.erase()
    s.setPoint((0, 0, 0))
    s.setVector((0, 0, 1))
    return s
