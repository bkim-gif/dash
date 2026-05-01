"""
components/charts.py
====================
Todos os gráficos do dashboard usando Plotly.

Por que Plotly?
  - Interativo (hover, zoom, pan) sem nenhum JS extra
  - Dark theme nativo
  - Exporta como PNG com um clique
  - Integra perfeitamente com Streamlit via st.plotly_chart()

ESTRUTURA:
  chart_timeline()     → linha do tempo semanal/mensal
  chart_by_network()   → barras agrupadas por rede
  chart_pillar_donut() → donut de distribuição por pilar
  chart_pillar_radar() → radar current vs target
  chart_fy_pacing()    → pacing do target anual (25M)
"""

from __future__ import annotations
import math
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from config import THEME, NETWORK_COLORS, PILLAR_TARGETS, FY_TARGET, FY_POSTS_TARGET


# ---------------------------------------------------------------------------
# HELPER — layout base compartilhado por todos os gráficos
# ---------------------------------------------------------------------------

def _base_layout(**overrides) -> dict:
    """
    Retorna o dicionário de layout padrão do tema escuro.
    Aceita overrides para personalizar por gráfico.
    """
    base = dict(
        paper_bgcolor = "rgba(0,0,0,0)",   # transparente (fundo do card)
        plot_bgcolor  = "rgba(0,0,0,0)",
        font          = dict(color=THEME["text_primary"], family="Inter, sans-serif"),
        margin        = dict(l=8, r=8, t=36, b=8),
        legend        = dict(
            bgcolor     = "rgba(0,0,0,0)",
            bordercolor = THEME["border"],
            font        = dict(color=THEME["text_secondary"], size=11),
        ),
        xaxis = dict(
            gridcolor    = THEME["grid_line"],
            linecolor    = THEME["border"],
            tickcolor    = THEME["border"],
            tickfont     = dict(color=THEME["text_secondary"], size=11),
        ),
        yaxis = dict(
            gridcolor    = THEME["grid_line"],
            linecolor    = THEME["border"],
            tickcolor    = THEME["border"],
            tickfont     = dict(color=THEME["text_secondary"], size=11),
            zerolinecolor= THEME["border"],
        ),
        hoverlabel = dict(
            bgcolor   = THEME["bg_card2"],
            bordercolor = THEME["border"],
            font      = dict(color=THEME["text_primary"]),
        ),
    )
    base.update(overrides)
    return base


def _fmt_axis(val, suffix=""):
    """Formata eixo Y: 1.5M, 500K, 250"""
    if val >= 1_000_000: return f"{val/1_000_000:.1f}M{suffix}"
    if val >= 1_000:     return f"{val/1_000:.0f}K{suffix}"
    return f"{val:.0f}{suffix}"


# ---------------------------------------------------------------------------
# 1. LINHA DO TEMPO
# ---------------------------------------------------------------------------

