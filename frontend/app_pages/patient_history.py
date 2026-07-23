import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from frontend.api.client import get_api_client
from frontend.ui.components import data_table, empty_state, page_header, section_title


def page_patient_history():
    page_header(
        "Records",
        "Patient history",
        "Retrieve previous MRI assessments and observe risk movement over time.",
        badge="Longitudinal view",
    )

    api = get_api_client()
    search, action = st.columns([3, 1], vertical_alignment="bottom")
    patient_id = search.text_input(
        "Patient ID",
        value=st.session_state.get("active_patient_id", ""),
        placeholder="Enter patient ID",
    )
    load_history = action.button(
        "Load history", type="primary", use_container_width=True
    )
    if not load_history:
        empty_state(
            "Enter a patient ID",
            "Load history to review prior assessments for a registered patient.",
            icon="◷",
        )
        return
    if not patient_id.strip():
        st.error("Patient ID is required.")
        return

    with st.spinner("Loading patient record..."):
        try:
            history = api.get_patient_history(patient_id.strip()).get("history", [])
        except Exception as error:
            st.error(f"History could not be loaded: {error}")
            return
    if not history:
        empty_state(
            "No assessments found",
            "No previous assessments were found for this patient.",
            icon="∅",
        )
        return

    dataframe = pd.DataFrame(history)
    section_title("Assessment timeline", "Stored predictions for this patient.")
    if "risk_score" in dataframe.columns and len(dataframe) > 1:
        dark = st.session_state.get("ui_theme") == "dark"
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                y=dataframe["risk_score"],
                mode="lines+markers",
                line=dict(color="#0d9488", width=3, shape="spline"),
                marker=dict(size=9, color="#4f46e5"),
                fill="tozeroy",
                fillcolor="rgba(13,148,136,0.1)",
                name="Risk",
            )
        )
        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#eef3fb" if dark else "#0b1f36"),
            yaxis_title="Risk / 100",
            xaxis_title="Assessment #",
        )
        st.plotly_chart(fig, use_container_width=True)

    display_cols = [
        c
        for c in dataframe.columns
        if c not in {"gradcam_image_base64", "pdf_base64"}
    ]
    data_table(dataframe, columns=display_cols)
