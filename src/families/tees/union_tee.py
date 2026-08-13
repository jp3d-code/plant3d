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
    LengthUnit="in",
    Ports="3"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Outside diameter of main tube")
@param(L=LENGTH, TooltipShort="Main line length (end to end)")
@param(H=LENGTH, TooltipShort="Branch height (center to branch end)")
@param(T=LENGTH, TooltipShort="Wall thickness")
def SIMPLE_TEE(s, OD=1, L=4, H=2, T=0.1, **kw):
    R = OD / 2

    # Tubo principal (Linea corrida), centrado en Z
    main = CYLINDER(s, R=R, H=L)
    main.translate((0, 0, -L/2))

    # Derivacion (Branch): sale del centro del main hacia +X
    branch = CYLINDER(s, R=R, H=H)
    branch.rotateY(90)
    main.uniteWith(branch)
    branch.erase()

    # Puerto 1 (Entrada principal, extremo inferior)
    s.setPoint((0, 0, -L/2), (0, 0, -1), 0)

    # Puerto 2 (Salida principal, extremo superior)
    s.setPoint((0, 0, L/2), (0, 0, 1), 0)

    # Puerto 3 (Derivacion, extremo de la rama)
    s.setPoint((H, 0, 0), (1, 0, 0), 0)

    return s