def chart_timeline(
    df: pd.DataFrame,
    granularity: str = "Weekly",
    date_start=None,
    date_end=None,
) -> go.Figure:
    """
    Linha do tempo com Impressions (barras) e ER w/o swipes (linha suave, eixo Y2).
    date_start / date_end são usados para gerar todos os períodos do range,
    mesmo aqueles sem posts (barras zeradas), cobrindo o período completo.
    """
    period_col = "week" if granularity == "Weekly" else "month"

    agg = df.groupby(period_col).agg(
        impressions       = ("gdc_impressions_sum",    "sum"),
        engagement_wo_swp = ("engagement_wo_swipes",   "sum") if "engagement_wo_swipes" in df.columns
                            else ("gdc_total_engagements_sum", "sum"),
        posts             = ("outbound_post",           "count"),
    ).reset_index()

    # Preenche todos os períodos do range selecionado (sem lacunas)
    if date_start is not None and date_end is not None:
        freq = "7D" if granularity == "Weekly" else "MS"
        _start = pd.to_datetime(date_start)
        _end   = pd.to_datetime(date_end)
        # Alinha ao primeiro período real igual ou anterior a date_start
        if not agg.empty:
            _start = min(_start, agg[period_col].min())
        full_range = pd.date_range(start=_start, end=_end, freq=freq)
        full_df = pd.DataFrame({period_col: full_range})
        agg = full_df.merge(agg, on=period_col, how="left").fillna(0)

    # ER w/o swipes por período (sum engagement / sum impressions * 100)
    agg["er_wo_swipes"] = (
        agg["engagement_wo_swp"]
        / agg["impressions"].replace(0, float("nan"))
        * 100
    ).fillna(0).round(2)

    agg["period_label"] = pd.to_datetime(agg[period_col]).dt.strftime(
        "%b %d" if granularity == "Weekly" else "%b %Y"
    )

    fig = go.Figure()

    # Barras — Impressions (eixo Y principal)
    fig.add_trace(go.Bar(
        x             = agg["period_label"],
        y             = agg["impressions"],
        name          = "Impressions",
        marker_color  = THEME["accent_purple"],
        opacity       = 0.85,
        hovertemplate = "<b>%{x}</b><br>Impressions: %{y:.2s}<extra></extra>",
    ))

    # Linha suave — ER w/o swipes (eixo Y secundário)
    fig.add_trace(go.Scatter(
        x             = agg["period_label"],
        y             = agg["er_wo_swipes"],
        name          = "ER w/o swipes",
        mode          = "lines+markers",
        line          = dict(color=THEME["accent_blue"], width=2.5,
                             shape="spline", smoothing=1.3),
        marker        = dict(size=9, symbol="diamond", color=THEME["accent_blue"]),
        yaxis         = "y2",
        hovertemplate = "<b>%{x}</b><br>ER w/o swipes: %{y:.2f}%<extra></extra>",
    ))

    layout = _base_layout(
        title   = dict(text=f"Performance Over Time — {granularity}", font=dict(size=14)),
        barmode = "group",
        yaxis   = dict(tickformat=".2s"),
        yaxis2  = dict(
            overlaying   = "y",
            side         = "right",
            gridcolor    = "rgba(0,0,0,0)",
            tickfont     = dict(color=THEME["accent_blue"], size=10),
            ticksuffix   = "%",
            showgrid     = False,
        ),
    )
    fig.update_layout(layout)

    fig.update_layout(
        legend=dict(
            bgcolor     = "rgba(15,25,35,0.80)",
            bordercolor = THEME["border"],
            borderwidth = 1,
            font        = dict(color=THEME["text_primary"], size=13),
            x           = 0.01,
            y           = 0.97,
            xanchor     = "left",
            yanchor     = "top",
            orientation = "v",
        )
    )
    return fig


# ---------------------------------------------------------------------------
# 2. BARRAS POR REDE SOCIAL
# ---------------------------------------------------------------------------

def chart_by_network(df: pd.DataFrame) -> go.Figure:
    """
    Barras horizontais mostrando Impressions e AQE por rede.
    Horizontal porque os nomes das redes ficam mais legíveis.
    """
    from config import AQE_COLS

    present = [c for c in AQE_COLS if c in df.columns]
    df = df.copy()
    df["AQE"] = df[present].sum(axis=1)

    agg = df.groupby("social_network").agg(
        impressions = ("gdc_impressions_sum", "sum"),
        aqe_total   = ("AQE",                 "sum"),
        posts       = ("outbound_post",        "count"),
    ).reset_index()

    agg["aqe_per_post"] = agg["aqe_total"] / agg["posts"].replace(0, 1)
    agg = agg.sort_values("impressions", ascending=True)

    colors = [NETWORK_COLORS.get(n, THEME["accent_purple"]) for n in agg["social_network"]]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y           = agg["social_network"],
        x           = agg["impressions"],
        orientation = "h",
        name        = "Impressions",
        marker_color= colors,
        opacity     = 0.9,
        hovertemplate = "<b>%{y}</b><br>Impressions: %{x:,.0f}<extra></extra>",
    ))

    layout = _base_layout(
        title  = dict(text="Impressions by Network", font=dict(size=14)),
        xaxis  = dict(title="", tickformat=","),
        yaxis  = dict(title=""),
        height = 300,
    )
    fig.update_layout(layout)
    return fig


def chart_er_by_network(df: pd.DataFrame) -> go.Figure:
    """
    Barras de ER médio por rede — complementa o gráfico de impressões.
    """
    agg = df.groupby("social_network").agg(
        impressions = ("gdc_impressions_sum",       "sum"),
        engagement  = ("gdc_total_engagements_sum", "sum"),
    ).reset_index()

    agg["er"] = (agg["engagement"] / agg["impressions"].replace(0, 1) * 100).round(2)
    agg = agg.sort_values("er", ascending=True)

    colors = [NETWORK_COLORS.get(n, THEME["accent_purple"]) for n in agg["social_network"]]

    fig = go.Figure(go.Bar(
        y           = agg["social_network"],
        x           = agg["er"],
        orientation = "h",
        marker_color= colors,
        text        = agg["er"].apply(lambda v: f"{v:.1f}%"),
        textposition= "outside",
        textfont    = dict(color=THEME["text_primary"], size=11),
        hovertemplate = "<b>%{y}</b><br>ER: %{x:.2f}%<extra></extra>",
    ))

    layout = _base_layout(
        title  = dict(text="Engagement Rate by Network", font=dict(size=14)),
        xaxis  = dict(title="", ticksuffix="%"),
        yaxis  = dict(title=""),
        height = 300,
        showlegend = False,
    )
    fig.update_layout(layout)
    return fig


