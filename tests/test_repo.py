import py_compile
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build

SOURCES = list(ROOT.glob("*.py")) + [
    p for sub in build.SOURCE_DIRS for p in (ROOT / sub).rglob("*.py")
    if p.name not in ("__init__.py",) and build.GENERATED_PREFIX
    not in p.read_text(encoding="utf-8", errors="ignore")
]


class TestComponentes(unittest.TestCase):
    def setUp(self):
        self.components = build.iter_components()

    def test_nombres_registrables_unicos(self):
        names = list(self.components)
        self.assertEqual(len(names), len(set(names)), "Nombres duplicados")

    def test_todos_tienen_puertos(self):
        for name, src in self.components.items():
            text = src.read_text(encoding="utf-8")
            self.assertIn("setPoint", text, f"{name} no define puertos (setPoint)")
            self.assertIn("setVector", text, f"{name} no define vectores (setVector)")

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
            [sys.executable, str(ROOT / "build.py"), "--check"],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_outputs_tienen_marcador(self):
        for name in build.iter_components():
            out = build.output_path(ROOT, name)
            self.assertTrue(out.exists(), f"Falta output aplanado {out.name}")
            self.assertIn(build.GENERATED_PREFIX, out.read_text(encoding="utf-8"),
                          f"{out.name} no fue generado por build.py")

    def test_fuentes_sin_marcador(self):
        for sub in build.SOURCE_DIRS:
            for p in (ROOT / sub).rglob("*.py"):
                if p.name == "__init__.py":
                    continue
                self.assertNotIn(build.GENERATED_PREFIX,
                                 p.read_text(encoding="utf-8", errors="ignore"),
                                 f"Fuente {p} tiene marcador de generado")


if __name__ == "__main__":
    unittest.main()
