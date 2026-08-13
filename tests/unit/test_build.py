import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import build  # noqa: E402


def write(root, relpath, content):
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def component_body(name="SIMPLE_TEE", def_line=None):
    if def_line is None:
        def_line = f"def {name}(s, OD=1, L=2, T=0.1, **kw):"
    return "\n".join(
        [
            '"""Docstring del componente."""',
            "",
            "# comentario antes del codigo",
            "# otro comentario",
            "",
            "from varmain.primitiv import *",
            "from varmain.custom import *",
            "from math import *",
            "",
            "@activate(",
            '    Group="Tees",',
            '    TooltipShort="Simple Tee",',
            '    LengthUnit="in"',
            ")",
            "",
            def_line,
            "    R = OD / 2  # radio",
            "    s = CYLINDER(s, R=R, H=L)",
            "    s.setPoint(1, (0, 0, 0))  # entrada",
            "    s.setVector(1, (0, 0, -1))",
            "    s.setPoint(2, (0, 0, L))  # salida",
            "    s.setVector(2, (0, 0, 1))",
            "    return s",
            "",
        ]
    )


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.families_dir = self.root / "src" / "families"
        self.families_dir.mkdir(parents=True, exist_ok=True)

    def add_component(self, relpath, name="SIMPLE_TEE", def_line=None):
        return write(self.root, f"src/families/{relpath}", component_body(name, def_line))


class TestFindRegistrationName(BaseTestCase):
    def test_nombre_simple(self):
        path = self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        self.assertEqual(build.find_registration_name(path), "SIMPLE_TEE")

    def test_ignora_docstring_y_comentarios(self):
        path = self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        self.assertEqual(build.find_registration_name(path), "SIMPLE_TEE")

    def test_comentario_en_misma_linea_del_def(self):
        path = self.add_component(
            "tees/simple_tee.py", "SIMPLE_TEE",
            def_line="def SIMPLE_TEE(s, OD=1, L=2, T=0.1, **kw):  # el componente",
        )
        self.assertEqual(build.find_registration_name(path), "SIMPLE_TEE")

    def test_firma_multilinea(self):
        path = self.add_component(
            "tees/simple_tee.py", "SIMPLE_TEE",
            def_line="def SIMPLE_TEE(\n    s, OD=1, L=2, T=0.1, **kw,\n):",
        )
        self.assertEqual(build.find_registration_name(path), "SIMPLE_TEE")

    def test_helper_uppercase_antes_del_componente(self):
        content = (
            "def CALC_RADIUS(x):\n"
            "    return x / 2\n\n"
            + component_body("SIMPLE_TEE")
        )
        path = write(self.root, "src/families/tees/simple_tee.py", content)
        self.assertEqual(build.find_registration_name(path), "SIMPLE_TEE")

    def test_def_minuscula_no_registrable(self):
        path = self.add_component("tees/simple_tee.py", def_line="def simple_tee(s):")
        with self.assertRaises(ValueError):
            build.find_registration_name(path)

    def test_sin_activate_lanza_error(self):
        content = "def SIMPLE_TEE(s, OD=1, **kw):\n    return s\n"
        path = write(self.root, "src/families/tees/simple_tee.py", content)
        with self.assertRaises(ValueError):
            build.find_registration_name(path)

    def test_activate_sin_def_lanza_error(self):
        content = "@activate(Group='Tees')\npass\n"
        path = write(self.root, "src/families/tees/simple_tee.py", content)
        with self.assertRaises(ValueError):
            build.find_registration_name(path)


