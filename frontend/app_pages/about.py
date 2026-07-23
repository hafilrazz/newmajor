import streamlit as st

from frontend.ui.components import clinical_disclaimer, feature_cards, page_header


def page_about():
    page_header(
        "About",
        "Responsible imaging support",
        "NeuroLens is an Alzheimer's MRI workflow platform designed to organize AI outputs for clinical review.",
        badge="Decision support",
    )

    feature_cards(
        [
            (
                "MRI",
                "MRI staging",
                "Processes uploaded scans to present a predicted disease stage and confidence score.",
            ),
            (
                "XAI",
                "Explainability",
                "Displays Grad-CAM attention overlays for transparent model review by clinicians.",
            ),
            (
                "DOC",
                "Reporting",
                "Packages imaging output and clinical notes into downloadable documentation.",
            ),
        ]
    )

    st.markdown(
        """
        <div class="card" style="margin-top:.75rem;">
          <span class="status-pill"><span class="status-dot"></span>Design principles</span>
          <p style="margin:1rem 0 0;color:var(--muted);line-height:1.75;font-size:.95rem;">
            NeuroLens prioritizes clarity, auditability, and a calm clinical interface.
            Predictions are presented with confidence, risk context, and visual explanations
            so teams can review model output alongside professional judgment.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.85rem;margin-top:1rem;">
          <div class="glass-panel">
            <div class="metric-label">Stack</div>
            <div style="font-weight:700;margin-top:.35rem;">Streamlit + Flask</div>
            <div class="metric-hint">PyTorch · MongoDB</div>
          </div>
          <div class="glass-panel">
            <div class="metric-label">Model</div>
            <div style="font-weight:700;margin-top:.35rem;">ResNet18 MRI</div>
            <div class="metric-hint">4-class stage prediction</div>
          </div>
          <div class="glass-panel">
            <div class="metric-label">Transparency</div>
            <div style="font-weight:700;margin-top:.35rem;">Grad-CAM + faithfulness</div>
            <div class="metric-hint">Region focus &amp; masking tests</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    clinical_disclaimer(
        "This prototype supports clinical review and research workflows. It is not a diagnostic device "
        "and must not be used as a standalone medical diagnosis."
    )
