import json
import math
import sqlite3
import unicodedata
from datetime import datetime
from typing import List

from models.designs import (
    DESIGN_CATEGORIES,
    DesignCatalogRecord,
    DesignSubcategoryRecord,
)
from repositories.quote_repository import DB_PATH


def _normalize_name(name):
    normalized = unicodedata.normalize("NFKD", name.casefold().strip())
    return "".join(
        character for character in normalized
        if not unicodedata.combining(character)
    )


def subcategory_code(subcategory_id):
    return f"{subcategory_id:04d}"


def design_code(category_id, subcategory_id, design_number):
    if category_id not in DESIGN_CATEGORIES:
        raise ValueError("La categoría del diseño no es válida.")
    if subcategory_id < 1 or design_number < 1:
        raise ValueError("Los identificadores deben ser mayores que cero.")
    return (
        f"{category_id}-{subcategory_code(subcategory_id)}-"
        f"{design_number:04d}"
    )


def list_subcategories(include_archived=False) -> List[DesignSubcategoryRecord]:
    query = """
        SELECT id, nombre, activo
        FROM diseno_subcategorias
    """
    if not include_archived:
        query += " WHERE activo = 1"
    query += " ORDER BY nombre COLLATE NOCASE"
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(query).fetchall()]


def get_subcategory(subcategory_id):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT id, nombre, activo
            FROM diseno_subcategorias WHERE id = ?
            """,
            (subcategory_id,),
        ).fetchone()
    return dict(row) if row else None


def create_subcategory(name):
    name = name.strip()
    normalized = _normalize_name(name)
    if not normalized:
        raise ValueError("El nombre de la subcategoría no puede estar vacío.")
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as connection:
        existing = connection.execute(
            """
            SELECT id, nombre, activo
            FROM diseno_subcategorias
            WHERE nombre_normalizado = ?
            """,
            (normalized,),
        ).fetchone()
        if existing:
            if not existing[2]:
                raise ValueError(
                    "Esta subcategoría está archivada. Reactívala para volver "
                    "a utilizarla."
                )
            raise ValueError("Ya existe una subcategoría con ese nombre.")
        cursor = connection.execute(
            """
            INSERT INTO diseno_subcategorias
                (nombre, nombre_normalizado, activo, created_at, updated_at)
            VALUES (?, ?, 1, ?, ?)
            """,
            (name, normalized, now, now),
        )
        connection.commit()
        return cursor.lastrowid


def update_subcategory(subcategory_id, name):
    name = name.strip()
    normalized = _normalize_name(name)
    if not normalized:
        raise ValueError("El nombre de la subcategoría no puede estar vacío.")
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            """
            UPDATE diseno_subcategorias
            SET nombre = ?, nombre_normalizado = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, normalized, now, subcategory_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("La subcategoría que intentas actualizar no existe.")
        connection.commit()


