from datetime import date, datetime

import pandas as pd
import streamlit as st

from exports.pdf_export import build_quote_pdfs
from repositories.quote_repository import quote_exists, save_quote
from services.quote_calculations import (
    calculate_design_line,
    calculate_material_costs,
    find_applicable_margin,
    validate_quote,
)
from views.configuration.designs import new_design_item, render_designs
from views.configuration.direct_costs import render_direct_cost_config
from views.configuration.financial import render_financial_config
from views.configuration.margin import render_margin_config
from views.configuration.materials import render_material_config
from views.configuration.order import render_order_config


def _restore_quote():
    if "pending_quote_load" in st.session_state:
        loaded = st.session_state.pop("pending_quote_load")
        widget_values = loaded.pop("widget_values", {})
        for key, value in widget_values.items():
            if key == "delivery_date" and isinstance(value, str):
                value = date.fromisoformat(value)
            st.session_state[key] = value
        for name in ("monthly_costs", "materials", "extras", "margin_tiers"):
            if name in loaded:
                st.session_state[name] = pd.DataFrame(loaded[name])

        design_items = loaded.get("design_items")
        if not design_items:
            legacy_item = new_design_item()
            legacy_item.update({
                "cantidad": widget_values.get("quantity", 10),
                "bordado_minutos": widget_values.get(
                    "embroidery_minutes_per_run", 12.0
                ),
                "preparacion_minutos": widget_values.get("setup_minutes", 0.0),
                "minutos_adicionales": widget_values.get(
                    "extra_operator_minutes", 0.0
                ),
            })
            design_items = [legacy_item]
        st.session_state.quote_design_items = design_items
        for item in design_items:
            prefix = f"design_{item['id']}_"
            st.session_state[prefix + "catalog_id"] = item.get("catalog_id")
            st.session_state[prefix + "category"] = item.get(
                "categoria_codigo", "000"
            )
            st.session_state[prefix + "name"] = item.get("nombre", "")
            st.session_state[prefix + "quantity"] = item.get("cantidad", 10)
            st.session_state[prefix + "embroidery_minutes"] = item.get(
                "bordado_minutos", 12.0
            )
            st.session_state[prefix + "setup_minutes"] = item.get(
                "preparacion_minutos", 0.0
            )
            st.session_state[prefix + "extra_minutes"] = item.get(
                "minutos_adicionales", 0.0
            )

    if "pending_quote_metadata" in st.session_state:
        metadata = st.session_state.pop("pending_quote_metadata")
        for name, value in metadata.items():
            st.session_state[f"quote_{name}"] = value
        st.session_state["quote_client_id"] = metadata.get("client_id")


def _calculate_design_items(design_items, materials, extras_total, order,
                            financial, margin_tiers):
    line_inputs = []
    for item in design_items:
        _, material_total = calculate_material_costs(
            materials, item["cantidad"]
        )
        times = calculate_design_line(
            item["cantidad"],
            order["heads"],
            item["bordado_minutos"],
            item["preparacion_minutos"],
            item["minutos_adicionales"],
            financial["allocation_rate"],
            material_total,
            0.0,
            0.0,
        )
        line_inputs.append({
            **item,
            **times,
            "materiales_total": material_total,
            "costo_antes_otros_directos": times["cost_total"],
        })

    total_weight = sum(
        item["costo_antes_otros_directos"] for item in line_inputs
    )
    total_quantity = sum(item["cantidad"] for item in line_inputs)
    for item in line_inputs:
        if total_weight > 0:
            share = (
                extras_total
                * item["costo_antes_otros_directos"]
                / total_weight
            )
        else:
            share = extras_total * item["cantidad"] / total_quantity
        margin_pct = find_applicable_margin(margin_tiers, item["cantidad"])
        if margin_pct is None:
            margin_pct = st.number_input(
                f"Margen manual para {item['codigo']} — {item['nombre'] or 'Diseño sin nombre'} (%)",
                min_value=0.0,
                max_value=99.0,
                value=30.0,
                step=0.1,
                format="%.2f",
                key=f"design_{item['id']}_manual_margin",
            )
        final = calculate_design_line(
            item["cantidad"],
            order["heads"],
            item["bordado_minutos"],
            item["preparacion_minutos"],
            item["minutos_adicionales"],
            financial["allocation_rate"],
            item["materiales_total"],
            share,
            margin_pct,
        )
        item.update(final)
        item["otros_directos_asignados"] = share
        item["margen_pct"] = margin_pct
    return line_inputs


