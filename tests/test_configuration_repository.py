import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import repositories.configuration_repository as configuration_repository
import repositories.quote_repository as quote_repository


class ConfigurationRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "test.db"
        self.db_patch = patch.object(quote_repository, "DB_PATH", database)
        self.db_patch.start()
        quote_repository.init_database()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_configuration_is_saved_and_loaded_from_database(self):
        configuration = {
            "monthly_costs": [
                {
                    "Concepto": "Renta",
                    "Activo": True,
                    "Costo mensual ($)": 3450.0,
                }
            ],
            "materials": [
                {
                    "Material": "Hilo",
                    "Activo": True,
                    "Precio presentación ($)": 90.0,
                    "Contenido presentación": 5000.0,
                    "Unidad": "m",
                }
            ],
            "extras": [
                {
                    "Concepto": "Envío",
                    "Activo": True,
                    "Importe ($)": 250.0,
                }
            ],
            "monthly_goal": 12000.0,
            "idle_pct": 12.5,
            "work_hours": 7.5,
            "work_days": 24,
            "operator_monthly_pay": 9000.0,
            "heads": 4,
            "machine_heads_note": True,
        }

        self.assertIsNone(configuration_repository.get_configuration())
        configuration_repository.save_configuration(configuration)

        self.assertEqual(
            configuration_repository.get_configuration(),
            configuration,
        )

    def test_configuration_rejects_non_finite_numbers(self):
        with self.assertRaises(ValueError):
            configuration_repository.save_configuration(
                {"monthly_goal": float("nan")}
            )

        self.assertIsNone(configuration_repository.get_configuration())

    def test_defaults_load_with_25000_goal_and_no_order_specific_costs(self):
        configuration = configuration_repository.with_default_configuration(None)

        self.assertEqual(configuration["monthly_goal"], 25000.0)
        self.assertEqual(
            len(configuration["monthly_costs"]),
            len(configuration_repository.DEFAULT_CONFIGURATION["monthly_costs"]),
        )
        self.assertEqual(
            len(configuration["materials"]),
            len(configuration_repository.DEFAULT_CONFIGURATION["materials"]),
        )
        self.assertNotIn("extras", configuration)

    def test_existing_configuration_with_empty_goal_uses_25000_default(self):
        configuration = configuration_repository.with_default_configuration(
            {"monthly_goal": None, "heads": 4}
        )

        self.assertEqual(configuration["monthly_goal"], 25000.0)
        self.assertEqual(configuration["heads"], 4)

    def test_existing_empty_config_tables_restore_their_defaults(self):
        configuration = configuration_repository.with_default_configuration(
            {
                "monthly_costs": [],
                "materials": [],
                "extras": [{"Concepto": "Old global extra"}],
                "monthly_goal": None,
                "idle_pct": None,
                "work_hours": None,
                "work_days": None,
                "operator_monthly_pay": None,
                "heads": None,
                "machine_heads_note": None,
            }
        )

        self.assertEqual(configuration["monthly_costs"],
                         configuration_repository.DEFAULT_CONFIGURATION["monthly_costs"])
        self.assertEqual(configuration["materials"],
                         configuration_repository.DEFAULT_CONFIGURATION["materials"])
        self.assertNotIn("extras", configuration)
        self.assertEqual(configuration["monthly_goal"], 25000.0)
        self.assertEqual(configuration["idle_pct"], 10.0)
        self.assertEqual(configuration["work_hours"], 8.0)
        self.assertEqual(configuration["work_days"], 26)
        self.assertEqual(configuration["operator_monthly_pay"], 8000.0)
        self.assertEqual(configuration["heads"], 2)
        self.assertTrue(configuration["machine_heads_note"])

    def test_explicit_monthly_goal_is_preserved(self):
        configuration = configuration_repository.with_default_configuration(
            {"monthly_goal": 17500.0}
        )

        self.assertEqual(configuration["monthly_goal"], 17500.0)


if __name__ == "__main__":
    unittest.main()
