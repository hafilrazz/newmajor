import base64
import os

import streamlit as st

from frontend.ui.components import clinical_disclaimer, feature_cards

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
_WALLPAPER_PATH = os.path.join(_ASSETS_DIR, "home_brain_wallpaper.jpg")


def _brain_wallpaper_data_uri() -> str:
    if not os.path.isfile(_WALLPAPER_PATH):
        return ""
    with open(_WALLPAPER_PATH, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def page_home():
    wallpaper_uri = _brain_wallpaper_data_uri()
    bg_layers = (
        'var(--hero-overlay),'
        + (f'url("{wallpaper_uri}")' if wallpaper_uri else "linear-gradient(135deg,#0b1f36,#0f766e)")
    )

    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] > .main .block-container {{
            max-width: 1240px;
            padding-top: 1.2rem;
        }}
        .hero {{
            background-image: {bg_layers};
            background-size: cover;
            background-position: center;
        }}
        </style>
        <section class="hero">
          <div class="hero-content">
            <div class="hero-kicker">Clinical MRI decision support</div>
            <h1>Precision insight for cognitive care.</h1>
            <p>
              NeuroLens unifies Alzheimer&apos;s stage prediction, Grad-CAM explainability,
              and clinician-ready reporting in one secure, modern workspace.
            </p>
            <div class="hero-meta">
              <span class="hero-chip">MRI staging</span>
              <span class="hero-chip">Explainable AI</span>
              <span class="hero-chip">PDF reporting</span>
              <span class="hero-chip">Longitudinal history</span>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    primary, secondary, tertiary, _ = st.columns([1.15, 1.15, 1.15, 2.5], gap="small")
    if primary.button("Enter workspace", type="primary", use_container_width=True):
        if st.session_state.get("authenticated"):
            st.session_state["active_page"] = "Dashboard"
        else:
            st.session_state["active_page"] = "Login"
        st.rerun()
    if secondary.button("View dashboard", use_container_width=True):
        st.session_state["active_page"] = "Dashboard"
        st.rerun()
    if tertiary.button("Create account", use_container_width=True):
        st.session_state["active_page"] = "Registration"
        st.rerun()

    st.markdown(
        '<div class="home-heading">A connected clinical pathway</div>'
        '<p class="home-subheading">'
        "From imaging intake through structured documentation — designed for focused review."
        "</p>",
        unsafe_allow_html=True,
    )

    feature_cards(
        [
            (
                "01",
                "MRI analysis",
                "Upload a brain MRI slice and review predicted stage, confidence, and risk indicators.",
            ),
            (
                "02",
                "Visual evidence",
                "Inspect Grad-CAM attention overlays to understand regions informing the model output.",
            ),
            (
                "03",
                "Clinical reporting",
                "Combine assessment notes with AI findings into a downloadable PDF report.",
            ),
        ]
    )

    st.markdown(
        """
        <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.85rem;margin:1.25rem 0 0.5rem;">
          <div class="glass-panel">
            <div class="metric-label">Model classes</div>
            <div class="metric-value" style="font-size:1.35rem;">4 stages</div>
            <div class="metric-hint">No → Very mild → Mild → Moderate</div>
          </div>
          <div class="glass-panel">
            <div class="metric-label">Explainability</div>
            <div class="metric-value" style="font-size:1.35rem;">Grad-CAM</div>
            <div class="metric-hint">Attention overlays + faithfulness checks</div>
          </div>
          <div class="glass-panel">
            <div class="metric-label">Delivery</div>
            <div class="metric-value" style="font-size:1.35rem;">PDF + Email</div>
            <div class="metric-hint">Clinician notes included in reports</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    clinical_disclaimer(
        "This platform is a clinical decision-support prototype for education and research. "
        "It does not replace professional medical diagnosis or specialist review."
    )
