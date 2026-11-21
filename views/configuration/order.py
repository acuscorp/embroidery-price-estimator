from datetime import datetime

import streamlit as st

from repositories.client_repository import (
    client_display_name,
    get_client,
    list_clients,
)


def render_order_config():
    st.header("2. Cliente y operación")
    cols = st.columns(3)
    with cols[0]:
        folio = st.text_input(
            "Folio", value=st.session_state.get("quote_folio", ""),
            key="quote_folio",
        )
    clients = list_clients()
    client_options = [None] + [client["id"] for client in clients]
    current_client_id = st.session_state.get("quote_client_id")
    archived_client = None
    if current_client_id is not None and current_client_id not in client_options:
        archived_client = get_client(current_client_id)
        if archived_client:
            clients.append(archived_client)
            client_options.append(archived_client["id"])
    if current_client_id not in client_options:
        current_client_id = None
    with cols[1]:
        client_id = st.selectbox(
            "Ficha de cliente",
            options=client_options,
            index=client_options.index(current_client_id),
            format_func=lambda selected_id: (
                "Captura manual" if selected_id is None else next(
                    client_display_name(client)
                    + (" (Archivado)" if not client["activo"] else "")
                    for client in clients if client["id"] == selected_id
                )
            ),
            key="quote_client_id",
        )
    selected_client = next(
        (client for client in clients if client["id"] == client_id), None
    )
    with cols[0]:
        if selected_client:
            client = client_display_name(selected_client)
            st.text_input("Cliente", value=client, disabled=True)
        else:
            client = st.text_input(
                "Cliente", value=st.session_state.get("quote_cliente", ""),
                key="quote_cliente",
            )
    with cols[2]:
        status_options = ["Borrador", "Enviada", "Aprobada", "Cancelada"]
        current_status = st.session_state.get("quote_estado", "Borrador")
        status = st.selectbox(
            "Estado", status_options, index=status_options.index(current_status),
            key="quote_estado",
        )

    cols = st.columns(3)
    if selected_client:
        phone = selected_client["telefono"]
        email = selected_client["correo"]
        with cols[0]:
            st.text_input("Teléfono", value=phone, disabled=True)
        with cols[1]:
            st.text_input("Correo", value=email, disabled=True)
        st.caption("El teléfono y correo se toman de la ficha del cliente.")
    else:
        with cols[0]:
            phone = st.text_input(
                "Teléfono", value=st.session_state.get("quote_telefono", ""),
                key="quote_telefono",
            )
        with cols[1]:
            email = st.text_input(
                "Correo", value=st.session_state.get("quote_correo", ""),
                key="quote_correo",
            )

    cols = st.columns(2)
    with cols[0]:
        heads = st.number_input(
            "Cabezales que trabajan simultáneamente",
            min_value=1, max_value=20, value=2, step=1, key="heads",
        )
    with cols[1]:
        heads_simultaneous = st.checkbox(
            "Los cabezales ejecutan el diseño actual simultáneamente",
            value=True, key="machine_heads_note",
        )

    with st.columns(3)[0]:
        delivery_date = st.date_input(
            "Fecha estimada de entrega",
            value=datetime.now().date(),
            min_value=datetime.now().date(),
            key="delivery_date",
        )

    st.caption(
        "Las puntadas, RPM y datos de Wilcom son técnicos/estimaciones; no se "
        "cobran aparte. Durante el bordado se consume tiempo de máquina y operador "
        "simultáneamente; preparación y tareas adicionales consumen tiempo de operador."
    )
    return {
        "quote_folio": folio,
        "client_name": client,
        "quote_status": status,
        "client_phone": phone,
        "client_email": email,
        "client_id": client_id,
        "heads": heads,
        "machine_heads_note": heads_simultaneous,
        "delivery_date": delivery_date,
    }
