from decimal import Decimal, ROUND_DOWN
from typing import Iterable, Sequence

from models.contracts import OrderStatus


CENT = Decimal("0.01")


class DomainRuleError(ValueError):
    pass


def ensure_positive_quantity(quantity: int) -> None:
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        raise DomainRuleError("La cantidad debe ser un entero mayor que cero.")


def can_commit_quantity(line_quantity: int, currently_committed: Iterable[int], requested: int) -> bool:
    ensure_positive_quantity(line_quantity)
    ensure_positive_quantity(requested)
    committed = sum(currently_committed)
    return committed + requested <= line_quantity


def prorate_cents(total: Decimal, subtotals: Sequence[Decimal]) -> list:
    if total < 0:
        raise DomainRuleError("El cargo directo no puede ser negativo.")
    if not subtotals:
        return []

    total_cents = int((total * 100).quantize(CENT, rounding=ROUND_DOWN))
    subtotal_sum = sum(subtotals, Decimal("0"))
    if subtotal_sum == 0:
        quotient, remainder = divmod(total_cents, len(subtotals))
        return [quotient + (1 if index < remainder else 0) for index in range(len(subtotals))]

    raw_cents = [total_cents * subtotal / subtotal_sum for subtotal in subtotals]
    allocations = [int(raw.to_integral_value(rounding=ROUND_DOWN)) for raw in raw_cents]
    remaining = total_cents - sum(allocations)
    remainders = sorted(
        range(len(raw_cents)),
        key=lambda index: (raw_cents[index] - allocations[index], subtotals[index]),
        reverse=True,
    )
    for index in remainders[:remaining]:
        allocations[index] += 1
    return allocations


def net_delivered(deliveries: Iterable[int], adjustments: Iterable[int]) -> int:
    net = sum(deliveries) - sum(adjustments)
    return max(0, net)


def can_deliver(quantity_requested: int, quantity_ordered: int, deliveries: Iterable[int], adjustments: Iterable[int]) -> bool:
    ensure_positive_quantity(quantity_requested)
    ensure_positive_quantity(quantity_ordered)
    return quantity_requested <= quantity_ordered - net_delivered(deliveries, adjustments)


def calculate_order_status_after_adjustment(
    current_status: OrderStatus,
    quantity_ordered: int,
    deliveries: Iterable[int],
    adjustments: Iterable[int],
) -> OrderStatus:
    net = net_delivered(deliveries, adjustments)
    if net < quantity_ordered and current_status == OrderStatus.DELIVERED:
        return OrderStatus.READY
    if net >= quantity_ordered:
        return OrderStatus.DELIVERED
    return current_status


def can_cancel_order(status: OrderStatus, started_work: bool) -> bool:
    return status == OrderStatus.PENDING and not started_work


def can_accept_quote(status: str) -> bool:
    return status == "Aceptada"


def validate_quote_acceptance(status: str) -> None:
    if status == "Cancelada":
        raise DomainRuleError("Una cotización cancelada no puede ser aceptada.")


def payment_balance(total: Decimal, payments: Iterable[Decimal], refunds: Iterable[Decimal], cancelled: bool = False) -> dict:
    paid_net = sum(payments, Decimal("0")) - sum(refunds, Decimal("0"))
    if cancelled:
        return {"balance": Decimal("0.00"), "refund_due": max(paid_net, Decimal("0.00"))}
    balance = total - paid_net
    if balance < 0:
        return {"balance": Decimal("0.00"), "refund_due": -balance}
    return {"balance": balance, "refund_due": Decimal("0.00")}


def can_retrograde_from(current_status: OrderStatus, next_status: OrderStatus) -> bool:
    if current_status == OrderStatus.CANCELLED:
        return False
    if next_status == OrderStatus.PENDING:
        return True
    if current_status == OrderStatus.DELIVERED:
        return next_status in (
            OrderStatus.READY,
            OrderStatus.IN_PRODUCTION,
            OrderStatus.PENDING,
        )
    return True


def can_update_in_production(status: OrderStatus, quantity: int, delivered_net: int) -> bool:
    ensure_positive_quantity(quantity)
    return status == OrderStatus.IN_PRODUCTION and quantity >= delivered_net
