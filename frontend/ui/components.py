"""Shared advanced UI building blocks for NeuroLens."""

from __future__ import annotations

import html
from typing import Any, Iterable, List, Optional, Sequence, Tuple, Union

import streamlit as st


def _html(markup: str) -> None:
    compact = "\n".join(line for line in markup.splitlines() if line.strip())
    if hasattr(st, "html"):
        st.html(compact)
    else:
        st.markdown(compact, unsafe_allow_html=True)


def _esc(v: object) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def data_table(
    data: Union[Any, Sequence[dict]],
    *,
    columns: Optional[Sequence[str]] = None,
    max_rows: int = 100,
) -> None:
    """Render a table without pyarrow (avoids st.dataframe DLL policy issues)."""
    rows: List[dict] = []
    cols: List[str] = []

    if data is None:
        empty_state("No rows", "Nothing to display.", icon="∅")
        return

    # pandas DataFrame (duck-typed — no hard dependency on pyarrow)
    if hasattr(data, "to_dict") and hasattr(data, "columns"):
        try:
            frame = data if columns is None else data[[c for c in columns if c in data.columns]]
            cols = [str(c) for c in frame.columns.tolist()]
            records = frame.head(max_rows).to_dict(orient="records")
            rows = [{str(k): v for k, v in rec.items()} for rec in records]
        except Exception:
            rows = []
            cols = []
    elif isinstance(data, list):
        if not data:
            empty_state("No rows", "Nothing to display.", icon="∅")
            return
        if isinstance(data[0], dict):
            if columns:
                cols = [str(c) for c in columns]
            else:
                seen = []
                for rec in data:
                    for k in rec.keys():
                        if k not in seen:
                            seen.append(k)
                cols = [str(c) for c in seen]
            rows = [{str(k): rec.get(k) for k in cols} for rec in data[:max_rows]]
        else:
            cols = ["value"]
            rows = [{"value": v} for v in data[:max_rows]]
    else:
        st.write(data)
        return

    if not cols or not rows:
        empty_state("No rows", "Nothing to display.", icon="∅")
        return

    head = "".join(f"<th>{_esc(c)}</th>" for c in cols)
    body_parts = []
    for rec in rows:
        cells = "".join(f"<td>{_esc(rec.get(c, ''))}</td>" for c in cols)
        body_parts.append(f"<tr>{cells}</tr>")

    _html(
        f"""
        <div class="nl-table-wrap">
          <table class="nl-table">
            <thead><tr>{head}</tr></thead>
            <tbody>{''.join(body_parts)}</tbody>
          </table>
        </div>
        """
    )


def page_header(
    eyebrow: str,
    title: str,
    lead: str,
    *,
    badge: Optional[str] = None,
) -> None:
    badge_html = (
        f'<span class="nl-page-badge">{_esc(badge)}</span>' if badge else ""
    )
    _html(
        f"""
        <div class="nl-page-header">
          <div style="display:flex;align-items:center;gap:.55rem;flex-wrap:wrap;margin-bottom:.45rem;">
            <span class="eyebrow">{_esc(eyebrow)}</span>{badge_html}
          </div>
          <h1 class="nl-page-title">{_esc(title)}</h1>
          <p class="page-lead">{_esc(lead)}</p>
        </div>
        """
    )


def section_title(title: str, subtitle: str = "") -> None:
    sub = f'<p class="nl-section-sub">{_esc(subtitle)}</p>' if subtitle else ""
    _html(
        f"""
        <div style="margin:.5rem 0 1rem;">
          <h3 class="nl-section-title">{_esc(title)}</h3>{sub}
        </div>
        """
    )


def feature_cards(items: Sequence[Tuple[str, str, str]]) -> None:
    cols = st.columns(len(items), gap="medium")
    for col, (icon, title, body) in zip(cols, items):
        with col:
            _html(
                f"""
                <div class="feature-card">
                  <div class="feature-card-icon">{_esc(icon)}</div>
                  <strong>{_esc(title)}</strong>
                  <span>{_esc(body)}</span>
                </div>
                """
            )


def metric_cards(items: Sequence[Tuple[str, str, str, str]]) -> None:
    """items: (icon, label, value, hint)"""
    cols = st.columns(len(items), gap="medium")
    for col, (icon, label, value, hint) in zip(cols, items):
        with col:
            _html(
                f"""
                <div class="metric-card">
                  <div class="metric-icon">{_esc(icon)}</div>
                  <div class="metric-label">{_esc(label)}</div>
                  <div class="metric-value">{_esc(value)}</div>
                  <div class="metric-hint">{_esc(hint)}</div>
                </div>
                """
            )


def info_panel(title: str, body: str, *, pill: str = "Guidance") -> None:
    _html(
        f"""
        <div class="card">
          <span class="status-pill"><span class="status-dot"></span>{_esc(pill)}</span>
          <h3 style="margin:.9rem 0 .4rem;font-size:1.08rem;font-family:'Plus Jakarta Sans',sans-serif;">
            {_esc(title)}
          </h3>
          <p style="margin:0;color:var(--muted);line-height:1.65;font-size:.93rem;">{_esc(body)}</p>
        </div>
        """
    )


def clinical_disclaimer(text: str) -> None:
    _html(
        f"""
        <div class="nl-disclaimer">
          <div class="nl-disclaimer-label">Clinical notice</div>
          <div class="nl-disclaimer-text">{_esc(text)}</div>
        </div>
        """
    )


