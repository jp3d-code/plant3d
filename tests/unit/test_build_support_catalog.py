"""
Pruebas unitarias para el generador de Support Catalog (.acat) de Plant 3D 2027.
"""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from builders.build_support_catalog import build_support_catalog, DEFAULT_TEMPLATE_ACAT


class TestBuildSupportCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEFAULT_TEMPLATE_ACAT.exists():
            raise unittest.SkipTest("Plantilla oficial SUPPORTS Catalog.acat no disponible en este entorno.")

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name)

        self.mock_json = self.out_dir / "MOCK_UBOLT.json"
        mock_data = {
            "metadata": {
                "manufacturer": "ITECO SRL",
                "model": "ITECO B3S",
                "description": "Standard U-Bolt MSS-SP-58 Type 24",
                "design_standard": "MSS-SP-58-2018",
                "plant3d_template": "UBOLT_STANDARD"
            },
            "plant3d_records": [
                {
                    "DN_mm": 50,
                    "NPS_inch": "2\"",
                    "Pipe_OD_mm": 60.325,
                    "Rod_Diameter_mm": 9.525,
                    "B_Inside_Width_mm": 63.5,
                    "C_Center_Distance_mm": 73.025,
                    "D_Total_Height_mm": 104.775,
                    "E_Leg_Height_mm": 69.85,
                    "F_Thread_Length_mm": 50.8,
                    "Weight_kg": 0.35,
                    "Material": "Carbon Steel"
                }
            ]
        }
        with open(self.mock_json, "w", encoding="utf-8") as f:
            json.dump(mock_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_build_support_catalog_creates_file_and_records(self):
        res = build_support_catalog(
            spec_json_path=self.mock_json,
            output_dir=self.out_dir,
            catalog_name="TEST_UBOLT_CATALOG",
            template_acat=DEFAULT_TEMPLATE_ACAT
        )
        self.assertEqual(res["items_count"], 1)

        acat_path = Path(res["acat_path"])
        self.assertTrue(acat_path.exists())

        conn = sqlite3.connect(acat_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()

            # Check EngineeringItems
            cur.execute("SELECT * FROM EngineeringItems")
            rows = cur.fetchall()
            self.assertEqual(len(rows), 1)
            r = rows[0]
            self.assertEqual(r["NominalDiameter"], 2.0)
            self.assertEqual(r["NominalUnit"], "in")
            self.assertEqual(r["LengthUnit"], "in")
            self.assertEqual(r["WeightUnit"], "LB")
            self.assertEqual(r["MatchingPipeOd"], 2.375)
            self.assertEqual(r["EndType"], "Undefined_ET")
            self.assertEqual(r["PartCategory"], "Default")
            self.assertEqual(r["ConnectionPortCount"], 1)
            self.assertEqual(r["PortName"], "S1")
            self.assertEqual(r["ContentDomain"], "P3D")
            self.assertEqual(r["ContentGeometryTemplate"], "UBOLT_STANDARD")
            self.assertEqual(r["ContentIsoSymbolDefinition"], "TYPE=SUPPORT,SKEY=ANCH")

            # Check RepositoryDescriptor
            cur.execute("SELECT * FROM RepositoryDescriptor WHERE PnPID = 1")
            repo_row = cur.fetchone()
            self.assertEqual(repo_row["ContentType"], "Pipe Supports")
            self.assertEqual(repo_row["Type"], "Autodesk.ProcessPower.PartsRepository.Catalog.PipePartCatalog")

            # Check Support and PipeRunComponent tables
            cur.execute("SELECT * FROM Support WHERE PnPID = ?", (r["PnPID"],))
            s_row = cur.fetchone()
            self.assertIsNotNone(s_row)
            self.assertEqual(s_row["PartSubType"], "Support")

            cur.execute("SELECT * FROM PipeRunComponent WHERE PnPID = ?", (r["PnPID"],))
            self.assertIsNotNone(cur.fetchone())

            cur.execute("SELECT * FROM PnPBase WHERE PnPID = ?", (r["PnPID"],))
            base_row = cur.fetchone()
            self.assertIsNotNone(base_row)
            self.assertEqual(base_row["PnPClassName"], "Support")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
