import streamlit as st

from frontend.api.client import get_api_client
from frontend.ui.auth_card import inject_auth_card_styles, render_auth_header


def page_user_registration():
    inject_auth_card_styles()
    api = get_api_client()

    _, center, _ = st.columns([1, 1.25, 1])
    with center:
        render_auth_header(
            eyebrow="Get started",
            title="Create your account",
            subtitle="Register once. Sign in anytime to continue your workflow.",
        )

        full_name = st.text_input("Full name", key="reg_full_name", placeholder="Dr. Jane Smith")
        email = st.text_input("Email", key="reg_email", placeholder="you@clinic.org")
        username = st.text_input("Username", key="reg_username", placeholder="jsmith")
        password = st.text_input(
            "Password", type="password", key="reg_password", placeholder="Min. 4 characters"
        )
        confirm = st.text_input(
            "Confirm password", type="password", key="reg_confirm_password"
        )

        if st.button("Register", type="primary", use_container_width=True, key="reg_submit"):
            if not full_name.strip():
                st.error("Enter your full name.")
            elif not email.strip() or "@" not in email:
                st.error("Enter a valid email.")
            elif not username.strip():
                st.error("Enter a username.")
            elif len(password) < 4:
                st.error("Password must be at least 4 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    result = api.register_user(
                        full_name=full_name.strip(),
                        email=email.strip(),
                        username=username.strip(),
                        password=password,
                    )
                    user = result.get("user") or {}
                    st.session_state["registered"] = True
                    st.session_state["user_profile"] = {
                        "user_id": user.get("user_id", ""),
                        "full_name": user.get("full_name", full_name.strip()),
                        "email": user.get("email", email.strip()),
                        "username": user.get("username", username.strip()),
                    }
                    st.session_state["active_page"] = "Login"
                    st.success("Account created. Please sign in.")
                    st.rerun()
                except Exception as err:
                    st.error(str(err))

        st.markdown('<hr class="nl-auth-divider" />', unsafe_allow_html=True)
        if st.button(
            "Already have an account? Sign in",
            use_container_width=True,
            key="reg_goto_login",
        ):
            st.session_state["active_page"] = "Login"
            st.rerun()
