import sqlite3

import pandas as pd
import streamlit as st

from repositories.design_repository import (
    create_design,
    list_designs,
    set_design_active,
    update_design,
)
from models.designs import DESIGN_CATEGORIES
from services.design_catalog import delete_catalog_design
from repositories.design_image_repository import (
    create_design_image,
    delete_design_image,
    list_design_images,
    update_design_image,
)


def _reset_confirmation_after_rerun():
    for key in st.session_state.pop("confirmation_keys_to_reset", []):
        st.session_state[key] = False


def _design_label(design):
    return f"{design['codigo']} — {design['nombre']}"


def render_designs_page():
    _reset_confirmation_after_rerun()
    st.header("Catálogo de diseños")
    st.caption(
        "Los diseños guardados se pueden seleccionar al cotizar. También puedes "
        "capturar un diseño nuevo directamente en una cotización sin guardarlo."
    )
    designs = list_designs(include_archived=True)
    search = st.text_input(
        "Buscar por código o nombre",
        key="design_catalog_search",
    ).strip().casefold()
    filtered = [
        design for design in designs
        if search in f"{design['codigo']} {design['nombre']}".casefold()
    ]
    if filtered:
        display = pd.DataFrame([
            {
                "Código": design["codigo"],
                "Categoría": DESIGN_CATEGORIES[design["categoria_codigo"]],
                "Nombre": design["nombre"],
                "Estado": "Activo" if design["activo"] else "Archivado",
            }
            for design in filtered
        ])
        st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.info("No hay diseños en el catálogo que coincidan con la búsqueda.")

    with st.expander("Agregar diseño al catálogo"):
        with st.form("create_design_form"):
            cols = st.columns([1, 3])
            with cols[0]:
                category = st.selectbox(
                    "Categoría",
                    options=list(DESIGN_CATEGORIES),
                    format_func=lambda value: (
                        f"{value} — {DESIGN_CATEGORIES[value]}"
                    ),
                    key="new_catalog_design_category",
                )
            with cols[1]:
                name = st.text_input(
                    "Nombre del diseño",
                    placeholder="Ej. Palomas",
                    key="new_catalog_design_name",
                )
            st.caption("El código se forma automáticamente, por ejemplo: 000-palomas.")
            if st.form_submit_button("Guardar diseño"):
                try:
                    create_design(category, name)
                except (ValueError, sqlite3.IntegrityError) as error:
                    st.error(f"No se pudo guardar el diseño: {error}")
                else:
                    st.success("Diseño guardado en el catálogo.")
                    st.rerun()

    if not designs:
        return

    design_ids = {design["id"] for design in designs}
    if st.session_state.get("catalog_selected_design") not in design_ids:
        st.session_state["catalog_selected_design"] = designs[0]["id"]
    st.subheader("Editar o administrar diseño")
    selected_id = st.selectbox(
        "Seleccionar diseño",
        options=[design["id"] for design in designs],
        format_func=lambda design_id: _design_label(
            next(item for item in designs if item["id"] == design_id)
        ),
        key="catalog_selected_design",
    )
    selected = next(item for item in designs if item["id"] == selected_id)
    with st.form(f"edit_design_form_{selected_id}"):
        cols = st.columns([1, 3])
        with cols[0]:
            category = st.selectbox(
                "Categoría",
                options=list(DESIGN_CATEGORIES),
                index=list(DESIGN_CATEGORIES).index(selected["categoria_codigo"]),
                format_func=lambda value: (
                    f"{value} — {DESIGN_CATEGORIES[value]}"
                ),
                key=f"edit_design_category_{selected_id}",
            )
        with cols[1]:
            name = st.text_input(
                "Nombre del diseño",
                value=selected["nombre"],
                key=f"edit_design_name_{selected_id}",
            )
        confirm_update = st.checkbox(
            "Confirmo guardar estos cambios",
            key=f"confirm_update_design_{selected_id}",
        )
        if st.form_submit_button(
            "Guardar cambios",
            disabled=not confirm_update,
        ):
            try:
                update_design(selected_id, category, name)
            except (ValueError, sqlite3.IntegrityError) as error:
                st.error(f"No se pudo actualizar el diseño: {error}")
            else:
                st.success("Diseño actualizado.")
                st.session_state["confirmation_keys_to_reset"] = [
                    f"confirm_update_design_{selected_id}"
                ]
                st.rerun()

    action_cols = st.columns(2)
    confirm_status_change = action_cols[0].checkbox(
        "Confirmar cambio de estado",
        key=f"confirm_status_design_{selected_id}",
    )
    if selected["activo"]:
        if action_cols[0].button(
            "Archivar diseño",
            disabled=not confirm_status_change,
            key=f"archive_design_{selected_id}",
        ):
            set_design_active(selected_id, False)
            st.session_state["confirmation_keys_to_reset"] = [
                f"confirm_status_design_{selected_id}"
            ]
            st.rerun()
    else:
        if action_cols[0].button(
            "Reactivar diseño",
            disabled=not confirm_status_change,
            key=f"restore_design_{selected_id}",
        ):
            set_design_active(selected_id, True)
            st.session_state["confirmation_keys_to_reset"] = [
                f"confirm_status_design_{selected_id}"
            ]
            st.rerun()

    confirm_delete = action_cols[1].checkbox(
        "Confirmo eliminarlo y borrar sus imágenes",
        key=f"confirm_delete_design_{selected_id}",
    )
    if action_cols[1].button(
        "Eliminar definitivamente",
        disabled=not confirm_delete,
        key=f"delete_design_{selected_id}",
    ):
        try:
            delete_catalog_design(selected_id)
        except (ValueError, OSError, sqlite3.Error) as error:
            st.error(f"No se pudo eliminar el diseño: {error}")
        else:
            st.success(
                "Diseño eliminado del catálogo. Las cotizaciones guardadas "
                "conservan su propia copia de los datos."
            )
            st.rerun()

    st.subheader("Imágenes de referencia")
    st.caption(
        "Las imágenes se guardan localmente en la carpeta de datos de la app "
        "y se relacionan solo con este diseño del catálogo."
    )
    with st.form(f"create_design_image_form_{selected_id}"):
        image_file = st.file_uploader(
            "Agregar imagen",
            type=["png", "jpg", "jpeg", "webp", "bmp"],
            key=f"new_design_image_file_{selected_id}",
        )
        caption = st.text_input(
            "Descripción de la imagen",
            key=f"new_design_image_caption_{selected_id}",
        )
        if st.form_submit_button(
            "Guardar imagen",
            disabled=image_file is None,
        ):
            try:
                create_design_image(
                    selected_id,
                    image_file.getvalue(),
                    caption,
                )
            except (ValueError, OSError, sqlite3.Error) as error:
                st.error(f"No se pudo guardar la imagen: {error}")
            else:
                st.success("Imagen agregada al diseño.")
                st.rerun()

    for image in list_design_images(selected_id):
        with st.expander(
            image["caption"] or f"Imagen {image['id']}"
        ):
            if image["path"].is_file():
                st.image(str(image["path"]), width=360)
            else:
                st.error(
                    f"No se encontró el archivo de imagen: {image['filename']}"
                )
            with st.form(f"edit_design_image_form_{image['id']}"):
                replacement = st.file_uploader(
                    "Reemplazar imagen (opcional)",
                    type=["png", "jpg", "jpeg", "webp", "bmp"],
                    key=f"replace_design_image_{image['id']}",
                )
                updated_caption = st.text_input(
                    "Descripción",
                    value=image["caption"],
                    key=f"edit_design_image_caption_{image['id']}",
                )
                confirm_image_update = st.checkbox(
                    "Confirmo actualizar esta imagen",
                    key=f"confirm_update_image_{image['id']}",
                )
                if st.form_submit_button(
                    "Guardar cambios de imagen",
                    disabled=not confirm_image_update,
                ):
                    try:
                        update_design_image(
                            image["id"],
                            updated_caption,
                            replacement.getvalue() if replacement else None,
                        )
                    except (ValueError, OSError, sqlite3.Error) as error:
                        st.error(f"No se pudo actualizar la imagen: {error}")
                    else:
                        st.success("Imagen actualizada.")
                        st.session_state["confirmation_keys_to_reset"] = [
                            f"confirm_update_image_{image['id']}"
                        ]
                        st.rerun()

            confirm_image_delete = st.checkbox(
                "Confirmo eliminar esta imagen",
                key=f"confirm_delete_image_{image['id']}",
            )
            if st.button(
                "Eliminar imagen",
                disabled=not confirm_image_delete,
                key=f"delete_image_{image['id']}",
            ):
                try:
                    delete_design_image(image["id"])
                except (ValueError, OSError, sqlite3.Error) as error:
                    st.error(f"No se pudo eliminar el archivo de imagen: {error}")
                else:
                    st.success("Imagen eliminada.")
                    st.rerun()
