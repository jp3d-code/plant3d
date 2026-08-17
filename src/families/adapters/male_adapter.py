"""
Adaptador de tubo a rosca macho NPT/RT Swagelok con conicidad NPT y anillo de tope.
Ver guía en guide/12-adaptadores-tubo/macho-npt-rt.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Adapters",
    TooltipShort="Adaptador macho",
    TooltipLong="Adaptador de espiga de tubo Swagelok a rosca macho NPT/RT",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total")
@param(D=LENGTH, TooltipShort="Diámetro exterior de la espiga de tubo")
@param(DX=LENGTH, TooltipShort="Diámetro exterior en el extremo roscado")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def MALE_ADAPTER(s, A=1.50, D=0.375, DX=0.50, E=0.17, **kw):
    Rtube = D / 2
    Rthread = DX / 2
    Rbore = E / 2
    halfA = A / 2

    # Cuerpo cónico de transición
    body = CONE(s, R1=Rtube, R2=Rthread, H=A, E=0.0)
    body.translate((0, 0, -halfA))

    # Anillo de tope central
    ring_height = A * 0.10
    ring = CYLINDER(s, R=max(Rtube, Rthread) + 0.04, H=ring_height)
    ring.translate((0, 0, -ring_height / 2))
    body.uniteWith(ring)
    ring.erase()

    # Perforación interna pasante
    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
