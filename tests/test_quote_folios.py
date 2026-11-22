import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import repositories.quote_repository as quote_repository


class QuoteFolioTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "test.db"
        self.db_patch = patch.object(quote_repository, "DB_PATH", database)
        self.db_patch.start()
        quote_repository.init_database()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def save(self, folio, price):
        return quote_repository.save_quote(
            folio,
            "Cliente de prueba",
            "",
            "",
            "Borrador",
            date(2026, 11, 21),
            {"precio_unitario": price, "precio_total": price},
        )

    def test_auto_folio_is_daily_sequential_and_saved_in_snapshot(self):
        class FrozenDate(date):
            @classmethod
            def today(cls):
                return cls(2026, 11, 21)

        with patch.object(quote_repository, "date", FrozenDate):
            first_id = self.save("", 10.0)
            second_id = self.save("", 20.0)
        first = quote_repository.get_quote(first_id)
        second = quote_repository.get_quote(second_id)

        self.assertEqual(first["folio"], "COT-20261121-0001")
        self.assertEqual(second["folio"], "COT-20261121-0002")
        self.assertEqual(
            json.loads(first["datos_json"])["folio"],
            first["folio"],
        )

    def test_editing_quote_keeps_its_original_folio(self):
        quote_id = self.save("", 10.0)
        original = quote_repository.get_quote(quote_id)["folio"]
        self.save(original, 25.0)
        quotes = quote_repository.list_quotes()

        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0]["folio"], original)
        self.assertEqual(quotes[0]["precio_total"], 25.0)


if __name__ == "__main__":
    unittest.main()
