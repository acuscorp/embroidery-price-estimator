import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import repositories.client_repository as client_repository
import repositories.quote_repository as quote_repository


class ClientCrudTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "test.db"
        self.quote_db_patch = patch.object(quote_repository, "DB_PATH", database)
        self.client_db_patch = patch.object(client_repository, "DB_PATH", database)
        self.quote_db_patch.start()
        self.client_db_patch.start()
        quote_repository.init_database()
        self.client_id = client_repository.create_client({
            "nombres": "Ana",
            "apellidos": "López",
            "empresa": "",
            "telefono": "",
            "correo": "",
            "direccion": "",
            "notas": "",
        })

    def tearDown(self):
        self.client_db_patch.stop()
        self.quote_db_patch.stop()
        self.temp_dir.cleanup()

    def test_client_without_quotes_can_be_deleted(self):
        self.assertEqual(client_repository.client_quote_count(self.client_id), 0)
        client_repository.delete_client(self.client_id)
        self.assertIsNone(client_repository.get_client(self.client_id))

    def test_client_with_quote_history_must_be_archived_not_deleted(self):
        quote_repository.save_quote(
            "COT-1",
            "Ana López",
            "",
            "",
            "Borrador",
            date.today(),
            {"precio_unitario": 10.0, "precio_total": 10.0},
            client_id=self.client_id,
        )
        self.assertEqual(client_repository.client_quote_count(self.client_id), 1)
        with self.assertRaisesRegex(ValueError, "con cotizaciones relacionadas"):
            client_repository.delete_client(self.client_id)
        self.assertIsNotNone(client_repository.get_client(self.client_id))


if __name__ == "__main__":
    unittest.main()
