"""
Válvula de bola bridada de 2 piezas INTEC K200 KLINGER SCHÖNEBERG.
ANSI Class 150 / Class 300, 1/2" a 4".
"""
from varmain.primitiv import *
from varmain.var_basic import *
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
def INTEC_K200_BALL_VALVE(s, L=4.2520, D=3.5039, H=3.7402, L1=6.2992, E=1.5551, OD=0.5000, **kw):
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
    
    # 5. Cuello del bonete vertical (Eje X, altura H)
    Rstem = max(float(OD) * 0.35, 0.30)
    stem_h = max(0.5, float(H))
    stem = CYLINDER(s, R=Rstem, H=stem_h)
    stem.rotateY(90)
    body.uniteWith(stem)
    
    # 6. Brida superior de montaje ISO 5211 (en altura E)
    if float(E) > 0 and float(E) < stem_h:
        Riso = Rstem * 1.4
        iso_pad = CYLINDER(s, R=Riso, H=0.18)
        iso_pad.rotateY(90)
        iso_pad.translate((float(E), 0, 0))
        body.uniteWith(iso_pad)
    
    # 7. Buje central superior de la manija
    Rhub = Rstem * 1.3
    hub = CYLINDER(s, R=Rhub, H=0.20)
    hub.rotateY(90)
    hub.translate((stem_h, 0, 0))
    body.uniteWith(hub)

    # 8. Manija / Palanca de accionamiento
    arm_len = float(L1)
    arm_w = max(0.30, float(OD) * 0.22)   # Ancho en Z (a lo largo del tubo)
    arm_th = 0.18                         # Espesor vertical en X
    
    lever = BOX(s, L=arm_th, W=arm_len, H=arm_w)
    lever.translate((stem_h, 0.0, -arm_len/2.0))
    body.uniteWith(lever)

    # 9. Perforación interna pasante
    bore = CYLINDER(s, R=Rbore, H=float(L) + 0.1)
    bore.translate((0, 0, -halfL - 0.05))
    body.subtractFrom(bore)

    # 10. Perforaciones para pernos en ambas bridas (45°, 135°, 225°, 315°)
    Rbc = Rbore + (Rflange - Rbore) * (2.0 / 3.0)
    Rbolt = max(0.08, min(0.25, (Rflange - Rbore) * 0.22))
    
    for angle in [45, 135, 225, 315]:
        rad = radians(angle)
        bx = Rbc * cos(rad)
        by = Rbc * sin(rad)
        
        # Agujero en Brida 1 (Entrada)
        bhole1 = CYLINDER(s, R=Rbolt, H=flange_th + 0.1)
        bhole1.translate((bx, by, -halfL - 0.05))
        body.subtractFrom(bhole1)
        
        # Agujero en Brida 2 (Salida)
        bhole2 = CYLINDER(s, R=Rbolt, H=flange_th + 0.1)
        bhole2.translate((bx, by, halfL - flange_th - 0.05))
        body.subtractFrom(bhole2)
    
    # Puertos de conexión en los extremos de las bridas
    s.setPoint((0, 0, halfL), (0, 0, 1), 0)
    s.setPoint((0, 0, -halfL), (0, 0, -1), 0)
    
    return s
