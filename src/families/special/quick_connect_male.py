"""
Vástago acople rápido macho Serie QC Swagelok.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Special",
    TooltipShort="Acople rápido vástago QC",
    TooltipLong="Vástago acople rápido macho Serie QC con valona de inserción rápida",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total")
@param(D=LENGTH, TooltipShort="Diámetro exterior del cuerpo tubo")
@param(F=LENGTH, TooltipShort="Diámetro del vástago de inserción")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def QUICK_CONNECT_MALE(s, A=1.80, D=0.50, F=0.625, E=0.19, **kw):
    Rbody = D / 2
    Rstem = F / 2
    Rbore = E / 2
    halfA = A / 2
    stem_len = A * 0.45

    # Cuerpo principal tubo en P1 (halfA)
    body = CYLINDER(s, R=Rbody, H=A)
    body.translate((0, 0, -halfA))

    # Vástago de inserción rápida QC en P2 (-halfA)
    stem = CYLINDER(s, R=Rstem, H=stem_len)
    stem.translate((0, 0, -halfA))
    body.uniteWith(stem)
    stem.erase()

    # Valona / Anillo de retención
    ring = CYLINDER(s, R=Rstem + 0.05, H=A * 0.08)
    ring.translate((0, 0, -halfA + stem_len * 0.7))
    body.uniteWith(ring)
    ring.erase()

    # Perforación pasante interior
    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