def _build_quote_payload(design_items, order, financial, materials_total,
                         extras_total, margin_tiers):
    quantity = sum(item["cantidad"] for item in design_items)
    cost_total = sum(item["cost_total"] for item in design_items)
    price_total = sum(item["price_total"] for item in design_items)
    total_minutes = sum(
        item["combined_order_minutes"] for item in design_items
    )
    weighted_margin = (
        sum(
            item["price_total"] * item["margen_pct"]
            for item in design_items
        ) / price_total
        if price_total else 0.0
    )
    return {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "objetivo_mensual_capturado": financial["goal_entered"],
        "cantidad": quantity,
        "cabezales": int(order["heads"]),
        "corridas": sum(item["runs"] for item in design_items),
        "minutos_maquina": sum(item["machine_minutes"] for item in design_items),
        "minutos_operador": sum(item["operator_minutes"] for item in design_items),
        "minutos_recurso_combinados": total_minutes,
        "tarifa_unica_minuto_recurso": financial["allocation_rate"],
        "costos_indirectos_mensuales": financial["monthly_pool"],
        "pago_mensual_operador": financial["monthly_labor_pool"],
        "objetivo_mensual": financial["monthly_goal"],
        "costo_capacidad_combinada_pedido": sum(
            item["allocation_cost"] for item in design_items
        ),
        "materiales": materials_total,
        "otros_directos": extras_total,
        "costo_total": cost_total,
        "costo_unitario_base": cost_total / quantity,
        "margen_pct": weighted_margin,
        "precio_total": price_total,
        "precio_unitario": price_total / quantity,
        "fecha_entrega": order["delivery_date"].isoformat(),
        "cliente": order["client_name"],
        "telefono": order["client_phone"],
        "correo": order["client_email"],
        "estado": order["quote_status"],
        "folio": order["quote_folio"],
        "client_id": order["client_id"],
        "disenos": design_items,
        "margenes_configurados": margin_tiers.to_dict(orient="records"),
    }


