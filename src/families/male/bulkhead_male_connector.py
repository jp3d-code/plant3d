"""
Conector macho NPT pasamuros Swagelok con conicidad NPT.
Ver guía en guide/02-conectores-macho/npt-pasamuros.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="MaleConnectors",
    TooltipShort="Conector macho NPT pasamuros",
    TooltipLong="Conector macho NPT para atravesar paneles con tuerca pasamuros y rosca NPT",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total centro a extremo")
@param(D=LENGTH, TooltipShort="Diámetro exterior del cuerpo")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
@param(F=LENGTH, TooltipShort="Ancho entre caras del hexágono")
@param(NL=LENGTH, TooltipShort="Longitud de la tuerca pasamuros")
def BULKHEAD_MALE_CONNECTOR(s, A=2.17, D=0.60, E=0.19, F=0.625, NL=0.30, **kw):
    Rbody = D / 2
    Rnut = F / 2
    Rbore = E / 2
    halfA = A / 2
    thread_len = A * 0.35

    # Cuerpo principal
    body = CYLINDER(s, R=Rbody, H=A)
    body.translate((0, 0, -halfA))

    # Tuerca pasamuros
    nut = CYLINDER(s, R=Rnut, H=NL)
    nut.translate((0, 0, -NL / 2))
    body.uniteWith(nut)

    # Conicidad NPT en extremo macho (-halfA)
    thread = CONE(s, R1=Rbody * 0.92, R2=Rbody * 1.05, H=thread_len, E=0.0)
    thread.translate((0, 0, -halfA))
    body.uniteWith(thread)

    # Perforación interna pasante
    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
