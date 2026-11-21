import pandas as pd
import streamlit as st

from services.quote_calculations import calculate_direct_costs


DEFAULT_EXTRAS = [
    {"Concepto": "Digitalización", "Activo": False, "Importe ($)": 0.0},
    {"Concepto": "Empaque especial", "Activo": False, "Importe ($)": 0.0},
    {"Concepto": "Envío", "Activo": False, "Importe ($)": 0.0},
    {"Concepto": "Proceso externo", "Activo": False, "Importe ($)": 0.0},
]


def render_direct_cost_config():
    st.header("5. Otros costos directos del pedido")
    st.caption(
        "Incluye solo importes atribuibles a este pedido. Los gastos mensuales "
        "del taller se administran en gastos indirectos."
    )
    if "extras" not in st.session_state:
        st.session_state.extras = pd.DataFrame(DEFAULT_EXTRAS)
    extras = st.data_editor(
        st.session_state.extras,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Concepto": st.column_config.TextColumn("Concepto", required=True),
            "Activo": st.column_config.CheckboxColumn("Activo"),
            "Importe ($)": st.column_config.NumberColumn(
                "Importe ($)", min_value=0.0, step=0.01, format="$%.2f"
            ),
        },
        key="extras_editor",
    )
    st.session_state.extras = extras
    return extras, calculate_direct_costs(extras)
