from pathlib import Path
from typing import Dict, Optional, TypedDict


DESIGN_CATEGORIES: Dict[str, str] = {
    "000": "Boda",
    "100": "Bautizo",
    "200": "XV",
}


class DesignCatalogRecord(TypedDict):
    id: int
    codigo: str
    categoria_codigo: str
    nombre: str
    activo: int


class DesignImageRecord(TypedDict):
    id: int
    design_id: int
    filename: str
    mime_type: str
    caption: str
    created_at: str
    updated_at: str
    path: Path


class DesignQuoteLine(TypedDict):
    id: str
    catalog_id: Optional[int]
    codigo: str
    categoria_codigo: str
    categoria_nombre: str
    nombre: str
    cantidad: int
    bordado_minutos: float
    preparacion_minutos: float
    minutos_adicionales: float


class DesignPriceResult(TypedDict):
    runs: int
    machine_minutes: float
    operator_minutes: float
    combined_order_minutes: float
    allocation_cost: float
    cost_total: float
    cost_unit: float
    price_total: float
    price_unit: float


class QuotedDesignLine(DesignQuoteLine, DesignPriceResult):
    materiales_total: float
    costo_antes_otros_directos: float
    otros_directos_asignados: float
    margen_pct: float