class TestIterComponents(BaseTestCase):
    def test_sin_componentes_lanza_builderror(self):
        with self.assertRaises(build.BuildError):
            build.iter_components(self.root)

    def test_encuentra_anidados(self):
        self.add_component("elbows/90/simple_elbow_90.py", "SIMPLE_ELBOW_90")
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        components = build.iter_components(self.root)
        self.assertEqual(
            set(components), {"SIMPLE_ELBOW_90", "SIMPLE_TEE"}
        )

    def test_ignora_init_py(self):
        write(self.root, "src/families/tees/__init__.py", "def FAKE_COMPONENT(s):\n    return s\n")
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        self.assertEqual(set(build.iter_components(self.root)), {"SIMPLE_TEE"})

    def test_ignora_archivos_con_prefijo_guion_bajo(self):
        write(self.root, "src/families/tees/_internal.py", component_body("SIMPLE_INTERNAL"))
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        self.assertEqual(set(build.iter_components(self.root)), {"SIMPLE_TEE"})

    def test_ignora_outputs_generados_en_subcarpetas(self):
        marker = build.GENERATED_MARKER.format(src="src/families/tees/simple_tee.py")
        write(self.root, "src/families/tees/simple_tee.py", marker + "\n" + component_body("SIMPLE_TEE"))
        with self.assertRaises(build.BuildError):
            build.iter_components(self.root)

    def test_duplicados_lanzan_builderror(self):
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        self.add_component("straight/union/simple_tee.py", "SIMPLE_TEE")
        with self.assertRaises(build.BuildError) as ctx:
            build.iter_components(self.root)
        self.assertIn("duplicado", str(ctx.exception))

    def test_no_recorre_carpetas_ajenas(self):
        write(self.root, "extras/foo.py", component_body("SIMPLE_FOO"))
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        self.assertEqual(set(build.iter_components(self.root)), {"SIMPLE_TEE"})

    def test_orden_determinista(self):
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        self.add_component("primitives/simple_box.py", "SIMPLE_BOX")
        first = list(build.iter_components(self.root))
        second = list(build.iter_components(self.root))
        self.assertEqual(first, second)
        self.assertEqual(first, sorted(first))


class TestListGeneratedInRoot(BaseTestCase):
    def _marker_file(self, name):
        return write(
            self.root, name,
            build.GENERATED_MARKER.format(src="src/families/tees/simple_tee.py")
            + "\n"
            + component_body("SIMPLE_TEE"),
        )

    def test_encuentra_solo_con_marcador(self):
        gen = self._marker_file("simple_tee.py")
        write(self.root, "manual.py", component_body("SIMPLE_MANUAL"))
        found = build.list_generated_in_root(self.root)
        self.assertEqual([p.name for p in found], ["simple_tee.py"])
        self.assertEqual(found[0], gen)

    def test_no_incluye_protegidos(self):
        write(self.root, "build.py", build.GENERATED_MARKER.format(src="x") + "\npass\n")
        write(self.root, "__init__.py", "# AUTOGENERATED by build.py -- do not edit\n")
        self.assertEqual(build.list_generated_in_root(self.root), [])

    def test_no_incluye_archivos_sin_marcador(self):
        write(self.root, "manual.py", component_body("SIMPLE_MANUAL"))
        self.assertEqual(build.list_generated_in_root(self.root), [])


class TestOutputPath(BaseTestCase):
    def test_nombre_con_familia(self):
        src = self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        self.assertEqual(build.output_path(self.root, src).name, "tees.simple_tee.py")
        src2 = self.add_component("primitives/hollow_cylinder.py", "HOLLOW_CYLINDER")
        self.assertEqual(build.output_path(self.root, src2).name, "primitives.hollow_cylinder.py")

    def test_content_tiene_marcador_y_cuerpo(self):
        src = self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        content = build.expected_content(self.root, src)
        self.assertTrue(content.startswith(build.GENERATED_PREFIX))
        self.assertIn("tees/simple_tee.py", content.splitlines()[0])
        self.assertIn("def SIMPLE_TEE(", content)


