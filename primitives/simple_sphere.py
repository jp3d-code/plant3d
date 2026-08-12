"""
Esfera simple para Plant3D.
Dibuja una esfera solida con radio configurable.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *

@activate(
    Group="Primitives",
    TooltipShort="Simple Sphere",
    TooltipLong="A solid sphere with configurable radius",
    LengthUnit="in",
    Ports="1"
)
@group("MainDimensions")
@param(R=LENGTH, TooltipShort="Radius of the sphere")
def SIMPLE_SPHERE(s, R=2, **kw):
    sphere = SPHERE(s, R=R)
    s.setPoint((0, 0, 0), (0, 0, 1), 0)
    return s
