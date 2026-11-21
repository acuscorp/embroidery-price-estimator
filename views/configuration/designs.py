import sqlite3
from uuid import uuid4
from typing import List

import streamlit as st

from models.designs import DESIGN_CATEGORIES, DesignQuoteLine
from repositories.design_repository import (
    create_design,
    design_code,
    list_designs,
)


def _save_design_to_catalog(prefix, category_code, name):
    try:
        catalog_id = create_design(category_code, name)
    except (ValueError, sqlite3.IntegrityError) as error:
        st.session_state["design_catalog_error"] = str(error)
    else:
        st.session_state[prefix + "catalog_id"] = catalog_id
        st.session_state.pop("design_catalog_error", None)


def new_design_item() -> DesignQuoteLine:
    return {
        "id": uuid4().hex,
        "catalog_id": None,
        "categoria_codigo": "000",
        "nombre": "",
        "cantidad": 10,
        "bordado_minutos": 12.0,
        "preparacion_minutos": 0.0,
        "minutos_adicionales": 0.0,
    }


def render_designs() -> List[DesignQuoteLine]:
    st.header("3. Diseños y cantidades")
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
    rendered = []
    remove_ids = []

    for index, item in enumerate(designs):
        item_id = item["id"]
        prefix = f"design_{item_id}_"
        defaults = {
            "catalog_id": item.get("catalog_id"),
            "category": item.get("categoria_codigo", "000"),
            "name": item.get("nombre", ""),
            "quantity": item.get("cantidad", 10),
            "embroidery_minutes": item.get("bordado_minutos", 12.0),
            "setup_minutes": item.get("preparacion_minutos", 0.0),
            "extra_minutes": item.get("minutos_adicionales", 0.0),
        }
        for field, value in defaults.items():
            st.session_state.setdefault(prefix + field, value)
        if st.session_state[prefix + "catalog_id"] not in catalog_ids:
            st.session_state[prefix + "catalog_id"] = None

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
            )
            selected = catalog_by_id.get(catalog_id)
            if selected:
                category_code = selected["categoria_codigo"]
                name = selected["nombre"]
                code = selected["codigo"]
                st.caption(
                    f"Código: **{code}** · Categoría: "
                    f"**{DESIGN_CATEGORIES[category_code]}**"
                )
            else:
                cols = st.columns([1, 3])
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
                    name = st.text_input(
                        "Nombre del diseño",
                        placeholder="Ej. Palomas",
                        key=prefix + "name",
                    ).strip()
                valid_code = True
                try:
                    code = design_code(category_code, name) if name else category_code
                except ValueError:
                    code = category_code
                    valid_code = False
                if name and not valid_code:
                    st.warning("El nombre debe incluir letras o números.")
                if name:
                    st.button(
                        "Guardar diseño en catálogo",
                        disabled=not valid_code,
                        key=prefix + "save_to_catalog",
                        on_click=_save_design_to_catalog,
                        args=(prefix, category_code, name),
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

            rendered.append({
                "id": item_id,
                "catalog_id": catalog_id,
                "codigo": code,
                "categoria_codigo": category_code,
                "categoria_nombre": DESIGN_CATEGORIES[category_code],
                "nombre": name,
                "cantidad": int(quantity),
                "bordado_minutos": float(embroidery_minutes),
                "preparacion_minutos": float(setup_minutes),
                "minutos_adicionales": float(extra_minutes),
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
