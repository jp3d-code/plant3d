"""
Válvula de bola de 2 vías ON/OFF Serie 40G / 60 Swagelok.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Valves",
    TooltipShort="Válvula de bola 2 vías",
    TooltipLong="Válvula de bola de 2 vías ON/OFF con cuerpo de forja y palanca de accionamiento",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total cara a cara")
@param(D=LENGTH, TooltipShort="Diámetro exterior del racor tubo")
@param(H=LENGTH, TooltipShort="Altura desde el centro hasta la palanca")
@param(W=LENGTH, TooltipShort="Longitud de la palanca de accionamiento")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def BALL_VALVE_2WAY(s, A=2.40, D=0.60, H=1.50, W=2.0, E=0.19, **kw):
    Rbody = D / 2
    Rbore = E / 2
    halfA = A / 2

    # 1. Cuerpo del tubo en el eje Z
    body = CYLINDER(s, R=Rbody, H=A)
    body.translate((0, 0, -halfA))

    # 2. Bloque central de forja
    block_size = D * 1.4
    center_block = BOX(s, L=block_size, W=block_size, H=block_size)
    center_block.translate((-block_size / 2, -block_size / 2, -block_size / 2))
    body.uniteWith(center_block)
    center_block.erase()

    # 3. Cuello del bonete vertical en X
    stem_r = Rbody * 0.7
    stem = CYLINDER(s, R=stem_r, H=H)
    stem.rotateY(90)
    body.uniteWith(stem)
    stem.erase()

    # 4. Palanca de accionamiento superior en el extremo del cuello (H, 0, 0)
    handle_w = W
    handle_h = Rbody * 0.5
    handle_d = Rbody * 0.3
    handle = BOX(s, L=handle_d, W=handle_w, H=handle_h)
    handle.translate((-handle_d / 2, -handle_w * 0.2, H))
    body.uniteWith(handle)
    handle.erase()

    # 5. Perforación interna pasante
    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)
    bore.erase()

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
