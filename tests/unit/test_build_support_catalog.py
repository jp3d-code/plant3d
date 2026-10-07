"""
Pruebas unitarias para el generador de Support Catalog (.acat) de Plant 3D 2027.

Contrato .acat (via unica para soportes):
- ConnectionPortCount=1, PortName=S1, EndType=Undefined_ET
- MatchingPipeOd SIEMPRE B36.10 (no OD medido)
- Weight siempre en LB (0.0 si Weight_kg==0), WeightUnit=LB
- Sanitizacion ASCII en catalog/manufacturer/desc
"""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from builders.build_support_catalog import build_support_catalog


def make_minimal_acat_template(path: Path):
    """Crea una plantilla .acat minima para correr en Linux sin Autodesk."""
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE PnPBase (PnPID INTEGER PRIMARY KEY, PnPClassName TEXT, PnPStatus INT, PnPRevision INT, PnPGuid BLOB, PnPTimestamp INT);")
    cur.execute("CREATE TABLE PnPSys_PnPBase_PnPID (d TEXT);")
    cur.execute("""CREATE TABLE RepositoryDescriptor (
        PnPID INTEGER PRIMARY KEY, Name TEXT, Description TEXT,
        ContentType TEXT, Type TEXT);""")
    cur.execute("""INSERT INTO RepositoryDescriptor (PnPID, Name, Description, ContentType, Type)
        VALUES (1, 'TEMPLATE', 'Template', 'Pipe Supports',
        'Autodesk.ProcessPower.PartsRepository.Catalog.PipePartCatalog');""")
    cur.execute("INSERT INTO PnPBase (PnPID, PnPClassName, PnPStatus, PnPRevision, PnPGuid, PnPTimestamp) VALUES (1, 'RepositoryDescriptor', 0, 4, X'00', 0);")
    cur.execute("""CREATE TABLE EngineeringItems (
        PnPID INTEGER PRIMARY KEY, PartFamilyId GUID, CatalogPartFamilyId GUID,
        PartFamilyLongDesc TEXT, PartSizeLongDesc TEXT, ShortDescription TEXT,
        Manufacturer TEXT, Material TEXT, MaterialCode TEXT, DesignStd TEXT,
        CompatibleStandard TEXT, Weight REAL, WeightUnit TEXT,
        ConnectionPortCount INT, SizeRecordId GUID, PortName TEXT,
        NominalDiameter REAL, NominalUnit TEXT, MatchingPipeOd REAL,
        EndType TEXT, LengthUnit TEXT, PartCategory TEXT, ContentDomain TEXT,
        ContentGeometryParamDefinition TEXT, ContentIsoSymbolDefinition TEXT,
        ContentGeometryTemplate TEXT, PartVersion TEXT);""")
    cur.execute("CREATE TABLE PipeRunComponent (PnPID INTEGER);")
    cur.execute("CREATE TABLE Support (PnPID INTEGER, PartSubType TEXT);")
    cur.execute("CREATE TABLE Port (PnPID INTEGER PRIMARY KEY, PortName TEXT);")
    cur.execute("CREATE TABLE PartPort (PnPID INTEGER PRIMARY KEY, Part INT, Port INT, Name TEXT);")
    cur.execute("CREATE TABLE PnPRowRelations (ROWID INT, RELID INT, RelationshipTypeName TEXT);")
    # Fila huerfana para verificar limpieza exhaustiva
    cur.execute("INSERT INTO Port (PnPID, PortName) VALUES (999, 'STALE');")
    conn.commit()
    conn.close()


