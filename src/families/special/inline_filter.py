"""
Filtro en línea para atrapamiento de partículas Serie F Swagelok.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Special",
    TooltipShort="Filtro en línea Serie F",
    TooltipLong="Filtro en línea para retención de partículas con cuerpo ensanchado de elemento filtrante",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total")
@param(D=LENGTH, TooltipShort="Diámetro exterior del racor tubo")
@param(F=LENGTH, TooltipShort="Ancho del cuerpo del filtro")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def INLINE_FILTER(s, A=2.15, D=0.60, F=0.75, E=0.19, **kw):
    Rbody = D / 2
    Rfilter = F / 2
    Rbore = E / 2
    halfA = A / 2
    filter_len = A * 0.55

    # Cuerpo del tubo
    body = CYLINDER(s, R=Rbody, H=A)
    body.translate((0, 0, -halfA))

    # Cuerpo central ensanchado del elemento filtrante
    filter_body = CYLINDER(s, R=Rfilter, H=filter_len)
    filter_body.translate((0, 0, -filter_len / 2))
    body.uniteWith(filter_body)
    filter_body.erase()

    # Perforación pasante interior
    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
