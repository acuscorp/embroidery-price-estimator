import streamlit as st

from services.quote_calculations import calculate_direct_costs
from views.configuration.state import ensure_configuration_state


def get_direct_cost_config():
    ensure_configuration_state()
    return st.session_state.extras, calculate_direct_costs(
        st.session_state.extras
    )


def render_direct_cost_config():
    st.header("Otros costos directos del pedido")
    st.caption(
        "Edita aquí los valores base reutilizables en nuevas cotizaciones. "
        "Cada cotización conserva su propia copia de estos importes."
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
        key="extras_editor",
    )
    st.session_state.extras = extras
    return get_direct_cost_config()
