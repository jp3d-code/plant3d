import py_compile
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from builders import build

CATALOGS_DIR = ROOT / "src" / "catalogs"
FAMILIES_DIR = ROOT / "src" / "families"

ALL_SRC_DIRS = [CATALOGS_DIR, FAMILIES_DIR]

SOURCES = list(ROOT.glob("*.py")) + list((ROOT / "builders").glob("*.py")) + [
    p for d in ALL_SRC_DIRS if d.is_dir() for p in d.rglob("*.py")
    if p.name not in ("__init__.py",) and build.GENERATED_PREFIX
    not in p.read_text(encoding="utf-8", errors="ignore")
]


class TestComponentes(unittest.TestCase):
    def setUp(self):
        self.components = build.iter_components(ROOT)

    def test_nombres_registrables_unicos(self):
        names = list(self.components)
        self.assertEqual(len(names), len(set(names)), "Nombres duplicados")

    def test_todos_tienen_puertos(self):
        for name, src in self.components.items():
            text = src.read_text(encoding="utf-8")
            self.assertIn("setPoint", text, f"{name} no define puertos (setPoint)")
            self.assertIn("Ports=", text, f"{name} no declara Ports= en @activate")

    def test_todos_tienen_activate(self):
        for name, src in self.components.items():
            self.assertIn("@activate", src.read_text(encoding="utf-8"),
                          f"{name} no tiene decorador @activate")

    def test_sintaxis_valida(self):
        for src in SOURCES:
            with self.subTest(file=src.name):
                py_compile.compile(str(src), doraise=True)


class TestBuild(unittest.TestCase):
    def test_check_pasa(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "builders" / "build.py"), "--check"],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fuentes_sin_marcador(self):
        for d in ALL_SRC_DIRS:
            if not d.is_dir():
                continue
            for p in d.rglob("*.py"):
                if p.name == "__init__.py":
                    continue
                self.assertNotIn(build.GENERATED_PREFIX,
                                 p.read_text(encoding="utf-8", errors="ignore"),
                                 f"Fuente {p} tiene marcador de generado")


if __name__ == "__main__":
    unittest.main()
