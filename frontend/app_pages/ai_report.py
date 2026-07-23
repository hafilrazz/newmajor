import base64

import streamlit as st

from frontend.api.client import get_api_client
from frontend.ui.components import (
    empty_state,
    page_header,
    result_strip,
    section_title,
    workflow_stepper,
)


def page_ai_report():
    page_header(
        "Documentation",
        "AI-assisted report",
        "Turn the latest imaging result and clinician observations into a shareable patient report.",
        badge="Workflow step 5",
    )
    workflow_stepper(5)

    api = get_api_client()
    prediction = st.session_state.get("last_prediction")
    if not prediction:
        empty_state(
            "No prediction available",
            "Complete an MRI prediction first to create a report.",
            icon="DOC",
        )
        return

    stage = prediction.get("predicted_stage") or "Unavailable"
    confidence = prediction.get("confidence_score")
    risk = prediction.get("risk_score")
    result_strip(
        [
            ("Predicted stage", stage),
            (
                "Confidence",
                f"{float(confidence) * 100:.1f}%" if confidence is not None else "--",
            ),
            ("Risk score", f"{risk}/100" if risk is not None else "--"),
        ]
    )

    section_title(
        "Report input", "Confirm patient identity and optional clinician notes."
    )
    patient_id = st.text_input(
        "Patient ID",
        value=st.session_state.get("active_patient_id", ""),
        help="Used to save this report to the patient record.",
    )
    assessment = st.session_state.get("clinician_assessment", {}) or {}
    clinician_notes = st.text_area(
        "Clinician notes (optional)",
        value=assessment.get("additional_findings", "") or "",
        placeholder="Summarize findings or recommended follow-up.",
        height=120,
    )

    if st.button("Generate report", type="primary", use_container_width=True):
        if not patient_id.strip():
            st.error("Patient ID is required.")
            return
        with st.spinner("Preparing clinical report and PDF..."):
            try:
                result = api.generate_ai_report(
                    patient_id=patient_id.strip(),
                    prediction=prediction,
                    clinician_notes=clinician_notes,
                )
            except Exception as error:
                st.error(f"Report generation failed: {error}")
                return
        st.session_state["last_report_id"] = result.get("report_id", "")
        st.session_state["last_report_pdf_base64"] = result.get("pdf_base64", "")
        st.session_state["last_report_text"] = result.get("report_text", "")
        st.success("Report prepared successfully.")

    report_text = st.session_state.get("last_report_text", "")
    pdf_data = st.session_state.get("last_report_pdf_base64", "")
    report_id = st.session_state.get("last_report_id", "")
    if not report_text and not pdf_data:
        return

    st.divider()
    section_title("Report preview", "Review text and deliver the PDF.")
    if report_text:
        st.text_area("Generated report", value=report_text, height=250, disabled=True)

    if pdf_data:
        pdf_bytes = base64.b64decode(pdf_data)
        download, delivery = st.columns([1, 1.5], gap="large")
        with download:
            st.download_button(
                label="Download PDF report",
                data=pdf_bytes,
                file_name=f"alzheimer_report_{report_id or 'preview'}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
        with delivery:
            recipient_email = st.text_input(
                "Send a copy by email",
                value=st.session_state.get("active_patient_email", ""),
                placeholder="patient@example.com",
            )
            if st.button("Email report", use_container_width=True):
                _email_report(api, report_id, recipient_email)


def _email_report(api, report_id, recipient_email):
    if not recipient_email.strip():
        st.error("Recipient email is required.")
        return
    if not report_id:
        st.error("Generate a report before sending email.")
        return

    with st.spinner("Sending report..."):
        try:
            result = api.email_report(
                report_id=report_id,
                recipient_email=recipient_email.strip(),
            )
        except Exception as error:
            st.error(f"Email could not be sent: {error}")
            return

    if result.get("status") == "email_sent":
        st.success("Report emailed successfully.")
        if result.get("test_inbox_url"):
            st.info(f"Test inbox: {result['test_inbox_url']}")
        return

    st.error(f"Email could not be sent: {result.get('error') or 'unknown error'}")
    if result.get("hint"):
        st.info(result["hint"])
