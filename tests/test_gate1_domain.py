import unittest
from decimal import Decimal

from models.contracts import OrderStatus
from models.snapshot_adapters import adapt_legacy_quote_snapshot
from services.domain_rules import (
    DomainRuleError,
    calculate_order_status_after_adjustment,
    can_commit_quantity,
    can_cancel_order,
    can_deliver,
    can_update_in_production,
    net_delivered,
    payment_balance,
    prorate_cents,
    validate_quote_acceptance,
)


class Gate1DomainTests(unittest.TestCase):
    def test_quantity_assignment_never_exceeds_line_quantity(self):
        self.assertTrue(can_commit_quantity(100, [30, 40], 30))
        self.assertFalse(can_commit_quantity(100, [30, 40], 31))

    def test_proration_uses_cents_and_largest_remainder(self):
        allocations = prorate_cents(Decimal("10.00"), [Decimal("1"), Decimal("1"), Decimal("1")])
        self.assertEqual(allocations, [334, 333, 333])
        self.assertEqual(sum(allocations), 1000)

    def test_proration_splits_zero_subtotals_equally(self):
        allocations = prorate_cents(Decimal("1.00"), [Decimal("0"), Decimal("0"), Decimal("0")])
        self.assertEqual(allocations, [34, 33, 33])

    def test_cancelled_order_shows_refund_not_debt(self):
        result = payment_balance(
            Decimal("100"),
            [Decimal("150")],
            [Decimal("20")],
            cancelled=True,
        )
        self.assertEqual(result["balance"], Decimal("0.00"))
        self.assertEqual(result["refund_due"], Decimal("130.00"))

    def test_delivered_adjustment_automatically_returns_to_ready(self):
        status = calculate_order_status_after_adjustment(
            OrderStatus.DELIVERED,
            100,
            [100],
            [10],
        )
        self.assertEqual(status, OrderStatus.READY)
        self.assertEqual(net_delivered([100], [10]), 90)

    def test_cannot_deliver_more_than_pending_quantity(self):
        self.assertFalse(can_deliver(12, 100, [89], [0]))
        self.assertTrue(can_deliver(11, 100, [89], [0]))

    def test_cancelled_quote_cannot_be_accepted(self):
        with self.assertRaises(DomainRuleError):
            validate_quote_acceptance("Cancelada")

    def test_in_production_update_respects_delivered_net(self):
        self.assertTrue(can_update_in_production(OrderStatus.IN_PRODUCTION, 120, 50))
        self.assertFalse(can_update_in_production(OrderStatus.IN_PRODUCTION, 40, 50))

    def test_cancel_requires_pending_and_never_started(self):
        self.assertTrue(can_cancel_order(OrderStatus.PENDING, False))
        self.assertFalse(can_cancel_order(OrderStatus.PENDING, True))

    def test_legacy_snapshot_adapter_is_versioned_and_non_destructive(self):
        legacy = {"folio": "COT-1", "cliente": "Ana", "precio_total": "125.50"}
        adapted = adapt_legacy_quote_snapshot(legacy)
        self.assertEqual(adapted["snapshot_version"], 1)
        self.assertEqual(adapted["cliente_snapshot"]["nombres"], "Ana")
        self.assertNotIn("snapshot_version", legacy)


if __name__ == "__main__":
    unittest.main()
