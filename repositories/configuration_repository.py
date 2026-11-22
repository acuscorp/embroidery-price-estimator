import copy
import json
import sqlite3
from datetime import datetime

import repositories.quote_repository as quote_repository


DEFAULT_CONFIGURATION = {
    "monthly_costs": [
        {"Concepto": "Renta", "Activo": True, "Costo mensual ($)": 3000.0},
        {"Concepto": "Electricidad", "Activo": True, "Costo mensual ($)": 500.0},
        {"Concepto": "Internet", "Activo": True, "Costo mensual ($)": 390.0},
        {"Concepto": "Agua para beber", "Activo": True, "Costo mensual ($)": 120.0},
        {"Concepto": "Limpieza del taller", "Activo": True, "Costo mensual ($)": 200.0},
        {
            "Concepto": "Lubricantes y consumibles de máquina",
            "Activo": True,
            "Costo mensual ($)": 200.0,
        },
        {"Concepto": "Depreciación", "Activo": True, "Costo mensual ($)": 1500.0},
        {"Concepto": "Reserva de refacciones", "Activo": True, "Costo mensual ($)": 250.0},
    ],
    "monthly_goal": 25000.0,
    "idle_pct": 10.0,
    "work_hours": 8.0,
    "work_days": 26,
    "operator_monthly_pay": 8000.0,
    "materials": [
        {
            "Material": "Hilo superior",
            "Activo": True,
            "Precio presentación ($)": 45.0,
            "Contenido presentación": 5000.0,
            "Unidad": "m",
        },
        {
            "Material": "Hilo de bobina",
            "Activo": True,
            "Precio presentación ($)": 220.0,
            "Contenido presentación": 72000.0,
            "Unidad": "m",
        },
        {
            "Material": "Pellón",
            "Activo": True,
            "Precio presentación ($)": 900.0,
            "Contenido presentación": 1400000.0,
            "Unidad": "cm²",
        },
    ],
    "extras": [
        {"Concepto": "Digitalización", "Activo": False, "Importe ($)": 0.0},
        {"Concepto": "Empaque especial", "Activo": False, "Importe ($)": 0.0},
        {"Concepto": "Envío", "Activo": False, "Importe ($)": 0.0},
        {"Concepto": "Proceso externo", "Activo": False, "Importe ($)": 0.0},
    ],
    "heads": 2,
    "machine_heads_note": True,
}


def with_default_configuration(configuration):
    resolved = copy.deepcopy(DEFAULT_CONFIGURATION)
    if configuration:
        resolved.update(configuration)
    for name in ("monthly_costs", "materials", "extras"):
        if not isinstance(resolved[name], list) or not resolved[name]:
            resolved[name] = copy.deepcopy(DEFAULT_CONFIGURATION[name])
    for name in (
        "monthly_goal",
        "idle_pct",
        "work_hours",
        "work_days",
        "operator_monthly_pay",
        "heads",
        "machine_heads_note",
    ):
        if resolved[name] is None:
            resolved[name] = DEFAULT_CONFIGURATION[name]
    return resolved


def get_configuration():
    with sqlite3.connect(quote_repository.DB_PATH) as connection:
        row = connection.execute(
            "SELECT data_json FROM configuracion_app WHERE id = 1"
        ).fetchone()
    return json.loads(row[0]) if row else None


def save_configuration(configuration):
    serialized = json.dumps(
        configuration,
        ensure_ascii=False,
        allow_nan=False,
        default=_json_value,
    )
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(quote_repository.DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO configuracion_app (id, data_json, updated_at)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                data_json = excluded.data_json,
                updated_at = excluded.updated_at
            """,
            (serialized, now),
        )
        connection.commit()


def _json_value(value):
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"El valor {type(value).__name__} no se puede guardar.")
