"""Integracion de add_catalog_family contra SQLite en memoria.

Verifica en Linux lo que antes solo se veia en Windows: valores, unidades
y reseteo de herencia tal como quedarian en el .pcat.
"""
import sqlite3
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from builders import build_catalog as bc  # noqa: E402


def make_db():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE PnPBase (PnPID INTEGER PRIMARY KEY, PnPClassName TEXT, PnPStatus INT, PnPRevision INT, PnPGuid BLOB, PnPTimestamp INT);")
    cur.execute("CREATE TABLE PnPSys_PnPBase_PnPID (d TEXT);")
    cur.execute("""CREATE TABLE EngineeringItems (
        PnPID INTEGER PRIMARY KEY, PartFamilyId GUID, CatalogPartFamilyId GUID,
        PartFamilyLongDesc TEXT, PartSizeLongDesc TEXT, ShortDescription TEXT,
        Manufacturer TEXT, Material TEXT, MaterialCode TEXT, DesignStd TEXT,
        CompatibleStandard TEXT, ItemCode TEXT, Schedule TEXT, WallThickness REAL,
        EngagementLength REAL, Weight REAL, WeightUnit TEXT, ConnectionPortCount INT,
        SizeRecordId GUID, PortName TEXT, NominalDiameter REAL, NominalUnit TEXT,
        MatchingPipeOd REAL, EndType TEXT, PressureClass TEXT, Facing TEXT,
        FlangeStd TEXT, FlangeThickness REAL, LengthUnit TEXT, PartCategory TEXT,
        ContentDomain TEXT, PartVersion TEXT, ContentGeometryParamDefinition TEXT,
        ContentIsoSymbolDefinition TEXT, ContentGeometryTemplate TEXT, Status TEXT);""")
    cur.execute("CREATE TABLE PipeRunComponent (PnPID INTEGER);")
    cur.execute("CREATE TABLE ValveBody (PnPID INTEGER);")
    cur.execute("""CREATE TABLE Port (PnPID INTEGER PRIMARY KEY, SizeRecordId GUID,
        PortName TEXT, NominalDiameter REAL, NominalUnit TEXT, MatchingPipeOd REAL,
        EndType TEXT, FlangeStd TEXT, GasketStd TEXT, Facing TEXT, FlangeThickness REAL,
        PressureClass TEXT, Schedule TEXT, WallThickness REAL, EngagementLength REAL,
        LengthUnit TEXT);""")
    cur.execute("CREATE TABLE PartPort (PnPID INTEGER PRIMARY KEY, PnPGuid BLOB, PnPTimestamp INT, Part INT, Port INT, Name TEXT);")
    cur.execute("CREATE TABLE PnPRowRelations (ROWID INT, RELID INT, RelationshipTypeName TEXT);")
    conn.commit()
    return conn


def template_row():
    return {
        "Manufacturer": "TMPL", "Material": "TMPL", "MaterialCode": "TMPL",
        "DesignStd": "TEMPLATE-LEAK", "CompatibleStandard": "TEMPLATE-LEAK",
        "ItemCode": "LEAK", "Schedule": "LEAK", "WallThickness": 9.9,
        "EngagementLength": 9.9, "Weight": -1.0, "WeightUnit": "LB",
        "ConnectionPortCount": 2, "SizeRecordId": None, "PortName": "S1",
        "NominalDiameter": 0.0, "NominalUnit": "in", "MatchingPipeOd": 0.0,
        "EndType": "XX", "PressureClass": "999", "Facing": None, "FlangeStd": "LEAK",
        "FlangeThickness": 0.0, "LengthUnit": "in", "PartCategory": "Valves",
        "ContentDomain": "P3D", "PartVersion": "4_0",
        "ContentGeometryParamDefinition": "", "ContentIsoSymbolDefinition": "",
        "ContentGeometryTemplate": "", "Status": None,
        "PartFamilyId": None, "CatalogPartFamilyId": None,
        "PartFamilyLongDesc": "", "PartSizeLongDesc": "", "ShortDescription": "",
    }


def sizes_flanged_150():
    return [{
        "nd": 2.0, "part_num": "C15F2-2IN-150LBS", "OD": 2.0, "ports_count": 2,
        "params": {"L": 7.0079, "D": 3.5433, "OD": 2.0},
        "end_type": "FL", "manufacturer": "Saidi", "material": "WCB",
        "pressure_class": "150LBS", "weight": 0.0,
    }]


def sizes_threaded_800():
    return [{
        "nd": 0.5, "part_num": "C800NPT-1-2IN-800LBS", "OD": 0.5, "ports_count": 2,
        "params": {"L": 3.5433, "D": 0.0, "OD": 0.5},
        "end_type": "THDF", "manufacturer": "Saidi", "material": "CF8M",
        "pressure_class": "800LBS", "weight": 0.0,
    }]


