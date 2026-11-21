import json
from datetime import date

import pandas as pd
import streamlit as st

from repositories.quote_repository import delete_quote, get_quote, list_quotes


def _queue_quote_load(quote_id):
    quote = get_quote(quote_id)
    if not quote:
        st.session_state["history_error"] = (
            "La cotización seleccionada ya no existe."
        )
        return
    st.session_state.pending_quote_load = json.loads(quote["datos_json"])
    st.session_state.pending_quote_metadata = {
        "folio": quote["folio"],
        "client_id": quote.get("client_id"),
        "cliente": quote["cliente"] or "",
        "telefono": quote["telefono"] or "",
        "correo": quote["correo"] or "",
        "estado": quote["estado"],
    }
    st.session_state.app_page = "Cotizador"


def render_history_page():
    history_error = st.session_state.pop("history_error", None)
    if history_error:
        st.error(history_error)
    st.header("Historial de cotizaciones")
    st.caption("Busca por nombre, apellido o folio, y filtra por fecha de cotización.")
    quotes = list_quotes()
    if not quotes:
        st.info("Todavía no hay cotizaciones guardadas.")
        return

    filter_cols = st.columns([2, 1])
    with filter_cols[0]:
        search = st.text_input(
            "Buscar por nombre, apellido o folio",
            placeholder="Escribe el nombre o folio",
            key="history_search",
        ).strip().casefold()
    with filter_cols[1]:
        quote_dates = [
            date.fromisoformat(quote["fecha_cotizacion"][:10])
            for quote in quotes if quote.get("fecha_cotizacion")
        ]
        date_range = st.date_input(
            "Rango de fecha de cotización",
            value=(min(quote_dates), max(quote_dates)),
            min_value=min(quote_dates),
            max_value=max(quote_dates),
            key="history_date_range",
        )
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range[0]

    filtered = []
    for quote in quotes:
        quote_date = date.fromisoformat(quote["fecha_cotizacion"][:10])
        searchable = f"{quote.get('cliente') or ''} {quote.get('folio') or ''}".casefold()
        if start_date <= quote_date <= end_date and (not search or search in searchable):
            filtered.append(quote)

    st.caption(f"{len(filtered)} cotización(es) encontrada(s)")
    if not filtered:
        st.info("No se encontraron cotizaciones con esos filtros.")
        return

    quote_ids = {quote["id"] for quote in filtered}
    if st.session_state.get("history_quote_id") not in quote_ids:
        st.session_state["history_quote_id"] = filtered[0]["id"]
    display = pd.DataFrame(filtered)[[
        "id", "folio", "cliente", "estado", "fecha_cotizacion",
        "fecha_entrega", "precio_unitario", "precio_total",
    ]].copy()
    for column in ("precio_unitario", "precio_total"):
        display[column] = display[column].map(
            lambda value: f"${value:,.2f}" if pd.notna(value) else ""
        )
    st.dataframe(display, use_container_width=True, hide_index=True)

    quote_id = st.selectbox(
        "Seleccionar cotización",
        options=[quote["id"] for quote in filtered],
        format_func=lambda selected_id: next(
            f'{quote["folio"]} — {quote["cliente"] or "Sin cliente"} ({quote["estado"]})'
            for quote in filtered if quote["id"] == selected_id
        ),
        key="history_quote_id",
    )
    open_col, delete_col = st.columns(2)
    open_col.button(
        "Abrir cotización",
        use_container_width=True,
        type="primary",
        on_click=_queue_quote_load,
        args=(quote_id,),
    )
    confirm_delete = delete_col.checkbox(
        "Confirmo eliminar esta cotización",
        key=f"confirm_delete_quote_{quote_id}",
    )
    if delete_col.button(
        "Eliminar cotización",
        use_container_width=True,
        disabled=not confirm_delete,
    ):
        delete_quote(quote_id)
        st.rerun()
