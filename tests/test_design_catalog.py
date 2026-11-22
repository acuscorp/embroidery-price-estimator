import json
import sqlite3
import tempfile
import unittest
from datetime import date
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

    def make_design(self, category, subcategory_id, name, width=8.5, height=6.0):
        return design_repository.create_design(
            category,
            subcategory_id,
            name,
            {"ancho_cm": width, "alto_cm": height},
        )

    def test_subcategory_ids_are_unique_and_not_reused(self):
        first_id = design_repository.create_subcategory("Cruz")
        second_id = design_repository.create_subcategory("Cristo")
        with self.assertRaisesRegex(ValueError, "Ya existe"):
            design_repository.create_subcategory(" CRUZ ")

        design_repository.delete_subcategory(first_id)
        replacement_id = design_repository.create_subcategory("Angel")

        self.assertNotEqual(first_id, second_id)
        self.assertGreater(replacement_id, second_id)

    def test_design_codes_increment_and_preserve_dimensions(self):
        subcategory_id = design_repository.create_subcategory("Palomas")
        first_id = self.make_design("0000", subcategory_id, "Palomas 1")
        second_id = self.make_design("0000", subcategory_id, "Palomas 2")
        first, second = design_repository.list_designs()

        self.assertEqual(first["id"], first_id)
        self.assertEqual(second["id"], second_id)
        self.assertEqual(first["codigo"], "0000-0001-0001")
        self.assertEqual(second["codigo"], "0000-0001-0002")
        self.assertEqual(first["configuracion"]["ancho_cm"], 8.5)
        self.assertEqual(first["configuracion"]["alto_cm"], 6.0)

    def test_deleted_design_number_is_not_reused_and_update_gets_new_group_code(self):
        first_subcategory = design_repository.create_subcategory("Cruz")
        second_subcategory = design_repository.create_subcategory("Anillos")
        first_id = self.make_design("0000", first_subcategory, "Diseño 1")
        second_id = self.make_design("0000", first_subcategory, "Diseño 2")

        design_repository.update_design(
            first_id,
            "1000",
            second_subcategory,
            "Diseño movido",
            {"ancho_cm": 4.0, "alto_cm": 3.0},
        )
        moved = design_repository.get_design(first_id)
        self.assertEqual(moved["codigo"], "1000-0002-0001")

        delete_catalog_design(second_id)
        next_id = self.make_design("0000", first_subcategory, "Diseño 3")
        next_design = design_repository.get_design(next_id)
        self.assertEqual(next_design["codigo"], "0000-0001-0003")

    def test_quote_only_design_gets_a_consecutive_without_entering_catalog(self):
        subcategory_id = design_repository.create_subcategory("Angel")
        item = {
            "id": "quote-design-1",
            "catalog_id": None,
            "category_id": "2000",
            "categoria_codigo": "2000",
            "subcategory_id": subcategory_id,
            "design_number": None,
            "codigo": f"2000-{subcategory_id:04d}-pendiente",
            "nombre": "Angel pequeño",
            "ancho_cm": 5.0,
            "alto_cm": 7.0,
        }
        snapshot = {
            "precio_unitario": 2.0,
            "precio_total": 20.0,
            "design_items": [dict(item)],
            "disenos": [dict(item)],
        }
        quote_id = quote_repository.save_quote(
            "",
            "Cliente",
            "",
            "",
            "Borrador",
            date(2026, 11, 21),
            snapshot,
        )
        saved = json.loads(
            quote_repository.get_quote(quote_id)["datos_json"]
        )

        self.assertEqual(
            saved["design_items"][0]["codigo"],
            f"2000-{subcategory_id:04d}-0001",
        )
        self.assertEqual(saved["design_items"][0]["design_number"], 1)
        self.assertEqual(design_repository.list_designs(), [])

    def test_existing_design_table_migrates_idempotently(self):
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
        first_migration = design_repository.get_design(1)
        quote_repository.init_database()
        second_migration = design_repository.get_design(1)

        self.assertEqual(first_migration["nombre"], "Palomas")
        self.assertEqual(first_migration["codigo"], "0000-0001-0001")
        self.assertEqual(
            first_migration["configuracion"]["ancho_cm"], 0.0
        )
        self.assertEqual(second_migration["codigo"], first_migration["codigo"])
        self.assertEqual(
            second_migration["subcategory_id"],
            first_migration["subcategory_id"],
        )


if __name__ == "__main__":
    unittest.main()