class TestFlatten(BaseTestCase):
    def test_genera_outputs_con_marcador(self):
        src1 = self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        src2 = self.add_component("primitives/simple_box.py", "SIMPLE_BOX")
        build.flatten(self.root)
        for src in (src1, src2):
            out = build.output_path(self.root, src)
            self.assertTrue(out.exists())
            text = out.read_text(encoding="utf-8")
            self.assertIn(build.GENERATED_PREFIX, text)

    def test_contenido_output_igual_a_fuente(self):
        src = self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        build.flatten(self.root)
        out = build.output_path(self.root, src)
        expected = build.expected_content(self.root, src)
        self.assertEqual(out.read_text(encoding="utf-8"), expected)

    def test_no_modifica_fuentes(self):
        src = self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        before = src.read_text(encoding="utf-8")
        build.flatten(self.root)
        self.assertEqual(src.read_text(encoding="utf-8"), before)

    def test_remueve_outputs_obsoletos(self):
        stale = write(
            self.root, "ghost.py",
            build.GENERATED_MARKER.format(src="src/families/tees/viejo.py") + "\npass\n",
        )
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        build.flatten(self.root)
        self.assertFalse(stale.exists())

    def test_no_toca_archivos_manuales_sin_marcador(self):
        manual = write(self.root, "manual.py", component_body("SIMPLE_MANUAL"))
        before = manual.read_text(encoding="utf-8")
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        build.flatten(self.root)
        self.assertEqual(manual.read_text(encoding="utf-8"), before)

    def test_componente_colisiona_con_protegido(self):
        # Un componente cuyo output {family}.{stem}.py coincide con PROTECTED.
        # Creamos familia "__init__" => output "__init__.__init__.py" no sirve.
        # Mejor: nombre de archivo que produzca colision directa.
        # Con naming {family}.{stem}.py, necesitamos family+stem = nombre protegido.
        # Imposible colision directa, pero build.py checa output_name in PROTECTED.
        # Creamos un test que verifica que _collisions detecta nombres protegidos.
        collisions = build._collisions({"build.py", "tees.simple_tee.py"})
        self.assertIn("build.py", collisions)
        self.assertNotIn("tees.simple_tee.py", collisions)

    def test_actualiza_gitignore(self):
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        build.flatten(self.root)
        gi = (self.root / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(build.GITIGNORE_START, gi)
        self.assertIn("/tees.simple_tee.py", gi)

    def test_devuelve_componentes(self):
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        result = build.flatten(self.root)
        self.assertEqual(set(result), {"SIMPLE_TEE"})


class TestSyncGitignore(BaseTestCase):
    def test_crea_bloque_si_no_existe(self):
        build.sync_gitignore(self.root, ["tees.simple_tee.py", "primitives.simple_box.py"])
        text = (self.root / ".gitignore").read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertIn(build.GITIGNORE_START, lines)
        self.assertIn(build.GITIGNORE_END, lines)
        self.assertIn("/primitives.simple_box.py", lines)
        self.assertIn("/tees.simple_tee.py", lines)

    def test_reemplaza_bloque_existente(self):
        write(self.root, ".gitignore",
              "# >>> generated by build.py\n/old_one.py\n# <<< generated by build.py\n")
        build.sync_gitignore(self.root, ["tees.simple_tee.py"])
        text = (self.root / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/tees.simple_tee.py", text)
        self.assertNotIn("/old_one.py", text)

    def test_preserva_contenido_ajeno(self):
        write(self.root, ".gitignore", "# Python\n__pycache__/\n*.xml\n")
        build.sync_gitignore(self.root, ["tees.simple_tee.py"])
        text = (self.root / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("__pycache__/", text)
        self.assertIn("*.xml", text)

    def test_no_duplica_bloque(self):
        build.sync_gitignore(self.root, ["tees.simple_tee.py"])
        build.sync_gitignore(self.root, ["tees.simple_tee.py"])
        text = (self.root / ".gitignore").read_text(encoding="utf-8")
        self.assertEqual(text.count(build.GITIGNORE_START), 1)

    def test_nombres_ordenados(self):
        build.sync_gitignore(self.root, ["zzz.py", "aaa.py"])
        lines = (self.root / ".gitignore").read_text(encoding="utf-8").splitlines()
        i_aaa = lines.index("/aaa.py")
        i_zzz = lines.index("/zzz.py")
        self.assertLess(i_aaa, i_zzz)


class TestCollectErrors(BaseTestCase):
    def test_ok_cuando_sincronizado(self):
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        build.flatten(self.root)
        self.assertEqual(build.collect_errors(self.root), [])

    def test_error_si_falta_output(self):
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        errors = build.collect_errors(self.root)
        self.assertTrue(any("Falta output" in e for e in errors))

    def test_error_si_output_desactualizado(self):
        src = self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        build.flatten(self.root)
        write(self.root, "src/families/tees/simple_tee.py", src.read_text(encoding="utf-8") + "pass\n")
        errors = build.collect_errors(self.root)
        self.assertTrue(any("desactualizado" in e for e in errors))

    def test_error_si_output_obsoleto(self):
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        build.flatten(self.root)
        write(self.root, "ghost.py",
              build.GENERATED_MARKER.format(src="src/families/tees/ghost.py") + "\npass\n")
        errors = build.collect_errors(self.root)
        self.assertTrue(any("obsoletos" in e for e in errors))
        self.assertIn("ghost.py", errors[0] if errors else "")

    def test_error_si_colision_con_protegido(self):
        # Con el naming {family}.{stem}.py, una colision real requiere que
        # el output coincida con un nombre protegido. Verificamos la logica
        # de _collisions directamente.
        collisions = build._collisions({"README.md", "tees.simple_tee.py"})
        self.assertIn("README.md", collisions)

    def test_error_doble_registro(self):
        self.add_component("tees/simple_tee.py", "SIMPLE_TEE")
        self.add_component("straight/simple_tee.py", "SIMPLE_TEE")
        with self.assertRaises(build.BuildError):
            build.collect_errors(self.root)


if __name__ == "__main__":
    unittest.main()
