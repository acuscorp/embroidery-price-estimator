import streamlit as st

from services.quote_calculations import calculate_financials
from views.configuration.state import ensure_configuration_state


def ensure_financial_state():
    ensure_configuration_state()


def calculate_financial_config():
    ensure_financial_state()
    monthly_costs = st.session_state.monthly_costs
    monthly_goal_input = st.session_state.monthly_goal
    idle_pct = st.session_state.idle_pct
    work_hours = st.session_state.work_hours
    work_days = st.session_state.work_days
    operator_monthly_pay = st.session_state.operator_monthly_pay
    financial = calculate_financials(
        monthly_costs, monthly_goal_input, idle_pct, work_hours, work_days,
        operator_monthly_pay,
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


def render_financial_config():
    st.header("Gastos indirectos y capacidad")
    st.write(
        "Configura los gastos mensuales y la capacidad del taller. Estos valores "
        "se guardan en cada cotización."
    )
    ensure_financial_state()
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

    financial = calculate_financial_config()
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

    return financial
