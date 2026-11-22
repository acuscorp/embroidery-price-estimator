from datetime import datetime

import streamlit as st

from repositories.client_repository import (
    client_display_name,
    get_client,
    list_clients,
)
from views.configuration.state import ensure_configuration_state

MANUAL_CLIENT_OPTION = "manual"


def get_machine_config():
    ensure_configuration_state()
    return {
        "heads": st.session_state.heads,
        "machine_heads_note": st.session_state.machine_heads_note,
    }


def render_machine_config():
    st.header("Configuración de máquina")
    st.caption(
        "Estos valores describen la máquina utilizada para esta cotización y se "
        "guardan junto con ella."
    )
    cols = st.columns(2)
    with cols[0]:
        st.number_input(
            "Cabezales que trabajan simultáneamente",
            min_value=1, max_value=20, value=2, step=1, key="heads",
        )
    with cols[1]:
        st.checkbox(
            "Los cabezales ejecutan el diseño actual simultáneamente",
            value=True, key="machine_heads_note",
        )
    st.caption(
        "Durante el bordado se consume tiempo de máquina y operador "
        "simultáneamente; preparación y tareas adicionales consumen tiempo "
        "de operador."
    )
    return get_machine_config()


def _client_option_label(client):
    label = client_display_name(client)
    if client.get("telefono"):
        label += f" · {client['telefono']}"
    if not client["activo"]:
        label += " (Archivado)"
    return label


def _on_client_selected():
    selected_id = st.session_state["quote_client_selector"]
    if selected_id == MANUAL_CLIENT_OPTION:
        st.session_state["quote_client_id"] = None
        st.session_state["quote_cliente"] = ""
        st.session_state["quote_telefono"] = ""
        st.session_state["quote_correo"] = ""
        return

    selected_client = get_client(selected_id)
    if selected_client is None:
        raise ValueError("La ficha seleccionada ya no está disponible.")
    st.session_state["quote_client_id"] = selected_client["id"]
    st.session_state["quote_cliente"] = client_display_name(selected_client)
    st.session_state["quote_telefono"] = selected_client["telefono"]
    st.session_state["quote_correo"] = selected_client["correo"]


def render_order_config():
    st.header("Cliente y entrega")
    current_client_id = st.session_state.get("quote_client_id")
    clients = list_clients()
    selected_client = (
        get_client(current_client_id) if current_client_id is not None else None
    )
    if current_client_id is not None and selected_client is None:
        st.session_state["quote_client_id"] = None
    if selected_client and all(
        client["id"] != current_client_id for client in clients
    ):
        clients.append(selected_client)

    client_options = [MANUAL_CLIENT_OPTION] + [
        client["id"] for client in clients
    ]
    selected_option = (
        current_client_id
        if current_client_id in client_options
        else MANUAL_CLIENT_OPTION
    )
    st.session_state["quote_client_selector"] = selected_option
    if selected_client:
        st.session_state["quote_cliente"] = client_display_name(selected_client)
        st.session_state["quote_telefono"] = selected_client["telefono"]
        st.session_state["quote_correo"] = selected_client["correo"]

    cols = st.columns(2)
    with cols[0]:
        folio = st.text_input(
            "Folio",
            key="quote_folio",
            disabled=True,
        )
        if not folio:
            st.caption("Se genera automáticamente al guardar.")
    with cols[1]:
        status_options = ["Borrador", "Enviada", "Aprobada", "Cancelada"]
        current_status = st.session_state.get("quote_estado", "Borrador")
        status = st.selectbox(
            "Estado", status_options, index=status_options.index(current_status),
            key="quote_estado",
        )

    cols = st.columns([2, 3])
    with cols[0]:
        client_id = st.selectbox(
            "Ficha de cliente",
            options=client_options,
            format_func=lambda option: (
                "Captura manual" if option == MANUAL_CLIENT_OPTION else next(
                    _client_option_label(client)
                    for client in clients if client["id"] == option
                )
            ),
            key="quote_client_selector",
            on_change=_on_client_selected,
        )
        st.caption("Escribe en la lista para filtrar las fichas registradas.")
    selected_client = (
        next((client for client in clients if client["id"] == client_id), None)
        if client_id != MANUAL_CLIENT_OPTION else None
    )
    with cols[1]:
        client = st.text_input(
            "Cliente",
            key="quote_cliente",
            disabled=selected_client is not None,
            placeholder="Nombre y apellido o nombre del negocio",
        )

    cols = st.columns(2)
    with cols[0]:
        phone = st.text_input(
            "Teléfono",
            key="quote_telefono",
            disabled=selected_client is not None,
        )
    with cols[1]:
        email = st.text_input(
            "Correo",
            key="quote_correo",
            disabled=selected_client is not None,
        )
    if selected_client:
        st.caption("Los datos se toman de la ficha y no se pueden editar aquí.")

    machine = get_machine_config()

    with st.columns(3)[0]:
        delivery_date = st.date_input(
            "Fecha estimada de entrega",
            value=datetime.now().date(),
            min_value=datetime.now().date(),
            key="delivery_date",
        )

    return {
        "quote_folio": folio,
        "client_name": (
            client_display_name(selected_client)
            if selected_client else client
        ),
        "quote_status": status,
        "client_phone": phone,
        "client_email": email,
        "client_id": selected_client["id"] if selected_client else None,
        **machine,
        "delivery_date": delivery_date,
    }