# ---------------------------------------------------------------------------
# 3. DONUT — DISTRIBUIÇÃO POR PILAR
# ---------------------------------------------------------------------------

def chart_pillar_donut(df: pd.DataFrame) -> go.Figure:
    """
    Donut mostrando % de posts por pilar.
    Remove 'Unknown' da visualização para não poluir.
    """
    agg = (
        df[df["Pillars"] != "Unknown"]
        .groupby("Pillars")
        .size()
        .reset_index(name="posts")
    )

    if agg.empty:
        # Gráfico vazio com mensagem
        fig = go.Figure()
        fig.add_annotation(
            text="No pillar data for this period",
            xref="paper", yref="paper", x=0.5, y=0.5,
            font=dict(color=THEME["text_muted"], size=13),
            showarrow=False,
        )
        fig.update_layout(_base_layout(height=280))
        return fig

    pillar_colors = [
        "#9B72E8", "#50E6FF", "#FFB900", "#54D46A", "#FF4D6A"
    ]

    fig = go.Figure(go.Pie(
        labels       = agg["Pillars"],
        values       = agg["posts"],
        hole         = 0.55,
        marker_colors= pillar_colors[:len(agg)],
        textinfo     = "percent",
        textfont     = dict(size=11, color="white"),
        hovertemplate= "<b>%{label}</b><br>Posts: %{value}<br>%{percent}<extra></extra>",
    ))

    fig.update_layout(_base_layout(
        title      = dict(text="Posts by Pillar", font=dict(size=14)),
        height     = 280,
        showlegend = True,
        legend     = dict(orientation="v", x=1.0, y=0.5),
    ))
    return fig


# ---------------------------------------------------------------------------
# 4. RADAR — CURRENT vs TARGET por PILAR
# ---------------------------------------------------------------------------

def chart_pillar_radar(df: pd.DataFrame) -> go.Figure:
    """
    Radar chart replicando o gráfico do relatório DOJO.
    Current: % de posts em cada pilar no período selecionado
    Target:  valores do playbook (config.py → PILLAR_TARGETS)

    Cores idênticas ao script R:
      Current → #50E6FF  |  Target → #FFB900
    """
    pillars = list(PILLAR_TARGETS.keys())
    targets = list(PILLAR_TARGETS.values())

    # Calcula distribuição atual (sem Unknown)
    df_p = df[df["Pillars"] != "Unknown"]
    total = len(df_p)

    if total == 0:
        current = [0.0] * len(pillars)
    else:
        counts  = df_p["Pillars"].value_counts()
        current = [(counts.get(p, 0) / total * 100) for p in pillars]

    # Fecha o polígono repetindo o primeiro ponto
    pillars_c = pillars + [pillars[0]]
    current_c = current + [current[0]]
    targets_c = targets + [targets[0]]

    fig = go.Figure()

    # Target
    fig.add_trace(go.Scatterpolar(
        r           = targets_c,
        theta       = pillars_c,
        fill        = "toself",
        fillcolor   = "rgba(255,185,0,0.07)",
        line        = dict(color=THEME["accent_yellow"], width=2, dash="dash"),
        name        = "Target (Playbook)",
        hovertemplate = "<b>%{theta}</b><br>Target: %{r:.0f}%<extra></extra>",
    ))

    # Current
    fig.add_trace(go.Scatterpolar(
        r           = current_c,
        theta       = pillars_c,
        fill        = "toself",
        fillcolor   = "rgba(80,230,255,0.20)",
        line        = dict(color=THEME["accent_blue"], width=2),
        name        = "Current Period",
        hovertemplate = "<b>%{theta}</b><br>Current: %{r:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        polar = dict(
            bgcolor    = "rgba(0,0,0,0)",
            radialaxis = dict(
                visible    = True,
                range      = [0, 50],
                ticksuffix = "%",
                tickfont   = dict(color=THEME["text_muted"], size=9),
                gridcolor  = THEME["grid_line"],
                linecolor  = THEME["border"],
            ),
            angularaxis = dict(
                tickfont  = dict(color=THEME["text_primary"], size=12),
                linecolor = THEME["border"],
                gridcolor = THEME["grid_line"],
            ),
        ),
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
        font          = dict(color=THEME["text_primary"]),
        title         = dict(text="Pillar Distribution vs Target", font=dict(size=14)),
        legend        = dict(
            bgcolor     = "rgba(0,0,0,0)",
            font        = dict(color=THEME["text_secondary"], size=11),
            orientation = "h",
            y           = -0.15,
        ),
        margin = dict(l=40, r=40, t=50, b=40),
        height = 380,
    )
    return fig


