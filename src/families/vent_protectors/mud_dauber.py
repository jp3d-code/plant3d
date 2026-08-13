"""
Protector de venteo Mud Dauber Swagelok.
Ver guía en guide/06-tapones/protector-venteo.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="VentProtectors",
    TooltipShort="Protector de venteo",
    TooltipLong="Protector de malla metálica Mud Dauber para extremos de venteo (rosca NPT)",
    LengthUnit="in",
    Ports="1"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total")
@param(E=LENGTH, TooltipShort="Diámetro de paso interior")
@param(F=LENGTH, TooltipShort="Ancho entre caras del hexágono")
def VENT_PROTECTOR(s, A=0.78, E=0.28, F=0.5625, **kw):
    Rhex = F / 2
    Rbore = E / 2

    body = CYLINDER(s, R=Rhex, H=A)
    bore = CYLINDER(s, R=Rbore, H=A)
    body.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, 0), (0, 0, -1), 0)
    return s
