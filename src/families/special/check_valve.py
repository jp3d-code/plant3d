"""
Válvula de retención antirretorno Serie CH/CO Swagelok.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Special",
    TooltipShort="Válvula de retención",
    TooltipLong="Válvula de retención antirretorno por muelle Serie CH/CO con resalte indicador de flujo",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total")
@param(D=LENGTH, TooltipShort="Diámetro exterior del racor tubo")
@param(F=LENGTH, TooltipShort="Ancho entre caras del cuerpo hexagonal")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def CHECK_VALVE(s, A=2.40, D=0.60, F=0.875, E=0.19, **kw):
    Rbody = D / 2
    Rhex = F / 2
    Rbore = E / 2
    halfA = A / 2
    valve_len = A * 0.60

    # Cuerpo principal tubo
    body = CYLINDER(s, R=Rbody, H=A)
    body.translate((0, 0, -halfA))

    # Cuerpo hexagonal principal de la válvula
    hex_body = CYLINDER(s, R=Rhex, H=valve_len)
    hex_body.translate((0, 0, -valve_len / 2))
    body.uniteWith(hex_body)

    # Resalte indicador de sentido de flujo (anillo exterior en el lado de salida P1)
    arrow_ring = CYLINDER(s, R=Rhex + 0.05, H=A * 0.08)
    arrow_ring.translate((0, 0, valve_len * 0.25))
    body.uniteWith(arrow_ring)

    # Perforación pasante interior
    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
