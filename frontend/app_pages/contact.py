import streamlit as st

from frontend.ui.components import contact_card, page_header


def page_contact():
    page_header(
        "Support",
        "Contact the team",
        "Need assistance with access, an assessment workflow, or an integration? Our support channel is here to help.",
    )

    email, phone = st.columns(2, gap="medium")
    with email:
        contact_card(
            "Email support",
            "neurolenscompany@gmail.com",
            "For product access, account help, and technical questions.",
        )
    with phone:
        contact_card(
            "Telephone",
            "+91 63646 17730",
            "For urgent operational support during business hours.",
        )

    st.markdown(
        """
        <div class="card" style="margin-top:1rem;">
          <span class="status-pill"><span class="status-dot"></span>Response guidance</span>
          <p style="margin:1rem 0 0;color:var(--muted);line-height:1.65;font-size:.93rem;">
            Include your username, approximate time of the issue, and whether the problem relates to
            login, MRI upload, reporting, or email delivery so we can assist faster.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("demonstration contact details.")
