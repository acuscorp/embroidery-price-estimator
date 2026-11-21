import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import repositories.design_repository as design_repository
import repositories.design_image_repository as image_repository
import repositories.quote_repository as quote_repository
from services.design_catalog import delete_catalog_design


class DesignCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "test.db"
        self.quote_db_patch = patch.object(quote_repository, "DB_PATH", database)
        self.design_db_patch = patch.object(design_repository, "DB_PATH", database)
        self.image_db_patch = patch.object(image_repository, "DB_PATH", database)
        self.image_dir_patch = patch.object(
            image_repository,
            "IMAGE_DIR",
            Path(self.temp_dir.name) / "images",
        )
        self.quote_db_patch.start()
        self.design_db_patch.start()
        self.image_db_patch.start()
        self.image_dir_patch.start()
        quote_repository.init_database()

    def tearDown(self):
        self.image_dir_patch.stop()
        self.image_db_patch.stop()
        self.design_db_patch.stop()
        self.quote_db_patch.stop()
        self.temp_dir.cleanup()

    def test_design_catalog_supports_create_read_update_archive_and_delete(self):
        design_id = design_repository.create_design("000", "Palomas")
        self.assertEqual(
            design_repository.create_design("000", "Palomas"), design_id
        )
        self.assertEqual(
            design_repository.list_designs()[0]["codigo"], "000-palomas"
        )

        design_repository.update_design(design_id, "100", "Angel")
        updated = design_repository.list_designs()[0]
        self.assertEqual(updated["codigo"], "100-angel")
        self.assertEqual(updated["nombre"], "Angel")

        design_repository.set_design_active(design_id, False)
        self.assertEqual(design_repository.list_designs(), [])
        with self.assertRaisesRegex(ValueError, "está archivado"):
            design_repository.create_design("100", "Angel")
        design_repository.set_design_active(design_id, True)
        self.assertEqual(design_repository.list_designs()[0]["activo"], 1)

        design_repository.set_design_active(design_id, False)
        self.assertEqual(
            design_repository.list_designs(include_archived=True)[0]["activo"],
            0,
        )

        delete_catalog_design(design_id)
        self.assertEqual(
            design_repository.list_designs(include_archived=True), []
        )

    def test_existing_design_table_is_migrated(self):
        with sqlite3.connect(quote_repository.DB_PATH) as connection:
            connection.execute("DROP TABLE disenos")
            connection.execute(
                """
                CREATE TABLE disenos (
                    id INTEGER PRIMARY KEY,
                    codigo TEXT NOT NULL UNIQUE,
                    categoria_codigo TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT INTO disenos
                    (id, codigo, categoria_codigo, nombre, created_at)
                VALUES (1, '000-palomas', '000', 'Palomas', '2026-01-01')
                """
            )
        quote_repository.init_database()
        migrated = design_repository.list_designs(include_archived=True)
        self.assertEqual(migrated[0]["nombre"], "Palomas")
        self.assertEqual(migrated[0]["activo"], 1)


if __name__ == "__main__":
    unittest.main()
