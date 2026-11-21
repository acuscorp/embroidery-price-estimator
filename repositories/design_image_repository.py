import sqlite3
from datetime import datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from typing import List, Optional

from PIL import Image

from models.designs import DesignImageRecord
from repositories.quote_repository import DB_PATH


IMAGE_DIR = Path(__file__).resolve().parents[1] / "data" / "design_images"
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000


def _normalize_image(image_bytes: bytes) -> bytes:
    if not image_bytes:
        raise ValueError("Selecciona una imagen antes de continuar.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("La imagen no puede superar los 15 MB.")
    try:
        with Image.open(BytesIO(image_bytes)) as source:
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise ValueError("La imagen excede el tamaño máximo permitido.")
            source.load()
            normalized = source.convert("RGBA")
            output = BytesIO()
            normalized.save(output, format="PNG", optimize=True)
    except OSError as error:
        raise ValueError("El archivo seleccionado no es una imagen válida.") from error
    return output.getvalue()


def list_design_images(design_id: int) -> List[DesignImageRecord]:
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, design_id, filename, mime_type, caption, created_at,
                   updated_at
            FROM diseno_imagenes
            WHERE design_id = ?
            ORDER BY created_at, id
            """,
            (design_id,),
        ).fetchall()
    return [
        {**dict(row), "path": IMAGE_DIR / row["filename"]}
        for row in rows
    ]


def create_design_image(design_id: int, image_bytes: bytes,
                        caption: str = "") -> int:
    normalized = _normalize_image(image_bytes)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.png"
    image_path = IMAGE_DIR / filename
    image_path.write_bytes(normalized)
    now = datetime.now().isoformat(timespec="seconds")
    try:
        with sqlite3.connect(DB_PATH) as connection:
            exists = connection.execute(
                "SELECT 1 FROM disenos WHERE id = ?", (design_id,)
            ).fetchone()
            if not exists:
                raise ValueError("El diseño seleccionado ya no existe.")
            connection.execute(
                """
                INSERT INTO diseno_imagenes
                    (design_id, filename, mime_type, caption, created_at,
                     updated_at)
                VALUES (?, ?, 'image/png', ?, ?, ?)
                """,
                (design_id, filename, caption.strip(), now, now),
            )
            connection.commit()
            image_id = connection.execute(
                "SELECT id FROM diseno_imagenes WHERE filename = ?",
                (filename,),
            ).fetchone()[0]
    except (sqlite3.Error, ValueError, OSError):
        image_path.unlink(missing_ok=True)
        raise
    return image_id


def update_design_image(image_id: int, caption: str,
                        replacement_bytes: Optional[bytes] = None) -> None:
    filename = None
    new_path = None
    if replacement_bytes is not None:
        normalized = _normalize_image(replacement_bytes)
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4().hex}.png"
        new_path = IMAGE_DIR / filename
        new_path.write_bytes(normalized)

    now = datetime.now().isoformat(timespec="seconds")
    try:
        with sqlite3.connect(DB_PATH) as connection:
            row = connection.execute(
                "SELECT filename FROM diseno_imagenes WHERE id = ?",
                (image_id,),
            ).fetchone()
            if not row:
                raise ValueError("La imagen seleccionada ya no existe.")
            old_path = IMAGE_DIR / row[0]
            if filename:
                connection.execute(
                    """
                    UPDATE diseno_imagenes
                    SET filename = ?, mime_type = 'image/png', caption=?,
                        updated_at=?
                    WHERE id = ?
                    """,
                    (filename, caption.strip(), now, image_id),
                )
            else:
                connection.execute(
                    """
                    UPDATE diseno_imagenes
                    SET caption = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (caption.strip(), now, image_id),
                )
            connection.commit()
    except (sqlite3.Error, ValueError, OSError):
        if new_path and new_path.exists():
            new_path.unlink()
        raise
    if new_path and old_path.exists():
        old_path.unlink()


def delete_design_image(image_id: int) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT filename FROM diseno_imagenes WHERE id = ?",
            (image_id,),
        ).fetchone()
        if not row:
            raise ValueError("La imagen seleccionada ya no existe.")
        connection.execute(
            "DELETE FROM diseno_imagenes WHERE id = ?", (image_id,)
        )
        connection.commit()
    image_path = IMAGE_DIR / row[0]
    if image_path.exists():
        image_path.unlink()


def delete_design_images(design_id: int) -> None:
    for image in list_design_images(design_id):
        delete_design_image(image["id"])
