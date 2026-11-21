import pandas as pd
import streamlit as st

from repositories.client_repository import (
    client_quote_count,
    client_display_name,
    create_client,
    delete_client,
    list_clients,
    set_client_active,
    update_client,
)


def _client_form_values(prefix, client=None):
    client = client or {}
    with st.form(f"{prefix}_form"):
        first, last = st.columns(2)
        with first:
            nombres = st.text_input(
                "Nombre(s)",
                value=client.get("nombres", ""),
                key=f"{prefix}_nombres",
            )
        with last:
            apellidos = st.text_input(
                "Apellidos",
                value=client.get("apellidos", ""),
                key=f"{prefix}_apellidos",
            )

        company, phone = st.columns(2)
        with company:
            empresa = st.text_input(
                "Empresa (opcional)",
                value=client.get("empresa", ""),
                key=f"{prefix}_empresa",
            )
        with phone:
            telefono = st.text_input(
                "Teléfono",
                value=client.get("telefono", ""),
                key=f"{prefix}_telefono",
            )

        email = st.text_input(
            "Correo electrónico",
            value=client.get("correo", ""),
            key=f"{prefix}_correo",
        )
        direccion = st.text_area(
            "Dirección de entrega",
            value=client.get("direccion", ""),
            key=f"{prefix}_direccion",
        )
        notas = st.text_area(
            "Notas",
            value=client.get("notas", ""),
            key=f"{prefix}_notas",
        )
        confirm_update = True
        if client:
            confirm_update = st.checkbox(
                "Confirmo guardar los cambios de esta ficha",
                key=f"{prefix}_confirm_update",
            )
        submitted = st.form_submit_button(
            "Guardar cambios" if client else "Registrar cliente",
            type="primary",
            use_container_width=True,
            disabled=bool(client and not confirm_update),
        )

    return submitted, {
        "nombres": nombres,
        "apellidos": apellidos,
        "empresa": empresa,
        "telefono": telefono,
        "correo": email,
        "direccion": direccion,
        "notas": notas,
    }


def render_clients_page():
    for key in st.session_state.pop("client_confirmations_to_reset", []):
        st.session_state[key] = False
    update_message = st.session_state.pop("client_update_message", None)
    if update_message:
        st.success(update_message)

    st.header("Clientes")
    st.caption(
        "Registra y administra los datos de contacto. Los clientes archivados "
        "se conservan para no perder su historial."
    )

    with st.expander("Registrar cliente", expanded=True):
        submitted, client_data = _client_form_values("new_client")
        if submitted:
            if not client_data["nombres"].strip() and not client_data["empresa"].strip():
                st.error("Captura el nombre del cliente o el nombre de la empresa.")
            else:
                create_client(client_data)
                st.success("Cliente registrado.")
                st.rerun()

    show_archived = st.toggle("Incluir clientes archivados", value=False)
    clients = list_clients(include_archived=show_archived)
    search = st.text_input(
        "Buscar cliente",
        placeholder="Nombre, apellido, empresa, teléfono o correo",
        key="clients_search",
    ).strip().casefold()
    if search:
        clients = [
            client for client in clients
            if search in " ".join(
                str(client.get(field) or "")
                for field in (
                    "nombres", "apellidos", "empresa", "telefono", "correo"
                )
            ).casefold()
        ]

    st.caption(f"{len(clients)} cliente(s) encontrado(s)")
    if not clients:
        st.info("No hay clientes que coincidan con la búsqueda.")
        return

    client_ids = {client["id"] for client in clients}
    if st.session_state.get("selected_client_id") not in client_ids:
        st.session_state["selected_client_id"] = clients[0]["id"]
    table = pd.DataFrame([
        {
            "ID": client["id"],
            "Nombre": client_display_name(client),
            "Teléfono": client["telefono"],
            "Correo": client["correo"],
            "Estado": "Activo" if client["activo"] else "Archivado",
        }
        for client in clients
    ])
    st.dataframe(table, use_container_width=True, hide_index=True)

    selected_id = st.selectbox(
        "Seleccionar cliente para editar",
        options=[client["id"] for client in clients],
        format_func=lambda client_id: next(
            client_display_name(client)
            for client in clients if client["id"] == client_id
        ),
        key="selected_client_id",
    )
    selected = next(client for client in clients if client["id"] == selected_id)
    with st.expander("Editar ficha del cliente", expanded=False):
        submitted, client_data = _client_form_values(
            f"edit_client_{selected_id}", selected
        )
        if submitted:
            if not client_data["nombres"].strip() and not client_data["empresa"].strip():
                st.error("Captura el nombre del cliente o el nombre de la empresa.")
            else:
                update_client(selected_id, client_data)
                st.session_state["client_update_message"] = (
                    "Ficha del cliente actualizada."
                )
                st.session_state["client_confirmations_to_reset"] = [
                    f"edit_client_{selected_id}_confirm_update"
                ]
                st.rerun()

    action_label = "Reactivar cliente" if not selected["activo"] else "Archivar cliente"
    confirm_status = st.checkbox(
        "Confirmo cambiar el estado del cliente",
        key=f"confirm_status_client_{selected_id}",
    )
    if st.button(
        action_label,
        disabled=not confirm_status,
        key=f"toggle_client_{selected_id}",
    ):
        set_client_active(selected_id, not bool(selected["activo"]))
        st.session_state["client_confirmations_to_reset"] = [
            f"confirm_status_client_{selected_id}"
        ]
        st.rerun()

    related_quotes = client_quote_count(selected_id)
    if related_quotes:
        st.info(
            f"Este cliente tiene {related_quotes} cotización(es) vinculada(s). "
            "Archívalo para conservar ese historial."
        )
    else:
        confirm_delete = st.checkbox(
            "Confirmo eliminar definitivamente este cliente",
            key=f"confirm_delete_client_{selected_id}",
        )
        if st.button(
            "Eliminar definitivamente",
            disabled=not confirm_delete,
            key=f"delete_client_{selected_id}",
        ):
            delete_client(selected_id)
            st.rerun()
