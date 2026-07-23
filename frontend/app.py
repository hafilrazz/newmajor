"""NeuroLens Clinical Intelligence — Streamlit application entrypoint."""

from __future__ import annotations

import os
import sys

import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from frontend.ui.theme import apply_theme
from frontend.app_pages.login import page_login
from frontend.app_pages.user_registration import page_user_registration
from frontend.app_pages.home import page_home
from frontend.app_pages.dashboard import page_dashboard
from frontend.app_pages.patient_registration import page_patient_registration
from frontend.app_pages.mri_upload_prediction import page_mri_upload_prediction
from frontend.app_pages.gradcam_visualization import page_gradcam_visualization
from frontend.app_pages.clinical_assessment_form import page_clinical_assessment_form
from frontend.app_pages.ai_report import page_ai_report
from frontend.app_pages.patient_history import page_patient_history
from frontend.app_pages.analytics_dashboard import page_analytics_dashboard
from frontend.app_pages.settings import page_settings
from frontend.app_pages.contact import page_contact
from frontend.app_pages.about import page_about

st.set_page_config(
    page_title="NeuroLens | Clinical MRI Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

PAGES = {
    "Home": page_home,
    "Registration": page_user_registration,
    "Login": page_login,
    "Dashboard": page_dashboard,
    "Contact": page_contact,
    "About": page_about,
    "Patient Registration": page_patient_registration,
    "MRI Upload & Prediction": page_mri_upload_prediction,
    "Grad-CAM Visualization": page_gradcam_visualization,
    "Clinical Assessment Form": page_clinical_assessment_form,
    "AI Report": page_ai_report,
    "Patient History": page_patient_history,
    "Analytics Dashboard": page_analytics_dashboard,
    "Settings": page_settings,
}

PUBLIC_PAGES = {"Home", "Dashboard", "Contact", "About"}
AUTH_PAGES = {"Login", "Registration"}
ADMIN_ONLY = {
    "Analytics Dashboard",
    "Patient History",
    "AI Report",
    "Patient Registration",
    "Clinical Assessment Form",
    "Grad-CAM Visualization",
    "MRI Upload & Prediction",
}
USER_NAV = {"Home", "Dashboard", "Contact", "About", "Settings"}

# (section, [(nav label, page key), ...])
NAV_GROUPS = [
    (
        "Overview",
        [
            ("⌂  Home", "Home"),
            ("◫  Dashboard", "Dashboard"),
        ],
    ),
    (
        "Clinical workflow",
        [
            ("①  Patient registration", "Patient Registration"),
            ("②  MRI prediction", "MRI Upload & Prediction"),
            ("③  Grad-CAM", "Grad-CAM Visualization"),
            ("④  Clinical assessment", "Clinical Assessment Form"),
            ("⑤  AI report", "AI Report"),
            ("◷  Patient history", "Patient History"),
        ],
    ),
    (
        "Insights",
        [
            ("◈  Analytics", "Analytics Dashboard"),
        ],
    ),
    (
        "System",
        [
            ("⚙  Settings", "Settings"),
            ("ⓘ  About", "About"),
            ("✉  Contact", "Contact"),
        ],
    ),
]


def ensure_session() -> None:
    defaults = {
        "authenticated": False,
        "registered": False,
        "user_profile": None,
        "role": "user",
        "active_patient_id": "",
        "active_patient_email": "",
        "last_prediction": None,
        "last_gradcam": "",
        "last_mri_image": "",
        "last_report_id": "",
        "ui_theme": "light",
        "active_page": "Home",
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def render_sidebar() -> None:
    role = st.session_state.get("role", "user")
    profile = st.session_state.get("user_profile") or {}
    name = profile.get("full_name") or profile.get("username") or role

    st.sidebar.markdown(
        """
        <div class="side-brand">
          <div class="side-brand-mark">N</div>
          <div>
            <div class="side-brand-name">NeuroLens</div>
            <div class="side-brand-sub">Clinical MRI intelligence</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for section, items in NAV_GROUPS:
        visible = [
            (label, key)
            for label, key in items
            if (role == "admin" or key in USER_NAV) and key not in AUTH_PAGES
        ]
        if not visible:
            continue
        st.sidebar.markdown(
            f'<div class="side-section">{section}</div>', unsafe_allow_html=True
        )
        for label, page_key in visible:
            active = st.session_state.get("active_page") == page_key
            st.sidebar.button(
                label,
                use_container_width=True,
                type="primary" if active else "secondary",
                key=f"nav_{page_key}",
                on_click=lambda pn=page_key: st.session_state.update(
                    {"active_page": pn}
                ),
            )

    patient = st.session_state.get("active_patient_id") or ""
    patient_line = (
        f'<span style="display:block;margin-top:.35rem;font-size:.72rem;opacity:.9;">'
        f"Active patient · {patient[:12]}{'…' if len(patient) > 12 else ''}</span>"
        if patient
        else ""
    )

    st.sidebar.markdown(
        f"""
        <div class="side-user">
          Signed in
          <strong>{name}</strong>
          <span style="display:block;margin-top:.35rem;font-size:.75rem;opacity:.85;">
            Role · {role}
          </span>
          {patient_line}
          <div class="side-status"><span class="side-status-dot"></span> Session active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Sign out", use_container_width=True, key="nav_sign_out"):
        st.session_state.update(
            {"authenticated": False, "role": "user", "active_page": "Home"}
        )
        st.rerun()


def main() -> None:
    ensure_session()

    if not st.session_state["authenticated"]:
        current = st.session_state.get("active_page", "Home")
        if current not in (PUBLIC_PAGES | AUTH_PAGES):
            st.session_state["active_page"] = "Login"
        if st.session_state["active_page"] in AUTH_PAGES:
            st.markdown(
                """
                <style>
                [data-testid="stSidebar"],
                [data-testid="stSidebarCollapsedControl"] { display: none !important; }
                </style>
                """,
                unsafe_allow_html=True,
            )
        PAGES[st.session_state["active_page"]]()
        return

    if st.session_state.get("active_page") in AUTH_PAGES:
        st.session_state["active_page"] = "Home"

    render_sidebar()

    if (
        st.session_state.get("role") != "admin"
        and st.session_state["active_page"] in ADMIN_ONLY
    ):
        st.session_state["active_page"] = "Dashboard"

    PAGES[st.session_state["active_page"]]()


if __name__ == "__main__":
    main()
