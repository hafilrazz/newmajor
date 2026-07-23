import streamlit as st

from frontend.ui.components import page_header, section_title


def page_settings():
    st.session_state.setdefault("ui_theme", "light")
    page_header(
        "Preferences",
        "Settings",
        "Personalize the workspace appearance and review connection information.",
    )

    current = st.session_state.get("ui_theme", "light")
    section_title(
        "Appearance", "Choose the theme that is comfortable for your reading environment."
    )
    light, dark = st.columns(2, gap="medium")
    with light:
        st.markdown(
            f"""
            <div class="card" style="{'outline:2px solid var(--primary);' if current == 'light' else ''}">
              <span class="status-pill">Light</span>
              <h3 style="margin:.75rem 0 .35rem;font-size:1.05rem;">Clinical light</h3>
              <p style="margin:0;color:var(--muted);font-size:.88rem;line-height:1.5;">
                Soft neutrals and teal accents for bright clinical environments.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "Use light theme",
            use_container_width=True,
            type="primary" if current == "light" else "secondary",
            key="theme_light",
        ):
            st.session_state["ui_theme"] = "light"
            st.rerun()
    with dark:
        st.markdown(
            f"""
            <div class="card" style="{'outline:2px solid var(--primary);' if current == 'dark' else ''}">
              <span class="status-pill">Dark</span>
              <h3 style="margin:.75rem 0 .35rem;font-size:1.05rem;">Clinical dark</h3>
              <p style="margin:0;color:var(--muted);font-size:.88rem;line-height:1.5;">
                Deep navy surfaces with teal highlights for low-light review sessions.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "Use dark theme",
            use_container_width=True,
            type="primary" if current == "dark" else "secondary",
            key="theme_dark",
        ):
            st.session_state["ui_theme"] = "dark"
            st.rerun()

    st.divider()
    section_title("System connection", "Configured services for this workspace.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            """
            <div class="card">
              <span class="status-pill"><span class="status-dot"></span>Backend API</span>
              <p style="margin:1rem 0 .3rem;color:var(--muted);font-size:.85rem;">Endpoint</p>
              <strong style="font-size:1.05rem;">http://localhost:5000</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        profile = st.session_state.get("user_profile") or {}
        name = profile.get("full_name") or profile.get("username") or "—"
        role = st.session_state.get("role", "user")
        st.markdown(
            f"""
            <div class="card">
              <span class="status-pill"><span class="status-dot"></span>Session</span>
              <p style="margin:1rem 0 .3rem;color:var(--muted);font-size:.85rem;">Signed in as</p>
              <strong style="font-size:1.05rem;">{name}</strong>
              <p style="margin:.45rem 0 0;color:var(--muted);font-size:.85rem;">Role · {role}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
