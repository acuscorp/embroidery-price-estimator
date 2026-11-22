import pandas as pd
import streamlit as st

from services.quote_calculations import calculate_direct_costs


DEFAULT_EXTRAS = [
    {"Concepto": "Digitalización", "Activo": False, "Importe ($)": 0.0},
    {"Concepto": "Empaque especial", "Activo": False, "Importe ($)": 0.0},
    {"Concepto": "Envío", "Activo": False, "Importe ($)": 0.0},
    {"Concepto": "Proceso externo", "Activo": False, "Importe ($)": 0.0},
]


def get_direct_cost_config():
    if "quote_extras" not in st.session_state:
        st.session_state.quote_extras = pd.DataFrame(DEFAULT_EXTRAS)
    return st.session_state.quote_extras, calculate_direct_costs(
        st.session_state.quote_extras
    )


def render_direct_cost_config():
    st.header("Otros costos directos del pedido")
    st.caption(
        "Estos conceptos e importes son específicos de esta cotización y se "
        "conservan al guardarla."
    )
    extras, _ = get_direct_cost_config()
    extras = st.data_editor(
        extras,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Concepto": st.column_config.TextColumn("Concepto", required=True),
            "Activo": st.column_config.CheckboxColumn("Activo"),
            "Importe ($)": st.column_config.NumberColumn(
                "Importe ($)", min_value=0.0, step=0.01, format="$%.2f"
            ),
        },
        key="quote_extras_editor",
    )
    st.session_state.quote_extras = extras
    return get_direct_cost_config()
