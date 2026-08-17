"""
Cuerpo acople rápido hembra con casquillo exterior Serie QC Swagelok.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Special",
    TooltipShort="Acople rápido cuerpo QC",
    TooltipLong="Cuerpo acople rápido hembra con casquillo exterior de desacople retráctil Serie QC",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total")
@param(D=LENGTH, TooltipShort="Diámetro exterior del cuerpo tubo")
@param(F=LENGTH, TooltipShort="Diámetro del casquillo de desacople")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def QUICK_CONNECT_FEMALE(s, A=2.10, D=0.50, F=0.875, E=0.19, **kw):
    Rbody = D / 2
    Rsleeve = F / 2
    Rbore = E / 2
    halfA = A / 2
    sleeve_len = A * 0.50

    # Cuerpo tubo principal en P1 (halfA)
    body = CYLINDER(s, R=Rbody, H=A)
    body.translate((0, 0, -halfA))

    # Casquillo móvil retráctil QC en P2 (-halfA)
    sleeve = CYLINDER(s, R=Rsleeve, H=sleeve_len)
    sleeve.translate((0, 0, -halfA))
    body.uniteWith(sleeve)
    sleeve.erase()

    # Perforación pasante interior
    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
