"""
Codo de 90 grados simple con puertos.
Conecta dos tubos en angulo de 90 grados.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *

@activate(
    Group="Elbows",
    TooltipShort="Simple 90 Elbow",
    TooltipLong="Connects two tubes at 90 degree angle",
    LengthUnit="in"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Outside diameter of tube")
@param(L=LENGTH, TooltipShort="Center to end dimension")
@param(T=LENGTH, TooltipShort="Wall thickness")
def SIMPLE_ELBOW_90(s, OD=1, L=2, T=0.1, **kw):
    R1 = L       # Radio de curvatura
    R2 = OD / 2  # Radio exterior del tubo
    
    # Codo curvo de 90 grados
    s = TORUS(s, R1=R1, R2=R2, A=90)
    
    # Puerto 1 (Entrada)
    s.setPoint(1, (-R1, 0, 0))
    s.setVector(1, (-1, 0, 0))
    
    # Puerto 2 (Salida a 90 grados)
    s.setPoint(2, (0, R1, 0))
    s.setVector(2, (0, 1, 0))
    
    return s
