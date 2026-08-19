"""
Unión simple Swagelok.
Ver guía en guide/01-uniones/union.md.
"""
from varmain.primitiv import *
from varmain.custom import *
from math import *


@activate(
    Group="Straight",
    TooltipShort="Unión simple",
    TooltipLong="Conecta dos tubos del mismo diámetro en línea recta",
    LengthUnit="in",
    Ports="2"
)
@group("MainDimensions")
@param(D=LENGTH, TooltipShort="Diámetro exterior del cuerpo")
@param(L=LENGTH, TooltipShort="Longitud total")
@param(E=LENGTH, TooltipShort="Diámetro de paso interior")
@param(OD=LENGTH, TooltipShort="Diámetro exterior del tubo")
def SIMPLE_UNION(s, D=0.50, L=1.61, E=0.19, **kw):
    D = float(kw.get("D", kw.get("OD", D)))
    L = float(kw.get("L", kw.get("A", L)))
    E = float(kw.get("E", E))

    if D <= 0 or L <= 0:
        raise ValueError("Diámetro (D) y Longitud (L) deben ser mayores a 0")

    Rbody = D / 2.0
    halfL = L / 2.0

    body = CYLINDER(s, R=Rbody, H=L)
    body.translate((0, 0, -halfL))

    if 0 < E < D:
        Rbore = E / 2.0
        bore = CYLINDER(s, R=Rbore, H=L * 1.1)
        bore.translate((0, 0, -halfL * 1.05))
        body.subtractFrom(bore)

    s.setPoint((0, 0, -halfL), (0, 0, -1), 0)
    s.setPoint((0, 0, halfL), (0, 0, 1), 0)

    return s
