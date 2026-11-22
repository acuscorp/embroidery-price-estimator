import sqlite3

import streamlit as st

from views.configuration.state import (
    ensure_configuration_state,
    persist_configuration_state,
)
from views.configuration.financial import render_financial_config
from views.configuration.direct_costs import render_direct_cost_config
from views.configuration.materials import render_material_config
from views.configuration.order import render_machine_config


def render_configuration_page():
    ensure_configuration_state()
    st.header("Configuración")
    st.caption(
        "Edita y guarda los valores base reutilizables para nuevas cotizaciones. "
        "Cada cotización conserva una copia de los valores usados al guardarse."
    )
    render_financial_config()
    st.divider()
    render_direct_cost_config()
    st.divider()
    render_material_config()
    st.divider()
    render_machine_config()
    st.divider()
    if st.button("Guardar configuración", type="primary"):
        try:
            persist_configuration_state()
        except (TypeError, ValueError, sqlite3.Error) as error:
            st.error(f"No se pudo guardar la configuración: {error}")
        else:
            st.success("Configuración guardada en la base de datos.")
