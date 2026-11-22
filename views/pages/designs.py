import sqlite3

import pandas as pd
import streamlit as st

from repositories.design_repository import (
    create_subcategory,
    create_design,
    delete_subcategory,
    list_designs,
    list_subcategories,
    set_subcategory_active,
    set_design_active,
    update_subcategory,
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


def _subcategory_label(subcategory):
    status = "" if subcategory["activo"] else " (Archivada)"
    return f"{subcategory['id']:04d} — {subcategory['nombre']}{status}"


def render_designs_page():
    _reset_confirmation_after_rerun()
    st.header("Catálogo de diseños")
    st.caption(
        "Los diseños guardados se pueden seleccionar al cotizar. También puedes "
        "capturar un diseño nuevo directamente en una cotización sin guardarlo."
    )
    with st.expander("Administrar subcategorías"):
        st.caption(
            "Cada subcategoría recibe un identificador único que no se reutiliza."
        )
        with st.form("create_subcategory_form"):
            new_subcategory_name = st.text_input(
                "Nombre de subcategoría", placeholder="Ej. Anillos"
            )
            if st.form_submit_button("Agregar subcategoría"):
                try:
                    create_subcategory(new_subcategory_name)
                except (ValueError, sqlite3.Error) as error:
                    st.error(f"No se pudo crear la subcategoría: {error}")
                else:
                    st.rerun()

        subcategories = list_subcategories(include_archived=True)
        if subcategories:
            subcategory_id = st.selectbox(
                "Subcategoría para administrar",
                options=[item["id"] for item in subcategories],
                format_func=lambda value: _subcategory_label(
                    next(item for item in subcategories if item["id"] == value)
                ),
                key="catalog_selected_subcategory",
            )
            selected_subcategory = next(
                item for item in subcategories if item["id"] == subcategory_id
            )
            with st.form(f"edit_subcategory_{subcategory_id}"):
                updated_name = st.text_input(
                    "Nombre", value=selected_subcategory["nombre"],
                    key=f"subcategory_name_{subcategory_id}",
                )
                confirm_update = st.checkbox(
                    "Confirmo actualizar la subcategoría",
                    key=f"confirm_subcategory_update_{subcategory_id}",
                )
                if st.form_submit_button(
                    "Guardar subcategoría", disabled=not confirm_update
                ):
                    try:
                        update_subcategory(subcategory_id, updated_name)
                    except (ValueError, sqlite3.Error) as error:
                        st.error(f"No se pudo actualizar: {error}")
                    else:
                        st.session_state["confirmation_keys_to_reset"] = [
                            f"confirm_subcategory_update_{subcategory_id}"
                        ]
                        st.rerun()

            subcategory_actions = st.columns(2)
            confirm_subcategory_status = subcategory_actions[0].checkbox(
                "Confirmar cambio de estado",
                key=f"confirm_subcategory_status_{subcategory_id}",
            )
            if subcategory_actions[0].button(
                "Reactivar subcategoría"
                if not selected_subcategory["activo"]
                else "Archivar subcategoría",
                disabled=not confirm_subcategory_status,
                key=f"toggle_subcategory_{subcategory_id}",
            ):
                set_subcategory_active(
                    subcategory_id, not selected_subcategory["activo"]
                )
                st.session_state["confirmation_keys_to_reset"] = [
                    f"confirm_subcategory_status_{subcategory_id}"
                ]
                st.rerun()
            confirm_subcategory_delete = subcategory_actions[1].checkbox(
                "Confirmo eliminar subcategoría",
                key=f"confirm_subcategory_delete_{subcategory_id}",
            )
            if subcategory_actions[1].button(
                "Eliminar subcategoría",
                disabled=not confirm_subcategory_delete,
                key=f"delete_subcategory_{subcategory_id}",
            ):
                try:
                    delete_subcategory(subcategory_id)
                except (ValueError, sqlite3.Error) as error:
                    st.error(f"No se pudo eliminar: {error}")
                else:
                    st.rerun()

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
                "Subcategoría": design["subcategory_name"],
                "Nombre": design["nombre"],
                "Ancho (cm)": (
                    design["configuracion"].get("ancho_cm") or "Pendiente"
                ),
                "Alto (cm)": (
                    design["configuracion"].get("alto_cm") or "Pendiente"
                ),
                "Estado": "Activo" if design["activo"] else "Archivado",
            }
            for design in filtered
        ])
        st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.info("No hay diseños en el catálogo que coincidan con la búsqueda.")

    with st.expander("Agregar diseño al catálogo"):
        with st.form("create_design_form"):
            cols = st.columns([1, 2, 2])
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
                available_subcategories = list_subcategories()
                if not available_subcategories:
                    st.info("Agrega una subcategoría antes de crear un diseño.")
                    subcategory_id = None
                else:
                    subcategory_id = st.selectbox(
                        "Subcategoría",
                        options=[item["id"] for item in available_subcategories],
                        format_func=lambda value: _subcategory_label(
                            next(
                                item for item in available_subcategories
                                if item["id"] == value
                            )
                        ),
                        key="new_catalog_design_subcategory",
                    )
            with cols[2]:
                name = st.text_input(
                    "Nombre del diseño",
                    placeholder="Ej. Palomas",
                    key="new_catalog_design_name",
                )
            size_cols = st.columns(2)
            with size_cols[0]:
                width = st.number_input(
                    "Ancho (cm)", min_value=0.0, value=0.0, step=0.1,
                    key="new_catalog_design_width",
                )
            with size_cols[1]:
                height = st.number_input(
                    "Alto (cm)", min_value=0.0, value=0.0, step=0.1,
                    key="new_catalog_design_height",
                )
            time_cols = st.columns(3)
            with time_cols[0]:
                embroidery_minutes = st.number_input(
                    "Bordado por corrida (min)", min_value=0.0, value=12.0,
                    step=0.1, key="new_catalog_design_embroidery",
                )
            with time_cols[1]:
                setup_minutes = st.number_input(
                    "Preparación (min)", min_value=0.0, value=0.0,
                    step=0.1, key="new_catalog_design_setup",
                )
            with time_cols[2]:
                extra_minutes = st.number_input(
                    "Tiempo adicional (min)", min_value=0.0, value=0.0,
                    step=0.1, key="new_catalog_design_extra",
                )
            st.caption(
                "El código se asigna automáticamente: categoryId-subcategoryId-designId."
            )
            if st.form_submit_button("Guardar diseño"):
                configuration = {
                    "ancho_cm": width,
                    "alto_cm": height,
                    "bordado_minutos": embroidery_minutes,
                    "preparacion_minutos": setup_minutes,
                    "minutos_adicionales": extra_minutes,
                    "materiales": [],
                }
                try:
                    if subcategory_id is None:
                        raise ValueError(
                            "Crea o selecciona una subcategoría."
                        )
                    create_design(
                        category, subcategory_id, name, configuration
                    )
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
        cols = st.columns([1, 2, 2])
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
            design_subcategories = list_subcategories(include_archived=True)
            editable_subcategories = [
                subcategory for subcategory in design_subcategories
                if subcategory["activo"]
                or subcategory["id"] == selected["subcategory_id"]
            ]
            subcategory_id = st.selectbox(
                "Subcategoría",
                options=[item["id"] for item in editable_subcategories],
                index=[
                    item["id"] for item in editable_subcategories
                ].index(selected["subcategory_id"]),
                format_func=lambda value: _subcategory_label(
                    next(
                        item for item in editable_subcategories
                        if item["id"] == value
                    )
                ),
                key=f"edit_design_subcategory_{selected_id}",
            )
        with cols[2]:
            name = st.text_input(
                "Nombre del diseño",
                value=selected["nombre"],
                key=f"edit_design_name_{selected_id}",
            )
        config = selected["configuracion"]
        dimension_cols = st.columns(2)
        with dimension_cols[0]:
            width = st.number_input(
                "Ancho (cm)", min_value=0.0,
                value=float(config.get("ancho_cm", 0.0)), step=0.1,
                key=f"edit_design_width_{selected_id}",
            )
        with dimension_cols[1]:
            height = st.number_input(
                "Alto (cm)", min_value=0.0,
                value=float(config.get("alto_cm", 0.0)), step=0.1,
                key=f"edit_design_height_{selected_id}",
            )
        time_cols = st.columns(3)
        with time_cols[0]:
            embroidery_minutes = st.number_input(
                "Bordado por corrida (min)", min_value=0.0,
                value=float(config.get("bordado_minutos", 12.0)), step=0.1,
                key=f"edit_design_embroidery_{selected_id}",
            )
        with time_cols[1]:
            setup_minutes = st.number_input(
                "Preparación (min)", min_value=0.0,
                value=float(config.get("preparacion_minutos", 0.0)), step=0.1,
                key=f"edit_design_setup_{selected_id}",
            )
        with time_cols[2]:
            extra_minutes = st.number_input(
                "Tiempo adicional (min)", min_value=0.0,
                value=float(config.get("minutos_adicionales", 0.0)), step=0.1,
                key=f"edit_design_extra_{selected_id}",
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
                configuration = {
                    **config,
                    "ancho_cm": width,
                    "alto_cm": height,
                    "bordado_minutos": embroidery_minutes,
                    "preparacion_minutos": setup_minutes,
                    "minutos_adicionales": extra_minutes,
                }
                update_design(
                    selected_id, category, subcategory_id, name, configuration
                )
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
