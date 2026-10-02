"""
Abrazadera U Standard (Pipe Support U-Bolt) ITECO B3S según MSS-SP-58-2018.
Modelo de alta fidelidad con ensamble de contratuerca (4 tuercas y 4 arandelas)
para AutoCAD Plant 3D 2027.
"""
from varmain.primitiv import *
from varmain.var_basic import *
from varmain.custom import *
from math import *


@activate(
    Group="PipeSupports",
    TooltipShort="Abrazadera U Standard ITECO B3S",
    TooltipLong="Abrazadera U Standard ITECO B3S MSS-SP-58 Tipo 24 con ensamble de contratuerca (4 tuercas, 4 arandelas)",
    LengthUnit="in",
    Ports="1"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Diámetro exterior del tubo soportado")
@param(A=LENGTH, TooltipShort="Diámetro de varilla roscada")
@param(B=LENGTH, TooltipShort="Ancho interior libre entre patas")
@param(C=LENGTH, TooltipShort="Distancia entre centros de ramas")
@param(D=LENGTH, TooltipShort="Altura total exterior de la abrazadera")
@param(E=LENGTH, TooltipShort="Altura de pata recta / zona de fijación")
@param(F=LENGTH, TooltipShort="Longitud útil roscada")
def UBOLT_STANDARD(s, OD=0.840, A=0.250, B=0.945, C=1.181, D=2.638, E=2.244, F=2.205, **kw):
    eff_OD = float(OD) if float(OD) > 0 else 0.840
    eff_A = float(A) if float(A) > 0 else 0.250
    eff_C = float(C) if float(C) > 0 else (eff_OD + eff_A)
    eff_B = float(B) if float(B) > 0 else (eff_C - eff_A)
    eff_D = float(D) if float(D) > 0 else (eff_OD * 3.0)
    eff_E = float(E) if float(E) > 0 else (eff_D * 0.7)
    eff_F = float(F) if float(F) > 0 else (eff_E * 0.8)

    Rpipe = eff_OD / 2.0
    Rrod = max(eff_A / 2.0, 0.0625)
    Rbend = eff_C / 2.0
    if Rbend <= Rrod:
        Rbend = Rpipe + Rrod

    # 1. Arco superior (Semicírculo de la varilla en el plano XY abrazando el tubo en Z=0)
    body = TORUS(s, R1=Rbend, R2=Rrod)

    # Cortar mitad inferior del toroide (X < 0) para dejar solo el semicírculo superior (X >= 0)
    cut_size = 2.0 * (Rbend + Rrod + 2.0)
    cutter = BOX(s, L=cut_size, W=cut_size, H=cut_size)
    cutter.translate((-cut_size / 2.0, 0.0, 0.0))
    body.subtractFrom(cutter)
    cutter.erase()

    # 2. Ramas rectas verticales paralelas (Patas) extendiéndose en -X
    # Altura del semicírculo sobre el origen: Rbend + Rrod.
    # Longitud de pata para cumplir la cota D:
    leg_len = max(eff_D - (Rbend + Rrod), eff_E, 0.5)

    # Solape de penetración volumétrica (0.05") para evitar fallo de caras coincidentes en ACIS CSG
    overlap = 0.05

    # Pata izquierda (Y = -Rbend)
    leg1 = CYLINDER(s, R=Rrod, H=leg_len + overlap)
    leg1.rotateY(90)
    leg1.translate((-leg_len, -Rbend, 0.0))
    body.uniteWith(leg1)
    leg1.erase()

    # Pata derecha (Y = +Rbend)
    leg2 = CYLINDER(s, R=Rrod, H=leg_len + overlap)
    leg2.rotateY(90)
    leg2.translate((-leg_len, Rbend, 0.0))
    body.uniteWith(leg2)
    leg2.erase()

    # 3. Ensamble de Contratuerca (4 Tuercas y 4 Arandelas: 2 tuercas y 2 arandelas por pata)
    # Dimensiones estándar de tuercas y arandelas basadas en el diámetro A:
    H_nut = max(0.18, eff_A * 0.85)          # Altura de tuerca hexagonal
    R_nut = Rrod * 1.55                      # Radio envolvente de tuerca
    th_washer = max(0.05, eff_A * 0.12)      # Espesor de arandela
    R_washer = Rrod * 1.85                   # Radio de arandela plana
    t_plate = max(0.25, eff_A * 0.50)        # Espesor de placa / viga estructural

    # Posición de la placa de apoyo estructural (justo bajo la tubería)
    X_mount = -Rpipe - 0.05

    # Límite inferior para asegurar que las tuercas queden sobre la pata
    X_jam_bot = -leg_len + 0.05
    X_mount = max(X_mount, X_jam_bot + t_plate + (2.0 * th_washer) + (2.0 * H_nut))

    leg_y_positions = [-Rbend, Rbend]

    # Las arandelas y tuercas se añaden como primitivas nativas en s sin operación booleana CSG
    # para evitar problemas de caras coincidentes o corrupción de memoria en ACIS C++.
    for y_pos in leg_y_positions:
        # A. Arandela plana superior (sobre la placa de montaje)
        w_top = CYLINDER(s, R=R_washer, H=th_washer)
        w_top.rotateY(90)
        w_top.translate((X_mount, y_pos, 0.0))

        # B. Tuerca hexagonal superior (tope)
        n_top = CYLINDER(s, R=R_nut, H=H_nut)
        n_top.rotateY(90)
        n_top.translate((X_mount + th_washer, y_pos, 0.0))

        # C. Arandela inferior (bajo la placa de montaje)
        w_bot_pos = X_mount - t_plate - th_washer
        w_bot = CYLINDER(s, R=R_washer, H=th_washer)
        w_bot.rotateY(90)
        w_bot.translate((w_bot_pos, y_pos, 0.0))

        # D. Contratuerca hexagonal inferior (bloqueo)
        n_bot_pos = w_bot_pos - H_nut
        n_bot = CYLINDER(s, R=R_nut, H=H_nut)
        n_bot.rotateY(90)
        n_bot.translate((n_bot_pos, y_pos, 0.0))

    # 4. Puerto oficial de fijación de soporte en el centro de la tubería (origen 0,0,0)
    s.setPoint((0, 0, 0), (-1, 0, 0), 0)

    return s
