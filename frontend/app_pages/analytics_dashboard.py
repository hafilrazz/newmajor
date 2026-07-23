import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from frontend.api.client import get_api_client
from frontend.ui.components import data_table, empty_state, page_header, section_title


def _base_layout(fig, height: int = 340):
    dark = st.session_state.get("ui_theme") == "dark"
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, sans-serif",
            color="#eef3fb" if dark else "#0b1f36",
            size=12,
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,0.12)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,0.12)", zeroline=False)
    return fig


def page_analytics_dashboard():
    page_header(
        "Analytics",
        "Population insights",
        "Explore recorded disease stage distribution and recent risk patterns across assessments.",
        badge="Population view",
    )
    api = get_api_client()

    left, right = st.columns(2, gap="large")
    with left:
        section_title(
            "Disease stage distribution", "Aggregate counts by predicted stage."
        )
        try:
            distribution = api.stage_distribution().get("distribution", [])
            if distribution:
                dataframe = pd.DataFrame(distribution)
                fig = px.pie(
                    dataframe,
                    values="count",
                    names="stage",
                    hole=0.55,
                    color_discrete_sequence=[
                        "#0d9488",
                        "#4f46e5",
                        "#06b6d4",
                        "#f59e0b",
                        "#e11d48",
                    ],
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(_base_layout(fig, 360), use_container_width=True)
                data_table(dataframe)
            else:
                empty_state("No stage data", "No stage data available yet.", icon="◎")
        except Exception:
            st.warning("Stage distribution is currently unavailable.")

    with right:
        section_title("Risk trend", "Latest stored risk observations.")
        try:
            trend = api.risk_trend().get("trend", [])
            if trend:
                dataframe = pd.DataFrame(trend)
                if "risk_score" in dataframe.columns and len(dataframe) >= 1:
                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            y=dataframe["risk_score"],
                            mode="lines+markers",
                            line=dict(color="#4f46e5", width=3),
                            marker=dict(size=8, color="#0d9488"),
                            fill="tozeroy",
                            fillcolor="rgba(79,70,229,0.08)",
                            name="Risk",
                        )
                    )
                    fig.update_layout(yaxis_title="Risk / 100")
                    st.plotly_chart(_base_layout(fig), use_container_width=True)
                show = dataframe.head(20)
                if "gradcam_image_base64" in show.columns:
                    show = show.drop(columns=["gradcam_image_base64"])
                data_table(show)
            else:
                empty_state(
                    "No risk data", "No risk observations available yet.", icon="↗"
                )
        except Exception:
            st.warning("Risk trend is currently unavailable.")

    st.caption(
        "Insights update from stored prediction history as new assessments are completed."
    )
