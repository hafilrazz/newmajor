import base64
from typing import Any, Dict, List, Optional

import streamlit as st

from frontend.api.client import get_api_client
from frontend.ui.components import (
    explanation_block,
    page_header,
    probability_bars,
    result_strip,
    section_title,
    workflow_stepper,
)


def _init_mri_fields() -> None:
    if "mri_patient_id" not in st.session_state:
        st.session_state["mri_patient_id"] = st.session_state.get("active_patient_id", "")
    if "mri_patient_email" not in st.session_state:
        st.session_state["mri_patient_email"] = st.session_state.get(
            "active_patient_email", ""
        )

    active_id = st.session_state.get("active_patient_id", "") or ""
    active_email = st.session_state.get("active_patient_email", "") or ""
    if active_id and not (st.session_state.get("mri_patient_id") or "").strip():
        st.session_state["mri_patient_id"] = active_id
    if active_email and not (st.session_state.get("mri_patient_email") or "").strip():
        st.session_state["mri_patient_email"] = active_email


def page_mri_upload_prediction():
    page_header(
        "Assessment",
        "MRI upload & prediction",
        "Attach a scan to the active patient record and run AI-assisted staging with visual explainability.",
        badge="Workflow step 2",
    )
    workflow_stepper(2)
    _init_mri_fields()
    api = get_api_client()

    details, scan = st.columns([1, 1.05], gap="large")
    with details:
        section_title("Patient context", "Identify the record this assessment belongs to.")
        st.text_input(
            "Patient ID",
            key="mri_patient_id",
            placeholder="Paste the patient ID from registration",
            help="Created on the Patient Registration page.",
        )
        st.text_input(
            "Patient email",
            key="mri_patient_email",
            placeholder="patient@example.com",
        )
        clinical_notes = st.text_area(
            "Clinical notes (optional)",
            placeholder="Add observations that may assist later report generation.",
            height=122,
            key="mri_clinical_notes",
        )
        if st.session_state.get("active_patient_id"):
            st.caption(
                f"Active patient in session: `{st.session_state.get('active_patient_id')}`"
            )

    with scan:
        section_title("MRI image", "PNG or JPEG exported 2D brain MRI slice.")
        uploaded = st.file_uploader(
            "Upload scan",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=False,
            key="mri_uploader",
            help="Use a grayscale brain MRI slice export. Photos of people/objects are rejected.",
        )
        st.caption("Only exported 2D brain MRI slices are accepted for analysis.")

        file_bytes: Optional[bytes] = None
        file_name = ""
        if uploaded is not None:
            file_bytes = uploaded.getvalue()
            file_name = uploaded.name or "scan.png"
            st.image(file_bytes, caption=file_name, use_container_width=True)
            st.caption(f"Size: {len(file_bytes) / 1024:.1f} KB")

    run_prediction = st.button(
        "Run prediction",
        type="primary",
        use_container_width=True,
        key="mri_run_prediction",
    )

    if run_prediction:
        patient_id = (st.session_state.get("mri_patient_id") or "").strip()
        patient_email = (st.session_state.get("mri_patient_email") or "").strip()
        notes = (clinical_notes or "").strip()

        if not file_bytes:
            st.error("Please upload an MRI image before running prediction.")
        elif not patient_id:
            st.error(
                "Patient ID is required. Register a patient first, then paste the ID here."
            )
        elif not patient_email or "@" not in patient_email:
            st.error("A valid patient email is required.")
        else:
            with st.spinner("Analyzing MRI scan… this may take a few seconds on first run."):
                try:
                    result = api.predict_mri(
                        mri_file_bytes=file_bytes,
                        mri_filename=file_name,
                        patient_id=patient_id,
                        patient_email=patient_email,
                        clinical_notes=notes,
                    )
                except Exception as error:
                    st.error(f"Prediction failed: {error}")
                    st.info(
                        "Tip: use a grayscale brain MRI slice (PNG/JPEG). "
                        "If the model just started, try again once."
                    )
                else:
                    st.session_state["active_patient_id"] = patient_id
                    st.session_state["active_patient_email"] = patient_email
                    st.session_state["last_prediction"] = result
                    st.session_state["last_gradcam"] = (
                        result.get("gradcam_image_base64", "") or ""
                    )
                    st.session_state["last_mri_image"] = base64.b64encode(
                        file_bytes
                    ).decode("utf-8")
                    saved = (result.get("meta") or {}).get("history_saved")
                    if saved:
                        st.success(
                            "Analysis complete. Results were saved to the patient history."
                        )
                    else:
                        st.success(
                            "Analysis complete. Results are ready (history may not have been saved)."
                        )
                    st.rerun()

    result = st.session_state.get("last_prediction")
    if result:
        _render_result(result)
    else:
        st.markdown(
            """
            <div class="nl-empty" style="margin-top:1.25rem;">
              <div class="nl-empty-icon">MRI</div>
              <div class="nl-empty-title">No prediction yet</div>
              <div class="nl-empty-body">
                Register a patient, upload a brain MRI slice, then click <strong>Run prediction</strong>.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_result(result: Dict[str, Any]) -> None:
    predicted_stage = result.get("predicted_stage") or "Unavailable"
    confidence = result.get("confidence_score")
    risk = result.get("risk_score")
    confidence_text = (
        f"{float(confidence) * 100:.1f}%" if confidence is not None else "--"
    )
    risk_text = f"{risk}/100" if risk is not None else "--"

    st.divider()
    section_title("Latest analysis", "Model output for the most recent scan.")
    result_strip(
        [
            ("Predicted stage", predicted_stage),
            ("Confidence", confidence_text),
            ("Risk score", risk_text),
        ]
    )

    probs: List[float] = result.get("raw_probs") or []
    names: List[str] = result.get("class_names") or [
        "Mild Impairment",
        "Moderate Impairment",
        "No Impairment",
        "Very Mild Impairment",
    ]
    if probs and len(probs) == len(names):
        section_title(
            "Class probabilities", "Softmax scores across impairment stages."
        )
        probability_bars(names, probs)

    meta = result.get("meta") or {}
    meta_bits = []
    if result.get("prediction_id"):
        meta_bits.append(f"Prediction ID: `{result.get('prediction_id')}`")
    if result.get("patient_id"):
        meta_bits.append(f"Patient: `{result.get('patient_id')}`")
    if meta.get("history_saved") is False:
        meta_bits.append("History not saved to database")
    if meta_bits:
        st.caption(" · ".join(meta_bits))

    gradcam_data = result.get("gradcam_image_base64", "") or ""
    if gradcam_data:
        section_title("Explainability preview", "Grad-CAM++ attention overlay.")
        g1, g2 = st.columns([1.15, 1], gap="large")
        with g1:
            try:
                image_bytes = base64.b64decode(gradcam_data, validate=False)
                st.image(
                    image_bytes,
                    caption="Grad-CAM++ attention overlay",
                    use_container_width=True,
                )
            except Exception:
                st.info("The visual explanation could not be displayed for this scan.")
        with g2:
            st.markdown(
                """
                <div class="card">
                  <span class="status-pill"><span class="status-dot"></span>Next steps</span>
                  <p style="margin:1rem 0 0;color:var(--muted);line-height:1.65;font-size:.93rem;">
                    Open <strong>Grad-CAM Visualization</strong> for a larger view, add notes in
                    <strong>Clinical Assessment</strong>, then generate an <strong>AI Report</strong>.
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Open Grad-CAM", use_container_width=True, key="mri_goto_gradcam"):
                st.session_state["active_page"] = "Grad-CAM Visualization"
                st.rerun()
    else:
        detail = meta.get("gradcam_error") or (
            "A visual explanation is not available for this analysis."
        )
        st.info(detail)

    explanation_block(result.get("explanation"))
