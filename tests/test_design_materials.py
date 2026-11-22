import unittest

import pandas as pd

from services.quote_calculations import calculate_design_materials


class DesignMaterialsTests(unittest.TestCase):
    def setUp(self):
        self.catalog = pd.DataFrame([
            {
                "Material": "Hilo",
                "Activo": True,
                "Precio presentación ($)": 50.0,
                "Contenido presentación": 100.0,
                "Unidad": "m",
            },
            {
                "Material": "Pellón",
                "Activo": True,
                "Precio presentación ($)": 20.0,
                "Contenido presentación": 10.0,
                "Unidad": "cm²",
            },
        ])

    def test_consumption_is_specific_to_each_design(self):
        first_details, first_total = calculate_design_materials(
            self.catalog,
            [
                {"Material": "Hilo", "Consumo por pieza": 2.0},
                {"Material": "Pellón", "Consumo por pieza": 0.0},
            ],
            3,
        )
        second_details, second_total = calculate_design_materials(
            self.catalog,
            [
                {"Material": "Hilo", "Consumo por pieza": 0.0},
                {"Material": "Pellón", "Consumo por pieza": 1.5},
            ],
            3,
        )

        self.assertAlmostEqual(first_total, 3.0)
        self.assertAlmostEqual(second_total, 9.0)
        self.assertAlmostEqual(
            first_details.loc[
                first_details["Material"] == "Hilo", "Costo total ($)"
            ].iloc[0],
            3.0,
        )
        self.assertAlmostEqual(
            second_details.loc[
                second_details["Material"] == "Pellón", "Costo total ($)"
            ].iloc[0],
            9.0,
        )

    def test_catalog_prices_override_legacy_global_consumption(self):
        legacy_catalog = self.catalog.assign(**{"Consumo por pieza": 100.0})
        details, total = calculate_design_materials(
            legacy_catalog,
            [{"Material": "Hilo", "Consumo por pieza": 2.0}],
            3,
        )

        self.assertAlmostEqual(total, 3.0)
        self.assertEqual(details["Material"].tolist(), ["Hilo"])


if __name__ == "__main__":
    unittest.main()
