"""
Conector macho NPT Swagelok con conicidad de rosca NPT.
Ver guía en guide/02-conectores-macho/npt.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="MaleConnectors",
    TooltipShort="Conector macho NPT",
    TooltipLong="Conector recto tubo Swagelok a rosca macho NPT con conicidad real",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total centro a extremo")
@param(D=LENGTH, TooltipShort="Diámetro exterior del cuerpo")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
@param(F=LENGTH, TooltipShort="Ancho entre caras del hexágono")
def MALE_CONNECTOR(s, A=1.49, D=0.60, E=0.19, F=0.5625, **kw):
    Rbody = D / 2
    Rnut = F / 2
    Rbore = E / 2
    halfA = A / 2
    thread_len = A * 0.45

    # Cuerpo principal tubo
    body = CYLINDER(s, R=Rbody, H=A)
    body.translate((0, 0, -halfA))

    # Tuerca / Hexágono central
    nut = CYLINDER(s, R=Rnut, H=A * 0.3)
    nut.translate((0, 0, -A * 0.15))
    body.uniteWith(nut)
    nut.erase()

    # Conicidad de rosca NPT en extremo P2 (-halfA)
    thread = CONE(s, R1=Rbody * 0.92, R2=Rbody * 1.05, H=thread_len, E=0.0)
    thread.translate((0, 0, -halfA))
    body.uniteWith(thread)
    thread.erase()

    # Perforación interna pasante
    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
