import sqlite3
from uuid import uuid4
from typing import List

import pandas as pd
import streamlit as st

from models.designs import DESIGN_CATEGORIES, DesignQuoteLine
from repositories.design_repository import (
    create_design,
    design_code,
    create_subcategory,
    get_design,
    list_designs,
    list_subcategories,
)
from views.configuration.materials import render_design_materials


def _create_quote_subcategory(prefix):
    name = st.session_state.get(prefix + "new_subcategory_name", "").strip()
    try:
        subcategory_id = create_subcategory(name)
    except (ValueError, sqlite3.Error) as error:
        st.session_state["design_catalog_error"] = str(error)
    else:
        st.session_state[prefix + "subcategory_id"] = subcategory_id
        st.session_state[prefix + "new_subcategory_name"] = ""
        st.session_state.pop("design_catalog_error", None)


def _save_design_to_catalog(prefix, category_id, subcategory_id, name):
    configuration = {
        "ancho_cm": st.session_state[prefix + "width"],
        "alto_cm": st.session_state[prefix + "height"],
        "bordado_minutos": st.session_state[prefix + "embroidery_minutes"],
        "preparacion_minutos": st.session_state[prefix + "setup_minutes"],
        "minutos_adicionales": st.session_state[prefix + "extra_minutes"],
        "materiales": st.session_state.get(
            prefix + "materials_editor", pd.DataFrame()
        ).to_dict(orient="records"),
    }
    try:
        catalog_id = create_design(
            category_id, subcategory_id, name, configuration
        )
    except (ValueError, sqlite3.Error) as error:
        st.session_state["design_catalog_error"] = str(error)
    else:
        st.session_state[prefix + "catalog_id"] = catalog_id
        st.session_state.pop("design_catalog_error", None)


def _on_quote_design_selected(prefix):
    design_id = st.session_state.get(prefix + "catalog_id")
    if design_id is None:
        return
    design = get_design(design_id)
    if design is None:
        raise ValueError("El diseño seleccionado ya no está disponible.")
    configuration = design["configuracion"]
    values = {
        "category": design["category_id"],
        "subcategory_id": design["subcategory_id"],
        "name": design["nombre"],
        "code": design["codigo"],
        "design_number": design["design_number"],
        "width": configuration.get("ancho_cm", 0.0),
        "height": configuration.get("alto_cm", 0.0),
        "embroidery_minutes": configuration.get("bordado_minutos", 12.0),
        "setup_minutes": configuration.get("preparacion_minutos", 0.0),
        "extra_minutes": configuration.get("minutos_adicionales", 0.0),
    }
    for field, value in values.items():
        st.session_state[prefix + field] = value
    st.session_state[prefix + "materials"] = configuration.get("materiales", [])
    st.session_state.pop(prefix + "materials_editor", None)


def new_design_item() -> DesignQuoteLine:
    return {
        "id": uuid4().hex,
        "catalog_id": None,
        "category_id": "0000",
        "subcategory_id": None,
        "design_number": None,
        "categoria_codigo": "0000",
        "nombre": "",
        "ancho_cm": 0.0,
        "alto_cm": 0.0,
        "cantidad": 10,
        "bordado_minutos": 12.0,
        "preparacion_minutos": 0.0,
        "minutos_adicionales": 0.0,
        "materiales": [],
    }


