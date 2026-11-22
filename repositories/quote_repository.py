import json
import re
import sqlite3
import unicodedata
from datetime import date, datetime
from pathlib import Path

from models.designs import DESIGN_CATEGORIES, LEGACY_DESIGN_CATEGORIES


DB_PATH = Path(__file__).resolve().parents[1] / "cotizaciones.db"


def init_database():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS configuracion_app (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombres TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                empresa TEXT NOT NULL DEFAULT '',
                telefono TEXT NOT NULL DEFAULT '',
                correo TEXT NOT NULL DEFAULT '',
                direccion TEXT NOT NULL DEFAULT '',
                notas TEXT NOT NULL DEFAULT '',
                activo INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS diseno_subcategorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                nombre_normalizado TEXT NOT NULL UNIQUE,
                activo INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS disenos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                categoria_codigo TEXT NOT NULL,
                category_id TEXT,
                subcategory_id INTEGER,
                design_number INTEGER,
                configuracion_json TEXT NOT NULL DEFAULT '{}',
                nombre TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (subcategory_id)
                    REFERENCES diseno_subcategorias(id)
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS diseno_consecutivos (
                category_id TEXT NOT NULL,
                subcategory_id INTEGER NOT NULL,
                last_number INTEGER NOT NULL,
                PRIMARY KEY (category_id, subcategory_id)
            )
        """)
        design_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(disenos)")
        }
        for column, declaration in (
            ("activo", "INTEGER NOT NULL DEFAULT 1"),
            ("category_id", "TEXT"),
            ("subcategory_id", "INTEGER"),
            ("design_number", "INTEGER"),
            ("configuracion_json", "TEXT NOT NULL DEFAULT '{}'"),
        ):
            if column not in design_columns:
                connection.execute(
                    f"ALTER TABLE disenos ADD COLUMN {column} {declaration}"
                )
        _migrate_design_identifiers(connection)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS diseno_imagenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                design_id INTEGER NOT NULL,
                filename TEXT NOT NULL UNIQUE,
                mime_type TEXT NOT NULL,
                caption TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (design_id) REFERENCES disenos(id)
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS cotizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folio TEXT NOT NULL,
                cliente TEXT,
                telefono TEXT,
                correo TEXT,
                estado TEXT NOT NULL,
                fecha_cotizacion TEXT NOT NULL,
                fecha_entrega TEXT,
                precio_unitario REAL,
                precio_total REAL,
                datos_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        quote_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(cotizaciones)")
        }
        if "client_id" not in quote_columns:
            connection.execute("ALTER TABLE cotizaciones ADD COLUMN client_id INTEGER")
        connection.commit()


def _normalize_subcategory_name(name):
    normalized = unicodedata.normalize("NFKD", name.casefold().strip())
    return "".join(
        character for character in normalized
        if not unicodedata.combining(character)
    )


def _migrate_design_identifiers(connection):
    rows = connection.execute("""
        SELECT id, categoria_codigo, category_id, subcategory_id,
               design_number, configuracion_json, nombre
        FROM disenos
        ORDER BY id
    """).fetchall()
    now = datetime.now().isoformat(timespec="seconds")
    for (design_id, legacy_category, category_id, subcategory_id,
         number, configuration_json, name) in rows:
        if category_id is None:
            category_id = LEGACY_DESIGN_CATEGORIES.get(legacy_category)
            if category_id is None and legacy_category in DESIGN_CATEGORIES:
                category_id = legacy_category
            if category_id is None:
                raise ValueError(
                    f"La categoría heredada {legacy_category!r} del diseño "
                    f"{design_id} no se reconoce."
                )
        if subcategory_id is None:
            normalized_name = _normalize_subcategory_name(name)
            if not normalized_name:
                normalized_name = f"diseno-{design_id}"
                subcategory_name = f"Diseño heredado {design_id}"
            else:
                subcategory_name = name.strip()
            subcategory = connection.execute(
                """
                SELECT id FROM diseno_subcategorias
                WHERE nombre_normalizado = ?
                """,
                (normalized_name,),
            ).fetchone()
            if subcategory:
                subcategory_id = subcategory[0]
            else:
                cursor = connection.execute(
                    """
                    INSERT INTO diseno_subcategorias
                        (nombre, nombre_normalizado, activo, created_at, updated_at)
                    VALUES (?, ?, 1, ?, ?)
                    """,
                    (subcategory_name, normalized_name, now, now),
                )
                subcategory_id = cursor.lastrowid
        if number is None:
            previous = connection.execute(
                """
                SELECT COALESCE(MAX(design_number), 0)
                FROM disenos
                WHERE category_id = ? AND subcategory_id = ?
                  AND id != ?
                """,
                (category_id, subcategory_id, design_id),
            ).fetchone()[0]
            number = previous + 1
        configuration = json.loads(configuration_json or "{}")
        configuration.setdefault("ancho_cm", 0.0)
        configuration.setdefault("alto_cm", 0.0)
        configuration.setdefault("bordado_minutos", 12.0)
        configuration.setdefault("preparacion_minutos", 0.0)
        configuration.setdefault("minutos_adicionales", 0.0)
        configuration.setdefault("materiales", [])
        connection.execute(
            """
            UPDATE disenos
            SET categoria_codigo = ?, category_id = ?, subcategory_id = ?,
                design_number = ?, configuracion_json = ?, codigo = ?
            WHERE id = ?
            """,
            (
                category_id, category_id, subcategory_id, number,
                json.dumps(configuration, ensure_ascii=False),
                f"{category_id}-{subcategory_id:04d}-{number:04d}",
                design_id,
            ),
        )
        connection.execute(
            """
            INSERT INTO diseno_consecutivos
                (category_id, subcategory_id, last_number)
            VALUES (?, ?, ?)
            ON CONFLICT(category_id, subcategory_id)
            DO UPDATE SET last_number = MAX(last_number, excluded.last_number)
            """,
            (category_id, subcategory_id, number),
        )


def save_quote(
    folio, cliente, telefono, correo, estado, delivery_date: date,
    snapshot, client_id=None,
):
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("BEGIN IMMEDIATE")
        folio = (folio or "").strip()
        if not folio:
            folio = _next_quote_folio(connection, date.today())
        snapshot["folio"] = folio
        _assign_quote_design_numbers(connection, snapshot)
        serialized = json.dumps(snapshot, ensure_ascii=False)
        existing = connection.execute(
            "SELECT id FROM cotizaciones WHERE folio = ?", (folio,)
        ).fetchone()
        if existing:
            connection.execute("""
                UPDATE cotizaciones
                SET cliente=?, telefono=?, correo=?, estado=?, fecha_entrega=?,
                    precio_unitario=?, precio_total=?, datos_json=?, updated_at=?,
                    client_id=?
                WHERE folio=?
            """, (
                cliente, telefono, correo, estado, delivery_date.isoformat(),
                snapshot["precio_unitario"], snapshot["precio_total"],
                serialized, now, client_id, folio,
            ))
            quote_id = existing[0]
        else:
            cursor = connection.execute("""
                INSERT INTO cotizaciones
                (folio, cliente, telefono, correo, estado, fecha_cotizacion,
                 fecha_entrega, precio_unitario, precio_total, datos_json,
                 created_at, updated_at, client_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                folio, cliente, telefono, correo, estado, now,
                delivery_date.isoformat(), snapshot["precio_unitario"],
                snapshot["precio_total"], serialized, now, now, client_id,
            ))
            quote_id = cursor.lastrowid
        connection.commit()
    return quote_id


