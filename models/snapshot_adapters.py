from decimal import Decimal, InvalidOperation
from typing import Dict, Optional


def decimal_amount(value) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def adapt_legacy_quote_snapshot(snapshot: Dict) -> Dict:
    """Normaliza snapshots antiguos sin modificar ni eliminar el snapshot original."""
    if not isinstance(snapshot, dict):
        raise ValueError("El snapshot de cotización debe ser un objeto JSON.")

    result = dict(snapshot)
    result.setdefault("snapshot_version", 1)

    if "cliente" not in result:
        result["cliente"] = ""
    if "cliente_snapshot" not in result:
        result["cliente_snapshot"] = {
            "id": result.get("client_id"),
            "nombres": result.get("cliente", ""),
            "apellidos": "",
            "empresa": "",
            "telefono": result.get("telefono", ""),
            "correo": result.get("correo", ""),
        }

    result["folio"] = result.get("folio") or "Sin folio"
    result["precio_total"] = decimal_amount(result.get("precio_total"))
    result["precio_unitario"] = decimal_amount(result.get("precio_unitario"))

    widget_values = result.get("widget_values")
    if not isinstance(widget_values, dict):
        widget_values = {}
    result["widget_values"] = dict(widget_values)

    for collection_name in ("monthly_costs", "materials", "extras", "margin_tiers"):
        collection = result.get(collection_name)
        if not isinstance(collection, list):
            result[collection_name] = []

    return result


def get_snapshot_version(snapshot: Dict) -> int:
    try:
        version = int(snapshot.get("snapshot_version", 1))
    except (TypeError, ValueError):
        version = 1
    return max(1, version)
