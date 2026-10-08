import tempfile
import unittest
import zipfile
from pathlib import Path

from builders.export_bundle import create_distribution_bundle, README_CONTENT, INSTALL_BAT_CONTENT


class TestExportBundle(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

        # Mock custom scripts dir
        self.scripts_dir = self.tmp_dir / "CustomScripts"
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        (self.scripts_dir / "my_comp.py").write_text("# my_comp", encoding="utf-8")
        (self.scripts_dir / "utils.py").write_text("# utils", encoding="utf-8")
        (self.scripts_dir / "ScriptGroup.xml").write_text("<xml/>", encoding="utf-8")

        # Mock catalogs
        self.catalogs_dir = self.tmp_dir / "Catalogs"
        self.catalogs_dir.mkdir(parents=True, exist_ok=True)
        (self.catalogs_dir / "MyPipingCatalog.pcat").write_bytes(b"PCAT_CONTENT")
        (self.catalogs_dir / "MySupportCatalog.acat").write_bytes(b"ACAT_CONTENT")

        # Mock specs
        self.specs_dir = self.tmp_dir / "Specs"
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        (self.specs_dir / "CS150_Soportes.pspc").write_bytes(b"PSPC_CONTENT")
        (self.specs_dir / "CS150_Soportes.pspx").write_bytes(b"PSPX_CONTENT")
        (self.specs_dir / "PipeSupportsSpec.pspc").write_bytes(b"SUPPORTS_PSPC")

    def test_bundle_creation_and_contents(self):
        out_zip = self.tmp_dir / "bundle.zip"
        created = create_distribution_bundle(
            output_zip=out_zip,
            scripts_dir=self.scripts_dir,
            catalogs_dir=self.catalogs_dir,
            specs_dir=self.specs_dir
        )

        self.assertTrue(created.exists())
        with zipfile.ZipFile(created, "r") as z:
            names = z.namelist()
            # Archivos raíz
            self.assertIn("LEEME_INSTALACION.txt", names)
            self.assertIn("instalar.bat", names)
            self.assertIn("probar_instalacion.lsp", names)

            # CustomScripts
            self.assertIn("CustomScripts/my_comp.py", names)
            self.assertIn("CustomScripts/utils.py", names)
            self.assertIn("CustomScripts/ScriptGroup.xml", names)

            # Catalogs
            self.assertIn("Catalogs/MyPipingCatalog.pcat", names)
            self.assertIn("Catalogs/MySupportCatalog.acat", names)

            # Specs
            self.assertIn("Specs/CS150_Soportes.pspc", names)
            self.assertIn("Specs/CS150_Soportes.pspx", names)
            self.assertIn("Specs/PipeSupportsSpec.pspc", names)

            # Check content
            readme_text = z.read("LEEME_INSTALACION.txt").decode("utf-8")
            self.assertEqual(readme_text, README_CONTENT)
            bat_text = z.read("instalar.bat").decode("utf-8")
            self.assertEqual(bat_text, INSTALL_BAT_CONTENT)
            self.assertEqual(z.read("Catalogs/MyPipingCatalog.pcat"), b"PCAT_CONTENT")
            self.assertEqual(z.read("Catalogs/MySupportCatalog.acat"), b"ACAT_CONTENT")
            self.assertEqual(z.read("Specs/CS150_Soportes.pspc"), b"PSPC_CONTENT")

    def test_catalog_filter(self):
        out_zip = self.tmp_dir / "filtered.zip"
        create_distribution_bundle(
            output_zip=out_zip,
            scripts_dir=self.scripts_dir,
            catalogs_dir=self.catalogs_dir,
            specs_dir=self.specs_dir,
            catalog_filter="Support"
        )

        with zipfile.ZipFile(out_zip, "r") as z:
            names = z.namelist()
            self.assertIn("Catalogs/MySupportCatalog.acat", names)
            self.assertNotIn("Catalogs/MyPipingCatalog.pcat", names)


if __name__ == "__main__":
    unittest.main()