def render_quote_page():
    _restore_quote()
    pending_folio = st.session_state.pop("pending_quote_folio", None)
    if pending_folio:
        st.session_state["quote_folio"] = pending_folio
    confirmation_key = st.session_state.pop(
        "quote_confirmation_key_to_reset", None
    )
    if confirmation_key:
        st.session_state[confirmation_key] = False
    saved_message = st.session_state.pop("quote_saved_message", None)
    if saved_message:
        st.success(saved_message)
    financial = render_financial_config()
    order = render_order_config()
    design_items = render_designs()
    total_quantity = sum(item["cantidad"] for item in design_items)
    materials, material_detail, materials_total = render_material_config(
        total_quantity
    )
    extras, extras_total = render_direct_cost_config()
    margin_tiers = render_margin_config()
    calculated_items = _calculate_design_items(
        design_items, materials, extras_total, order, financial, margin_tiers
    )
    designs_complete = all(
        item["nombre"].strip()
        and item["codigo"].startswith(f"{item['categoria_codigo']}-")
        for item in design_items
    )
    if not designs_complete:
        st.warning(
            "Asigna un nombre válido a cada diseño para generar su código "
            "antes de guardar la cotización."
        )

    st.header("7. Resultado por diseño")
    display = pd.DataFrame([
        {
            "Código": item["codigo"],
            "Diseño": item["nombre"] or "Sin nombre",
            "Piezas": item["cantidad"],
            "Corridas": item["runs"],
            "Costo total ($)": item["cost_total"],
            "Margen (%)": item["margen_pct"],
            "Precio por pieza ($)": item["price_unit"],
            "Subtotal ($)": item["price_total"],
        }
        for item in calculated_items
    ])
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Costo total ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Margen (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Precio por pieza ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Subtotal ($)": st.column_config.NumberColumn(format="$%.2f"),
        },
    )
    quantity = sum(item["cantidad"] for item in calculated_items)
    price_total = sum(item["price_total"] for item in calculated_items)
    st.subheader("Total de la cotización")
    cols = st.columns(3)
    cols[0].metric("Piezas totales", f"{quantity:,}")
    cols[1].metric("Precio promedio por pieza", f"${price_total / quantity:,.2f}")
    cols[2].metric("TOTAL", f"${price_total:,.2f}")

    total_runs = sum(item["runs"] for item in calculated_items)
    machine_minutes = sum(
        item["machine_minutes"] for item in calculated_items
    )
    operator_minutes = sum(
        item["operator_minutes"] for item in calculated_items
    )
    combined_minutes = sum(
        item["combined_order_minutes"] for item in calculated_items
    )
    st.caption(
        f"Corridas: {total_runs} · Tiempo de máquina: {machine_minutes:,.2f} min · "
        f"Tiempo de operador: {operator_minutes:,.2f} min · "
        f"Minutos-recurso combinados: {combined_minutes:,.2f} min"
    )

    issues = validate_quote(
        order["machine_heads_note"],
        order["heads"],
        material_detail,
        financial["combined_productive_minutes"],
        margin_tiers,
    )
    if issues:
        for issue in issues:
            st.warning(issue)
    else:
        st.success(
            "El precio y el tramo de margen se calculan de forma independiente "
            "para cada diseño. Los otros costos directos compartidos se "
            "distribuyen proporcionalmente entre los diseños."
        )
    st.caption("El margen se aplica sobre el precio de venta. No se calcula IVA.")

    quote = _build_quote_payload(
        calculated_items,
        order,
        financial,
        materials_total,
        extras_total,
        margin_tiers,
    )
    csv_bytes = pd.DataFrame(calculated_items).to_csv(
        index=False
    ).encode("utf-8-sig")
    snapshot = dict(quote)
    snapshot.update({
        "monthly_costs": financial["monthly_costs"].to_dict(orient="records"),
        "materials": materials.to_dict(orient="records"),
        "extras": extras.to_dict(orient="records"),
        "margin_tiers": margin_tiers.to_dict(orient="records"),
        "design_items": design_items,
        "widget_values": {
            "monthly_goal": financial["monthly_goal_input"],
            "idle_pct": financial["idle_pct"],
            "work_hours": financial["work_hours"],
            "work_days": financial["work_days"],
            "operator_monthly_pay": financial["operator_monthly_pay"],
            "heads": order["heads"],
            "machine_heads_note": order["machine_heads_note"],
            "delivery_date": order["delivery_date"].isoformat(),
        },
    })

    st.divider()
    st.subheader("Guardar y descargar")
    folio = order["quote_folio"].strip()
    updating = bool(folio and quote_exists(folio))
    confirmation = True
    if updating:
        st.warning(
            "Este folio ya existe. Al continuar, se actualizarán los datos "
            "guardados de esa cotización."
        )
        confirmation = st.checkbox(
            "Confirmo actualizar la cotización existente",
            key=f"confirm_update_quote_{folio}",
        )
    if st.button(
        "Confirmar actualización" if updating else "Guardar cotización",
        use_container_width=True,
        disabled=not confirmation or not designs_complete,
        key="save_quote",
    ):
        if not folio:
            folio = f"COT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            st.session_state["pending_quote_folio"] = folio
            quote["folio"] = folio
            snapshot["folio"] = folio
        save_quote(
            folio,
            order["client_name"].strip(),
            order["client_phone"].strip(),
            order["client_email"].strip(),
            order["quote_status"],
            order["delivery_date"],
            snapshot,
            client_id=order["client_id"],
        )
        message = (
            f"Cotización actualizada con folio {folio}."
            if updating
            else f"Cotización guardada con folio {folio}."
        )
        if updating:
            st.session_state["quote_confirmation_key_to_reset"] = (
                f"confirm_update_quote_{folio}"
            )
            st.session_state["quote_saved_message"] = message
            st.rerun()
        if not order["quote_folio"].strip():
            st.session_state["quote_saved_message"] = message
            st.rerun()
        st.success(message)
    client_pdf, internal_pdf = build_quote_pdfs(quote, margin_tiers)
    cols = st.columns(3)
    cols[0].download_button(
        "PDF para cliente", data=client_pdf, file_name="cotizacion_cliente.pdf",
        mime="application/pdf", type="primary", use_container_width=True,
    )
    cols[1].download_button(
        "PDF interno", data=internal_pdf, file_name="cotizacion_interna.pdf",
        mime="application/pdf", use_container_width=True,
    )
    cols[2].download_button(
        "Diseños CSV", data=csv_bytes, file_name="cotizacion_disenos.csv",
        mime="text/csv", use_container_width=True,
    )