def _next_quote_folio(connection, reference_date):
    prefix = f"COT-{reference_date:%Y%m%d}-"
    rows = connection.execute(
        "SELECT folio FROM cotizaciones WHERE folio LIKE ?",
        (f"{prefix}%",),
    ).fetchall()
    sequence = max(
        (
            int(match.group(1))
            for (folio,) in rows
            if (match := re.fullmatch(re.escape(prefix) + r"(\d+)", folio))
        ),
        default=0,
    ) + 1
    return f"{prefix}{sequence:04d}"


def _next_quote_design_number(connection, category_id, subcategory_id):
    row = connection.execute(
        """
        SELECT last_number FROM diseno_consecutivos
        WHERE category_id = ? AND subcategory_id = ?
        """,
        (category_id, subcategory_id),
    ).fetchone()
    number = row[0] + 1 if row else 1
    connection.execute(
        """
        INSERT INTO diseno_consecutivos
            (category_id, subcategory_id, last_number)
        VALUES (?, ?, ?)
        ON CONFLICT(category_id, subcategory_id)
        DO UPDATE SET last_number = excluded.last_number
        """,
        (category_id, subcategory_id, number),
    )
    return number


def _assign_quote_design_numbers(connection, snapshot):
    quote_designs = snapshot.get("design_items", [])
    output_designs = snapshot.get("disenos", [])
    output_by_id = {item.get("id"): item for item in output_designs}
    for item in quote_designs:
        if item.get("catalog_id") is not None:
            continue
        category_id = item.get("category_id") or item.get("categoria_codigo")
        subcategory_id = item.get("subcategory_id")
        if category_id not in DESIGN_CATEGORIES or not subcategory_id:
            raise ValueError(
                "Cada diseño debe tener una categoría y subcategoría para "
                "generar su código."
            )
        expected_prefix = f"{category_id}-{int(subcategory_id):04d}-"
        design_number = item.get("design_number")
        code = item.get("codigo", "")
        if not design_number or not code.startswith(expected_prefix):
            design_number = _next_quote_design_number(
                connection, category_id, int(subcategory_id)
            )
            code = (
                f"{expected_prefix}{design_number:04d}"
            )
        item["category_id"] = category_id
        item["categoria_codigo"] = category_id
        item["design_number"] = design_number
        item["codigo"] = code
        output_item = output_by_id.get(item.get("id"))
        if output_item:
            output_item["category_id"] = category_id
            output_item["categoria_codigo"] = category_id
            output_item["subcategory_id"] = int(subcategory_id)
            output_item["design_number"] = design_number
            output_item["codigo"] = code


def list_quotes():
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute("""
            SELECT id, folio, cliente, telefono, correo, estado,
                   fecha_cotizacion, fecha_entrega, precio_unitario, precio_total,
                   client_id
            FROM cotizaciones
            ORDER BY updated_at DESC
        """).fetchall()]


def get_quote(quote_id):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM cotizaciones WHERE id = ?", (quote_id,)
        ).fetchone()
        return dict(row) if row else None


def quote_exists(folio):
    with sqlite3.connect(DB_PATH) as connection:
        return connection.execute(
            "SELECT 1 FROM cotizaciones WHERE folio = ?", (folio,)
        ).fetchone() is not None


def delete_quote(quote_id):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "DELETE FROM cotizaciones WHERE id = ?", (quote_id,)
        )
        if cursor.rowcount == 0:
            raise ValueError("La cotización que intentas eliminar ya no existe.")
        connection.commit()
