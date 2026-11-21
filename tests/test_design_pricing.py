import unittest

import pandas as pd

from services.quote_calculations import (
    calculate_design_line,
    find_applicable_margin,
)


class DesignPricingTests(unittest.TestCase):
    def test_each_design_uses_its_own_quantity_margin(self):
        tiers = pd.DataFrame([
            {"Desde piezas": 1, "Hasta piezas": 29, "Margen (%)": 50.0},
            {"Desde piezas": 30, "Hasta piezas": 999999, "Margen (%)": 30.0},
        ])
        small_quantity = 20
        large_quantity = 1000
        small_margin = find_applicable_margin(tiers, small_quantity)
        large_margin = find_applicable_margin(tiers, large_quantity)
        self.assertEqual(small_margin, 50.0)
        self.assertEqual(large_margin, 30.0)

        small_design = calculate_design_line(
            small_quantity, 2, 5.0, 5.0, 0.0, 1.0, 2.0, 0.0, small_margin
        )
        large_design = calculate_design_line(
            large_quantity, 2, 5.0, 5.0, 0.0, 1.0, 100.0, 0.0, large_margin
        )
        self.assertAlmostEqual(
            small_design["price_total"],
            small_design["cost_total"] / 0.5,
        )
        self.assertAlmostEqual(
            large_design["price_total"],
            large_design["cost_total"] / 0.7,
        )
        self.assertNotEqual(
            small_design["price_unit"], large_design["price_unit"]
        )


if __name__ == "__main__":
    unittest.main()
