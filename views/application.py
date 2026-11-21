import streamlit as st

from repositories.quote_repository import init_database
from views.pages.clients import render_clients_page
from views.pages.designs import render_designs_page
from views.pages.history import render_history_page
from views.pages.quote import render_quote_page


def run_app():
    st.set_page_config(page_title="Cotizador de bordados", page_icon="🧵", layout="wide")
    init_database()
    st.title("Cotizador de bordados")
    page = st.sidebar.radio(
        "Navegación",
        ["Cotizador", "Clientes", "Diseños", "Historial de cotizaciones"],
        key="app_page",
    )
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
