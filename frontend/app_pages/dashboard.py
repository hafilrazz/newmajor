import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from frontend.api.client import get_api_client
from frontend.ui.components import data_table, empty_state, metric_cards, page_header, section_title


def _chart_layout(fig, *, height: int = 320):
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
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,0.12)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,0.12)", zeroline=False)
    return fig


def page_dashboard():
    page_header(
        "Overview",
        "Clinical dashboard",
        "Monitor prediction volume and risk movement across recent MRI assessments.",
        badge="Live insights",
    )

    api = get_api_client()
    try:
        dist = api.stage_distribution().get("distribution", [])
        trend = api.risk_trend().get("trend", [])
    except Exception:
        st.warning(
            "Analytics are unavailable right now. Start the backend service to view live insights."
        )
        _empty_dashboard()
        return

    prediction_count = sum(int(row.get("count", 0)) for row in dist)
    stages_recorded = len(dist)
    latest_risk = trend[0].get("risk_score", 0) if trend else 0
    has_pred = bool(st.session_state.get("last_prediction"))

    metric_cards(
        [
            ("Σ", "Assessments", str(prediction_count), "Stored MRI predictions"),
            ("◎", "Stages observed", str(stages_recorded), "Distinct impairment classes"),
            ("▲", "Latest risk", f"{latest_risk or 0}/100", "Most recent risk score"),
            (
                "●",
                "Session status",
                "Ready" if has_pred else "Idle",
                "Last prediction in this session",
            ),
        ]
    )

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

    left, right = st.columns(2, gap="large")
    with left:
        section_title(
            "Stage distribution", "Count of stored predictions by impairment class."
        )
        if not dist:
            empty_state(
                "No assessments yet",
                "Stage distribution will appear after the first MRI prediction is saved.",
                icon="◉",
            )
        else:
            dataframe = pd.DataFrame(dist)
            fig = px.bar(
                dataframe,
                x="stage",
                y="count",
                color="count",
                color_continuous_scale=["#99f6e4", "#0d9488", "#134e4a"],
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(xaxis_title="", yaxis_title="Count")
            st.plotly_chart(_chart_layout(fig), use_container_width=True)
            data_table(dataframe)

    with right:
        section_title(
            "Risk trend", "Recent risk scores ordered by assessment time."
        )
        if not trend:
            empty_state(
                "No risk history",
                "Risk history will appear after the first assessment is completed.",
                icon="↗",
            )
        else:
            trend_df = pd.DataFrame(trend)
            if "created_at" in trend_df.columns:
                trend_df = trend_df.sort_values(by="created_at")
            if "risk_score" in trend_df.columns:
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        y=trend_df["risk_score"],
                        mode="lines+markers",
                        line=dict(color="#4f46e5", width=3, shape="spline"),
                        marker=dict(size=8, color="#0d9488", line=dict(width=2, color="#fff")),
                        fill="tozeroy",
                        fillcolor="rgba(79,70,229,0.08)",
                        name="Risk",
                    )
                )
                fig.update_layout(yaxis_title="Risk / 100", xaxis_title="Assessment #")
                st.plotly_chart(_chart_layout(fig), use_container_width=True)
            data_table(
                trend_df,
                columns=[
                    col
                    for col in ["predicted_stage", "risk_score", "created_at"]
                    if col in trend_df.columns
                ],
            )

    st.caption(
        "Dashboard metrics reflect stored prediction history and update as assessments are completed."
    )


def _empty_dashboard():
    metric_cards(
        [
            ("Σ", "Assessments", "—", "Backend offline"),
            ("◎", "Stages observed", "—", "Backend offline"),
            ("▲", "Latest risk", "—", "Backend offline"),
            ("●", "Session status", "Offline", "Connect API to continue"),
        ]
    )
    empty_state(
        "Waiting for analytics service",
        "Once the backend is connected, clinical trends will be displayed here.",
        icon="⚡",
    )
