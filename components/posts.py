from __future__ import annotations
import pandas as pd
import streamlit as st
from config import THEME, NETWORK_COLORS, SORT_OPTIONS, TOP_N, AQE_COLS


def _fmt(value: float, is_pct: bool = False) -> str:
    if is_pct:
        return f"{value:.1f}%"
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value/1_000:.1f}K"
    return f"{int(value)}"


def _post_card(row: pd.Series, rank: int, is_top: bool) -> str:
    border_color = THEME["accent_green"] if is_top else THEME["accent_red"]
    rank_icon    = "▲" if is_top else "▼"

    text      = str(row.get("outbound_post", ""))
    text      = (text[:140] + "…") if len(text) > 140 else text
    text      = text.replace("<", "&lt;").replace(">", "&gt;")

    network   = str(row.get("social_network", ""))
    permalink = str(row.get("permalink", ""))
    net_color = NETWORK_COLORS.get(network, "#888")

    impr    = _fmt(row.get("gdc_impressions_sum", 0))
    eng     = _fmt(row.get("gdc_total_engagements_sum", 0))
    er      = _fmt(row.get("ER", 0), is_pct=True)
    likes   = _fmt(row.get("post_likes_and_reactions_sum", 0))
    comments= _fmt(row.get("post_comments_sum", 0))
    shares  = _fmt(row.get("post_shares_sum", 0))
    clicks  = _fmt(row.get("estimated_clicks_sum", 0))

    link_html = ""
    if permalink and permalink not in ["", "nan"]:
        link_html = (
            f'<a href="{permalink}" target="_blank" style="'
            f'color:{THEME["accent_blue"]};font-size:11px;text-decoration:none;display:inline-block;margin-top:10px;">'
            f'↗ View post</a>'
        )

    def chip(label: str, val: str) -> str:
        return (
            f'<div style="background:{THEME["bg_card2"]};border-radius:6px;'
            f'padding:4px 10px;text-align:center;min-width:56px;">'
            f'<div style="color:{THEME["text_muted"]};font-size:10px;margin-bottom:2px">{label}</div>'
            f'<div style="color:{THEME["text_primary"]};font-size:12px;font-weight:600">{val}</div>'
            f'</div>'
        )

    chips = "".join([
        chip("Impr",    impr),
        chip("Eng",     eng),
        chip("ER",      er),
        chip("Likes",   likes),
        chip("Cmts",    comments),
        chip("Shares",  shares),
        chip("Clicks",  clicks),
    ])

    return (
        f'<div style="background:{THEME["bg_card"]};border:1px solid {border_color}44;'
        f'border-left:3px solid {border_color};border-radius:10px;padding:16px;margin-bottom:10px;">'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
        f'<span style="background:{net_color}22;color:{net_color};border:1px solid {net_color}55;'
        f'border-radius:6px;padding:2px 8px;font-size:11px;font-weight:600;">{network}</span>'
        f'<span style="color:{THEME["text_muted"]};font-size:11px;margin-left:auto;">#{rank} {rank_icon}</span>'
        f'</div>'
        f'<div style="color:{THEME["text_primary"]};font-size:13px;line-height:1.5;margin-bottom:12px;">{text}</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:6px;">{chips}</div>'
        f'{link_html}'
        f'</div>'
    )


def render_top_bottom(df: pd.DataFrame, sort_by_label: str) -> None:
    sort_col = SORT_OPTIONS.get(sort_by_label, "gdc_total_engagements_sum")

    present = [c for c in AQE_COLS if c in df.columns]
    df = df.copy()
    df["AQE"] = df[present].sum(axis=1)

    if "ER" not in df.columns:
        if "gdc_impressions_sum" in df.columns and "gdc_total_engagements_sum" in df.columns:
            df["ER"] = (df["gdc_total_engagements_sum"] / df["gdc_impressions_sum"].replace(0, 1)) * 100
        else:
            df["ER"] = 0.0

    if df.empty:
        st.info("No posts in the selected period.")
        return

    df_sorted = df.sort_values(sort_col, ascending=False).reset_index(drop=True)
    top    = df_sorted.head(TOP_N)
    bottom = df_sorted.tail(TOP_N).sort_values(sort_col, ascending=True).reset_index(drop=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f'<div style="color:{THEME["accent_green"]};font-weight:700;font-size:14px;margin-bottom:12px">▲ TOP {TOP_N} POSTS</div>',
            unsafe_allow_html=True,
        )
        for i, (_, row) in enumerate(top.iterrows(), 1):
            st.markdown(_post_card(row, i, is_top=True), unsafe_allow_html=True)

    with col2:
        st.markdown(
            f'<div style="color:{THEME["accent_red"]};font-weight:700;font-size:14px;margin-bottom:12px">▼ BOTTOM {TOP_N} POSTS</div>',
            unsafe_allow_html=True,
        )
        for i, (_, row) in enumerate(bottom.iterrows(), 1):
            st.markdown(_post_card(row, i, is_top=False), unsafe_allow_html=True)
