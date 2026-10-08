"""
Pruebas unitarias para el incorporador de Catálogos de Válvulas (.pcat) a Specs de Tubería CS150 (.pspc).
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from builders.build_piping_spec import (
    add_valves_to_piping_spec,
    parse_geometry_params
)


def make_mock_pcat(path: Path):
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
        EndType TEXT, FlangeThickness REAL, PressureClass TEXT, Facing TEXT,
        LengthUnit TEXT, PartCategory TEXT, ContentDomain TEXT,
        ContentGeometryParamDefinition TEXT, ContentIsoSymbolDefinition TEXT,
        ContentGeometryTemplate TEXT, PartVersion TEXT);""")

    cur.execute("""CREATE TABLE Port (
        PnPID INTEGER PRIMARY KEY, SizeRecordId GUID, PortName TEXT,
        NominalDiameter REAL, NominalUnit TEXT, MatchingPipeOd REAL,
        EndType TEXT, Facing TEXT, FlangeThickness REAL, PressureClass TEXT,
        LengthUnit TEXT);""")

    cur.execute("""CREATE TABLE PartPort (
        PnPID INTEGER PRIMARY KEY, PnPGuid BLOB, PnPTimestamp INT,
        Part INT, Port INT, Name TEXT);""")

    # Item 1: Clase 150 (debe ser incorporado)
    cur.execute("""INSERT INTO EngineeringItems (
        PnPID, PartFamilyLongDesc, PartSizeLongDesc, ShortDescription,
        Manufacturer, NominalDiameter, MatchingPipeOd, ConnectionPortCount,
        PressureClass, EndType, Facing, FlangeThickness,
        ContentGeometryTemplate, ContentGeometryParamDefinition, PartCategory
    ) VALUES (
        100, 'INTEC K200 Class 150# Flanged Ball Valve', 'INTEC K200 2in 150#', 'INTEC K200 150#',
        'KLINGER', 2.0, 2.375, 2, '150', 'FL', 'RF', 0.75,
        'INTEC_K200_BALL_VALVE', 'L=7.0,D=6.0,H=5.5,L1=11.5,OD=2.0', 'Valves'
    );""")
    cur.execute("""INSERT INTO Port (
        PnPID, PortName, NominalDiameter, NominalUnit, MatchingPipeOd,
        EndType, Facing, FlangeThickness, PressureClass, LengthUnit
    ) VALUES (101, 'S2', 2.0, 'in', 2.375, 'FL', 'RF', 0.75, '150', 'in');""")
    cur.execute("INSERT INTO PartPort (PnPID, Part, Port, Name) VALUES (200, 100, 101, 'S2');")

    # Item 2: Clase 300 (NO debe ser incorporado al spec 150)
    cur.execute("""INSERT INTO EngineeringItems (
        PnPID, PartFamilyLongDesc, PartSizeLongDesc, ShortDescription,
        Manufacturer, NominalDiameter, MatchingPipeOd, ConnectionPortCount,
        PressureClass, EndType, Facing, FlangeThickness,
        ContentGeometryTemplate, ContentGeometryParamDefinition, PartCategory
    ) VALUES (
        300, 'INTEC K200 Class 300# Flanged Ball Valve', 'INTEC K200 2in 300#', 'INTEC K200 300#',
        'KLINGER', 2.0, 2.375, 2, '300', 'FL', 'RF', 0.88,
        'INTEC_K200_BALL_VALVE', 'L=8.5,D=6.5,H=5.5,L1=11.5,OD=2.0', 'Valves'
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
    cur.execute("""CREATE TABLE Valve (
        PnPID INTEGER PRIMARY KEY, Length REAL, ValveAlignment TEXT, ValveDetail TEXT,
        ValveBodyType TEXT, FlowDependent INT, ValveBodyFamilyId BLOB, ValveBodyPartSizeId BLOB,
        ActuatorFamilyName TEXT, OperatorType TEXT, ActuatorType TEXT, ActuatorHeight REAL,
        ActuatorWidth REAL);""")
    cur.execute("""CREATE TABLE Port (
        PnPID INTEGER PRIMARY KEY, SizeRecordId BLOB, PortName TEXT, NominalDiameter REAL,
        NominalUnit TEXT, MatchingPipeOd REAL, EndType TEXT, Facing TEXT,
        FlangeThickness REAL, PressureClass TEXT, LengthUnit TEXT);""")
    cur.execute("""CREATE TABLE PartPort (
        PnPID INTEGER PRIMARY KEY, PnPGuid BLOB, PnPTimestamp INT,
        Part INT, Port INT, Name TEXT);""")
    cur.execute("""CREATE TABLE EngineeringItems (
        PnPID INTEGER PRIMARY KEY, PartFamilyId BLOB, CatalogPartFamilyId BLOB,
        PartFamilyLongDesc TEXT, PartSizeLongDesc TEXT, ShortDescription TEXT,
        Manufacturer TEXT, Material TEXT, MaterialCode TEXT, DesignStd TEXT,
        CompatibleStandard TEXT, Weight REAL, WeightUnit TEXT,
        ConnectionPortCount INT, SizeRecordId BLOB, PortName TEXT,
        NominalDiameter REAL, NominalUnit TEXT, MatchingPipeOd REAL,
        EndType TEXT, FlangeThickness REAL, Facing TEXT, PressureClass TEXT,
        LengthUnit TEXT, PartCategory TEXT, ContentDomain TEXT,
        ContentGeometryParamDefinition TEXT, ContentIsoSymbolDefinition TEXT,
        ContentGeometryTemplate TEXT, CatalogPartId INT, CatalogId TEXT,
        PartVersion TEXT);""")

    # Insertar componente nativo existente (tubo ASME) para verificar preservación
    cur.execute("INSERT INTO PnPBase (PnPID, PnPClassName) VALUES (1, 'Pipe');")
    cur.execute("INSERT INTO PipeRunComponent (PnPID) VALUES (1);")
    cur.execute("""INSERT INTO EngineeringItems (
        PnPID, PartFamilyLongDesc, ShortDescription, NominalDiameter,
        MatchingPipeOd, PartCategory, ContentGeometryTemplate
    ) VALUES (1, 'Pipe, Sch 40, CS, ASME B36.10', 'Pipe', 2.0, 2.375, 'Pipe', 'CPPI008001');""")

    conn.commit()
    conn.close()


class TestBuildPipingSpec(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.pcat = self.dir / "TEST_VALVES_Catalog.pcat"
        self.pspc = self.dir / "TEST_CS150.pspc"
        make_mock_pcat(self.pcat)
        make_mock_pspc(self.pspc)

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse_geometry_params(self):
        params = parse_geometry_params("L=7.0,D=6.0,H=5.5,L1=11.5,OD=2.0")
        self.assertEqual(params["L"], 7.0)
        self.assertEqual(params["D"], 6.0)
        self.assertEqual(params["H"], 5.5)
        self.assertEqual(params["L1"], 11.5)
        self.assertEqual(params["OD"], 2.0)

    def test_add_valves_to_piping_spec(self):
        res = add_valves_to_piping_spec(
            pcat_paths=[self.pcat],
            spec_pspc_path=self.pspc,
            target_pressure_class="150",
            backup=True
        )

        self.assertEqual(res["items_added"], 1)
        self.assertIn("INTEC_K200_BALL_VALVE", res["families"])
        self.assertTrue(Path(res["backup_path"]).exists())

        conn = sqlite3.connect(self.pspc)
        cur = conn.cursor()

        # Verificar que el tubo original sigue intacto
        cur.execute("SELECT COUNT(*) FROM EngineeringItems WHERE PartCategory = 'Pipe';")
        self.assertEqual(cur.fetchone()[0], 1)

        # Verificar que solo la válvula clase 150 fue añadida
        cur.execute("SELECT PnPID, NominalDiameter, PressureClass, ContentGeometryTemplate FROM EngineeringItems WHERE PartCategory = 'Valves';")
        valves = cur.fetchall()
        self.assertEqual(len(valves), 1)
        self.assertEqual(valves[0][1], 2.0)
        self.assertEqual(valves[0][2], "150")
        self.assertEqual(valves[0][3], "INTEC_K200_BALL_VALVE")

        # Verificar registro en Valve
        v_pnp = valves[0][0]
        cur.execute("SELECT Length, ActuatorType, ActuatorHeight FROM Valve WHERE PnPID = ?;", (v_pnp,))
        v_info = cur.fetchone()
        self.assertIsNotNone(v_info)
        self.assertEqual(v_info[0], 7.0)
        self.assertEqual(v_info[1], "HandLever")
        self.assertEqual(v_info[2], 5.5)

        # Verificar registro en Port y PartPort (puerto S2)
        cur.execute("SELECT Port FROM PartPort WHERE Part = ? AND Name = 'S2';", (v_pnp,))
        port_row = cur.fetchone()
        self.assertIsNotNone(port_row)
        port_id = port_row[0]

        cur.execute("SELECT NominalDiameter, MatchingPipeOd, EndType, Facing FROM Port WHERE PnPID = ?;", (port_id,))
        p_info = cur.fetchone()
        self.assertIsNotNone(p_info)
        self.assertEqual(p_info[0], 2.0)
        self.assertEqual(p_info[1], 2.375)
        self.assertEqual(p_info[2], "FL")
        self.assertEqual(p_info[3], "RF")

        conn.close()

    def test_idempotent_replaces_without_duplicate(self):
        add_valves_to_piping_spec([self.pcat], self.pspc, backup=False)
        add_valves_to_piping_spec([self.pcat], self.pspc, backup=False)

        conn = sqlite3.connect(self.pspc)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM EngineeringItems WHERE ContentGeometryTemplate = 'INTEC_K200_BALL_VALVE';")
        self.assertEqual(cur.fetchone()[0], 1)

        cur.execute("SELECT COUNT(*) FROM Valve;")
        self.assertEqual(cur.fetchone()[0], 1)

        cur.execute("SELECT COUNT(*) FROM PartPort;")
        self.assertEqual(cur.fetchone()[0], 1)

        conn.close()


if __name__ == "__main__":
    unittest.main()