class TestBuildSupportCatalog(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name)
        self.template = self.out_dir / "TEMPLATE_SUPPORTS.acat"
        make_minimal_acat_template(self.template)

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

    def _row(self, acat_path):
        conn = sqlite3.connect(acat_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM EngineeringItems")
            rows = cur.fetchall()
            return conn, rows
        except Exception:
            conn.close()
            raise

    def test_build_support_catalog_creates_file_and_records(self):
        res = build_support_catalog(
            spec_json_path=self.mock_json,
            output_dir=self.out_dir,
            catalog_name="TEST_UBOLT_CATALOG",
            template_acat=self.template
        )
        self.assertEqual(res["items_count"], 1)

        acat_path = Path(res["acat_path"])
        self.assertTrue(acat_path.exists())

        conn = sqlite3.connect(acat_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()

            cur.execute("SELECT * FROM EngineeringItems")
            rows = cur.fetchall()
            self.assertEqual(len(rows), 1)
            r = rows[0]
            self.assertEqual(r["NominalDiameter"], 2.0)
            self.assertEqual(r["NominalUnit"], "in")
            self.assertEqual(r["LengthUnit"], "in")
            # Peso 0.35kg -> 0.77lb siempre con unidad LB
            self.assertEqual(r["Weight"], 0.77)
            self.assertEqual(r["WeightUnit"], "LB")
            # Contrato B36.10 + 1 puerto
            self.assertEqual(r["MatchingPipeOd"], 2.375)
            self.assertIn("OD=2.375000", r["ContentGeometryParamDefinition"])
            self.assertEqual(r["EndType"], "Undefined_ET")
            self.assertEqual(r["PartCategory"], "Default")
            self.assertEqual(r["ConnectionPortCount"], 1)
            self.assertEqual(r["PortName"], "S1")
            self.assertEqual(r["ContentDomain"], "P3D")
            self.assertEqual(r["ContentGeometryTemplate"], "UBOLT_STANDARD")
            self.assertEqual(r["ContentIsoSymbolDefinition"], "TYPE=SUPPORT,SKEY=ANCH")

            # Limpieza exhaustiva: la fila STALE de Port debe haber desaparecido
            cur.execute("SELECT COUNT(*) AS n FROM Port;")
            self.assertEqual(cur.fetchone()["n"], 0)

            cur.execute("SELECT * FROM RepositoryDescriptor WHERE PnPID = 1")
            repo_row = cur.fetchone()
            self.assertEqual(repo_row["ContentType"], "Pipe Supports")

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

    def test_matching_pipe_od_always_b36_not_measured(self):
        """DN15 con Pipe_OD medido 21.3mm (0.8386) debe dar B36.10 0.84."""
        spec = self.out_dir / "DN15.json"
        with open(self.mock_json, encoding="utf-8") as f:
            data = json.load(f)
        data["plant3d_records"][0].update({
            "DN_mm": 15, "NPS_inch": "1/2\"", "Pipe_OD_mm": 21.3, "Weight_kg": 0.0,
        })
        with open(spec, "w", encoding="utf-8") as f:
            json.dump(data, f)
        res = build_support_catalog(
            spec_json_path=spec, output_dir=self.out_dir,
            catalog_name="T15", template_acat=self.template)
        self.assertEqual(res["items_count"], 1)
        conn = sqlite3.connect(res["acat_path"])
        try:
            cur = conn.cursor()
            cur.execute("SELECT MatchingPipeOd, Weight, WeightUnit FROM EngineeringItems;")
            od, w, wu = cur.fetchone()
            self.assertEqual(od, 0.84)
            self.assertEqual(w, 0.0)
            self.assertEqual(wu, "LB")
        finally:
            conn.close()

    def test_ascii_sanitization(self):
        spec = self.out_dir / "ACCENT.json"
        with open(self.mock_json, encoding="utf-8") as f:
            data = json.load(f)
        data["manufacturer"] = "Klinger Schöneberg Ñandú"
        with open(spec, "w", encoding="utf-8") as f:
            json.dump(data, f)
        res = build_support_catalog(
            spec_json_path=spec, output_dir=self.out_dir,
            catalog_name="T_ACC", template_acat=self.template)
        conn = sqlite3.connect(res["acat_path"])
        try:
            cur = conn.cursor()
            cur.execute("SELECT Manufacturer, PartFamilyLongDesc FROM EngineeringItems;")
            mfr, fam = cur.fetchone()
            self.assertNotIn("ö", mfr)
            self.assertNotIn("Ñ", fam)
            self.assertIn("Schoneberg", mfr)
        finally:
            conn.close()

    def test_missing_records_raises(self):
        spec = self.out_dir / "EMPTY.json"
        with open(spec, "w", encoding="utf-8") as f:
            json.dump({"model": "X"}, f)
        with self.assertRaises(ValueError):
            build_support_catalog(
                spec_json_path=spec, output_dir=self.out_dir,
                catalog_name="T_EMPTY", template_acat=self.template)


if __name__ == "__main__":
    unittest.main()
