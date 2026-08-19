"""
Conector macho NPT con taladro pasante continuo (BT) Swagelok.
Ver guía en guide/11-aplicaciones-especiales/taladrados.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Special",
    TooltipShort="Conector taladrado BT",
    TooltipLong="Conector macho NPT con taladro pasante continuo de diámetro completo para sondas",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total centro a extremo")
@param(D=LENGTH, TooltipShort="Diámetro exterior del tubo")
@param(F=LENGTH, TooltipShort="Ancho entre caras del hexágono")
def BORED_THROUGH_CONNECTOR(s, A=1.49, D=0.60, F=0.5625, **kw):
    Rbody = D / 2
    Rnut = F / 2
    # Taladro pasante de paso completo igual al diámetro del tubo
    Rbore = Rbody
    halfA = A / 2
    thread_len = A * 0.45

    # Cuerpo principal
    body = CYLINDER(s, R=Rbody * 1.15, H=A)
    body.translate((0, 0, -halfA))

    # Tuerca central
    nut = CYLINDER(s, R=Rnut, H=A * 0.3)
    nut.translate((0, 0, -A * 0.15))
    body.uniteWith(nut)

    # Conicidad NPT en extremo macho
    thread = CONE(s, R1=Rbody * 0.95, R2=Rbody * 1.10, H=thread_len, E=0.0)
    thread.translate((0, 0, -halfA))
    body.uniteWith(thread)

    # Perforación pasante completa (BT)
    bore = CYLINDER(s, R=Rbore, H=A * 1.1)
    bore.translate((0, 0, -halfA * 1.05))
    body.subtractFrom(bore)

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
