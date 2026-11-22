import pandas as pd
import streamlit as st


DEFAULT_MARGINS = [
    {"Desde piezas": 1, "Hasta piezas": 29, "Margen (%)": 50.0},
    {"Desde piezas": 30, "Hasta piezas": 99, "Margen (%)": 45.0},
    {"Desde piezas": 100, "Hasta piezas": 499, "Margen (%)": 40.0},
    {"Desde piezas": 500, "Hasta piezas": 999, "Margen (%)": 35.0},
    {"Desde piezas": 1000, "Hasta piezas": 1000000000, "Margen (%)": 30.0},
]


def render_margin_config():
    st.header("Margen y resultado")
    st.caption("El tramo se aplica por separado a la cantidad de cada diseño.")
    if (
        "margin_tiers" not in st.session_state
        or st.session_state.margin_tiers.empty
    ):
        st.session_state.margin_tiers = pd.DataFrame(DEFAULT_MARGINS)

    edited = st.data_editor(
        st.session_state.margin_tiers,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Desde piezas": st.column_config.NumberColumn(min_value=1, step=1),
            "Hasta piezas": st.column_config.NumberColumn(min_value=1, step=1),
            "Margen (%)": st.column_config.NumberColumn(
                min_value=0.0, max_value=99.0, step=0.1, format="%.2f"
            ),
        },
        key="margin_editor_with_prices",
    )
    st.session_state.margin_tiers = edited
    return st.session_state.margin_tiers
