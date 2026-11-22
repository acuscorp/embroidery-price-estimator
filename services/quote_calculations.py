import math

import pandas as pd

from models.designs import DesignPriceResult


def calculate_financials(monthly_costs, monthly_goal_input, idle_pct,
                         work_hours, work_days, operator_monthly_pay):
    monthly_pool = 0.0
    if not monthly_costs.empty:
        monthly_pool = float(
            (
                pd.to_numeric(monthly_costs["Costo mensual ($)"], errors="coerce")
                .fillna(0)
                .clip(lower=0)
                * monthly_costs["Activo"].fillna(False).astype(bool)
            ).sum()
        )
    goal_entered = monthly_goal_input is not None
    monthly_goal = float(monthly_goal_input) if goal_entered else 0.0
    productive_minutes = work_hours * 60 * work_days * (1 - idle_pct / 100)
    monthly_labor_pool = float(operator_monthly_pay)
    combined_productive_minutes = productive_minutes * 2
    monthly_recovery = monthly_pool + monthly_labor_pool + monthly_goal
    allocation_rate = (
        monthly_recovery / combined_productive_minutes
        if combined_productive_minutes > 0 else 0.0
    )
    return {
        "monthly_pool": monthly_pool,
        "goal_entered": goal_entered,
        "monthly_goal": monthly_goal,
        "monthly_labor_pool": monthly_labor_pool,
        "combined_productive_minutes": combined_productive_minutes,
        "monthly_recovery": monthly_recovery,
        "allocation_rate": allocation_rate,
    }


def calculate_order_times(quantity, heads, embroidery_minutes_per_run,
                          setup_minutes, extra_operator_minutes):
    runs = math.ceil(quantity / heads)
    machine_minutes = runs * embroidery_minutes_per_run
    operator_minutes = machine_minutes + setup_minutes + extra_operator_minutes
    return {
        "runs": runs,
        "machine_minutes": machine_minutes,
        "operator_minutes": operator_minutes,
        "combined_order_minutes": machine_minutes + operator_minutes,
    }


def calculate_material_costs(materials, quantity):
    rows = []
    for _, row in materials.reset_index(drop=True).iterrows():
        name = str(row.get("Material", "")).strip()
        if not name:
            continue
        active = bool(row.get("Activo", True))
        price = max(0.0, float(row.get("Precio presentación ($)", 0) or 0))
        content = max(0.0, float(row.get("Contenido presentación", 0) or 0))
        consumption = max(0.0, float(row.get("Consumo por pieza", 0) or 0))
        unit_cost = price / content if content > 0 else 0.0
        total_consumption = consumption * quantity
        rows.append({
            "Material": name,
            "Activo": active,
            "Contenido presentación": content,
            "Consumo/pieza": consumption,
            "Consumo total": total_consumption,
            "Unidad": str(row.get("Unidad", "unidad")),
            "Costo por unidad ($)": unit_cost,
            "Costo total ($)": total_consumption * unit_cost if active else 0.0,
        })
    detail = pd.DataFrame(rows, columns=[
        "Material", "Activo", "Contenido presentación", "Consumo/pieza",
        "Consumo total", "Unidad", "Costo por unidad ($)", "Costo total ($)",
    ])
    total = float(detail["Costo total ($)"].sum()) if not detail.empty else 0.0
    return detail, total


def calculate_design_materials(material_catalog, design_materials, quantity):
    consumption = pd.DataFrame(
        design_materials,
        columns=["Material", "Consumo por pieza"],
    )
    priced_materials = material_catalog.drop(
        columns=["Consumo por pieza"], errors="ignore"
    ).merge(consumption, on="Material", how="inner")
    return calculate_material_costs(priced_materials, quantity)


def calculate_direct_costs(extras):
    if extras.empty:
        return 0.0
    return float(
        (
            pd.to_numeric(extras["Importe ($)"], errors="coerce")
            .fillna(0)
            .clip(lower=0)
            * extras["Activo"].fillna(False).astype(bool)
        ).sum()
    )


def calculate_order_costs(order_minutes, allocation_rate, material_total,
                          extras_total, quantity):
    allocation_cost = order_minutes * allocation_rate
    total = allocation_cost + material_total + extras_total
    unit = total / quantity
    summary = pd.DataFrame([
        ["Capacidad productiva combinada (máquina + operador)", allocation_cost, allocation_cost / quantity],
        ["Materiales directos", material_total, material_total / quantity],
        ["Otros costos directos", extras_total, extras_total / quantity],
        ["COSTO TOTAL DEL PEDIDO", total, unit],
    ], columns=["Concepto", "Importe total ($)", "Costo por pieza ($)"])
    return {
        "allocation_cost": allocation_cost,
        "total": total,
        "unit": unit,
        "summary": summary,
    }


def find_applicable_margin(margin_tiers, quantity):
    if margin_tiers.empty:
        return None
    matching = margin_tiers[
        (pd.to_numeric(margin_tiers["Desde piezas"], errors="coerce") <= quantity)
        & (pd.to_numeric(margin_tiers["Hasta piezas"], errors="coerce") >= quantity)
    ]
    return float(matching.iloc[0]["Margen (%)"]) if not matching.empty else None


def calculate_sale_price(cost_total, quantity, margin_pct):
    price_total = cost_total / (1 - margin_pct / 100)
    return price_total, price_total / quantity


def calculate_design_line(
    quantity: int,
    heads: int,
    embroidery_minutes_per_run: float,
    setup_minutes: float,
    extra_operator_minutes: float,
    allocation_rate: float,
    material_total: float,
    additional_cost: float,
    margin_pct: float,
) -> DesignPriceResult:
    times = calculate_order_times(
        quantity, heads, embroidery_minutes_per_run,
        setup_minutes, extra_operator_minutes,
    )
    allocation_cost = times["combined_order_minutes"] * allocation_rate
    cost_total = allocation_cost + material_total + additional_cost
    price_total, price_unit = calculate_sale_price(
        cost_total, quantity, margin_pct
    )
    return {
        **times,
        "allocation_cost": allocation_cost,
        "cost_total": cost_total,
        "cost_unit": cost_total / quantity,
        "price_total": price_total,
        "price_unit": price_unit,
    }


def validate_quote(machine_heads_note, heads, material_detail,
                   combined_productive_minutes, margin_tiers):
    issues = []
    if not machine_heads_note and heads > 1:
        issues.append(
            "Confirmar cómo trabajan los cabezales: el cálculo de corridas "
            "presupone que producen simultáneamente."
        )
    if not material_detail.empty:
        invalid = (
            material_detail["Activo"].fillna(False).astype(bool)
            & (
                pd.to_numeric(
                    material_detail["Contenido presentación"], errors="coerce"
                ).fillna(0) <= 0
            )
        )
        if invalid.any():
            issues.append(
                "Hay materiales activos con contenido de presentación igual a "
                "cero; su costo unitario no puede calcularse."
            )
    if combined_productive_minutes <= 0:
        issues.append("La capacidad productiva mensual debe ser mayor que cero.")
    if not margin_tiers.empty and (
        margin_tiers["Desde piezas"].isna().any()
        or margin_tiers["Hasta piezas"].isna().any()
        or (
            pd.to_numeric(margin_tiers["Desde piezas"], errors="coerce")
            > pd.to_numeric(margin_tiers["Hasta piezas"], errors="coerce")
        ).any()
    ):
        issues.append(
            "Revisa los límites de los tramos de margen: deben estar completos "
            "y el valor inicial no puede superar el final."
        )
    return issues
