from datetime import date, datetime
import json

import pandas as pd
import streamlit as st

from exports.pdf_export import build_quote_pdfs
from models.designs import LEGACY_DESIGN_CATEGORIES
from repositories.quote_repository import (
    get_quote,
    quote_exists,
    save_quote,
)
from services.quote_calculations import (
    calculate_design_materials,
    calculate_design_line,
    find_applicable_margin,
    validate_quote,
)
from views.configuration.designs import new_design_item, render_designs
from views.configuration.direct_costs import (
    get_direct_cost_config,
    render_direct_cost_config,
)
from views.configuration.financial import calculate_financial_config
from views.configuration.margin import render_margin_config
from views.configuration.materials import get_material_config
from views.configuration.order import render_order_config


def _start_new_quote():
    keys_to_clear = [
        key for key in st.session_state
        if key.startswith(("quote_", "design_", "confirm_update_quote_"))
        or key in {
            "pending_quote_load",
            "pending_quote_metadata",
            "delivery_date",
        }
    ]
    for key in keys_to_clear:
        del st.session_state[key]


def _restore_quote():
    if "pending_quote_load" in st.session_state:
        loaded = st.session_state.pop("pending_quote_load")
        widget_values = loaded.pop("widget_values", {})
        for key, value in widget_values.items():
            if key == "delivery_date" and isinstance(value, str):
                value = date.fromisoformat(value)
            st.session_state[key] = value
        for name in ("monthly_costs", "materials", "margin_tiers"):
            if name in loaded:
                st.session_state[name] = pd.DataFrame(loaded[name])
        if "extras" in loaded:
            st.session_state["quote_extras"] = pd.DataFrame(loaded["extras"])
        st.session_state.pop("quote_extras_editor", None)
        st.session_state.pop("monthly_cost_editor", None)
        st.session_state.pop("materials_editor", None)
        legacy_materials = loaded.get("materials", [])
        legacy_consumption = {
            row.get("Material", ""): row.get("Consumo por pieza", 0.0)
            for row in legacy_materials
        }

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
            if "materiales" not in item:
                item["materiales"] = [
                    {
                        "Material": row.get("Material", ""),
                        "Consumo por pieza": legacy_consumption.get(
                            row.get("Material", ""), 0.0
                        ),
                    }
                    for row in legacy_materials
                    if row.get("Material")
                ]
            st.session_state.pop(prefix + "materials_editor", None)
            st.session_state[prefix + "catalog_id"] = item.get("catalog_id")
            st.session_state[prefix + "category"] = item.get(
                "category_id",
                LEGACY_DESIGN_CATEGORIES.get(
                    item.get("categoria_codigo", "0000"),
                    item.get("categoria_codigo", "0000"),
                ),
            )
            st.session_state[prefix + "subcategory_id"] = item.get(
                "subcategory_id"
            )
            st.session_state[prefix + "design_number"] = item.get(
                "design_number"
            )
            st.session_state[prefix + "code"] = item.get("codigo", "")
            st.session_state[prefix + "name"] = item.get("nombre", "")
            st.session_state[prefix + "width"] = item.get("ancho_cm", 0.0)
            st.session_state[prefix + "height"] = item.get("alto_cm", 0.0)
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
            st.session_state[prefix + "materials"] = item.get("materiales", [])

    if "pending_quote_metadata" in st.session_state:
        metadata = st.session_state.pop("pending_quote_metadata")
        for name, value in metadata.items():
            st.session_state[f"quote_{name}"] = value
        st.session_state["quote_client_id"] = metadata.get("client_id")


def _calculate_design_items(design_items, materials, extras_total, order,
                            financial, margin_tiers):
    line_inputs = []
    material_details = []
    for item in design_items:
        details, material_total = calculate_design_materials(
            materials, item.get("materiales", []), item["cantidad"]
        )
        material_details.append(details)
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
    combined_details = (
        pd.concat(material_details, ignore_index=True)
        if material_details else pd.DataFrame()
    )
    return line_inputs, combined_details, sum(
        item["materiales_total"] for item in line_inputs
    )


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
    st.button(
        "Nueva cotización",
        on_click=_start_new_quote,
        key="start_new_quote",
    )
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
    financial = calculate_financial_config()
    order = render_order_config()
    materials = get_material_config()
    design_items = render_designs(materials)
    render_direct_cost_config()
    extras, extras_total = get_direct_cost_config()
    margin_tiers = render_margin_config()
    calculated_items, material_detail, materials_total = _calculate_design_items(
        design_items, materials, extras_total, order, financial, margin_tiers
    )
    designs_complete = bool(design_items) and all(
        item["nombre"].strip()
        and item["subcategory_id"] is not None
        and item["codigo"].startswith(
            f"{item['category_id']}-{item['subcategory_id']:04d}-"
        )
        and item["ancho_cm"] > 0
        and item["alto_cm"] > 0
        for item in design_items
    )

    st.header("Resultado por diseño")
    display = pd.DataFrame([
        {
            "Código": item["codigo"],
            "Diseño": item["nombre"] or "Sin nombre",
            "Ancho (cm)": item["ancho_cm"],
            "Alto (cm)": item["alto_cm"],
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
    if not financial["goal_entered"]:
        st.warning(
            "Falta el objetivo de ganancia mensual. Captúralo en "
            "Configuración para completar esta cotización."
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
    missing_requirements = []
    if not order["client_name"].strip():
        missing_requirements.append("Agregar o seleccionar un cliente.")
    if not design_items:
        missing_requirements.append("Agregar al menos un diseño.")
    elif not designs_complete:
        for index, item in enumerate(design_items, start=1):
            if not item["nombre"].strip():
                missing_requirements.append(
                    f"Escribir el nombre del diseño {index}."
                )
            if item["subcategory_id"] is None:
                missing_requirements.append(
                    f"Seleccionar la subcategoría del diseño {index}."
                )
            if item["ancho_cm"] <= 0 or item["alto_cm"] <= 0:
                missing_requirements.append(
                    f"Capturar ancho y alto mayores a cero (cm) para el diseño {index}."
                )
    if updating and not confirmation:
        missing_requirements.append(
            "Confirmar la actualización de la cotización existente."
        )
    if st.button(
        "Confirmar actualización" if updating else "Guardar cotización",
        use_container_width=True,
        disabled=bool(missing_requirements),
        key="save_quote",
    ):
        saved_quote_id = save_quote(
            folio,
            order["client_name"].strip(),
            order["client_phone"].strip(),
            order["client_email"].strip(),
            order["quote_status"],
            order["delivery_date"],
            snapshot,
            client_id=order["client_id"],
        )
        saved_quote = get_quote(saved_quote_id)
        folio = saved_quote["folio"]
        message = (
            f"Cotización actualizada con folio {folio}."
            if updating
            else f"Cotización guardada con folio {folio}."
        )
        st.session_state["pending_quote_load"] = json.loads(
            saved_quote["datos_json"]
        )
        st.session_state["pending_quote_folio"] = folio
        st.session_state["quote_saved_message"] = message
        if updating:
            st.session_state["quote_confirmation_key_to_reset"] = (
                f"confirm_update_quote_{folio}"
            )
        st.rerun()
    if missing_requirements:
        st.caption("Para habilitar el guardado falta:")
        for requirement in missing_requirements:
            st.markdown(f"- {requirement}")
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