def render_designs(materials) -> List[DesignQuoteLine]:
    st.header("Diseños y cantidades")
    if "design_catalog_error" in st.session_state:
        st.error(st.session_state.pop("design_catalog_error"))
    st.caption(
        "Cada diseño calcula su propio precio y margen según su cantidad. "
        "Puedes usar un diseño guardado o capturar uno solo para esta cotización."
    )
    if "quote_design_items" not in st.session_state:
        st.session_state.quote_design_items = [new_design_item()]

    designs: List[DesignQuoteLine] = st.session_state.quote_design_items
    if st.button("Agregar diseño", type="primary", key="add_quote_design"):
        designs.append(new_design_item())
        st.session_state.quote_design_items = designs

    catalog = list_designs()
    catalog_by_id = {design["id"]: design for design in catalog}
    catalog_ids = set(catalog_by_id)
    subcategories = list_subcategories()
    subcategory_ids = {subcategory["id"] for subcategory in subcategories}
    rendered = []
    remove_ids = []

    for index, item in enumerate(designs):
        item_id = item["id"]
        prefix = f"design_{item_id}_"
        defaults = {
            "catalog_id": item.get("catalog_id"),
            "category": item.get(
                "category_id", item.get("categoria_codigo", "0000")
            ),
            "subcategory_id": item.get("subcategory_id"),
            "design_number": item.get("design_number"),
            "code": item.get("codigo", ""),
            "name": item.get("nombre", ""),
            "width": item.get("ancho_cm", 0.0),
            "height": item.get("alto_cm", 0.0),
            "quantity": item.get("cantidad", 10),
            "embroidery_minutes": item.get("bordado_minutos", 12.0),
            "setup_minutes": item.get("preparacion_minutos", 0.0),
            "extra_minutes": item.get("minutos_adicionales", 0.0),
        }
        for field, value in defaults.items():
            st.session_state.setdefault(prefix + field, value)
        if st.session_state[prefix + "catalog_id"] not in catalog_ids:
            st.session_state[prefix + "catalog_id"] = None
        if st.session_state[prefix + "subcategory_id"] not in subcategory_ids:
            st.session_state[prefix + "subcategory_id"] = None

        with st.container(border=True):
            title = f"Diseño {index + 1}"
            selected_id = st.session_state[prefix + "catalog_id"]
            if selected_id in catalog_by_id:
                selected = catalog_by_id[selected_id]
                title = f"{selected['codigo']} — {selected['nombre']}"
            st.subheader(title)

            catalog_id = st.selectbox(
                "Diseño guardado (opcional)",
                options=[None] + [design["id"] for design in catalog],
                format_func=lambda value: (
                    "Capturar un diseño nuevo"
                    if value is None
                    else next(
                        f"{design['codigo']} — {design['nombre']}"
                        for design in catalog if design["id"] == value
                    )
                ),
                key=prefix + "catalog_id",
                on_change=_on_quote_design_selected,
                args=(prefix,),
            )
            selected = catalog_by_id.get(catalog_id)
            if selected:
                category_code = selected["category_id"]
                subcategory_id = selected["subcategory_id"]
                name = st.session_state[prefix + "name"]
                code = selected["codigo"]
                design_number = selected["design_number"]
                st.caption(
                    f"Código: **{code}** · "
                    f"{DESIGN_CATEGORIES[category_code]} / "
                    f"{selected['subcategory_name']}"
                )
                name = st.text_input(
                    "Nombre para esta cotización",
                    key=prefix + "name",
                ).strip()
            else:
                cols = st.columns([1, 2, 2])
                with cols[0]:
                    category_code = st.selectbox(
                        "Categoría",
                        options=list(DESIGN_CATEGORIES),
                        format_func=lambda value: (
                            f"{value} — {DESIGN_CATEGORIES[value]}"
                        ),
                        key=prefix + "category",
                    )
                with cols[1]:
                    subcategory_options = [None] + [
                        item["id"] for item in subcategories
                    ]
                    subcategory_id = st.selectbox(
                        "Subcategoría",
                        options=subcategory_options,
                        format_func=lambda value: (
                            "Seleccionar subcategoría" if value is None else next(
                                f"{item['id']:04d} — {item['nombre']}"
                                for item in subcategories
                                if item["id"] == value
                            )
                        ),
                        key=prefix + "subcategory_id",
                    )
                with cols[2]:
                    name = st.text_input(
                        "Nombre del diseño",
                        placeholder="Ej. Palomas",
                        key=prefix + "name",
                    ).strip()
                design_number = st.session_state[prefix + "design_number"]
                code = st.session_state[prefix + "code"]
                if category_code and subcategory_id:
                    if design_number:
                        code = design_code(
                            category_code, subcategory_id, design_number
                        )
                    else:
                        code = (
                            f"{category_code}-{subcategory_id:04d}-pendiente"
                        )
                if subcategory_id is None:
                    st.caption("Selecciona o crea una subcategoría.")
                with st.expander("Crear subcategoría"):
                    st.text_input(
                        "Nombre de la nueva subcategoría",
                        key=prefix + "new_subcategory_name",
                        placeholder="Ej. Cruz o Anillos",
                    )
                    st.button(
                        "Agregar subcategoría",
                        key=prefix + "create_subcategory",
                        on_click=_create_quote_subcategory,
                        args=(prefix,),
                        disabled=not st.session_state.get(
                            prefix + "new_subcategory_name", ""
                        ).strip(),
                    )
                if name:
                    st.button(
                        "Guardar diseño en catálogo",
                        disabled=subcategory_id is None,
                        key=prefix + "save_to_catalog",
                        on_click=_save_design_to_catalog,
                        args=(prefix, category_code, subcategory_id, name),
                    )

            cols = st.columns(4)
            with cols[0]:
                quantity = st.number_input(
                    "Cantidad de piezas",
                    min_value=1,
                    step=1,
                    key=prefix + "quantity",
                )
            with cols[1]:
                embroidery_minutes = st.number_input(
                    "Bordado por corrida (min)",
                    min_value=0.0,
                    step=0.1,
                    format="%.2f",
                    key=prefix + "embroidery_minutes",
                )
            with cols[2]:
                setup_minutes = st.number_input(
                    "Preparación (min)",
                    min_value=0.0,
                    step=0.1,
                    format="%.2f",
                    key=prefix + "setup_minutes",
                )
            with cols[3]:
                extra_minutes = st.number_input(
                    "Tiempo adicional (min)",
                    min_value=0.0,
                    step=0.1,
                    format="%.2f",
                    key=prefix + "extra_minutes",
                    help=(
                        "Tiempo del operador que no ocurre mientras la máquina "
                        "está bordando."
                    ),
                )

            dimension_cols = st.columns(2)
            with dimension_cols[0]:
                width = st.number_input(
                    "Ancho (cm)", min_value=0.0, step=0.1,
                    key=prefix + "width",
                )
            with dimension_cols[1]:
                height = st.number_input(
                    "Alto (cm)", min_value=0.0, step=0.1,
                    key=prefix + "height",
                )
            item["cantidad"] = int(quantity)
            item["materiales"] = st.session_state.get(
                prefix + "materials", item.get("materiales", [])
            )
            render_design_materials(item, materials, prefix)
            rendered.append({
                "id": item_id,
                "catalog_id": catalog_id,
                "codigo": code,
                "category_id": category_code,
                "subcategory_id": subcategory_id,
                "design_number": design_number,
                "categoria_codigo": category_code,
                "categoria_nombre": DESIGN_CATEGORIES[category_code],
                "nombre": name,
                "ancho_cm": float(width),
                "alto_cm": float(height),
                "cantidad": int(quantity),
                "bordado_minutos": float(embroidery_minutes),
                "preparacion_minutos": float(setup_minutes),
                "minutos_adicionales": float(extra_minutes),
                "materiales": item["materiales"],
            })
            if len(designs) > 1 and st.button(
                "Quitar diseño",
                key=prefix + "remove",
            ):
                remove_ids.append(item_id)

    if remove_ids:
        rendered = [item for item in rendered if item["id"] not in remove_ids]
    st.session_state.quote_design_items = rendered
    return rendered
