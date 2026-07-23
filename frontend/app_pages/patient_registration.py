import streamlit as st

from frontend.api.client import get_api_client
from frontend.ui.components import info_panel, page_header, workflow_stepper


def page_patient_registration():
    page_header(
        "Patients",
        "Register patient",
        "Create a patient record before beginning MRI assessment or reporting.",
        badge="Workflow step 1",
    )
    workflow_stepper(1)
    api = get_api_client()

    form_column, context_column = st.columns([1.45, 1], gap="large")
    with form_column:
        with st.form("register_patient_form", clear_on_submit=False):
            st.markdown("##### Patient demographics")
            name = st.text_input("Full name", placeholder="Patient full name")
            c1, c2 = st.columns(2, gap="medium")
            with c1:
                age = st.number_input("Age", min_value=0, max_value=120, step=1)
            with c2:
                gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])
            email = st.text_input("Email address", placeholder="patient@example.com")
            submitted = st.form_submit_button(
                "Create patient record", type="primary", use_container_width=True
            )
    with context_column:
        info_panel(
            "What happens next?",
            "A patient ID is created and carried into MRI analysis, explainability "
            "review, and report delivery. Keep the ID available for later steps.",
            pill="Workflow guidance",
        )
        st.markdown(
            """
            <div class="card" style="margin-top:1rem;">
              <span class="status-pill"><span class="status-dot"></span>Checklist</span>
              <p style="margin:1rem 0 0;color:var(--muted);line-height:1.75;font-size:.92rem;">
                <strong style="color:var(--primary);">1.</strong> Register patient<br/>
                <strong>2.</strong> Upload MRI &amp; predict<br/>
                <strong>3.</strong> Review Grad-CAM<br/>
                <strong>4.</strong> Clinical assessment<br/>
                <strong>5.</strong> Generate clinical report
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not submitted:
        return
    if not name.strip():
        st.error("Full name is required.")
        return
    if (
        not email.strip()
        or "@" not in email.strip()
        or "." not in email.strip().split("@")[-1]
    ):
        st.error("Please enter a valid email address.")
        return

    try:
        result = api.register_patient(
            name=name.strip(), age=int(age), gender=gender.strip(), email=email.strip()
        )
    except Exception as error:
        st.error(f"Registration failed: {error}")
        return

    patient = result.get("patient", {})
    patient_id = patient.get("patient_id", "")
    if patient_id:
        st.session_state["active_patient_id"] = patient_id
        st.session_state["active_patient_email"] = patient.get("email", email.strip())
        st.success(f"Patient created. Active patient ID: `{patient_id}`")
        st.info("Continue to **MRI prediction** in the sidebar to analyze a scan.")
    else:
        st.success("Patient record created.")
