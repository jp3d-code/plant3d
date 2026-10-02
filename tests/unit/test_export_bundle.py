import tempfile
import unittest
import zipfile
from pathlib import Path

from builders.export_bundle import create_distribution_bundle, README_CONTENT


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

    def test_bundle_creation_and_contents(self):
        out_zip = self.tmp_dir / "bundle.zip"
        created = create_distribution_bundle(
            output_zip=out_zip,
            scripts_dir=self.scripts_dir,
            catalogs_dir=self.catalogs_dir
        )

        self.assertTrue(created.exists())
        with zipfile.ZipFile(created, "r") as z:
            names = z.namelist()
            self.assertIn("LEEME_INSTALACION.txt", names)
            self.assertIn("CustomScripts/my_comp.py", names)
            self.assertIn("CustomScripts/utils.py", names)
            self.assertIn("CustomScripts/ScriptGroup.xml", names)
            self.assertIn("Catalogs/MyPipingCatalog.pcat", names)
            self.assertIn("Catalogs/MySupportCatalog.acat", names)

            # Check content
            readme_text = z.read("LEEME_INSTALACION.txt").decode("utf-8")
            self.assertEqual(readme_text, README_CONTENT)
            self.assertEqual(z.read("Catalogs/MyPipingCatalog.pcat"), b"PCAT_CONTENT")
            self.assertEqual(z.read("Catalogs/MySupportCatalog.acat"), b"ACAT_CONTENT")

    def test_catalog_filter(self):
        out_zip = self.tmp_dir / "filtered.zip"
        create_distribution_bundle(
            output_zip=out_zip,
            scripts_dir=self.scripts_dir,
            catalogs_dir=self.catalogs_dir,
            catalog_filter="Support"
        )

        with zipfile.ZipFile(out_zip, "r") as z:
            names = z.namelist()
            self.assertIn("Catalogs/MySupportCatalog.acat", names)
            self.assertNotIn("Catalogs/MyPipingCatalog.pcat", names)


if __name__ == "__main__":
    unittest.main()
