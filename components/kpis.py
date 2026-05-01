"""
components/kpis.py
==================
Renderiza os 4 KPI cards do topo:
  Posts | Impressions | ER | AQE/post

Cada card mostra:
  - Valor do período atual
  - Delta (▲▼ %) vs período anterior

CONCEITO — por que delta é importante:
  Um número absoluto não diz se a semana foi boa ou ruim.
  O delta contextualiza: 50K impressões é ótimo se semana passada
  foram 20K, é péssimo se foram 200K.
"""

from __future__ import annotations
import pandas as pd
import streamlit as st
from config import THEME, AQE_COLS, NETWORK_COLORS


def _safe_delta(current: float, previous: float) -> tuple[float | None, str]:
    """
    Calcula o delta percentual e retorna (valor, cor_css).
    Retorna (None, "") se não houver período anterior.
    """
    if previous == 0:
        return None, ""
    delta = ((current - previous) / previous) * 100
    color = THEME["accent_green"] if delta >= 0 else THEME["accent_red"]
    return delta, color


def _fmt(value: float, is_pct: bool = False) -> str:
    """Formata número: 1.234.567 ou 12.3%"""
    if is_pct:
        return f"{value:.1f}%"
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value/1_000:.1f}K"
    return f"{value:.0f}"


def render_kpis(df_current: pd.DataFrame, df_previous: pd.DataFrame) -> None:
    """
    Renderiza os 4 KPI cards em colunas lado a lado.

    Parâmetros:
      df_current  → posts do período selecionado
      df_previous → posts do período anterior (mesmo tamanho)
    """

    # ── Calcula métricas do período atual ──────────────────────────────────
    posts_cur  = len(df_current)
    impr_cur   = df_current["gdc_impressions_sum"].sum()
    eng_cur    = df_current["gdc_total_engagements_sum"].sum()
    er_cur     = (eng_cur / impr_cur * 100) if impr_cur > 0 else 0

    # ER w/o swipes — usa engagement_wo_swipes calculado no loader
    # (LinkedIn Document/Pdf: likes+comments+shares+clicks; outros: total engagement)
    eng_wo_cur     = df_current["engagement_wo_swipes"].sum() if "engagement_wo_swipes" in df_current.columns else eng_cur
    er_wo_swipes_cur = (eng_wo_cur / impr_cur * 100) if impr_cur > 0 else 0

    present    = [c for c in AQE_COLS if c in df_current.columns]
    aqe_total  = df_current[present].sum().sum()
    aqe_cur    = aqe_total / posts_cur if posts_cur > 0 else 0

    # ── Calcula métricas do período anterior ───────────────────────────────
    posts_prev = len(df_previous)
    impr_prev  = df_previous["gdc_impressions_sum"].sum()
    eng_prev   = df_previous["gdc_total_engagements_sum"].sum()
    er_prev    = (eng_prev / impr_prev * 100) if impr_prev > 0 else 0

    eng_wo_prev      = df_previous["engagement_wo_swipes"].sum() if "engagement_wo_swipes" in df_previous.columns else eng_prev
    er_wo_swipes_prev = (eng_wo_prev / impr_prev * 100) if impr_prev > 0 else 0

    present_p  = [c for c in AQE_COLS if c in df_previous.columns]
    aqe_prev   = (df_previous[present_p].sum().sum() / posts_prev
                  if posts_prev > 0 else 0)

    # ── Configuração dos cards ─────────────────────────────────────────────
    cards = [
        {
            "label":    "Posts",
            "value":    _fmt(posts_cur),
            "raw_cur":  posts_cur,
            "raw_prev": posts_prev,
            "is_pct":   False,
        },
        {
            "label":    "Impressions",
            "value":    _fmt(impr_cur),
            "raw_cur":  impr_cur,
            "raw_prev": impr_prev,
            "is_pct":   False,
        },
        {
            "label":       "Eng. Rate",
            # Exibe ER / ER w/o swipes* no card
            "value":       f"{_fmt(er_cur, is_pct=True)} / {_fmt(er_wo_swipes_cur, is_pct=True)}*",
            "er_note":     "* w/o swipes",   # nota exibida abaixo do valor
            "raw_cur":     er_cur,
            "raw_prev":    er_prev,
            "is_pct":      True,
            "suffix":      "pp",    # pontos percentuais, não %
        },
        {
            "label":    "AQE / post",
            "value":    _fmt(aqe_cur),
            "raw_cur":  aqe_cur,
            "raw_prev": aqe_prev,
            "is_pct":   False,
            "tooltip":  "AQE = Comments + Shares + Clicks",
        },
    ]

    # ── CSS para tooltip hover do ⓘ ──────────────────────────────────────
    st.markdown(f"""
    <style>
      .kpi-tooltip-wrap {{
          position: relative;
          display: inline-block;
          cursor: help;
          color: {THEME['text_muted']};
      }}
      .kpi-tooltip-box {{
          display: none;
          position: absolute;
          bottom: 130%;
          left: 50%;
          transform: translateX(-50%);
          background: {THEME['bg_card2']};
          border: 1px solid {THEME['border']};
          border-radius: 6px;
          padding: 6px 10px;
          white-space: nowrap;
          font-size: 11px;
          color: {THEME['text_secondary']};
          z-index: 200;
          pointer-events: none;
      }}
      .kpi-tooltip-wrap:hover .kpi-tooltip-box {{
          display: block;
      }}
    </style>
    """, unsafe_allow_html=True)

    # ── Renderiza ──────────────────────────────────────────────────────────
    cols = st.columns(4)
    for col, card in zip(cols, cards):
        with col:
            # Tooltip no label (ⓘ) com hover box
            tooltip = card.get("tooltip", "")
            if tooltip:
                label_html = (
                    f'{card["label"]} '
                    f'<span class="kpi-tooltip-wrap">ⓘ'
                    f'<span class="kpi-tooltip-box">{tooltip}</span>'
                    f'</span>'
                )
            else:
                label_html = card["label"]

            # Nota extra (ex: "*w/o swipes" para o card de ER)
            er_note = card.get("er_note", "")
            er_note_html = (
                f'<div style="color:{THEME["text_muted"]};font-size:10px;margin-top:4px">'
                f'{er_note}</div>'
                if er_note
                else f'<div style="font-size:10px;margin-top:4px">&nbsp;</div>'
            )

            st.markdown(
                f"""
                <div style="
                    background:{THEME['bg_card']};
                    border:1px solid {THEME['border']};
                    border-radius:12px;
                    padding:20px 24px;
                    margin-bottom:8px;
                    min-height:120px;
                    box-sizing:border-box;
                ">
                    <div style="
                        color:{THEME['text_secondary']};
                        font-size:13px;
                        font-weight:500;
                        letter-spacing:0.5px;
                        margin-bottom:8px;
                    ">{label_html}</div>
                    <div style="
                        color:{THEME['text_primary']};
                        font-size:28px;
                        font-weight:700;
                        line-height:1;
                        margin-bottom:4px;
                    ">{card['value']}</div>
                    {er_note_html}
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# FOLLOWERS CARD
# ---------------------------------------------------------------------------

# Ordem de exibição e ícones simples por rede
_FOLLOWER_NET_ORDER = ["LinkedIn", "X", "Instagram", "TikTok", "Threads"]
_FOLLOWER_NET_LABEL = {
    "LinkedIn":  "LinkedIn",
    "X":         "X (Twitter)",
    "Instagram": "Instagram",
    "TikTok":    "TikTok",
    "Threads":   "Threads",
}


def render_followers_card(
    df_followers: pd.DataFrame,
    date_end: pd.Timestamp,
) -> None:
    """
    Exibe um card de seguidores por rede com o valor mais próximo (<=) a date_end.
    """
    from data.loader import get_followers_at

    snap = get_followers_at(df_followers, date_end)

    if snap.empty:
        st.info("No follower data available for the selected period.")
        return

    # Data de referência (máxima entre as redes disponíveis)
    ref_date = snap["date"].max()
    ref_label = pd.to_datetime(ref_date).strftime("%b %d, %Y")

    # Monta o HTML de cada rede
    net_items = ""
    for net in _FOLLOWER_NET_ORDER:
        row = snap[snap["network"] == net]
        if row.empty:
            continue
        followers = int(row.iloc[0]["followers"])
        color     = NETWORK_COLORS.get(net, THEME["text_secondary"])
        label     = _FOLLOWER_NET_LABEL.get(net, net)
        fmt       = _fmt(followers)
        net_items += (
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">'
            f'  <span style="width:8px;height:8px;border-radius:50%;'
            f'background:{color};display:inline-block;flex-shrink:0"></span>'
            f'  <span style="color:{THEME["text_secondary"]};font-size:12px;'
            f'flex:1">{label}</span>'
            f'  <span style="color:{THEME["text_primary"]};font-size:14px;'
            f'font-weight:600">{fmt}</span>'
            f'</div>'
        )

    st.markdown(
        f"""
        <div style="
            background:{THEME['bg_card']};
            border:1px solid {THEME['border']};
            border-radius:12px;
            padding:16px 20px;
            margin-bottom:8px;
        ">
            <div style="
                color:{THEME['text_secondary']};
                font-size:13px;
                font-weight:500;
                letter-spacing:0.5px;
                margin-bottom:12px;
                display:flex;
                justify-content:space-between;
                align-items:center;
            ">
                <span>Followers</span>
                <span style="color:{THEME['text_muted']};font-size:10px">as of {ref_label}</span>
            </div>
            {net_items}
        </div>
        """,
        unsafe_allow_html=True,
    )
