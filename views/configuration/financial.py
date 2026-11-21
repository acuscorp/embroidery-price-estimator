import pandas as pd
import streamlit as st

from services.quote_calculations import calculate_financials


DEFAULT_MONTHLY_COSTS = [
    {"Concepto": "Renta", "Activo": True, "Costo mensual ($)": 3000.0},
    {"Concepto": "Electricidad", "Activo": True, "Costo mensual ($)": 500.0},
    {"Concepto": "Internet", "Activo": True, "Costo mensual ($)": 390.0},
    {"Concepto": "Agua para beber", "Activo": True, "Costo mensual ($)": 120.0},
    {"Concepto": "Limpieza del taller", "Activo": True, "Costo mensual ($)": 200.0},
    {"Concepto": "Lubricantes y consumibles de máquina", "Activo": True, "Costo mensual ($)": 200.0},
    {"Concepto": "Depreciación", "Activo": True, "Costo mensual ($)": 1500.0},
    {"Concepto": "Reserva de refacciones", "Activo": True, "Costo mensual ($)": 250.0},
]


def render_financial_config():
    st.header("1. Gastos indirectos y capacidad")
    st.write(
        "Los gastos indirectos del taller se combinan con el costo mensual del "
        "operador para calcular una tarifa por minuto-recurso. Los materiales y "
        "otros cargos directos del pedido se capturan por separado."
    )
    if "monthly_costs" not in st.session_state:
        st.session_state.monthly_costs = pd.DataFrame(DEFAULT_MONTHLY_COSTS)
    monthly_costs = st.data_editor(
        st.session_state.monthly_costs,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Concepto": st.column_config.TextColumn("Concepto", required=True),
            "Activo": st.column_config.CheckboxColumn("Activo"),
            "Costo mensual ($)": st.column_config.NumberColumn(
                "Costo mensual ($)", min_value=0.0, step=0.01, format="$%.2f"
            ),
        },
        key="monthly_cost_editor",
    )
    st.session_state.monthly_costs = monthly_costs

    cols = st.columns(3)
    with cols[0]:
        monthly_goal_input = st.number_input(
            "Objetivo de ganancia mensual ($)",
            min_value=0.0, value=None, step=0.01, format="%.2f",
            placeholder="Ingresa el objetivo para este pedido",
            key="monthly_goal",
        )
    with cols[1]:
        idle_pct = st.number_input(
            "Tiempo improductivo (%)", min_value=0.0, max_value=99.0,
            value=10.0, step=0.1, format="%.2f", key="idle_pct",
        )
    with cols[2]:
        st.metric("Modelo de costeo", "Máquina + operador")

    cols = st.columns(3)
    with cols[0]:
        work_hours = st.number_input(
            "Horas disponibles por día", min_value=0.1, value=8.0,
            step=0.1, format="%.2f", key="work_hours",
        )
    with cols[1]:
        work_days = st.number_input(
            "Días trabajados al mes", min_value=1, max_value=31,
            value=26, step=1, key="work_days",
        )
    with cols[2]:
        operator_monthly_pay = st.number_input(
            "Pago mensual del operador ($)", min_value=0.0, value=8000.0,
            step=0.01, format="%.2f", key="operator_monthly_pay",
        )

    financial = calculate_financials(
        monthly_costs, monthly_goal_input, idle_pct, work_hours, work_days,
        operator_monthly_pay,
    )
    if not financial["goal_entered"]:
        st.warning(
            "Ingresa el objetivo de ganancia mensual para completar esta "
            "cotización. Mientras esté vacío, el cálculo provisional usa $0.00."
        )
    with st.container(border=True):
        st.subheader("Resumen mensual")
        summary_cols = st.columns(2)
        summary_cols[0].metric(
            "Gastos indirectos mensuales", f"${financial['monthly_pool']:,.2f}"
        )
        summary_cols[1].metric(
            "Pago mensual del operador",
            f"${financial['monthly_labor_pool']:,.2f}",
        )
        summary_cols = st.columns(2)
        summary_cols[0].metric(
            "Objetivo de ganancia mensual",
            f"${financial['monthly_goal']:,.2f}",
        )
        summary_cols[1].metric(
            "Total mensual a recuperar",
            f"${financial['monthly_recovery']:,.2f}",
        )
        summary_cols = st.columns(2)
        summary_cols[0].metric(
            "Capacidad productiva combinada",
            f"{financial['combined_productive_minutes']:,.1f} min-recurso/mes",
        )
        summary_cols[1].metric(
            "Tarifa única", f"${financial['allocation_rate']:,.6f} / min-recurso"
        )

    financial.update({
        "monthly_costs": monthly_costs,
        "monthly_goal_input": monthly_goal_input,
        "idle_pct": idle_pct,
        "work_hours": work_hours,
        "work_days": work_days,
        "operator_monthly_pay": operator_monthly_pay,
    })
    return financial
