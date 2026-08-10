"""
Caja simple para Plant3D.
Dibuja una caja solida con dimensiones configurables.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *

@activate(
    Group="Primitives",
    TooltipShort="Simple Box",
    TooltipLong="A solid box with configurable length, width and height",
    LengthUnit="in"
)
@group("MainDimensions")
@param(X=LENGTH, TooltipShort="Length (X axis)")
@param(Y=LENGTH, TooltipShort="Width (Y axis)")
@param(Z=LENGTH, TooltipShort="Height (Z axis)")
def SIMPLE_BOX(s, X=4, Y=4, Z=4, **kw):
    s = BOX(s, X=X, Y=Y, Z=Z)
    return s
