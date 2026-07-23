"""Auth card chrome for login / registration."""

from __future__ import annotations

import html

import streamlit as st


def inject_auth_card_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        [data-testid="stAppViewContainer"] > .main .block-container {
          max-width: 460px !important;
          padding-top: 2.75rem !important;
        }
        .nl-auth {
          background: var(--panel-solid, #fff);
          border: 1px solid var(--border, rgba(15,45,75,.1));
          border-radius: 22px;
          padding: 1.75rem 1.6rem 1.45rem;
          box-shadow: 0 20px 50px var(--shadow, rgba(15,39,68,.1));
          margin-bottom: 1rem;
          position: relative;
          overflow: hidden;
        }
        .nl-auth::before {
          content: "";
          position: absolute; top: 0; left: 0; right: 0; height: 3px;
          background: linear-gradient(90deg, var(--primary), var(--accent));
        }
        .nl-auth-title {
          font-size: 1.55rem; font-weight: 800; letter-spacing: -.03em;
          margin: .4rem 0 .4rem; color: var(--text, #0f2744);
          font-family: "Plus Jakarta Sans", Inter, sans-serif;
        }
        .nl-auth-subtitle {
          color: var(--muted, #5b718a); font-size: .93rem; line-height: 1.55; margin: 0;
        }
        .nl-auth-footer {
          color: var(--muted, #5b718a); font-size: .8rem; text-align: center;
          margin-top: 1rem; line-height: 1.5;
        }
        .nl-auth-divider {
          height: 1px; border: 0; background: var(--border, rgba(15,45,75,.1));
          margin: 1.1rem 0;
        }
        .eyebrow {
          display: inline-flex; padding: .3rem .7rem; border-radius: 999px;
          background: var(--primary-soft, rgba(15,118,110,.1));
          color: var(--primary, #0f766e); font-size: .72rem; font-weight: 750;
          letter-spacing: .08em; text-transform: uppercase;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_auth_header(*, eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="auth-brand-row">
          <div class="auth-brand-mark">N</div>
          <div class="auth-brand-name">NeuroLens</div>
        </div>
        <div class="nl-auth">
          <span class="eyebrow">{html.escape(eyebrow)}</span>
          <div class="nl-auth-title">{html.escape(title)}</div>
          <p class="nl-auth-subtitle">{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
