"""
T simple con puertos.
Conecta tres tubos en configuracion de T.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *

@activate(
    Group="Tees",
    TooltipShort="Simple Tee",
    TooltipLong="Connects three tubes in T configuration",
    LengthUnit="in"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Outside diameter of main tube")
@param(L=LENGTH, TooltipShort="Main line length (end to end)")
@param(H=LENGTH, TooltipShort="Branch height (center to branch end)")
@param(T=LENGTH, TooltipShort="Wall thickness")
def SIMPLE_TEE(s, OD=1, L=4, H=2, T=0.1, **kw):
    R = OD / 2
    
    # Tubo principal (Linea corrida)
    s = CYLINDER(s, R=R, H=L)
    
    # Derivación (Branch)
    branch = CYLINDER(s, R=R, H=H)
    branch.rotateY(90)
    s.join(branch)
    branch.erase()
    
    # Puerto 1 (Entrada principal)
    s.setPoint(1, (0, 0, 0))
    s.setVector(1, (0, 0, -1))
    
    # Puerto 2 (Salida principal)
    s.setPoint(2, (0, 0, L))
    s.setVector(2, (0, 0, 1))
    
    # Puerto 3 (Derivación)
    s.setPoint(3, (H, 0, L/2))
    s.setVector(3, (1, 0, 0))
    
    return s
