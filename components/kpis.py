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
from config import THEME, AQE_COLS


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

    present    = [c for c in AQE_COLS if c in df_current.columns]
    aqe_total  = df_current[present].sum().sum()
    aqe_cur    = aqe_total / posts_cur if posts_cur > 0 else 0

    # ── Calcula métricas do período anterior ───────────────────────────────
    posts_prev = len(df_previous)
    impr_prev  = df_previous["gdc_impressions_sum"].sum()
    eng_prev   = df_previous["gdc_total_engagements_sum"].sum()
    er_prev    = (eng_prev / impr_prev * 100) if impr_prev > 0 else 0

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
            "label":    "Eng. Rate",
            "value":    _fmt(er_cur, is_pct=True),
            "raw_cur":  er_cur,
            "raw_prev": er_prev,
            "is_pct":   True,
            "suffix":   "pp",    # pontos percentuais, não %
        },
        {
            "label":    "AQE / post",
            "value":    _fmt(aqe_cur),
            "raw_cur":  aqe_cur,
            "raw_prev": aqe_prev,
            "is_pct":   False,
            "tooltip":  "Avg Qualified Engagement = comments + shares + clicks",
        },
    ]

    # ── Renderiza ──────────────────────────────────────────────────────────
    cols = st.columns(4)
    for col, card in zip(cols, cards):
        delta_val, delta_color = _safe_delta(card["raw_cur"], card["raw_prev"])

        # Delta: pp para ER, % para o resto
        if delta_val is not None:
            suffix  = card.get("suffix", "%")
            sign    = "+" if delta_val >= 0 else ""
            delta_str = f"{sign}{delta_val:.1f}{suffix}"
        else:
            delta_str = "No prev. data"
            delta_color = THEME["text_muted"]

        with col:
            # Tooltip no label (ⓘ) se existir
            tooltip = card.get("tooltip", "")
            label_html = (
                f'{card["label"]} <span title="{tooltip}" '
                f'style="cursor:help;color:{THEME["text_muted"]}">ⓘ</span>'
                if tooltip else card["label"]
            )

            st.markdown(
                f"""
                <div style="
                    background:{THEME['bg_card']};
                    border:1px solid {THEME['border']};
                    border-radius:12px;
                    padding:20px 24px;
                    margin-bottom:8px;
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
                        font-size:32px;
                        font-weight:700;
                        line-height:1;
                        margin-bottom:10px;
                    ">{card['value']}</div>
                    <div style="
                        color:{delta_color};
                        font-size:13px;
                        font-weight:600;
                    ">{delta_str} <span style="color:{THEME['text_muted']};font-weight:400">vs prev period</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
