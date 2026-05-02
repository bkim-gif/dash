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


def render_kpis(
    df_current: pd.DataFrame,
    df_previous: pd.DataFrame,
    df_organic: "pd.DataFrame | None" = None,
    df_prev_organic: "pd.DataFrame | None" = None,
) -> None:
    """
    Renderiza os 4 KPI cards em colunas lado a lado.

    Parâmetros:
      df_current      → todos os posts do período (inclui boosted) — usado p/ contagem de Posts
      df_previous     → todos os posts do período anterior — usado p/ delta de Posts
      df_organic      → posts sem boosted — usado p/ Impressions, ER, AQE
      df_prev_organic → posts sem boosted do período anterior — usado p/ deltas de Impressions/ER/AQE
    """
    # Posts: conta todos (incluindo boosted)
    posts_cur  = len(df_current)
    posts_prev = len(df_previous)

    # Métricas orgânicas: usa df_organic se fornecido, senão fallback para df_current
    _cur  = df_organic  if df_organic  is not None else df_current
    _prev = df_prev_organic if df_prev_organic is not None else df_previous

    # ── Calcula métricas do período atual ──────────────────────────────────
    impr_cur   = _cur["gdc_impressions_sum"].sum()
    eng_cur    = _cur["gdc_total_engagements_sum"].sum()
    er_cur     = (eng_cur / impr_cur * 100) if impr_cur > 0 else 0

    eng_wo_cur       = _cur["engagement_wo_swipes"].sum() if "engagement_wo_swipes" in _cur.columns else eng_cur
    er_wo_swipes_cur = (eng_wo_cur / impr_cur * 100) if impr_cur > 0 else 0

    n_org_cur  = len(_cur)
    present    = [c for c in AQE_COLS if c in _cur.columns]
    aqe_total  = _cur[present].sum().sum()
    aqe_cur    = aqe_total / n_org_cur if n_org_cur > 0 else 0

    # ── Calcula métricas do período anterior ───────────────────────────────
    impr_prev  = _prev["gdc_impressions_sum"].sum()
    eng_prev   = _prev["gdc_total_engagements_sum"].sum()
    er_prev    = (eng_prev / impr_prev * 100) if impr_prev > 0 else 0

    eng_wo_prev       = _prev["engagement_wo_swipes"].sum() if "engagement_wo_swipes" in _prev.columns else eng_prev
    er_wo_swipes_prev = (eng_wo_prev / impr_prev * 100) if impr_prev > 0 else 0

    n_org_prev = len(_prev)
    present_p  = [c for c in AQE_COLS if c in _prev.columns]
    aqe_prev   = (_prev[present_p].sum().sum() / n_org_prev if n_org_prev > 0 else 0)

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
            # Exibe ER / ER w/o swipes no card
            "value":       f"{_fmt(er_cur, is_pct=True)} / {_fmt(er_wo_swipes_cur, is_pct=True)}",
            "er_note":     "w/o swipes",   # exibido como ⓘ com tooltip
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

            # Nota extra (ⓘ com tooltip "w/o swipes" para o card de ER)
            er_note = card.get("er_note", "")
            er_note_html = (
                f'<div style="color:{THEME["text_muted"]};font-size:10px;margin-top:4px">'
                f'<span class="kpi-tooltip-wrap">ⓘ'
                f'<span class="kpi-tooltip-box">{er_note}</span>'
                f'</span></div>'
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
                        font-size:10px;
                        font-weight:500;
                        text-transform:uppercase;
                        letter-spacing:1.2px;
                        margin-bottom:8px;
                    ">{label_html}</div>
                    <div style="
                        color:{THEME['text_primary']};
                        font-size:28px;
                        font-weight:700;
                        line-height:1;
                        margin-bottom:4px;
                        font-variant-numeric:tabular-nums;
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
    selected_network: str = "ALL",
) -> None:
    """
    Sempre exibe UM card de seguidores.
    ALL  → soma de todas as redes (total)
    rede → valor daquela rede em destaque.
    """
    from data.loader import get_followers_at

    snap = get_followers_at(df_followers, date_end)

    if snap.empty:
        st.info("No follower data available for the selected period.")
        return

    ref_date  = snap["date"].max()
    ref_label = pd.to_datetime(ref_date).strftime("%b %d, %Y")

    if selected_network == "ALL":
        followers = int(snap[snap["network"].isin(_FOLLOWER_NET_ORDER)]["followers"].sum())
        color     = THEME["text_primary"]
        net_label = "All Platforms"
    else:
        row = snap[snap["network"] == selected_network]
        if row.empty:
            return
        followers = int(row.iloc[0]["followers"])
        color     = NETWORK_COLORS.get(selected_network, THEME["text_secondary"])
        net_label = _FOLLOWER_NET_LABEL.get(selected_network, selected_network)

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
                font-size:10px;font-weight:500;
                text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px;
                display:flex;justify-content:space-between;align-items:center;
            ">
                <span>Followers · {net_label}</span>
                <span style="color:{THEME['text_muted']};font-size:10px;text-transform:none;letter-spacing:0">as of {ref_label}</span>
            </div>
            <div style="
                color:{color};font-size:28px;font-weight:700;line-height:1;
                font-variant-numeric:tabular-nums;
            ">{_fmt(followers)}</div>
            <div style="font-size:10px;margin-top:4px">&nbsp;</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# COMMENTS CARD
# ---------------------------------------------------------------------------

def render_comments_card(df_organic: pd.DataFrame) -> None:
    """
    Card com o total de comentários do período (usa post_comments_sum do df orgânico).
    """
    col = "post_comments_sum"
    total = int(df_organic[col].sum()) if col in df_organic.columns else 0

    st.markdown(
        f"""
        <div style="
            background:{THEME['bg_card']};
            border:1px solid {THEME['border']};
            border-radius:12px;
            padding:20px 24px;
            margin-bottom:8px;
            height:100%;
            min-height:300px;
            box-sizing:border-box;
            display:flex;
            flex-direction:column;
            justify-content:flex-start;
        ">
            <div style="
                color:{THEME['text_secondary']};
                font-size:10px;font-weight:500;
                text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px;
            ">Comments</div>
            <div style="
                color:{THEME['text_primary']};font-size:28px;font-weight:700;
                line-height:1;font-variant-numeric:tabular-nums;
            ">{_fmt(total)}</div>
            <div style="font-size:10px;margin-top:4px">&nbsp;</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