def set_subcategory_active(subcategory_id, active):
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            """
            UPDATE diseno_subcategorias
            SET activo = ?, updated_at = ?
            WHERE id = ?
            """,
            (int(active), now, subcategory_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("La subcategoría que intentas cambiar no existe.")
        connection.commit()


def delete_subcategory(subcategory_id):
    with sqlite3.connect(DB_PATH) as connection:
        design_count = connection.execute(
            "SELECT COUNT(*) FROM disenos WHERE subcategory_id = ?",
            (subcategory_id,),
        ).fetchone()[0]
        if design_count:
            raise ValueError(
                "La subcategoría tiene diseños relacionados. Archívala para "
                "conservar sus identificadores."
            )
        cursor = connection.execute(
            "DELETE FROM diseno_subcategorias WHERE id = ?",
            (subcategory_id,),
        )
        if cursor.rowcount == 0:
            raise ValueError("La subcategoría que intentas eliminar no existe.")
        connection.commit()


def list_designs(include_archived=False) -> List[DesignCatalogRecord]:
    query = """
        SELECT d.id, d.codigo, d.categoria_codigo, d.category_id,
               d.subcategory_id, s.nombre AS subcategory_name,
               d.design_number, d.configuracion_json, d.nombre, d.activo
        FROM disenos d
        JOIN diseno_subcategorias s ON s.id = d.subcategory_id
    """
    if not include_archived:
        query += " WHERE d.activo = 1 AND s.activo = 1"
    query += """
        ORDER BY d.category_id, d.subcategory_id, d.design_number
    """
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return [_design_record(row) for row in connection.execute(query).fetchall()]


def get_design(design_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT d.id, d.codigo, d.categoria_codigo, d.category_id,
                   d.subcategory_id, s.nombre AS subcategory_name,
                   d.design_number, d.configuracion_json, d.nombre, d.activo
            FROM disenos d
            JOIN diseno_subcategorias s ON s.id = d.subcategory_id
            WHERE d.id = ?
            """,
            (design_id,),
        ).fetchone()
    return _design_record(row) if row else None


def _design_record(row):
    record = dict(row)
    record["configuracion"] = json.loads(
        record.pop("configuracion_json") or "{}"
    )
    return record


def _validate_configuration(configuration):
    configuration = dict(configuration or {})
    for field in ("ancho_cm", "alto_cm"):
        try:
            value = float(configuration.get(field, 0))
        except (TypeError, ValueError):
            raise ValueError(
                f"{field.replace('_', ' ').capitalize()} debe ser numérico."
            )
        if not math.isfinite(value) or value <= 0:
            raise ValueError(
                "El ancho y el alto del diseño deben ser mayores que cero."
            )
        configuration[field] = value
    for field in (
        "bordado_minutos",
        "preparacion_minutos",
        "minutos_adicionales",
    ):
        value = float(configuration.get(field, 0.0))
        if not math.isfinite(value):
            raise ValueError("Los tiempos deben ser valores numéricos válidos.")
        configuration[field] = max(0.0, value)
    configuration["materiales"] = list(configuration.get("materiales", []))
    return configuration


def _next_design_number(connection, category_id, subcategory_id):
    row = connection.execute(
        """
        SELECT last_number FROM diseno_consecutivos
        WHERE category_id = ? AND subcategory_id = ?
        """,
        (category_id, subcategory_id),
    ).fetchone()
    next_number = row[0] + 1 if row else 1
    connection.execute(
        """
        INSERT INTO diseno_consecutivos
            (category_id, subcategory_id, last_number)
        VALUES (?, ?, ?)
        ON CONFLICT(category_id, subcategory_id)
        DO UPDATE SET last_number = excluded.last_number
        """,
        (category_id, subcategory_id, next_number),
    )
    return next_number


def _validate_design_fields(connection, category_id, subcategory_id, name):
    name = name.strip()
    if not name:
        raise ValueError("El nombre del diseño no puede estar vacío.")
    if category_id not in DESIGN_CATEGORIES:
        raise ValueError("La categoría del diseño no es válida.")
    subcategory = connection.execute(
        """
        SELECT activo FROM diseno_subcategorias WHERE id = ?
        """,
        (subcategory_id,),
    ).fetchone()
    if not subcategory:
        raise ValueError("La subcategoría seleccionada no existe.")
    if not subcategory[0]:
        raise ValueError("La subcategoría seleccionada está archivada.")
    return name


def create_design(
    category_id, subcategory_id, name, configuration=None
) -> int:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("BEGIN IMMEDIATE")
        name = _validate_design_fields(
            connection, category_id, subcategory_id, name
        )
        configuration = _validate_configuration(configuration)
        design_number = _next_design_number(
            connection, category_id, subcategory_id
        )
        code = design_code(category_id, subcategory_id, design_number)
        cursor = connection.execute(
            """
            INSERT INTO disenos
                (codigo, categoria_codigo, category_id, subcategory_id,
                 design_number, configuracion_json, nombre, activo, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                code, category_id, category_id, subcategory_id, design_number,
                json.dumps(configuration, ensure_ascii=False), name,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        connection.commit()
        return cursor.lastrowid


def update_design(
    design_id, category_id, subcategory_id, name, configuration=None
):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("BEGIN IMMEDIATE")
        name = _validate_design_fields(
            connection, category_id, subcategory_id, name
        )
        existing = connection.execute(
            """
            SELECT category_id, subcategory_id, design_number,
                   configuracion_json
            FROM disenos WHERE id = ?
            """,
            (design_id,),
        ).fetchone()
        if not existing:
            raise ValueError("El diseño que intentas actualizar ya no existe.")
        if existing[:2] == (category_id, subcategory_id):
            number = existing[2]
        else:
            number = _next_design_number(
                connection, category_id, subcategory_id
            )
        code = design_code(category_id, subcategory_id, number)
        if configuration is None:
            serialized_configuration = existing[3] or "{}"
        else:
            serialized_configuration = json.dumps(
                _validate_configuration(configuration), ensure_ascii=False
            )
        connection.execute(
            """
            UPDATE disenos
            SET codigo = ?, categoria_codigo = ?, category_id = ?,
                subcategory_id = ?, design_number = ?,
                configuracion_json = ?, nombre = ?
            WHERE id = ?
            """,
            (
                code, category_id, category_id, subcategory_id,
                number, serialized_configuration, name, design_id,
            ),
        )
        connection.commit()


def set_design_active(design_id: int, active: bool) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "UPDATE disenos SET activo = ? WHERE id = ?",
            (int(active), design_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("El diseño que intentas cambiar ya no existe.")
        connection.commit()


def delete_design_record(design_id: int) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "DELETE FROM disenos WHERE id = ?", (design_id,)
        )
        if cursor.rowcount == 0:
            raise ValueError("El diseño que intentas eliminar ya no existe.")
        connection.commit()
