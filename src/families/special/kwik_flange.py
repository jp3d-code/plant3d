"""
Racor con brida sanitaria Kwik-Clamp (Tri-Clamp) a tubo Swagelok.
Ver guía en guide/11-aplicaciones-especiales/brida-kwik.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Special",
    TooltipShort="Brida Kwik",
    TooltipLong="Racor con brida sanitaria Tri-Clamp en un extremo y tubo Swagelok en el otro",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total centro a extremo")
@param(B=LENGTH, TooltipShort="Longitud del cuello de la brida")
@param(C=LENGTH, TooltipShort="Diámetro exterior del cuerpo tubo")
@param(G=LENGTH, TooltipShort="Diámetro exterior del plato de la brida")
@param(F=LENGTH, TooltipShort="Ancho entre caras del hexágono")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def KWIK_FLANGE(s, A=1.57, B=0.37, C=0.60, G=0.98, F=0.8125, E=0.19, **kw):
    Rbody = C / 2
    Rflange = G / 2
    Rhex = F / 2
    Rbore = E / 2
    halfA = A / 2

    # Cuerpo principal tubo en P1 (halfA)
    body = CYLINDER(s, R=Rbody, H=A)
    body.translate((0, 0, -halfA))

    # Tuerca central
    hex_nut = CYLINDER(s, R=Rhex, H=A * 0.25)
    hex_nut.translate((0, 0, -A * 0.125))
    body.uniteWith(hex_nut)
    hex_nut.erase()

    # Plato de la brida sanitaria Kwik en P2 (-halfA)
    flange = CYLINDER(s, R=Rflange, H=B)
    flange.translate((0, 0, -halfA))
    body.uniteWith(flange)
    flange.erase()

    # Perforación interna pasante
    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
