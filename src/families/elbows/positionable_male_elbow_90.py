"""
Codo de 90 grados macho orientable Swagelok.
Ver guía en guide/07-codos-90/orientable-pr-st.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Elbows",
    TooltipShort="Codo 90 macho orientable",
    TooltipLong="Codo macho de 90 grados orientable con contratuerca de ajuste",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Diámetro exterior del tubo")
@param(L=LENGTH, TooltipShort="Dimensión del centro al extremo del tubo")
@param(NL=LENGTH, TooltipShort="Longitud de la tuerca de ajuste")
def POSITIONABLE_MALE_ELBOW_90(s, OD=0.5, L=1.1, NL=0.2, **kw):
    R1 = L
    R2 = OD / 2
    if R1 <= R2:
        R1 = R2 + 0.0001

    elbow = ARC3D2(s, D=R2, D2=R2, R=R1, A=90)

    s.setPoint(elbow.pointAt(0), elbow.directionAt(0), 0)
    s.setPoint(elbow.pointAt(1), elbow.directionAt(1), 0)

    return s
