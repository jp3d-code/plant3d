"""
Válvula de bola bridada de 2 piezas INTEC K200 KLINGER SCHÖNEBERG.
ANSI Class 150 / Class 300, 1/2" a 4".
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Valves",
    TooltipShort="Válvula de bola bridada INTEC K200",
    TooltipLong="Válvula de bola de 2 piezas bridada Klinger Schöneberg INTEC K200 Class 150/300 paso total",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(L=LENGTH, TooltipShort="Longitud cara a cara ANSI B16.10")
@param(D=LENGTH, TooltipShort="Diámetro exterior de brida ANSI B16.5")
@param(H=LENGTH, TooltipShort="Altura desde centro a la palanca")
@param(L1=LENGTH, TooltipShort="Longitud de la palanca de accionamiento")
@param(E=LENGTH, TooltipShort="Altura desde centro al bonete ISO 5211")
@param(OD=LENGTH, TooltipShort="Diámetro nominal de paso de tubería")
def INTEC_K200_BALL_VALVE(s, L=4.25, D=3.50, H=3.74, L1=6.30, E=1.55, OD=0.50, **kw):
    halfL = float(L) / 2.0
    Rflange = float(D) / 2.0
    Rbore = float(OD) / 2.0
    
    # Espesor de la brida (aprox 11% del diámetro exterior de la brida, mín. 0.375 in)
    flange_th = max(0.375, float(D) * 0.11)
    
    # 1. Cuerpo esférico central
    Rbody = max(float(D) * 0.32, float(OD) * 1.2)
    body = SPHERE(s, R=Rbody)
    
    # 2. Cilindro del cuerpo entre las dos bridas
    Rneck = max(Rbody * 0.85, float(OD) * 0.9)
    cyl_len = max(0.1, float(L) - (2.0 * flange_th))
    main_cyl = CYLINDER(s, R=Rneck, H=cyl_len)
    main_cyl.translate((0, 0, -halfL + flange_th))
    body.uniteWith(main_cyl)
    
    # 3. Brida de entrada (Puerto 1, Z = -halfL)
    flange1 = CYLINDER(s, R=Rflange, H=flange_th)
    flange1.translate((0, 0, -halfL))
    body.uniteWith(flange1)
    
    # 4. Brida de salida (Puerto 2, Z = halfL - flange_th)
    flange2 = CYLINDER(s, R=Rflange, H=flange_th)
    flange2.translate((0, 0, halfL - flange_th))
    body.uniteWith(flange2)
    
    # 5. Cuello del bonete vertical (Eje X)
    Rstem = max(float(OD) * 0.4, 0.375)
    stem_h = max(0.5, float(H))
    stem = CYLINDER(s, R=Rstem, H=stem_h)
    stem.rotateY(90)
    body.uniteWith(stem)
    
    # 6. Brida superior de montaje ISO 5211 (en altura E)
    if float(E) > 0:
        Riso = Rstem * 1.5
        iso_pad = CYLINDER(s, R=Riso, H=0.25)
        iso_pad.rotateY(90)
        iso_pad.translate((float(E) - 0.25, 0, 0))
        body.uniteWith(iso_pad)
    
    # 7. Palanca de accionamiento (en altura H)
    handle_len = float(L1)
    handle_w = max(0.25, float(OD) * 0.25)
    handle_th = max(0.1875, float(OD) * 0.15)
    handle = BOX(s, L=handle_th, W=handle_len, H=handle_w)
    handle.translate((float(H) - handle_th, -handle_len * 0.15, -handle_w / 2.0))
    body.uniteWith(handle)
    
    # 8. Perforación interna pasante
    bore = CYLINDER(s, R=Rbore, H=float(L) + 0.1)
    bore.translate((0, 0, -halfL - 0.05))
    body.subtractFrom(bore)
    
    # Puertos de conexión en los extremos de las bridas
    s.setPoint((0, 0, halfL), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfL), (0, 0, -1), 0)
    
    return s