def empty_state(title: str, body: str, *, icon: str = "···") -> None:
    _html(
        f"""
        <div class="nl-empty">
          <div class="nl-empty-icon">{_esc(icon)}</div>
          <div class="nl-empty-title">{_esc(title)}</div>
          <div class="nl-empty-body">{_esc(body)}</div>
        </div>
        """
    )


def result_strip(items: Iterable[Tuple[str, str]]) -> None:
    parts = []
    for label, value in items:
        parts.append(
            "<div class='nl-result-cell'>"
            f"<div class='nl-result-label'>{_esc(label)}</div>"
            f"<div class='nl-result-value'>{_esc(value)}</div>"
            "</div>"
        )
    _html(f"<div class='nl-result-strip'>{''.join(parts)}</div>")


def workflow_stepper(current: int) -> None:
    """Clinical workflow progress: 1=Patient … 5=Report."""
    steps = [
        (1, "Patient"),
        (2, "MRI"),
        (3, "Explain"),
        (4, "Assess"),
        (5, "Report"),
    ]
    parts: List[str] = []
    for i, (num, label) in enumerate(steps):
        if num < current:
            cls = "done"
        elif num == current:
            cls = "active"
        else:
            cls = ""
        mark = "✓" if num < current else str(num)
        parts.append(
            f'<div class="wf-step {cls}"><span class="wf-num">{mark}</span>{_esc(label)}</div>'
        )
        if i < len(steps) - 1:
            parts.append('<div class="wf-sep"></div>')
    _html(f'<div class="workflow-stepper">{"".join(parts)}</div>')


def probability_bars(
    names: Sequence[str], probs: Sequence[float]
) -> None:
    rows = []
    for name, p in sorted(zip(names, probs), key=lambda x: x[1], reverse=True):
        pct = max(0.0, min(1.0, float(p)))
        width = f"{pct * 100:.1f}"
        rows.append(
            f"""
            <div class="prob-row">
              <div class="prob-name">{_esc(name)}</div>
              <div class="prob-track"><div class="prob-fill" style="width:{width}%;"></div></div>
              <div class="prob-pct">{width}%</div>
            </div>
            """
        )
    _html("".join(rows))


def explanation_block(explanation: Optional[dict]) -> None:
    if not explanation or not isinstance(explanation, dict):
        return
    regions = explanation.get("regions") or {}
    faithfulness = explanation.get("faithfulness") or {}
    narrative = explanation.get("narrative") or ""

    section_title(
        "Model decision explanation",
        "Faithful analysis of the Grad-CAM result.",
    )
    if narrative:
        _html(
            f"""
            <div class="card">
              <span class="status-pill"><span class="status-dot"></span>Explanation</span>
              <p style="margin:1rem 0 0;line-height:1.7;">{_esc(narrative)}</p>
            </div>
            """
        )

    def _pct(v):
        return f"{float(v) * 100:.0f}%" if isinstance(v, (int, float)) else "--"

    top_region = regions.get("top_region", "--")
    top_frac = regions.get("top_region_fraction")
    concentration_label = regions.get("concentration_label", "--")
    concentration = regions.get("concentration")
    coverage = regions.get("coverage")
    result_strip(
        [
            (
                "Focus region",
                f"{top_region}"
                + (f" · {_pct(top_frac)}" if top_frac is not None else ""),
            ),
            (
                "Concentration",
                f"{concentration_label}"
                + (f" · {_pct(concentration)}" if concentration is not None else ""),
            ),
            ("Strong coverage", _pct(coverage)),
        ]
    )

    if faithfulness:
        label = str(faithfulness.get("label", "")).upper()
        orig = faithfulness.get("original_confidence")
        masked = faithfulness.get("masked_confidence")
        rel = faithfulness.get("relative_drop")
        area = faithfulness.get("masked_area")
        _html(
            f"""
            <div class="card">
              <span class="status-pill"><span class="status-dot"></span>Faithfulness · {_esc(label or 'N/A')}</span>
              <p style="margin:.85rem 0 0;color:var(--muted);line-height:1.6;font-size:.9rem;">
                Masking the top {_esc(_pct(area))} most-active pixels changed confidence from
                <strong>{_esc(_pct(orig))}</strong> to <strong>{_esc(_pct(masked))}</strong>
                (<strong>{_esc(_pct(rel))}</strong> relative drop).
              </p>
            </div>
            """
        )


def contact_card(pill: str, title: str, body: str) -> None:
    _html(
        f"""
        <div class="card">
          <div class="status-pill">{_esc(pill)}</div>
          <h3 style="margin:.9rem 0 .4rem;font-family:'Plus Jakarta Sans',sans-serif;">{_esc(title)}</h3>
          <p style="margin:0;color:var(--muted);line-height:1.6;">{_esc(body)}</p>
        </div>
        """
    )


def top_bar(section: str, page: str, *, role: str = "") -> None:
    role_html = (
        f'<span class="chip chip-accent">Role · {_esc(role)}</span>' if role else ""
    )
    _html(
        f"""
        <div class="top-bar">
          <div class="top-bar-left">
            <span class="top-bar-crumb">{_esc(section)} / <strong>{_esc(page)}</strong></span>
          </div>
          <div style="display:flex;gap:.4rem;flex-wrap:wrap;">{role_html}</div>
        </div>
        """
    )