# ---------------------------------------------------------------------------
# 5. FY PACING
# ---------------------------------------------------------------------------

def chart_fy_pacing(monthly_df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de pacing do target anual (25M impressões).
    Replicando o Slide 3 do relatório semanal.

    Mostra 3 séries:
      🟢 Impressions Delivered  (barras verdes)
      🟫 Required Monthly Pace  (barras cinzas — meta mensal necessária)
      🟣 Remaining Target       (linha roxa — quanto falta)
    """
    from config import FY_START, FY_END
    import numpy as np

    # Gera todos os meses do FY (Aug 25 → Jul 26)
    all_months = pd.date_range(FY_START, FY_END, freq="MS")
    n_months   = len(all_months)

    # Pace mensal necessário para bater 25M
    monthly_pace = FY_TARGET / n_months

    # Merge com dados reais
    monthly_df = monthly_df.copy()
    monthly_df["month_dt"] = pd.to_datetime(monthly_df["month_dt"])

    full = pd.DataFrame({"month_dt": all_months})
    full = full.merge(monthly_df[["month_dt", "impressions"]], on="month_dt", how="left")
    full["impressions"] = full["impressions"].fillna(0)

    # Remaining target = 25M - cumsum das impressões reais
    full["cumulative"]  = full["impressions"].cumsum()
    full["remaining"]   = (FY_TARGET - full["cumulative"]).clip(lower=0)
    full["pace"]        = monthly_pace
    full["month_label"] = full["month_dt"].dt.strftime("%b").str.upper()

    # Cor das barras: verde se bateu o pace, vermelho se não
    bar_colors = [
        THEME["accent_green"] if imp >= monthly_pace else THEME["accent_red"]
        for imp in full["impressions"]
    ]

    fig = go.Figure()

    # Barras de impressões entregues
    fig.add_trace(go.Bar(
        x           = full["month_label"],
        y           = full["impressions"],
        name        = "Impressions Delivered",
        marker_color= bar_colors,
        opacity     = 0.9,
        hovertemplate = "<b>%{x}</b><br>Delivered: %{y:.2s}<extra></extra>",
    ))

    # Barras do pace necessário (transparente, como referência)
    fig.add_trace(go.Bar(
        x           = full["month_label"],
        y           = full["pace"],
        name        = "Required Monthly Pace",
        marker_color= THEME["text_muted"],
        opacity     = 0.3,
        hovertemplate = "<b>%{x}</b><br>Required pace: %{y:.2s}<extra></extra>",
    ))

    # Linha do target restante (eixo Y secundário)
    fig.add_trace(go.Scatter(
        x           = full["month_label"],
        y           = full["remaining"],
        name        = "Remaining Target",
        mode        = "lines+markers",
        line        = dict(color=THEME["accent_purple"], width=2.5),
        marker      = dict(size=5),
        yaxis       = "y2",
        hovertemplate = "<b>%{x}</b><br>Remaining: %{y:.2s}<extra></extra>",
    ))

    layout = _base_layout(
        title    = dict(text="FY 2026 Pacing — Organic Impressions", font=dict(size=14)),
        barmode  = "overlay",
        yaxis2   = dict(
            overlaying  = "y",
            side        = "right",
            gridcolor   = "rgba(0,0,0,0)",
            tickfont    = dict(color=THEME["accent_purple"], size=10),
            showgrid    = False,
            tickformat  = ".2s",
        ),
        yaxis    = dict(tickformat=".2s"),
        height   = 340,
        margin   = dict(l=8, r=8, t=50, b=50),
    )
    fig.update_layout(layout)

    # Legenda horizontal abaixo do gráfico para não sobrepor o eixo direito
    fig.update_layout(
        legend=dict(
            orientation = "h",
            x           = 0,
            y           = -0.18,
            xanchor     = "left",
            yanchor     = "top",
            bgcolor     = "rgba(0,0,0,0)",
            bordercolor = THEME["border"],
            font        = dict(color=THEME["text_secondary"], size=11),
        )
    )
    return fig


# ---------------------------------------------------------------------------
# 6. STACKED BAR — DISTRIBUIÇÃO DE PILARES POR REDE
# ---------------------------------------------------------------------------

def chart_pillar_by_network(df: pd.DataFrame) -> go.Figure:
    """
    Barras horizontais empilhadas mostrando % de cada pilar por rede.
    Replicando o painel direito do Slide 4 do relatório.
    """
    df_p = df[df["Pillars"] != "Unknown"]

    if df_p.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No pillar data for this period",
            xref="paper", yref="paper", x=0.5, y=0.5,
            font=dict(color=THEME["text_muted"], size=13),
            showarrow=False,
        )
        fig.update_layout(_base_layout(height=280))
        return fig

    pivot = (
        df_p.groupby(["social_network", "Pillars"])
        .size()
        .unstack(fill_value=0)
    )
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    pillar_colors = {
        "Brand":         "#9B72E8",
        "Conversation":  "#50E6FF",
        "Educational":   "#54D46A",
        "Informational": "#FFB900",
        "Micro-skilling":"#FF4D6A",
    }

    fig = go.Figure()
    for pillar in pivot_pct.columns:
        fig.add_trace(go.Bar(
            y           = pivot_pct.index,
            x           = pivot_pct[pillar],
            name        = pillar,
            orientation = "h",
            marker_color= pillar_colors.get(pillar, "#aaa"),
            hovertemplate = f"<b>%{{y}}</b><br>{pillar}: %{{x:.0f}}%<extra></extra>",
            text        = pivot_pct[pillar].apply(
                lambda v: f"{v:.0f}%" if v >= 8 else ""
            ),
            textposition = "inside",
            textfont     = dict(color="white", size=10),
        ))

    fig.update_layout(_base_layout(
        title   = dict(text="Pillar Mix by Network", font=dict(size=14)),
        barmode = "stack",
        xaxis   = dict(ticksuffix="%", range=[0, 100]),
        height  = 280,
    ))
    return fig


# ---------------------------------------------------------------------------
# 7. FY POSTS PACING
# ---------------------------------------------------------------------------

def chart_fy_posts(monthly_df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de pacing de posts do FY vs meta anual.
    Verde = mês bateu a meta mensal; vermelho = ficou abaixo.
    """
    from config import FY_START, FY_END

    all_months   = pd.date_range(FY_START, FY_END, freq="MS")
    n_months     = len(all_months)
    monthly_pace = FY_POSTS_TARGET / n_months

    monthly_df = monthly_df.copy()
    monthly_df["month_dt"] = pd.to_datetime(monthly_df["month_dt"])

    full = pd.DataFrame({"month_dt": all_months})
    full = full.merge(monthly_df[["month_dt", "posts"]], on="month_dt", how="left")
    full["posts"]       = full["posts"].fillna(0)
    full["pace"]        = monthly_pace
    full["month_label"] = full["month_dt"].dt.strftime("%b").str.upper()
    full["cumulative"]  = full["posts"].cumsum()

    bar_colors = [
        THEME["accent_green"] if p >= monthly_pace else THEME["accent_red"]
        for p in full["posts"]
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x             = full["month_label"],
        y             = full["posts"],
        name          = "Posts Delivered",
        marker_color  = bar_colors,
        opacity       = 0.9,
        hovertemplate = "<b>%{x}</b><br>Posts: %{y:.0f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x             = full["month_label"],
        y             = full["pace"],
        name          = "Required Monthly Pace",
        marker_color  = THEME["text_muted"],
        opacity       = 0.3,
        hovertemplate = "<b>%{x}</b><br>Required pace: %{y:.0f}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x             = full["month_label"],
        y             = full["cumulative"],
        name          = "Cumulative Posts",
        mode          = "lines+markers",
        line          = dict(color=THEME["accent_yellow"], width=2.5),
        marker        = dict(size=5),
        yaxis         = "y2",
        hovertemplate = "<b>%{x}</b><br>Cumulative: %{y:.0f}<extra></extra>",
    ))

    layout = _base_layout(
        title   = dict(text=f"FY 2026 Pacing — Posts (target: {FY_POSTS_TARGET:,})", font=dict(size=14)),
        barmode = "overlay",
        yaxis2  = dict(
            overlaying = "y",
            side       = "right",
            gridcolor  = "rgba(0,0,0,0)",
            tickfont   = dict(color=THEME["accent_yellow"], size=10),
            showgrid   = False,
        ),
        height  = 320,
        margin  = dict(l=8, r=8, t=50, b=50),
    )
    fig.update_layout(layout)
    fig.update_layout(
        legend=dict(
            orientation = "h",
            x           = 0,
            y           = -0.18,
            xanchor     = "left",
            yanchor     = "top",
            bgcolor     = "rgba(0,0,0,0)",
            bordercolor = THEME["border"],
            font        = dict(color=THEME["text_secondary"], size=11),
        )
    )
    return fig
