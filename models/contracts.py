from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional


class QuoteStatus(str, Enum):
    DRAFT = "Borrador"
    ACCEPTED = "Aceptada"
    CANCELLED = "Cancelada"


class OrderStatus(str, Enum):
    PENDING = "Pendiente"
    IN_PRODUCTION = "En producción"
    READY = "Listo para entregar"
    DELIVERED = "Entregado"
    CANCELLED = "Cancelado"


class PaymentMethod(str, Enum):
    CASH = "efectivo"
    TRANSFER = "transferencia"
    CARD = "tarjeta"
    OTHER = "otro"


class UserRole(str, Enum):
    ADMIN = "Administrador"
    OPERATOR = "Operador"


@dataclass(frozen=True)
class ClientSnapshot:
    id: Optional[int]
    names: str = ""
    surnames: str = ""
    company: str = ""
    phone: str = ""
    email: str = ""


@dataclass(frozen=True)
class QuoteLine:
    line_id: str
    lineage_id: str
    quantity: int
    design_snapshot: Dict[str, object] = field(default_factory=dict)
    measures: Dict[str, object] = field(default_factory=dict)
    agreed_price_total: Decimal = Decimal("0")


@dataclass(frozen=True)
class QuoteAcceptance:
    accepted_at: str
    actor_id: str
    medium: str


@dataclass(frozen=True)
class Quote:
    id: int
    folio: str
    status: QuoteStatus
    client_snapshot: ClientSnapshot
    lines: List[QuoteLine]
    direct_charges: List[Dict[str, object]] = field(default_factory=list)
    acceptance: Optional[QuoteAcceptance] = None
    snapshot_version: int = 1


@dataclass(frozen=True)
class OrderVersion:
    version_id: str
    order_id: str
    quote_id: int
    quote_line_id: str
    lineage_id: str
    design_snapshot: Dict[str, object]
    quantity: int
    total: Decimal
    is_current: bool = True


@dataclass(frozen=True)
class Delivery:
    id: str
    date: str
    quantity: int


@dataclass(frozen=True)
class DeliveryAdjustment:
    id: str
    delivery_id: str
    date: str
    quantity: int


@dataclass(frozen=True)
class Order:
    id: str
    folio: str
    status: OrderStatus
    started_work: bool
    quantity: int
    quote_line_id: str
    lineage_id: str
    design_snapshot: Dict[str, object]
    deliveries: List[Delivery] = field(default_factory=list)
    adjustments: List[DeliveryAdjustment] = field(default_factory=list)
    versions: List[OrderVersion] = field(default_factory=list)


@dataclass(frozen=True)
class Payment:
    id: str
    order_id: str
    date: str
    amount: Decimal
    method: PaymentMethod
    note: str = ""


@dataclass(frozen=True)
class Refund:
    id: str
    order_id: str
    date: str
    amount: Decimal
    note: str = ""


@dataclass(frozen=True)
class User:
    id: str
    username_normalized: str
    password_hash: str
    role: UserRole
    active: bool = True


@dataclass(frozen=True)
class AuditEvent:
    id: str
    actor_id: str
    operation: str
    entity_type: str
    entity_id: str
    occurred_at: str
    details: Dict[str, object] = field(default_factory=dict)
