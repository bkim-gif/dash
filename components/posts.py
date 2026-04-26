"""
components/posts.py
===================
Renderiza os cards de Top N e Bottom N posts.

Cada card mostra:
  - Rede social (badge colorido)
  - Texto do post (truncado em 120 chars)
  - Impressions | ER | AQE | Clicks | Shares
  - Link clicável para o permalink
  - Audiência (se disponível)
"""

from __future__ import annotations
import pandas as pd
import streamlit as st
from config import THEME, NETWORK_COLORS, SORT_OPTIONS, TOP_N


def _badge(network: str) -> str:
    """Gera o badge HTML colorido da rede social."""
    color = NETWORK_COLORS.get(network, "#888")
    return (
        f'<span style="'
        f'background:{color}22;'         # 22 = ~13% opacity
        f'color:{color};'
        f'border:1px solid {color}55;'
        f'border-radius:6px;'
        f'padding:2px 8px;'
        f'font-size:11px;'
        f'font-weight:600;'
        f'letter-spacing:0.3px;'
        f'">{network}</span>'
    )


def _metric_chip(label: str, value: str) -> str:
    """Gera um chip de métrica (label + valor)."""
    return (
        f'<div style="'
        f'background:{THEME["bg_card2"]};'
        f'border-radius:6px;'
        f'padding:4px 10px;'
        f'text-align:center;'
        f'min-width:60px;'
        f'">'
        f'<div style="color:{THEME["text_muted"]};font-size:10px;margin-bottom:2px">{label}</div>'
        f'<div style="color:{THEME["text_primary"]};font-size:13px;font-weight:600">{value}</div>'
        f'</div>'
    )


def _fmt(value: float, is_pct: bool = False) -> str:
    if is_pct:
        return f"{value:.1f}%"
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value/1_000:.1f}K"
    return f"{int(value)}"


def _post_card(row: pd.Series, rank: int, is_top: bool) -> str:
    """Monta o HTML completo de um card de post."""
    border_color = THEME["accent_green"] if is_top else THEME["accent_red"]
    rank_bg      = THEME["accent_green"] if is_top else THEME["accent_red"]

    # Texto truncado
    text    = str(row.get("outbound_post", ""))
    text    = text[:120] + "…" if len(text) > 120 else text
    text    = text.replace("<", "&lt;").replace(">", "&gt;")  # sanitiza HTML

    network   = str(row.get("social_network", ""))
    permalink = str(row.get("permalink", ""))
    audience  = str(row.get("msft_learn_primary_audience_outbound_message", ""))

    impr    = _fmt(row.get("gdc_impressions_sum", 0))
    er      = _fmt(row.get("ER", 0), is_pct=True)
    aqe     = _fmt(row.get("AQE", 0))
    clicks  = _fmt(row.get("estimated_clicks_sum", 0))
    shares  = _fmt(row.get("post_shares_sum", 0))

    link_html = (
        f'<a href="{permalink}" target="_blank" style="'
        f'color:{THEME["accent_blue"]};'
        f'font-size:11px;'
        f'text-decoration:none;'
        f'">↗ View post</a>'
        if permalink and permalink not in ["", "nan"] else ""
    )

    audience_html = (
        f'<span style="color:{THEME["text_muted"]};font-size:11px">Audience: {audience}</span>'
        if audience and audience not in ["", "nan"] else ""
    )

    chips = "".join([
        _metric_chip("Impr",   impr),
        _metric_chip("ER",     er),
        _metric_chip("AQE",    aqe),
        _metric_chip("Clicks", clicks),
        _metric_chip("Shares", shares),
    ])

    return f"""
    <div style="
        background:{THEME['bg_card']};
        border:1px solid {border_color}44;
        border-left:3px solid {border_color};
        border-radius:10px;
        padding:16px;
        margin-bottom:10px;
        position:relative;
    ">
        <!-- Rank badge -->
        <div style="
            position:absolute;top:12px;right:12px;
            background:{rank_bg};
            color:white;
            border-radius:50%;
            width:22px;height:22px;
            display:flex;align-items:center;justify-content:center;
            font-size:11px;font-weight:700;
        ">{'▲' if is_top else '▼'}{rank}</div>

        <!-- Network badge + audience -->
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
            {_badge(network)}
            {audience_html}
        </div>

        <!-- Post text -->
        <div style="
            color:{THEME['text_primary']};
            font-size:13px;
            line-height:1.5;
            margin-bottom:12px;
        ">{text}</div>

        <!-- Metrics chips -->
        <div style="
            display:flex;
            flex-wrap:wrap;
            gap:6px;
            margin-bottom:10px;
        ">{chips}</div>

        <!-- Link -->
        {link_html}
    </div>
    """


def render_top_bottom(df: pd.DataFrame, sort_by_label: str) -> None:
    """
    Renderiza a seção completa de Top N + Bottom N posts.

    Parâmetros:
      df            → DataFrame filtrado do período
      sort_by_label → label do selectbox (ex: "Total Engagement")
    """
    sort_col = SORT_OPTIONS.get(sort_by_label, "gdc_total_engagements_sum")

    # Garante que AQE existe
    from config import AQE_COLS
    present = [c for c in AQE_COLS if c in df.columns]
    df = df.copy()
    df["AQE"] = df[present].sum(axis=1)

    if df.empty:
        st.info("No posts in the selected period.")
        return

    df_sorted = df.sort_values(sort_col, ascending=False).reset_index(drop=True)
    top    = df_sorted.head(TOP_N)
    bottom = df_sorted.tail(TOP_N).sort_values(sort_col, ascending=True).reset_index(drop=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f'<div style="color:{THEME["accent_green"]};font-weight:700;'
            f'font-size:14px;margin-bottom:12px">▲ TOP {TOP_N} POSTS</div>',
            unsafe_allow_html=True,
        )
        for i, (_, row) in enumerate(top.iterrows(), 1):
            st.markdown(_post_card(row, i, is_top=True), unsafe_allow_html=True)

    with col2:
        st.markdown(
            f'<div style="color:{THEME["accent_red"]};font-weight:700;'
            f'font-size:14px;margin-bottom:12px">▼ BOTTOM {TOP_N} POSTS</div>',
            unsafe_allow_html=True,
        )
        for i, (_, row) in enumerate(bottom.iterrows(), 1):
            st.markdown(_post_card(row, i, is_top=False), unsafe_allow_html=True)
