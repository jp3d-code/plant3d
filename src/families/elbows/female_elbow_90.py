"""
Codo de 90 grados tubo Swagelok a rosca hembra NPT.
Ver guía en guide/07-codos-90/hembra-npt.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Elbows",
    TooltipShort="Codo 90 hembra NPT",
    TooltipLong="Conecta tubo Swagelok a rosca hembra NPT en un ángulo de 90 grados",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Diámetro exterior del tubo")
@param(L=LENGTH, TooltipShort="Dimensión del centro al extremo del tubo")
@param(A=LENGTH, TooltipShort="Dimensión del centro al extremo hembra")
def FEMALE_ELBOW_90(s, OD=0.5, L=1.1, A=1.1, **kw):
    R1 = L
    R2 = OD / 2
    if R1 <= R2:
        R1 = R2 + 0.0001

    elbow = ARC3D2(s, D=R2, D2=R2, R=R1, A=90)

    s.setPoint(elbow.pointAt(0), elbow.directionAt(0), 0)
    s.setPoint(elbow.pointAt(1), elbow.directionAt(1), 0)

    return s
