import base64

import streamlit as st

from frontend.ui.components import (
    clinical_disclaimer,
    empty_state,
    explanation_block,
    page_header,
    result_strip,
    section_title,
    workflow_stepper,
)


def page_gradcam_visualization():
    page_header(
        "Explainability",
        "Grad-CAM++ visualization",
        "Review the refined attention overlay for the latest MRI prediction with side-by-side comparison.",
        badge="Model transparency",
    )
    workflow_stepper(3)

    gradcam_data = st.session_state.get("last_gradcam", "") or ""
    if not gradcam_data:
        predicted = st.session_state.get("last_prediction", {}) or {}
        meta = predicted.get("meta", {}) if isinstance(predicted, dict) else {}
        empty_state(
            "No explanation available yet",
            meta.get("gradcam_error")
            or "Run an MRI prediction first to view an explanation overlay.",
            icon="◈",
        )
        return

    predicted = st.session_state.get("last_prediction", {}) or {}
    confidence = predicted.get("confidence_score")
    risk = predicted.get("risk_score")
    result_strip(
        [
            ("Predicted stage", predicted.get("predicted_stage") or "Unavailable"),
            (
                "Confidence",
                f"{float(confidence) * 100:.1f}%" if confidence is not None else "--",
            ),
            ("Risk score", f"{risk}/100" if risk is not None else "--"),
        ]
    )

    section_title(
        "Original vs. Grad-CAM++ overlay",
        "Warmer regions indicate stronger contribution to the predicted class. "
        "Grad-CAM++ sharpens multi-region localization over classic Grad-CAM.",
    )

    original = st.session_state.get("last_mri_image", "") or ""
    if original:
        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            st.image(
                base64.b64decode(original),
                caption="Source MRI",
                use_container_width=True,
            )
        with col_b:
            st.image(
                base64.b64decode(gradcam_data),
                caption="Grad-CAM++ overlay",
                use_container_width=True,
            )
    else:
        st.image(
            base64.b64decode(gradcam_data),
            caption="Grad-CAM++ overlay",
            use_container_width=True,
        )

    st.markdown(
        """
        <div class="nl-legend">
          <div class="nl-legend-bar"></div>
          <div class="nl-legend-scale">
            <span>Low attention</span>
            <span>High attention</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    explanation_block(predicted.get("explanation"))
    clinical_disclaimer(
        "Grad-CAM++ visualizations support model review and are not a definitive map of pathology."
    )
