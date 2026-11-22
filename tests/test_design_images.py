import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import repositories.design_image_repository as image_repository
import repositories.design_repository as design_repository
import repositories.quote_repository as quote_repository
from services.design_catalog import delete_catalog_design


def image_bytes(color):
    output = BytesIO()
    Image.new("RGB", (4, 4), color).save(output, format="PNG")
    return output.getvalue()


class DesignImageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        database = root / "test.db"
        self.quote_db_patch = patch.object(quote_repository, "DB_PATH", database)
        self.design_db_patch = patch.object(design_repository, "DB_PATH", database)
        self.image_db_patch = patch.object(image_repository, "DB_PATH", database)
        self.image_dir_patch = patch.object(image_repository, "IMAGE_DIR", root / "images")
        for patcher in (
            self.quote_db_patch,
            self.design_db_patch,
            self.image_db_patch,
            self.image_dir_patch,
        ):
            patcher.start()
        quote_repository.init_database()
        subcategory_id = design_repository.create_subcategory("Palomas")
        self.design_id = design_repository.create_design(
            "0000",
            subcategory_id,
            "Palomas",
            {"ancho_cm": 8.0, "alto_cm": 6.0},
        )

    def tearDown(self):
        for patcher in (
            self.image_dir_patch,
            self.image_db_patch,
            self.design_db_patch,
            self.quote_db_patch,
        ):
            patcher.stop()
        self.temp_dir.cleanup()

    def test_images_support_create_read_update_replace_and_delete(self):
        image_id = image_repository.create_design_image(
            self.design_id, image_bytes("red"), "Boceto inicial"
        )
        stored = image_repository.list_design_images(self.design_id)[0]
        self.assertEqual(stored["caption"], "Boceto inicial")
        self.assertTrue(stored["path"].is_file())
        old_path = stored["path"]

        image_repository.update_design_image(
            image_id, "Referencia final", image_bytes("blue")
        )
        updated = image_repository.list_design_images(self.design_id)[0]
        self.assertEqual(updated["caption"], "Referencia final")
        self.assertNotEqual(updated["path"], old_path)
        self.assertTrue(updated["path"].is_file())
        self.assertFalse(old_path.exists())

        image_repository.delete_design_image(image_id)
        self.assertEqual(image_repository.list_design_images(self.design_id), [])
        self.assertFalse(updated["path"].exists())

    def test_deleting_catalog_design_removes_related_images(self):
        image_repository.create_design_image(
            self.design_id, image_bytes("green"), "Referencia"
        )
        stored = image_repository.list_design_images(self.design_id)[0]
        delete_catalog_design(self.design_id)
        self.assertEqual(image_repository.list_design_images(self.design_id), [])
        self.assertFalse(stored["path"].exists())

    def test_invalid_upload_is_reported(self):
        with self.assertRaisesRegex(ValueError, "no es una imagen válida"):
            image_repository.create_design_image(
                self.design_id, b"not an image", "Archivo inválido"
            )


if __name__ == "__main__":
    unittest.main()
