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
            "value":       f"{_fmt(er_cur, is_pct=True)} / {_fmt(er_wo_swipes_cur, is_pct=True)}",
            "er_note":     "*w/o swipes",   # nota exibida abaixo do valor
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
            "tooltip":  "Avg Qualified Engagement = comments + shares + clicks",
        },
    ]

    # ── Renderiza ──────────────────────────────────────────────────────────
    cols = st.columns(4)
    for col, card in zip(cols, cards):
        # Variação "vs prev period" desativada.
        # Para reativar: substitua o bloco abaixo por:
        #   delta_val, delta_color = _safe_delta(card["raw_cur"], card["raw_prev"])
        #   delta_str = f"+{delta_val:.1f}%" if delta_val is not None else ""

        with col:
            # Tooltip no label (ⓘ) se existir
            tooltip = card.get("tooltip", "")
            label_html = (
                f'{card["label"]} <span title="{tooltip}" '
                f'style="cursor:help;color:{THEME["text_muted"]}">ⓘ</span>'
                if tooltip else card["label"]
            )

            # Nota extra (ex: "*w/o swipes" para o card de ER)
            er_note = card.get("er_note", "")
            er_note_html = (
                f'<div style="color:{THEME["text_muted"]};font-size:10px;margin-top:4px">'
                f'{er_note}</div>'
                if er_note else ""
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
