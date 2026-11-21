import sqlite3
import re
import unicodedata
from datetime import datetime
from typing import List

from models.designs import (
    DESIGN_CATEGORIES,
    DesignCatalogRecord,
)
from repositories.quote_repository import DB_PATH


def design_code(categoria_codigo: str, nombre: str) -> str:
    if categoria_codigo not in DESIGN_CATEGORIES:
        raise ValueError("La categoría del diseño no es válida.")
    normalized = unicodedata.normalize("NFKD", nombre)
    slug = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    if not slug:
        raise ValueError("El nombre debe incluir letras o números.")
    return f"{categoria_codigo}-{slug}"


def list_designs(include_archived=False) -> List[DesignCatalogRecord]:
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        query = """
            SELECT id, codigo, categoria_codigo, nombre, activo
            FROM disenos
        """
        if not include_archived:
            query += " WHERE activo = 1"
        query += " ORDER BY categoria_codigo, codigo"
        rows = connection.execute(query).fetchall()
    return [dict(row) for row in rows]


def get_design(design_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT id, codigo, categoria_codigo, nombre, activo
            FROM disenos
            WHERE id = ?
            """,
            (design_id,),
        ).fetchone()
    return dict(row) if row else None


def create_design(categoria_codigo: str, nombre: str) -> int:
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre del diseño no puede estar vacío.")
    if categoria_codigo not in DESIGN_CATEGORIES:
        raise ValueError("La categoría del diseño no es válida.")

    with sqlite3.connect(DB_PATH) as connection:
        code = design_code(categoria_codigo, nombre)
        existing = connection.execute(
            "SELECT id, nombre, activo FROM disenos WHERE codigo = ?", (code,)
        ).fetchone()
        if existing:
            if existing[1] == nombre:
                if not existing[2]:
                    raise ValueError(
                        "Este diseño está archivado. Reactívalo desde el catálogo "
                        "para volver a utilizarlo."
                    )
                return existing[0]
            raise ValueError(
                f"El código {code} ya existe para otro nombre."
            )
        cursor = connection.execute(
            """
            INSERT INTO disenos
                (codigo, categoria_codigo, nombre, activo, created_at)
            VALUES (?, ?, ?, 1, ?)
            """,
            (code, categoria_codigo, nombre, datetime.now().isoformat(timespec="seconds")),
        )
        connection.commit()
        return cursor.lastrowid


def update_design(design_id: int, categoria_codigo: str,
                  nombre: str) -> None:
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre del diseño no puede estar vacío.")
    if categoria_codigo not in DESIGN_CATEGORIES:
        raise ValueError("La categoría del diseño no es válida.")
    code = design_code(categoria_codigo, nombre)
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            """
            UPDATE disenos
            SET codigo = ?, categoria_codigo = ?, nombre = ?
            WHERE id = ?
            """,
            (code, categoria_codigo, nombre, design_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("El diseño que intentas actualizar ya no existe.")
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
