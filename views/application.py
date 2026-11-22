import streamlit as st

from repositories.quote_repository import init_database
from views.pages.clients import render_clients_page
from views.pages.configuration import render_configuration_page
from views.pages.designs import render_designs_page
from views.pages.history import render_history_page
from views.pages.quote import render_quote_page
from views.configuration.state import (
    ensure_configuration_state,
    reload_configuration_state,
)


def run_app():
    st.set_page_config(page_title="Cotizador de bordados", page_icon="🧵", layout="wide")
    init_database()
    st.title("Cotizador de bordados")
    ensure_configuration_state()
    page = st.sidebar.radio(
        "Navegación",
        [
            "Cotizador",
            "Configuración",
            "Clientes",
            "Diseños",
            "Historial de cotizaciones",
        ],
        key="app_page",
    )
    previous_page = st.session_state.get("last_app_page")
    if page == "Configuración" and previous_page != page:
        reload_configuration_state()
    st.session_state["last_app_page"] = page
    if page == "Configuración":
        render_configuration_page()
        return
    if page == "Clientes":
        render_clients_page()
        return
    if page == "Diseños":
        render_designs_page()
        return
    if page == "Historial de cotizaciones":
        render_history_page()
        return
    render_quote_page()
