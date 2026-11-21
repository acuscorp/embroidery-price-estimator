import pandas as pd
import streamlit as st

from services.quote_calculations import calculate_material_costs


DEFAULT_MATERIALS = [
    {"Material": "Hilo superior", "Activo": True, "Precio presentación ($)": 45.0, "Contenido presentación": 5000.0, "Unidad": "m", "Consumo por pieza": 28.71},
    {"Material": "Hilo de bobina", "Activo": True, "Precio presentación ($)": 220.0, "Contenido presentación": 72000.0, "Unidad": "m", "Consumo por pieza": 9.29},
    {"Material": "Pellón", "Activo": True, "Precio presentación ($)": 900.0, "Contenido presentación": 1400000.0, "Unidad": "cm²", "Consumo por pieza": 400.0},
]


def render_material_config(quantity):
    st.header("4. Materiales directos")
    st.write(
        "Captura el precio y contenido de compra, además del consumo estimado "
        "por pieza para esta cotización."
    )
    if "materials" not in st.session_state:
        st.session_state.materials = pd.DataFrame(DEFAULT_MATERIALS)
    materials = st.data_editor(
        st.session_state.materials,
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
            "Consumo por pieza": st.column_config.NumberColumn(
                "Consumo por pieza", min_value=0.0, step=0.01, format="%.2f"
            ),
        },
        key="materials_editor",
    )
    st.session_state.materials = materials
    details, total = calculate_material_costs(materials, quantity)
    if not details.empty:
        st.dataframe(
            details,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Costo por unidad ($)": st.column_config.NumberColumn(format="$%.8f"),
                "Costo total ($)": st.column_config.NumberColumn(format="$%.4f"),
            },
        )
    return materials, details, total
