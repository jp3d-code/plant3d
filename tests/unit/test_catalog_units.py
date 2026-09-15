"""Unidades y tablas del catalogo .pcat contra el oficial Autodesk.

Valores de referencia extraidos de 'ASME Valves Catalog.pcat'
(CPak ASME 2027): familias Ball Valve RF 150/300/600.
"""
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from builders import build_catalog as bc  # noqa: E402


class TestNormalizePressureClass(unittest.TestCase):
    def test_lbs_y_hash(self):
        self.assertEqual(bc.normalize_pressure_class("150LBS"), "150")
        self.assertEqual(bc.normalize_pressure_class("150#"), "150")
        self.assertEqual(bc.normalize_pressure_class("800LBS"), "800")

    def test_wog_numerico(self):
        self.assertEqual(bc.normalize_pressure_class("1000WOG"), "1000")

    def test_pn_se_conserva(self):
        # PN no tiene equivalente imperial: inventar '150' seria falso
        self.assertEqual(bc.normalize_pressure_class("PN16"), "PN16")
        self.assertEqual(bc.normalize_pressure_class("PN40"), "PN40")

    def test_vacio(self):
        self.assertEqual(bc.normalize_pressure_class(""), "150")
        self.assertEqual(bc.normalize_pressure_class(None), "150")


class TestMatchingPipeOd(unittest.TestCase):
    def test_b36_10_exacto(self):
        self.assertEqual(bc.get_matching_pipe_od(0.5), 0.84)
        self.assertEqual(bc.get_matching_pipe_od(2.0), 2.375)
        self.assertEqual(bc.get_matching_pipe_od(8.0), 8.625)

    def test_nunca_nominal_en_chicas(self):
        # Regla P1: el OD real difiere del nominal bajo 14"; usar el
        # nominal (rama PL antigua) subescala el tubo.
        for nd in (0.5, 0.75, 1.0, 2.0, 4.0, 8.0, 12.0):
            self.assertNotEqual(bc.get_matching_pipe_od(nd), nd)


class TestFlangeThickness(unittest.TestCase):
    # Valores EXACTOS del oficial (Ball Valve RF Short 150 / Long 300/600)
    def test_clase_150(self):
        self.assertEqual(bc.get_flange_thickness(0.5, "150"), 0.44)
        self.assertEqual(bc.get_flange_thickness(2.0, "150"), 0.75)
        self.assertEqual(bc.get_flange_thickness(4.0, "150"), 0.94)
        self.assertEqual(bc.get_flange_thickness(8.0, "150"), 1.12)

    def test_clase_300(self):
        self.assertEqual(bc.get_flange_thickness(0.5, "300"), 0.56)
        self.assertEqual(bc.get_flange_thickness(2.0, "300"), 0.87)
        self.assertEqual(bc.get_flange_thickness(4.0, "300"), 1.25)

    def test_clase_600(self):
        self.assertEqual(bc.get_flange_thickness(0.5, "600"), 0.81)
        self.assertEqual(bc.get_flange_thickness(2.0, "600"), 1.25)

    def test_clase_sin_tabla_fallback(self):
        self.assertGreater(bc.get_flange_thickness(2.0, "800"), 0.0)
        self.assertGreater(bc.get_flange_thickness(2.0, "PN16"), 0.0)


if __name__ == "__main__":
    unittest.main()
