import streamlit as st

from frontend.ui.components import info_panel, page_header, workflow_stepper


def page_clinical_assessment_form():
    page_header(
        "Clinical context",
        "Clinical assessment",
        "Record clinician observations that will accompany the imaging result in the final report.",
        badge="Workflow step 4",
    )
    workflow_stepper(4)

    left, right = st.columns([1.5, 1], gap="large")
    with left:
        patient_id = st.text_input(
            "Patient ID",
            value=st.session_state.get("active_patient_id", ""),
            help="Associates this assessment with the active patient workflow.",
        )
        with st.form("clinical_assessment_form", clear_on_submit=False):
            c1, c2 = st.columns(2, gap="large")
            with c1:
                symptoms = st.text_area(
                    "Reported symptoms (optional)",
                    placeholder="Memory concerns, cognitive changes or family observations.",
                    height=130,
                )
                cognitive_decline = st.slider("Cognitive decline", 0, 10, 5)
            with c2:
                additional_findings = st.text_area(
                    "Additional findings (optional)",
                    placeholder="Clinical interpretation and follow-up notes.",
                    height=130,
                )
                functional_impairment = st.slider("Functional impairment", 0, 10, 5)
            submitted = st.form_submit_button(
                "Save assessment", type="primary", use_container_width=True
            )
    with right:
        info_panel(
            "How this is used",
            "Saved notes feed into the AI-assisted report so imaging output and clinician "
            "context stay linked in one document.",
            pill="Documentation",
        )
        existing = st.session_state.get("clinician_assessment") or {}
        if existing:
            st.markdown(
                f"""
                <div class="card" style="margin-top:1rem;">
                  <span class="status-pill"><span class="status-dot"></span>Saved in session</span>
                  <p style="margin:1rem 0 0;color:var(--muted);line-height:1.65;font-size:.9rem;">
                    Cognitive decline: <strong>{existing.get('cognitive_decline', '—')}</strong><br/>
                    Functional impairment: <strong>{existing.get('functional_impairment', '—')}</strong>
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if submitted:
        st.session_state["clinician_assessment"] = {
            "patient_id": patient_id.strip(),
            "symptoms": symptoms,
            "additional_findings": additional_findings,
            "cognitive_decline": cognitive_decline,
            "functional_impairment": functional_impairment,
        }
        st.success("Clinical assessment saved and ready for report generation.")
