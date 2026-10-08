"""
Pruebas unitarias para el incorporador de Catálogos de Soporte (.acat) a Specs (.pspc).
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from builders.build_support_spec import add_support_catalog_to_spec


def make_mock_acat(path: Path):
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    cur = conn.cursor()
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
    cur.execute("""INSERT INTO EngineeringItems (
        PnPID, PartFamilyLongDesc, PartSizeLongDesc, ShortDescription,
        Manufacturer, NominalDiameter, MatchingPipeOd, ConnectionPortCount,
        ContentGeometryTemplate, ContentGeometryParamDefinition
    ) VALUES (
        2, 'ITECO B3S Abrazadera', 'ITECO B3S 2in', 'B3S 2in',
        'ITECO', 2.0, 2.375, 1, 'UBOLT_STANDARD', 'OD=2.375000'
    );""")
    conn.commit()
    conn.close()


def make_mock_pspc(path: Path):
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE PnPBase (PnPID INTEGER PRIMARY KEY, PnPClassName TEXT, PnPStatus INT, PnPRevision INT, PnPGuid BLOB, PnPTimestamp INT);")
    cur.execute("CREATE TABLE PipeRunComponent (PnPID INTEGER);")
    cur.execute("CREATE TABLE Support (PnPID INTEGER, PartSubType TEXT);")
    cur.execute("""CREATE TABLE EngineeringItems (
        PnPID INTEGER PRIMARY KEY, PartFamilyId GUID, CatalogPartFamilyId GUID,
        PartFamilyLongDesc TEXT, PartSizeLongDesc TEXT, ShortDescription TEXT,
        Manufacturer TEXT, Material TEXT, MaterialCode TEXT, DesignStd TEXT,
        CompatibleStandard TEXT, Weight REAL, WeightUnit TEXT,
        ConnectionPortCount INT, SizeRecordId GUID, PortName TEXT,
        NominalDiameter REAL, NominalUnit TEXT, MatchingPipeOd REAL,
        EndType TEXT, LengthUnit TEXT, PartCategory TEXT, ContentDomain TEXT,
        ContentGeometryParamDefinition TEXT, ContentIsoSymbolDefinition TEXT,
        ContentGeometryTemplate TEXT, CatalogPartId INT, CatalogId TEXT,
        PartVersion TEXT);""")
    # Insert existing item to verify it is preserved
    cur.execute("INSERT INTO PnPBase (PnPID, PnPClassName) VALUES (1, 'Support');")
    cur.execute("INSERT INTO PipeRunComponent (PnPID) VALUES (1);")
    cur.execute("INSERT INTO Support (PnPID) VALUES (1);")
    cur.execute("""INSERT INTO EngineeringItems (
        PnPID, PartFamilyLongDesc, PartSizeLongDesc, NominalDiameter, MatchingPipeOd,
        ContentGeometryTemplate, CatalogId
    ) VALUES (
        1, 'Existing Support Family', 'Existing 1in', 1.0, 1.315,
        'SIMPLE_SUPPORT', 'OLD_CATALOG'
    );""")
    conn.commit()
    conn.close()


class TestBuildSupportSpec(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp_dir.name)
        self.acat = self.dir / "TEST_CATALOG.acat"
        self.pspc = self.dir / "TEST_SPEC.pspc"
        make_mock_acat(self.acat)
        make_mock_pspc(self.pspc)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_support_catalog_to_spec(self):
        res = add_support_catalog_to_spec(
            acat_path=self.acat,
            spec_pspc_path=self.pspc,
            catalog_id="TEST_CATALOG",
            backup=True
        )
        self.assertEqual(res["items_added"], 1)
        self.assertTrue(Path(res["backup_path"]).exists())

        conn = sqlite3.connect(self.pspc)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM EngineeringItems;")
        self.assertEqual(cur.fetchone()[0], 2)  # 1 existente + 1 nuevo

        # Verificar nuevo item
        cur.execute("SELECT PnPID, PartFamilyLongDesc, MatchingPipeOd, CatalogId FROM EngineeringItems WHERE PnPID = 2;")
        row = cur.fetchone()
        self.assertEqual(row[1], "ITECO B3S Abrazadera")
        self.assertEqual(row[2], 2.375)
        self.assertEqual(row[3], "TEST_CATALOG")

        # Verificar tablas auxiliares
        cur.execute("SELECT COUNT(*) FROM Support WHERE PnPID = 2;")
        self.assertEqual(cur.fetchone()[0], 1)
        cur.execute("SELECT COUNT(*) FROM PipeRunComponent WHERE PnPID = 2;")
        self.assertEqual(cur.fetchone()[0], 1)
        conn.close()

    def test_idempotent_replaces_without_duplicate(self):
        # Correr dos veces consecutivas
        add_support_catalog_to_spec(self.acat, self.pspc, backup=False)
        add_support_catalog_to_spec(self.acat, self.pspc, backup=False)

        conn = sqlite3.connect(self.pspc)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM EngineeringItems WHERE PartFamilyLongDesc = 'ITECO B3S Abrazadera';")
        self.assertEqual(cur.fetchone()[0], 1)  # Debe seguir habiendo solo 1, no 2
        conn.close()


if __name__ == "__main__":
    unittest.main()
