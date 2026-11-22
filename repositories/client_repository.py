import sqlite3
from datetime import datetime
import unicodedata

from repositories.quote_repository import DB_PATH


def create_client(client):
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            """
            INSERT INTO clientes
                (nombres, apellidos, empresa, telefono, correo, direccion,
                 notas, activo, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                client["nombres"].strip(),
                client["apellidos"].strip(),
                client["empresa"].strip(),
                client["telefono"].strip(),
                client["correo"].strip(),
                client["direccion"].strip(),
                client["notas"].strip(),
                now,
                now,
            ),
        )
        connection.commit()
        return cursor.lastrowid


def update_client(client_id, client):
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            """
            UPDATE clientes
            SET nombres=?, apellidos=?, empresa=?, telefono=?, correo=?,
                direccion=?, notas=?, updated_at=?
            WHERE id=?
            """,
            (
                client["nombres"].strip(),
                client["apellidos"].strip(),
                client["empresa"].strip(),
                client["telefono"].strip(),
                client["correo"].strip(),
                client["direccion"].strip(),
                client["notas"].strip(),
                now,
                client_id,
            ),
        )
        if cursor.rowcount == 0:
            raise ValueError("El cliente que intentas actualizar ya no existe.")
        connection.commit()


def list_clients(include_archived=False):
    query = """
        SELECT id, nombres, apellidos, empresa, telefono, correo, direccion,
               notas, activo, created_at, updated_at
        FROM clientes
    """
    if not include_archived:
        query += " WHERE activo = 1"
    query += " ORDER BY nombres COLLATE NOCASE, apellidos COLLATE NOCASE"
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(query).fetchall()]


def search_clients(search, limit=20):
    normalized_search = _normalize_search_text(search).strip()
    if not normalized_search:
        return []
    search_terms = normalized_search.split()
    matches = []
    for client in list_clients():
        searchable = _normalize_search_text(" ".join(
            str(client.get(field) or "")
            for field in (
                "nombres", "apellidos", "empresa", "telefono", "correo"
            )
        ))
        if all(term in searchable for term in search_terms):
            matches.append(client)
    return matches[:limit]


def _normalize_search_text(value):
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def get_client(client_id):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM clientes WHERE id = ?", (client_id,)
        ).fetchone()
        return dict(row) if row else None


def set_client_active(client_id, active):
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "UPDATE clientes SET activo=?, updated_at=? WHERE id=?",
            (int(active), now, client_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("El cliente que intentas cambiar ya no existe.")
        connection.commit()


def client_quote_count(client_id):
    with sqlite3.connect(DB_PATH) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM cotizaciones WHERE client_id = ?",
            (client_id,),
        ).fetchone()[0]


def delete_client(client_id):
    with sqlite3.connect(DB_PATH) as connection:
        quote_count = connection.execute(
            "SELECT COUNT(*) FROM cotizaciones WHERE client_id = ?",
            (client_id,),
        ).fetchone()[0]
        if quote_count:
            raise ValueError(
                "No se puede eliminar un cliente con cotizaciones relacionadas. "
                "Archívalo para conservar el historial."
            )
        cursor = connection.execute(
            "DELETE FROM clientes WHERE id = ?", (client_id,)
        )
        if cursor.rowcount == 0:
            raise ValueError("El cliente que intentas eliminar ya no existe.")
        connection.commit()


def client_display_name(client):
    person_name = " ".join(
        part.strip() for part in
        (client.get("nombres") or "", client.get("apellidos") or "")
        if part and part.strip()
    )
    company = (client.get("empresa") or "").strip()
    if person_name and company:
        return f"{person_name} — {company}"
    return person_name or company or f"Cliente {client['id']}"
