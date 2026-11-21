import json
import sqlite3
from datetime import date, datetime
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "cotizaciones.db"


def init_database():
    with sqlite3.connect(DB_PATH) as connection:
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
            CREATE TABLE IF NOT EXISTS disenos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                categoria_codigo TEXT NOT NULL,
                nombre TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        design_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(disenos)")
        }
        if "activo" not in design_columns:
            connection.execute(
                "ALTER TABLE disenos ADD COLUMN activo INTEGER NOT NULL DEFAULT 1"
            )
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


def save_quote(
    folio, cliente, telefono, correo, estado, delivery_date: date,
    snapshot, client_id=None,
):
    now = datetime.now().isoformat(timespec="seconds")
    serialized = json.dumps(snapshot, ensure_ascii=False)
    with sqlite3.connect(DB_PATH) as connection:
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