class TestAddCatalogFamily(unittest.TestCase):
    def _row(self, conn, desc):
        cur = conn.cursor()
        cur.execute("SELECT * FROM EngineeringItems WHERE PartSizeLongDesc LIKE ?", (f"%{desc}%",))
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, cur.fetchone()))

    def test_flanged_150_row(self):
        conn = make_db()
        bc.add_catalog_family(
            conn, template_dict=dict(template_row()),
            family_desc="Saidi C15F2", short_desc="C15F2",
            script_name="BALL_VALVE_2PC_FLANGED", skey="VB",
            end_type="FL", pnp_class="ValveBody", category="Valves",
            sizes_list=sizes_flanged_150(),
        )
        row = self._row(conn, "C15F2-2IN-150LBS")
        self.assertEqual(row["NominalDiameter"], 2.0)
        self.assertEqual(row["NominalUnit"], "in")
        self.assertEqual(row["MatchingPipeOd"], 2.375)  # P1: B36.10, no nominal
        self.assertEqual(row["EndType"], "FL")
        self.assertEqual(row["PressureClass"], "150")
        self.assertEqual(row["Facing"], "RF")
        self.assertIsNone(row["FlangeStd"])  # como el oficial: vacio
        self.assertEqual(row["FlangeThickness"], 0.75)  # B16.5 150# 2"
        self.assertEqual(row["LengthUnit"], "in")
        self.assertEqual(row["WeightUnit"], "LB")
        self.assertIn("L=7.007900", row["ContentGeometryParamDefinition"])
        # P2: sin herencia del template
        self.assertEqual(row["DesignStd"], "")
        self.assertEqual(row["CompatibleStandard"], "ASME B16.10")
        self.assertEqual(row["ItemCode"], "")
        self.assertIsNone(row["Schedule"])

    def test_threaded_uses_thdf_and_b36(self):
        conn = make_db()
        bc.add_catalog_family(
            conn, template_dict=dict(template_row()),
            family_desc="Saidi C800NPT", short_desc="C800NPT",
            script_name="BALL_VALVE_1PC_COMPACT", skey="VB",
            end_type="THDF", pnp_class="ValveBody", category="Valves",
            sizes_list=sizes_threaded_800(),
        )
        row = self._row(conn, "C800NPT-1-2IN-800LBS")
        self.assertEqual(row["EndType"], "THDF")
        self.assertEqual(row["MatchingPipeOd"], 0.84)  # P1 tambien en roscadas
        self.assertEqual(row["PressureClass"], "800")
        self.assertEqual(row["FlangeThickness"], 0.0)  # sin brida: sin espesor

    def test_flange_thickness_per_class(self):
        for cls, expected in (("150LBS", 0.75), ("300LBS", 0.87), ("600LBS", 1.25)):
            conn = make_db()
            sizes = sizes_flanged_150()
            sizes[0]["pressure_class"] = cls
            bc.add_catalog_family(
                conn, template_dict=dict(template_row()),
                family_desc="F", short_desc="F",
                script_name="BALL_VALVE_2PC_FLANGED", skey="VB",
                end_type="FL", pnp_class="ValveBody", category="Valves",
                sizes_list=sizes,
            )
            row = self._row(conn, "C15F2-2IN-150LBS")
            self.assertEqual(row["FlangeThickness"], expected, f"clase {cls}")

    def test_weight_persisted(self):
        conn = make_db()
        sizes = sizes_flanged_150()
        sizes[0]["weight"] = 370.38
        bc.add_catalog_family(
            conn, template_dict=dict(template_row()),
            family_desc="F", short_desc="F",
            script_name="BALL_VALVE_2PC_FLANGED", skey="VB",
            end_type="FL", pnp_class="ValveBody", category="Valves",
            sizes_list=sizes,
        )
        row = self._row(conn, "C15F2-2IN-150LBS")
        self.assertEqual(row["Weight"], 370.38)

    def test_ports_created_with_units(self):
        conn = make_db()
        bc.add_catalog_family(
            conn, template_dict=dict(template_row()),
            family_desc="F", short_desc="F",
            script_name="BALL_VALVE_2PC_FLANGED", skey="VB",
            end_type="FL", pnp_class="ValveBody", category="Valves",
            sizes_list=sizes_flanged_150(),
        )
        cur = conn.cursor()
        cur.execute("SELECT PortName, NominalDiameter, NominalUnit, MatchingPipeOd, EndType, PressureClass, LengthUnit FROM Port;")
        ports = cur.fetchall()
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0], ("S2", 2.0, "in", 2.375, "FL", "150", "in"))


if __name__ == "__main__":
    unittest.main()
