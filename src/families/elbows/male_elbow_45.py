"""
Codo macho NPT de 45 grados Swagelok.
Ver guía en guide/08-codos-45/macho-npt.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Elbows",
    TooltipShort="Codo macho a 45 grados",
    TooltipLong="Conecta un tubo con una rosca macho NPT en un ángulo de 45 grados",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Diámetro exterior del tubo")
@param(L=LENGTH, TooltipShort="Dimensión del centro al extremo")
@param(T=LENGTH, TooltipShort="Espesor de pared")
def MALE_ELBOW_45(s, OD=1.0, L=2.0, T=0.1, **kw):
    R1 = float(L)
    R2 = float(OD) / 2.0
    if R1 <= R2:
        R1 = R2 + 0.0001

    elbow = ARC3D2(s, D=float(OD), D2=float(OD), R=R1, A=45)

    s.setPoint(elbow.pointAt(0), elbow.directionAt(0), 0)
    s.setPoint(elbow.pointAt(1), elbow.directionAt(1), 0)

    return s
