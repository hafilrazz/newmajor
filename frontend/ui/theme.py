"""Advanced clinical design system for NeuroLens Streamlit UI."""

from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.session_state.setdefault("ui_theme", "light")
    dark = st.session_state.get("ui_theme") == "dark"

    if dark:
        c = {
            "bg": "#070b14",
            "bg2": "#0c1424",
            "bg3": "#111b2e",
            "panel": "rgba(18, 28, 48, 0.92)",
            "panel_solid": "#121c30",
            "glass": "rgba(18, 28, 48, 0.72)",
            "text": "#eef3fb",
            "muted": "#8fa3bf",
            "faint": "#64748b",
            "border": "rgba(148, 163, 184, 0.14)",
            "border_strong": "rgba(148, 163, 184, 0.24)",
            "primary": "#2dd4bf",
            "primary_dark": "#14b8a6",
            "primary_soft": "rgba(45, 212, 191, 0.14)",
            "accent": "#818cf8",
            "accent_soft": "rgba(129, 140, 248, 0.14)",
            "danger": "#f87171",
            "danger_soft": "rgba(248, 113, 113, 0.12)",
            "warning": "#fbbf24",
            "warning_soft": "rgba(251, 191, 36, 0.12)",
            "success": "#34d399",
            "success_soft": "rgba(52, 211, 153, 0.12)",
            "shadow": "rgba(0, 0, 0, 0.45)",
            "glow": "rgba(45, 212, 191, 0.18)",
            "input_bg": "#0a1220",
            "input_text": "#eef3fb",
            "sidebar": "#0a1220",
            "sidebar_end": "#070b14",
            "sidebar_border": "rgba(148, 163, 184, 0.12)",
            "sidebar_text": "#94a3b8",
            "sidebar_strong": "#f1f5f9",
            "sidebar_muted": "#64748b",
            "sidebar_section": "#64748b",
            "sidebar_hover": "rgba(148, 163, 184, 0.08)",
            "sidebar_active_bg": "linear-gradient(135deg, rgba(20,184,166,0.22), rgba(129,140,248,0.12))",
            "sidebar_active_text": "#5eead4",
            "sidebar_active_border": "rgba(45, 212, 191, 0.28)",
            "sidebar_user_bg": "rgba(15, 23, 42, 0.55)",
            "hero_overlay": "linear-gradient(120deg, rgba(7,11,20,.96) 0%, rgba(12,20,36,.82) 50%, rgba(7,11,20,.4) 100%)",
            "metric_glow": "0 0 40px rgba(45,212,191,0.08)",
            "chart_primary": "#2dd4bf",
            "chart_secondary": "#818cf8",
            "chart_grid": "rgba(148,163,184,0.12)",
            "table_header": "#0f172a",
        }
        scheme = "dark"
    else:
        c = {
            "bg": "#f0f5fb",
            "bg2": "#e4eef8",
            "bg3": "#dce8f4",
            "panel": "rgba(255, 255, 255, 0.92)",
            "panel_solid": "#ffffff",
            "glass": "rgba(255, 255, 255, 0.78)",
            "text": "#0b1f36",
            "muted": "#5a7190",
            "faint": "#8a9bb0",
            "border": "rgba(15, 45, 75, 0.08)",
            "border_strong": "rgba(15, 45, 75, 0.14)",
            "primary": "#0d9488",
            "primary_dark": "#0f766e",
            "primary_soft": "rgba(13, 148, 136, 0.10)",
            "accent": "#4f46e5",
            "accent_soft": "rgba(79, 70, 229, 0.08)",
            "danger": "#e11d48",
            "danger_soft": "rgba(225, 29, 72, 0.08)",
            "warning": "#d97706",
            "warning_soft": "rgba(217, 119, 6, 0.10)",
            "success": "#059669",
            "success_soft": "rgba(5, 150, 105, 0.10)",
            "shadow": "rgba(15, 39, 68, 0.07)",
            "glow": "rgba(13, 148, 136, 0.12)",
            "input_bg": "#ffffff",
            "input_text": "#0b1f36",
            "sidebar": "#ffffff",
            "sidebar_end": "#f4f8fc",
            "sidebar_border": "rgba(15, 45, 75, 0.08)",
            "sidebar_text": "#3d536b",
            "sidebar_strong": "#0b1f36",
            "sidebar_muted": "#5a7190",
            "sidebar_section": "#8a9bb0",
            "sidebar_hover": "rgba(13, 148, 136, 0.07)",
            "sidebar_active_bg": "linear-gradient(135deg, rgba(13,148,136,0.14), rgba(79,70,229,0.06))",
            "sidebar_active_text": "#0f766e",
            "sidebar_active_border": "rgba(13, 148, 136, 0.22)",
            "sidebar_user_bg": "#f0f5fb",
            "hero_overlay": "linear-gradient(115deg, rgba(8,18,34,.94) 0%, rgba(10,28,48,.78) 48%, rgba(8,24,42,.35) 100%)",
            "metric_glow": "0 12px 40px rgba(13,148,136,0.08)",
            "chart_primary": "#0d9488",
            "chart_secondary": "#4f46e5",
            "chart_grid": "rgba(15,45,75,0.06)",
            "table_header": "#f8fafc",
        }
        scheme = "light"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

        :root {{
          --bg: {c["bg"]}; --bg2: {c["bg2"]}; --bg3: {c["bg3"]};
          --panel: {c["panel"]}; --panel-solid: {c["panel_solid"]}; --glass: {c["glass"]};
          --text: {c["text"]}; --muted: {c["muted"]}; --faint: {c["faint"]};
          --border: {c["border"]}; --border-strong: {c["border_strong"]};
          --primary: {c["primary"]}; --primary-dark: {c["primary_dark"]};
          --primary-soft: {c["primary_soft"]}; --accent: {c["accent"]};
          --accent-soft: {c["accent_soft"]};
          --danger: {c["danger"]}; --danger-soft: {c["danger_soft"]};
          --warning: {c["warning"]}; --warning-soft: {c["warning_soft"]};
          --success: {c["success"]}; --success-soft: {c["success_soft"]};
          --shadow: {c["shadow"]}; --glow: {c["glow"]};
          --input-bg: {c["input_bg"]}; --input-text: {c["input_text"]};
          --sidebar: {c["sidebar"]}; --sidebar-end: {c["sidebar_end"]};
          --sidebar-border: {c["sidebar_border"]}; --sidebar-text: {c["sidebar_text"]};
          --sidebar-strong: {c["sidebar_strong"]}; --sidebar-muted: {c["sidebar_muted"]};
          --sidebar-section: {c["sidebar_section"]}; --sidebar-hover: {c["sidebar_hover"]};
          --sidebar-active-bg: {c["sidebar_active_bg"]};
          --sidebar-active-text: {c["sidebar_active_text"]};
          --sidebar-active-border: {c["sidebar_active_border"]};
          --sidebar-user-bg: {c["sidebar_user_bg"]};
          --hero-overlay: {c["hero_overlay"]};
          --metric-glow: {c["metric_glow"]};
          --chart-primary: {c["chart_primary"]};
          --chart-secondary: {c["chart_secondary"]};
          --chart-grid: {c["chart_grid"]};
          --table-header: {c["table_header"]};
          --radius: 18px;
          --radius-sm: 12px;
          --radius-xs: 8px;
        }}

        html, body, [class*="css"] {{
          font-family: "Inter", "Plus Jakarta Sans", system-ui, sans-serif !important;
        }}

        .stApp {{
          color-scheme: {scheme};
          background:
            radial-gradient(1200px 600px at 10% -10%, var(--glow), transparent 55%),
            radial-gradient(900px 500px at 100% 0%, {c["accent_soft"]}, transparent 50%),
            linear-gradient(180deg, var(--bg) 0%, var(--bg2) 55%, var(--bg3) 100%);
          color: var(--text);
        }}
        [data-testid="stHeader"] {{
          background: transparent;
          backdrop-filter: blur(12px);
        }}
        [data-testid="stToolbar"] {{ right: 1rem; }}
        [data-testid="stAppViewContainer"] > .main .block-container {{
          max-width: 1240px;
          padding-top: 1.25rem;
          padding-bottom: 3.5rem;
          padding-left: 1.5rem;
          padding-right: 1.5rem;
        }}
        h1, h2, h3, h4, p, label, [data-testid="stMarkdownContainer"] {{
          color: var(--text);
        }}
        h1, h2, h3 {{
          font-family: "Plus Jakarta Sans", Inter, sans-serif !important;
          font-weight: 750 !important;
          letter-spacing: -.03em !important;
        }}

        /* ── Cards & surfaces ── */
        .card, .feature-card, .nl-empty, .nl-disclaimer, .metric-card, .glass-panel {{
          background: var(--panel);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          box-shadow: 0 10px 30px var(--shadow);
          backdrop-filter: blur(16px);
        }}
        .card {{
          padding: 1.3rem 1.4rem;
          position: relative;
          overflow: hidden;
          transition: transform .2s ease, box-shadow .2s ease;
        }}
        .card:hover {{
          box-shadow: 0 16px 40px var(--shadow), 0 0 0 1px var(--border-strong);
        }}
        .card::before {{
          content: "";
          position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
          background: linear-gradient(180deg, var(--primary), var(--accent));
          border-radius: 3px 0 0 3px;
        }}
        .glass-panel {{
          padding: 1.25rem 1.35rem;
          background: var(--glass);
        }}

        /* ── Pills & badges ── */
        .status-pill, .eyebrow, .nl-page-badge, .chip {{
          display: inline-flex; align-items: center; gap: .35rem;
          padding: .3rem .72rem; border-radius: 999px;
          font-size: .72rem; font-weight: 700; letter-spacing: .04em;
        }}
        .status-pill, .eyebrow {{
          background: var(--primary-soft); color: var(--primary);
          text-transform: uppercase; letter-spacing: .08em;
        }}
        .status-dot {{
          width: .4rem; height: .4rem; border-radius: 50%;
          background: var(--primary); box-shadow: 0 0 0 3px var(--primary-soft);
        }}
        .nl-page-badge {{
          background: var(--accent-soft); color: var(--accent);
          text-transform: uppercase;
        }}
        .chip {{
          background: var(--primary-soft); color: var(--primary);
          border: 1px solid transparent;
        }}
        .chip-accent {{ background: var(--accent-soft); color: var(--accent); }}
        .chip-warn {{ background: var(--warning-soft); color: var(--warning); }}
        .chip-danger {{ background: var(--danger-soft); color: var(--danger); }}
        .chip-success {{ background: var(--success-soft); color: var(--success); }}

        /* ── Page headers ── */
        .nl-page-header {{
          margin-bottom: 1.5rem;
          padding: 1.35rem 1.5rem;
          border-radius: var(--radius);
          background: var(--panel);
          border: 1px solid var(--border);
          box-shadow: 0 8px 28px var(--shadow);
          position: relative;
          overflow: hidden;
        }}
        .nl-page-header::after {{
          content: "";
          position: absolute; right: -40px; top: -40px;
          width: 180px; height: 180px; border-radius: 50%;
          background: radial-gradient(circle, var(--primary-soft), transparent 70%);
          pointer-events: none;
        }}
        .nl-page-title {{
          margin: .45rem 0 .35rem !important;
          font-size: clamp(1.55rem, 2.4vw, 1.95rem) !important;
        }}
        .page-lead {{
          color: var(--muted) !important;
          max-width: 720px;
          line-height: 1.65;
          margin: 0 !important;
          font-size: .95rem;
        }}
        .nl-section-title {{
          margin: 0 !important;
          font-size: 1.08rem !important;
          font-family: "Plus Jakarta Sans", sans-serif !important;
        }}
        .nl-section-sub {{
          margin: .25rem 0 0 !important;
          color: var(--muted) !important;
          font-size: .88rem;
        }}

        /* ── Metric cards ── */
        .metric-card {{
          padding: 1.15rem 1.25rem;
          position: relative;
          overflow: hidden;
          box-shadow: var(--metric-glow), 0 8px 24px var(--shadow);
        }}
        .metric-card::after {{
          content: "";
          position: absolute; right: -12px; bottom: -12px;
          width: 72px; height: 72px; border-radius: 50%;
          background: var(--primary-soft);
          opacity: .7;
        }}
        .metric-label {{
          color: var(--muted); font-size: .72rem; font-weight: 700;
          text-transform: uppercase; letter-spacing: .06em; margin-bottom: .45rem;
        }}
        .metric-value {{
          font-family: "Plus Jakarta Sans", sans-serif;
          font-size: 1.65rem; font-weight: 800; letter-spacing: -.03em;
          color: var(--text); line-height: 1.1;
        }}
        .metric-hint {{
          margin-top: .4rem; color: var(--faint); font-size: .78rem;
        }}
        .metric-icon {{
          display: inline-flex; align-items: center; justify-content: center;
          width: 2.1rem; height: 2.1rem; border-radius: 10px;
          background: var(--primary-soft); color: var(--primary);
          font-size: .85rem; font-weight: 800; margin-bottom: .65rem;
        }}

        /* ── Result strip ── */
        .nl-result-strip {{
          display: grid; grid-template-columns: repeat(3, minmax(0,1fr));
          gap: .85rem; margin: .5rem 0 1.25rem;
        }}
        .nl-result-cell {{
          background: var(--panel); border: 1px solid var(--border);
          border-radius: 14px; padding: 1rem 1.1rem;
          box-shadow: 0 8px 22px var(--shadow);
          position: relative; overflow: hidden;
        }}
        .nl-result-cell::top,
        .nl-result-cell::before {{
          content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
          background: linear-gradient(90deg, var(--primary), var(--accent));
        }}
        .nl-result-label {{
          color: var(--muted); font-size: .7rem; font-weight: 700;
          text-transform: uppercase; letter-spacing: .05em; margin-bottom: .35rem;
        }}
        .nl-result-value {{
          color: var(--text); font-family: "Plus Jakarta Sans", sans-serif;
          font-size: 1.2rem; font-weight: 750; letter-spacing: -.02em;
        }}

        /* ── Feature cards ── */
        .feature-card {{
          min-height: 148px; padding: 1.25rem; margin: .15rem 0 .5rem;
          transition: transform .2s ease, box-shadow .2s ease;
        }}
        .feature-card:hover {{
          transform: translateY(-3px);
          box-shadow: 0 18px 40px var(--shadow);
        }}
        .feature-card-icon {{
          display: inline-flex; height: 2.2rem; min-width: 2.2rem; padding: 0 .55rem;
          margin-bottom: .75rem; border-radius: 11px; place-items: center;
          background: linear-gradient(135deg, var(--primary-soft), var(--accent-soft));
          color: var(--primary); font-size: .78rem; font-weight: 800;
        }}
        .feature-card strong {{
          display: block; margin-bottom: .4rem;
          font-family: "Plus Jakarta Sans", sans-serif;
          font-size: 1rem;
        }}
        .feature-card span {{ color: var(--muted); font-size: .9rem; line-height: 1.55; }}

        /* ── Empty / disclaimer ── */
        .nl-empty {{
          padding: 2rem 1.5rem; text-align: center; margin: .6rem 0 1rem;
        }}
        .nl-empty-icon {{
          width: 48px; height: 48px; margin: 0 auto .85rem; border-radius: 14px;
          display: grid; place-items: center;
          background: var(--primary-soft); color: var(--primary);
          font-weight: 800; font-size: 1.1rem;
        }}
        .nl-empty-title {{ font-weight: 750; margin-bottom: .35rem; font-size: 1.05rem; }}
        .nl-empty-body {{ color: var(--muted); font-size: .92rem; line-height: 1.55; max-width: 420px; margin: 0 auto; }}
        .nl-disclaimer {{
          display: flex; gap: 1rem; align-items: flex-start;
          padding: 1.05rem 1.2rem; margin-top: 1.25rem;
          border-left: 4px solid var(--warning);
        }}
        .nl-disclaimer-label {{
          flex-shrink: 0; padding: .28rem .55rem; border-radius: 8px;
          background: var(--warning-soft); color: var(--warning);
          font-size: .68rem; font-weight: 800; text-transform: uppercase; letter-spacing: .06em;
        }}
        .nl-disclaimer-text {{ color: var(--muted); font-size: .9rem; line-height: 1.55; }}

        /* ── Workflow stepper ── */
        .workflow-stepper {{
          display: flex; gap: .5rem; flex-wrap: wrap;
          margin: 0 0 1.35rem; padding: .85rem 1rem;
          background: var(--panel); border: 1px solid var(--border);
          border-radius: 14px; box-shadow: 0 6px 18px var(--shadow);
        }}
        .wf-step {{
          display: flex; align-items: center; gap: .5rem;
          padding: .4rem .7rem; border-radius: 999px;
          font-size: .78rem; font-weight: 650; color: var(--muted);
          background: transparent; border: 1px solid transparent;
        }}
        .wf-step.active {{
          background: var(--primary-soft); color: var(--primary);
          border-color: var(--sidebar-active-border);
        }}
        .wf-step.done {{ color: var(--success); }}
        .wf-num {{
          width: 1.35rem; height: 1.35rem; border-radius: 50%;
          display: grid; place-items: center;
          font-size: .68rem; font-weight: 800;
          background: var(--bg2); color: var(--muted);
        }}
        .wf-step.active .wf-num {{
          background: var(--primary); color: #fff;
        }}
        .wf-step.done .wf-num {{
          background: var(--success-soft); color: var(--success);
        }}
        .wf-sep {{
          width: 16px; height: 1px; background: var(--border-strong);
          align-self: center;
        }}

        /* ── Probability bars ── */
        .prob-row {{
          display: flex; align-items: center; gap: .75rem;
          margin: .45rem 0; font-size: .88rem;
        }}
        .prob-name {{ min-width: 150px; color: var(--text); font-weight: 600; }}
        .prob-track {{
          flex: 1; height: 8px; border-radius: 999px;
          background: var(--bg2); overflow: hidden;
          border: 1px solid var(--border);
        }}
        .prob-fill {{
          height: 100%; border-radius: 999px;
          background: linear-gradient(90deg, var(--primary-dark), var(--primary), var(--accent));
        }}
        .prob-pct {{
          min-width: 48px; text-align: right;
          font-weight: 700; color: var(--muted); font-size: .82rem;
        }}

        /* ── Forms ── */
        [data-testid="stTextInputRootElement"],
        [data-testid="stNumberInputContainer"],
        [data-testid="stTextAreaRootElement"],
        [data-baseweb="select"] > div,
        [data-testid="stFileUploaderDropzone"] {{
          background: var(--input-bg) !important;
          border: 1px solid var(--border) !important;
          border-radius: var(--radius-sm) !important;
          color: var(--input-text) !important;
          box-shadow: 0 1px 2px var(--shadow) !important;
          transition: border-color .15s ease, box-shadow .15s ease !important;
        }}
        [data-testid="stTextInputRootElement"]:focus-within,
        [data-testid="stTextAreaRootElement"]:focus-within {{
          border-color: var(--primary) !important;
          box-shadow: 0 0 0 3px var(--primary-soft) !important;
        }}
        input, textarea {{
          color: var(--input-text) !important;
          -webkit-text-fill-color: var(--input-text) !important;
          caret-color: var(--input-text) !important;
          background: transparent !important;
        }}
        input::placeholder, textarea::placeholder {{
          color: var(--faint) !important;
          -webkit-text-fill-color: var(--faint) !important;
        }}
        .stButton > button {{
          border-radius: var(--radius-sm) !important;
          border: 1px solid var(--border) !important;
          background: var(--panel-solid) !important;
          color: var(--text) !important;
          font-weight: 650 !important;
          font-family: "Inter", sans-serif !important;
          transition: all .18s ease !important;
          min-height: 2.55rem !important;
        }}
        .stButton > button:hover {{
          border-color: var(--border-strong) !important;
          transform: translateY(-1px);
          box-shadow: 0 6px 16px var(--shadow) !important;
        }}
        .stButton > button[kind="primary"] {{
          background: linear-gradient(135deg, var(--primary-dark), var(--primary)) !important;
          color: #fff !important;
          border-color: transparent !important;
          box-shadow: 0 6px 18px var(--glow) !important;
        }}
        .stButton > button[kind="primary"]:hover {{
          filter: brightness(1.05);
          box-shadow: 0 10px 24px var(--glow) !important;
        }}
        [data-testid="stFileUploaderDropzone"] {{
          border-style: dashed !important;
          border-width: 1.5px !important;
          padding: 1.25rem !important;
        }}
        [data-testid="stMetric"] {{
          background: var(--panel);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: .9rem 1rem;
          box-shadow: 0 6px 18px var(--shadow);
        }}
        [data-testid="stMetricLabel"] {{ color: var(--muted) !important; }}
        [data-testid="stMetricValue"] {{
          font-family: "Plus Jakarta Sans", sans-serif !important;
          color: var(--text) !important;
        }}

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {{
          background: linear-gradient(180deg, var(--sidebar) 0%, var(--sidebar-end) 100%) !important;
          border-right: 1px solid var(--sidebar-border) !important;
        }}
        section[data-testid="stSidebar"] > div {{
          background: transparent !important;
          padding-top: .75rem;
        }}
        .side-brand {{
          display: flex; align-items: center; gap: .8rem;
          padding: .5rem .4rem 1.15rem; margin-bottom: .75rem;
          border-bottom: 1px solid var(--sidebar-border);
        }}
        .side-brand-mark {{
          height: 44px; width: 44px; border-radius: 13px;
          display: grid; place-items: center;
          background: linear-gradient(145deg, var(--primary-dark), var(--accent));
          color: #fff; font-weight: 800; font-size: 1.05rem;
          box-shadow: 0 8px 20px var(--glow);
          font-family: "Plus Jakarta Sans", sans-serif;
        }}
        .side-brand-name {{
          color: var(--sidebar-strong); font-size: 1.05rem; font-weight: 800;
          font-family: "Plus Jakarta Sans", sans-serif; letter-spacing: -.02em;
        }}
        .side-brand-sub {{
          color: var(--sidebar-muted); font-size: .72rem; margin-top: .12rem;
        }}
        .side-section {{
          color: var(--sidebar-section); letter-spacing: .12em; text-transform: uppercase;
          font-size: .62rem; font-weight: 750; margin: 1.05rem .35rem .45rem;
        }}
        section[data-testid="stSidebar"] .stButton > button {{
          width: 100%; min-height: 2.45rem; justify-content: flex-start;
          padding-left: .9rem; box-shadow: none !important;
          background: transparent !important;
          border: 1px solid transparent !important;
          color: var(--sidebar-text) !important;
          border-radius: 12px !important;
          font-weight: 600 !important;
        }}
        section[data-testid="stSidebar"] .stButton > button:hover {{
          background: var(--sidebar-hover) !important;
          color: var(--sidebar-strong) !important;
          transform: none !important;
          box-shadow: none !important;
        }}
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
          background: var(--sidebar-active-bg) !important;
          color: var(--sidebar-active-text) !important;
          border-color: var(--sidebar-active-border) !important;
          box-shadow: none !important;
        }}
        .side-user {{
          padding: .9rem 1rem; margin-top: 1.35rem; border-radius: 14px;
          border: 1px solid var(--sidebar-border);
          background: var(--sidebar-user-bg);
          color: var(--sidebar-muted); font-size: .8rem;
        }}
        .side-user strong {{
          display: block; color: var(--sidebar-strong); text-transform: capitalize;
          margin-top: .25rem; font-size: .95rem;
          font-family: "Plus Jakarta Sans", sans-serif;
        }}
        .side-status {{
          display: inline-flex; align-items: center; gap: .35rem;
          margin-top: .55rem; font-size: .72rem; color: var(--success);
        }}
        .side-status-dot {{
          width: 6px; height: 6px; border-radius: 50%;
          background: var(--success);
          box-shadow: 0 0 0 3px var(--success-soft);
          animation: pulse-dot 2s ease infinite;
        }}
        @keyframes pulse-dot {{
          0%, 100% {{ opacity: 1; }}
          50% {{ opacity: .55; }}
        }}
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
          color: var(--sidebar-text);
        }}

        /* ── Grad-CAM legend ── */
        .nl-legend {{
          margin: .4rem 0 1.1rem; padding: 1rem 1.1rem;
          background: var(--panel); border: 1px solid var(--border);
          border-radius: 14px;
        }}
        .nl-legend-bar {{
          height: 12px; border-radius: 999px;
          background: linear-gradient(90deg,#30123b,#4145ab,#26bce1,#4ac16d,#d2e935,#fb8022,#900c00);
        }}
        .nl-legend-scale {{
          display: flex; justify-content: space-between; margin-top: .4rem;
          font-size: .74rem; color: var(--muted); font-weight: 650;
        }}
        [data-testid="stImage"] img {{
          border-radius: 14px; border: 1px solid var(--border);
          box-shadow: 0 10px 28px var(--shadow);
        }}

        /* ── Auth layout ── */
        .auth-shell {{
          max-width: 440px; margin: 0 auto;
        }}
        .auth-brand-row {{
          display: flex; align-items: center; justify-content: center;
          gap: .65rem; margin-bottom: 1.5rem;
        }}
        .auth-brand-mark {{
          width: 42px; height: 42px; border-radius: 12px;
          display: grid; place-items: center;
          background: linear-gradient(145deg, var(--primary-dark), var(--accent));
          color: #fff; font-weight: 800; font-size: 1rem;
          box-shadow: 0 8px 22px var(--glow);
        }}
        .auth-brand-name {{
          font-family: "Plus Jakarta Sans", sans-serif;
          font-weight: 800; font-size: 1.15rem; letter-spacing: -.02em;
        }}

        /* ── Dataframes / HTML tables ── */
        [data-testid="stDataFrame"] {{
          border: 1px solid var(--border);
          border-radius: 14px;
          overflow: hidden;
          box-shadow: 0 6px 18px var(--shadow);
        }}
        .nl-table-wrap {{
          width: 100%;
          overflow-x: auto;
          border: 1px solid var(--border);
          border-radius: 14px;
          box-shadow: 0 6px 18px var(--shadow);
          background: var(--panel-solid);
          margin: .35rem 0 1rem;
        }}
        .nl-table {{
          width: 100%;
          border-collapse: collapse;
          font-size: .88rem;
        }}
        .nl-table thead th {{
          text-align: left;
          padding: .75rem 1rem;
          background: var(--table-header);
          color: var(--muted);
          font-size: .72rem;
          font-weight: 750;
          text-transform: uppercase;
          letter-spacing: .04em;
          border-bottom: 1px solid var(--border);
          white-space: nowrap;
        }}
        .nl-table tbody td {{
          padding: .7rem 1rem;
          border-bottom: 1px solid var(--border);
          color: var(--text);
          max-width: 280px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }}
        .nl-table tbody tr:last-child td {{ border-bottom: none; }}
        .nl-table tbody tr:hover td {{ background: var(--primary-soft); }}

        /* ── Dividers ── */
        hr {{
          border: none !important;
          border-top: 1px solid var(--border) !important;
          margin: 1.25rem 0 !important;
        }}

        /* ── Hero (home) ── */
        .hero {{
          position: relative; min-height: 440px;
          display: flex; align-items: flex-end; overflow: hidden;
          border-radius: 28px; padding: clamp(1.9rem, 5vw, 3.2rem);
          margin-bottom: 1.6rem;
          border: 1px solid rgba(255,255,255,.08);
          box-shadow: 0 28px 70px rgba(9, 31, 49, .2);
          background-size: cover; background-position: center;
        }}
        .hero-content {{ max-width: 620px; position: relative; z-index: 1; }}
        .hero .hero-kicker {{
          display: inline-flex; border: 1px solid rgba(94, 234, 212, .35);
          border-radius: 999px; padding: .42rem .85rem; color: #99f6e4;
          background: rgba(15, 118, 110, .28); font-size: .74rem;
          font-weight: 750; letter-spacing: .11em; text-transform: uppercase;
          margin-bottom: 1.05rem;
        }}
        .hero h1 {{
          margin: 0 0 .9rem !important; color: #ffffff !important;
          font-size: clamp(2.2rem, 4vw, 3.25rem) !important;
          line-height: 1.06 !important; letter-spacing: -.045em !important;
          font-family: "Plus Jakarta Sans", sans-serif !important;
        }}
        .hero p {{
          color: rgba(226, 236, 245, .9) !important;
          font-size: 1.05rem; line-height: 1.65; margin: 0; max-width: 36rem;
        }}
        .hero-meta {{
          display: flex; flex-wrap: wrap; gap: .55rem; margin-top: 1.35rem;
        }}
        .hero-chip {{
          display: inline-flex; padding: .4rem .75rem; border-radius: 999px;
          background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.14);
          color: rgba(226, 236, 245, .92); font-size: .78rem; font-weight: 650;
        }}
        .home-heading {{
          font-family: "Plus Jakarta Sans", sans-serif;
          font-size: 1.35rem; font-weight: 750; letter-spacing: -.02em;
          margin: 1.5rem 0 .35rem;
        }}
        .home-subheading {{
          color: var(--muted); font-size: .95rem; margin: 0 0 1.1rem; line-height: 1.55;
        }}

        /* ── Top bar ── */
        .top-bar {{
          display: flex; align-items: center; justify-content: space-between;
          gap: 1rem; flex-wrap: wrap;
          margin-bottom: 1rem; padding: .65rem 1rem;
          background: var(--glass); border: 1px solid var(--border);
          border-radius: 14px; backdrop-filter: blur(12px);
        }}
        .top-bar-left {{ display: flex; align-items: center; gap: .6rem; flex-wrap: wrap; }}
        .top-bar-crumb {{
          color: var(--muted); font-size: .8rem; font-weight: 600;
        }}
        .top-bar-crumb strong {{ color: var(--text); }}

        @media (max-width: 900px) {{
          .nl-result-strip {{ grid-template-columns: 1fr; }}
          .workflow-stepper {{ flex-direction: column; align-items: flex-start; }}
          .wf-sep {{ display: none; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
