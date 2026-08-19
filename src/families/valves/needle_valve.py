"""
Válvula de aguja reguladora de caudal Serie N/1 Swagelok.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Valves",
    TooltipShort="Válvula de aguja",
    TooltipLong="Válvula de aguja para regulación fina de caudal con bonete y volante giratorio superior",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(A=LENGTH, TooltipShort="Longitud total cara a cara")
@param(D=LENGTH, TooltipShort="Diámetro exterior del racor tubo")
@param(H=LENGTH, TooltipShort="Altura desde el centro hasta el volante")
@param(W=LENGTH, TooltipShort="Diámetro del volante giratorio")
@param(E=LENGTH, TooltipShort="Diámetro de paso mínimo interior")
def NEEDLE_VALVE(s, A=2.10, D=0.60, H=1.80, W=1.20, E=0.19, **kw):
    Rbody = D / 2
    Rbore = E / 2
    Rwheel = W / 2
    halfA = A / 2

    # 1. Cuerpo principal en Z
    body = CYLINDER(s, R=Rbody, H=A)
    body.translate((0, 0, -halfA))

    # 2. Bloque central hexagonal de la válvula
    block_size = D * 1.3
    center_block = BOX(s, L=block_size, W=block_size, H=block_size)
    center_block.translate((-block_size / 2, -block_size / 2, -block_size / 2))
    body.uniteWith(center_block)

    # 3. Bonete/Cuello vertical de regulación en X
    stem_r = Rbody * 0.65
    stem = CYLINDER(s, R=stem_r, H=H)
    stem.rotateY(90)
    body.uniteWith(stem)

    # 4. Volante giratorio circular superior en (H, 0, 0)
    wheel_h = Rbody * 0.4
    wheel = CYLINDER(s, R=Rwheel, H=wheel_h)
    wheel.rotateY(90)
    wheel.translate((H, 0, 0))
    body.uniteWith(wheel)

    # 5. Perforación interna pasante
    bore = CYLINDER(s, R=Rbore, H=A)
    bore.translate((0, 0, -halfA))
    body.subtractFrom(bore)

    s.setPoint((0, 0, halfA), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfA), (0, 0, -1), 0)

    return s
