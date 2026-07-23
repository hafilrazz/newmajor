import streamlit as st

from frontend.api.client import get_api_client
from frontend.ui.auth_card import inject_auth_card_styles, render_auth_header


def page_login():
    inject_auth_card_styles()
    api = get_api_client()

    _, center, _ = st.columns([1, 1.25, 1])
    with center:
        render_auth_header(
            eyebrow="Secure access",
            title="Welcome back",
            subtitle="Sign in to open the NeuroLens clinical workspace.",
        )

        username = st.text_input("Username", key="login_username", placeholder="your.username")
        password = st.text_input(
            "Password", type="password", key="login_password", placeholder="••••••••"
        )

        c1, c2 = st.columns(2, gap="small")
        user_login = c1.button(
            "User sign in", type="primary", use_container_width=True, key="login_user_btn"
        )
        admin_login = c2.button(
            "Admin sign in", use_container_width=True, key="login_admin_btn"
        )

        if user_login:
            if not username.strip() or not password:
                st.error("Enter username and password.")
            else:
                try:
                    result = api.login_user(username.strip(), password)
                    user = result.get("user") or {}
                    st.session_state.update(
                        {
                            "authenticated": True,
                            "registered": True,
                            "role": user.get("role") or "user",
                            "user_profile": {
                                "user_id": user.get("user_id", ""),
                                "full_name": user.get("full_name", ""),
                                "email": user.get("email", ""),
                                "username": user.get("username", ""),
                            },
                            "active_page": "Dashboard",
                        }
                    )
                    st.rerun()
                except Exception as err:
                    st.error(str(err))

        if admin_login:
            if username.strip() == "admin" and password == "123456":
                st.session_state.update(
                    {
                        "authenticated": True,
                        "registered": True,
                        "role": "admin",
                        "user_profile": {
                            "username": "admin",
                            "full_name": "Administrator",
                            "email": "",
                        },
                        "active_page": "Dashboard",
                    }
                )
                st.rerun()
            else:
                st.error("Invalid administrator credentials.")

        st.markdown('<hr class="nl-auth-divider" />', unsafe_allow_html=True)
        if st.button(
            "Create an account", use_container_width=True, key="login_goto_register"
        ):
            st.session_state["active_page"] = "Registration"
            st.rerun()

        st.markdown(
            '<div class="nl-auth-footer">'
            "Demo admin · <code>admin</code> / <code>123456</code> · Accounts stored in the database."
            "</div>",
            unsafe_allow_html=True,
        )
