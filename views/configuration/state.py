import pandas as pd
import streamlit as st

from repositories.configuration_repository import (
    get_configuration,
    save_configuration,
    with_default_configuration,
)


def ensure_configuration_state():
    if st.session_state.get("configuration_state_loaded"):
        return

    configuration = with_default_configuration(get_configuration())
    for name in ("monthly_costs", "materials"):
        st.session_state[name] = pd.DataFrame(configuration[name])
    for name in (
        "monthly_goal",
        "idle_pct",
        "work_hours",
        "work_days",
        "operator_monthly_pay",
        "heads",
        "machine_heads_note",
    ):
        st.session_state[name] = configuration[name]
    st.session_state["configuration_state_loaded"] = True


def reload_configuration_state():
    for key in ("monthly_cost_editor", "materials_editor"):
        st.session_state.pop(key, None)
    st.session_state["configuration_state_loaded"] = False
    ensure_configuration_state()


def persist_configuration_state():
    ensure_configuration_state()
    configuration = {
        "monthly_costs": st.session_state.monthly_costs.to_dict(orient="records"),
        "monthly_goal": st.session_state.monthly_goal,
        "idle_pct": st.session_state.idle_pct,
        "work_hours": st.session_state.work_hours,
        "work_days": st.session_state.work_days,
        "operator_monthly_pay": st.session_state.operator_monthly_pay,
        "materials": st.session_state.materials.to_dict(orient="records"),
        "heads": st.session_state.heads,
        "machine_heads_note": st.session_state.machine_heads_note,
    }
    save_configuration(configuration)
