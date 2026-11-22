import pandas as pd
import streamlit as st

from services.quote_calculations import calculate_design_materials
from views.configuration.state import ensure_configuration_state


def get_material_config():
    ensure_configuration_state()
    return st.session_state.materials.drop(
        columns=["Consumo por pieza"], errors="ignore"
    )


def render_material_config():
    st.header("Materiales directos disponibles")
    st.write(
        "Define los materiales y sus precios de compra. El consumo por pieza "
        "se captura por separado en cada diseño de la cotización."
    )
    materials = get_material_config()
    materials = st.data_editor(
        materials,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Material": st.column_config.TextColumn("Material", required=True),
            "Activo": st.column_config.CheckboxColumn("Activo"),
            "Precio presentación ($)": st.column_config.NumberColumn(
                "Precio presentación ($)", min_value=0.0, step=0.01, format="$%.4f"
            ),
            "Contenido presentación": st.column_config.NumberColumn(
                "Contenido presentación", min_value=0.0, step=0.01, format="%.2f"
            ),
            "Unidad": st.column_config.SelectboxColumn(
                "Unidad", options=["m", "cm²", "pieza", "ml", "g", "unidad"]
            ),
        },
        key="materials_editor",
    )
    st.session_state.materials = materials
    return materials


def render_design_materials(item, materials, prefix):
    existing = {
        row["Material"]: row.get("Consumo por pieza", 0.0)
        for row in item.get("materiales", [])
    }
    consumption = pd.DataFrame([
        {
            "Material": str(row.get("Material", "")),
            "Consumo por pieza": existing.get(str(row.get("Material", "")), 0.0),
        }
        for _, row in materials.iterrows()
        if str(row.get("Material", "")).strip()
    ], columns=["Material", "Consumo por pieza"])
    st.write(
        "Consumo estimado por pieza de este diseño. Deja 0 si no utiliza "
        "ese material."
    )
    consumption = st.data_editor(
        consumption,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Material": st.column_config.TextColumn(disabled=True),
            "Consumo por pieza": st.column_config.NumberColumn(
                min_value=0.0, step=0.01, format="%.2f", required=True
            ),
        },
        key=prefix + "materials_editor",
    )
    item["materiales"] = consumption.to_dict(orient="records")
    details, total = calculate_design_materials(
        materials, item["materiales"], item["cantidad"]
    )
    if not details.empty:
        st.dataframe(
            details,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Costo por unidad ($)": st.column_config.NumberColumn(
                    format="$%.8f"
                ),
                "Costo total ($)": st.column_config.NumberColumn(
                    format="$%.4f"
                ),
            },
        )
    return details, total
