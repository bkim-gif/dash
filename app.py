"""
app.py
======
Arquivo principal do dashboard. Rode com:
    streamlit run app.py

ESTRUTURA:
  1. Carrega dados
  2. Renderiza sidebar com filtros
  3. Renderiza 5 tabs:
     Tab 1 — Overview        (KPIs + timeline + breakdown por rede)
     Tab 2 — FY Pacing       (gauge + gráfico mensal vs target)
     Tab 3 — Pillars         (radar + stacked bar + tabela)
     Tab 4 — Network Detail  (tabela comparativa por rede)
     Tab 5 — Top / Bottom    (cards de posts)
"""

import sys
from pathlib import Path

# Garante que os imports relativos funcionam
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from config import (
    CLIENT, THEME, FY_TARGET, SORT_OPTIONS,
    NETWORK_COLORS, PILLAR_TARGETS, METRIC_LABELS
)
from data.loader import (
    load_raw, apply_filters, get_previous_period, get_fy_monthly
)
from components.kpis   import render_kpis
from components.charts import (
    chart_timeline, chart_by_network, chart_er_by_network,
    chart_pillar_donut, chart_pillar_radar, chart_pillar_by_network,
    chart_fy_pacing,
)
from components.posts import render_top_bottom


# ---------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# Deve ser a primeira chamada Streamlit do script
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title = f"{CLIENT['name']} · Analytics",
    page_icon  = "📊",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ---------------------------------------------------------------------------
# CSS GLOBAL — injeta o tema escuro e estilos base
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
  /* Fundo da página */
  .stApp {{ background-color: {THEME['bg_page']}; }}

  /* Remove padding padrão do Streamlit no topo */
  .block-container {{ padding-top: 1.5rem !important; }}

  /* Sidebar */
  [data-testid="stSidebar"] {{
      background-color: {THEME['bg_card']};
      border-right: 1px solid {THEME['border']};
  }}

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {{
      background: {THEME['bg_card']};
      border-radius: 8px;
      padding: 4px;
      gap: 4px;
  }}
  .stTabs [data-baseweb="tab"] {{
      color: {THEME['text_secondary']};
      font-weight: 500;
      border-radius: 6px;
      padding: 8px 16px;
  }}
  .stTabs [aria-selected="true"] {{
      background: {THEME['bg_card2']} !important;
      color: {THEME['text_primary']} !important;
  }}

  /* Divisor entre seções */
  hr {{ border-color: {THEME['border']}; margin: 20px 0; }}

  /* Texto geral */
  .stMarkdown, p, label, div {{ color: {THEME['text_primary']}; }}

  /* Selectbox e multiselect */
  .stSelectbox label, .stMultiSelect label,
  .stDateInput label, .stRadio label {{
      color: {THEME['text_secondary']} !important;
      font-size: 12px !important;
      text-transform: uppercase;
      letter-spacing: 0.5px;
  }}

  /* Section headers */
  .section-header {{
      color: {THEME['text_secondary']};
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin: 20px 0 8px 0;
  }}

  /* Calendar date picker — texto preto no popup */
  [data-baseweb="calendar"] *,
  [data-baseweb="datepicker"] *,
  .react-datepicker *,
  [class*="calendarMonth"] *,
  [class*="CalendarDay"] {{
      color: #000000 !important;
  }}
  [data-baseweb="calendar"] [aria-selected="true"],
  [data-baseweb="calendar"] [aria-selected="true"] * {{
      color: #ffffff !important;
  }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# CARREGA DADOS
# ---------------------------------------------------------------------------
df_all = load_raw()

if df_all.empty:
    st.error("❌ No data found. Check the file path in data/loader.py")
    st.stop()


# ---------------------------------------------------------------------------
# SIDEBAR — filtros
# ---------------------------------------------------------------------------
with st.sidebar:

    # Logo / nome do cliente
    st.markdown(
        f'<div style="font-size:18px;font-weight:700;color:{THEME["text_primary"]};'
        f'padding:8px 0 4px 0">{CLIENT["name"]}</div>'
        f'<div style="font-size:11px;color:{THEME["text_muted"]};'
        f'margin-bottom:20px">Social Analytics Dashboard</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Período ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Period</div>', unsafe_allow_html=True)

    min_date = df_all["published_date"].min().date()
    max_date = df_all["published_date"].max().date()

    # Padrão: última semana disponível
    default_start = max_date - pd.Timedelta(days=6)

    date_start = st.date_input("From", value=default_start, min_value=min_date, max_value=max_date)
    date_end   = st.date_input("To",   value=max_date,      min_value=min_date, max_value=max_date)

    # Toggle Weekly / Monthly (para o gráfico de timeline)
    granularity = st.radio(
        "Granularity",
        options=["Weekly", "Monthly"],
        horizontal=True,
    )

    st.divider()

    # ── Redes sociais ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Networks</div>', unsafe_allow_html=True)
    all_networks = sorted(df_all["social_network"].unique().tolist())
    networks = st.multiselect("", options=all_networks, default=all_networks, label_visibility="collapsed", key="filter_networks")

    # ── Pilares ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Pillars</div>', unsafe_allow_html=True)
    all_pillars = sorted(df_all["Pillars"].unique().tolist())
    pillars = st.multiselect("", options=all_pillars, default=all_pillars, label_visibility="collapsed", key="filter_pillars")

    # ── Tipo de mídia ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Media Type</div>', unsafe_allow_html=True)
    all_media = sorted(df_all["media_format_outbound_message"].unique().tolist())
    media_types = st.multiselect("", options=all_media, default=all_media, label_visibility="collapsed", key="filter_media")

    # ── Campanha ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Campaign</div>', unsafe_allow_html=True)
    all_campaigns = sorted(df_all["campaign_name"].unique().tolist())
    campaigns = st.multiselect("", options=all_campaigns, default=all_campaigns, label_visibility="collapsed", key="filter_campaigns")

    st.divider()

    # ── Ordenação dos cards Top/Bottom ────────────────────────────────────
    st.markdown('<div class="section-header">Sort Posts By</div>', unsafe_allow_html=True)
    sort_by = st.selectbox("", options=list(SORT_OPTIONS.keys()), index=0, label_visibility="collapsed")


# ---------------------------------------------------------------------------
# APLICA FILTROS
# ---------------------------------------------------------------------------
date_start_ts = pd.Timestamp(date_start)
date_end_ts   = pd.Timestamp(date_end)

df_filtered = apply_filters(
    df_all,
    date_start  = date_start_ts,
    date_end    = date_end_ts,
    networks    = networks,
    pillars     = pillars,
    media_types = media_types,
    campaigns   = campaigns,
)

df_prev = get_previous_period(df_all, date_start_ts, date_end_ts)

# Aviso se não há dados no período
if df_filtered.empty:
    st.warning("⚠️ No data for the selected filters and period.")
    st.stop()


# ---------------------------------------------------------------------------
# HEADER PRINCIPAL
# ---------------------------------------------------------------------------
col_title, col_period = st.columns([3, 1])
with col_title:
    st.markdown(
        f'<h1 style="font-size:24px;font-weight:700;margin:0;color:{THEME["text_primary"]}">'
        f'Social Analytics</h1>',
        unsafe_allow_html=True,
    )
with col_period:
    st.markdown(
        f'<div style="text-align:right;color:{THEME["text_muted"]};font-size:12px;padding-top:8px">'
        f'{date_start_ts.strftime("%b %d")} — {date_end_ts.strftime("%b %d, %Y")}'
        f'<br><span style="color:{THEME["text_muted"]}">{len(df_filtered)} posts</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  Overview",
    "🎯  FY Pacing",
    "🗂  Pillars",
    "🌐  Networks",
    "🏆  Top / Bottom",
])


# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════
with tab1:

    # KPI Cards
    render_kpis(df_filtered, df_prev)

    st.markdown("<br>", unsafe_allow_html=True)

    # Timeline
    st.plotly_chart(
        chart_timeline(df_filtered, granularity),
        use_container_width=True,
        key="overview_timeline",
    )

    # Barras por rede + ER por rede
    col_net1, col_net2 = st.columns(2)
    with col_net1:
        st.plotly_chart(chart_by_network(df_filtered), use_container_width=True, key="overview_by_network")
    with col_net2:
        st.plotly_chart(chart_er_by_network(df_filtered), use_container_width=True, key="overview_er_by_network")


# ══════════════════════════════════════════════════════════════════════════
# TAB 2 — FY PACING
# ══════════════════════════════════════════════════════════════════════════
with tab2:

    monthly_data = get_fy_monthly(df_all)
    total_fy     = monthly_data["impressions"].sum()
    pct_fy       = total_fy / FY_TARGET * 100

    # Gauge + número grande
    col_gauge, col_chart = st.columns([1, 2])

    with col_gauge:
        # Gauge de % atingido
        fig_gauge = go.Figure(go.Indicator(
            mode  = "gauge+number+delta",
            value = pct_fy,
            title = dict(text="FY 2026 Target", font=dict(color=THEME["text_secondary"], size=13)),
            number= dict(suffix="%", font=dict(color=THEME["text_primary"], size=40)),
            delta = dict(
                reference = 100,
                suffix    = "pp to target",
                font      = dict(size=12),
                increasing= dict(color=THEME["accent_green"]),
                decreasing= dict(color=THEME["accent_red"]),
            ),
            gauge = dict(
                axis        = dict(range=[0, 100], tickcolor=THEME["text_muted"],
                                   tickfont=dict(color=THEME["text_muted"])),
                bar         = dict(color=THEME["accent_blue"]),
                bgcolor     = THEME["bg_card2"],
                bordercolor = THEME["border"],
                steps       = [
                    dict(range=[0, 50],  color=THEME["bg_card2"]),
                    dict(range=[50, 80], color="#1E3A2F"),
                    dict(range=[80,100], color="#1A3A2A"),
                ],
                threshold   = dict(
                    line  = dict(color=THEME["accent_yellow"], width=3),
                    value = 100,
                ),
            ),
        ))
        fig_gauge.update_layout(
            paper_bgcolor = "rgba(0,0,0,0)",
            plot_bgcolor  = "rgba(0,0,0,0)",
            font          = dict(color=THEME["text_primary"]),
            height        = 280,
            margin        = dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_gauge, use_container_width=True, key="fy_gauge")

        # Números embaixo do gauge
        remaining = max(0, FY_TARGET - total_fy)
        st.markdown(
            f"""
            <div style="background:{THEME['bg_card']};border:1px solid {THEME['border']};
                border-radius:10px;padding:16px;text-align:center">
                <div style="color:{THEME['text_muted']};font-size:11px;margin-bottom:4px">ACHIEVED</div>
                <div style="color:{THEME['accent_blue']};font-size:24px;font-weight:700">
                    {total_fy/1e6:.1f}M
                </div>
                <div style="color:{THEME['text_muted']};font-size:11px;margin:8px 0 4px">REMAINING</div>
                <div style="color:{THEME['accent_yellow']};font-size:20px;font-weight:600">
                    {remaining/1e6:.1f}M
                </div>
                <div style="color:{THEME['text_muted']};font-size:10px;margin-top:8px">
                    Target: {FY_TARGET/1e6:.0f}M · Aug 2025 – Jul 2026
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_chart:
        st.plotly_chart(chart_fy_pacing(monthly_data), use_container_width=True, key="fy_pacing")


# ══════════════════════════════════════════════════════════════════════════
# TAB 3 — PILLARS
# ══════════════════════════════════════════════════════════════════════════
with tab3:

    col_radar, col_donut = st.columns(2)
    with col_radar:
        st.plotly_chart(chart_pillar_radar(df_filtered), use_container_width=True, key="pillar_radar")
    with col_donut:
        st.plotly_chart(chart_pillar_donut(df_filtered), use_container_width=True, key="pillar_donut")

    st.plotly_chart(chart_pillar_by_network(df_filtered), use_container_width=True, key="pillar_by_network")

    # Tabela de métricas médias por pilar
    st.markdown(
        f'<div class="section-header" style="margin-top:20px">Average Metrics per Post by Pillar</div>',
        unsafe_allow_html=True,
    )
    df_p = df_filtered[df_filtered["Pillars"] != "Unknown"]
    if not df_p.empty:
        pillar_table = df_p.groupby("Pillars").agg(
            Posts        = ("outbound_post",             "count"),
            Impressions  = ("gdc_impressions_sum",       "mean"),
            Likes        = ("post_likes_and_reactions_sum","mean"),
            Comments     = ("post_comments_sum",          "mean"),
            Shares       = ("post_shares_sum",            "mean"),
            Clicks       = ("estimated_clicks_sum",       "mean"),
            ER           = ("ER",                         "mean"),
            AQE          = ("AQE",                        "mean"),
        ).round(1).reset_index()

        st.dataframe(
            pillar_table,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No pillar data for this period.")


# ══════════════════════════════════════════════════════════════════════════
# TAB 4 — NETWORK DETAIL
# ══════════════════════════════════════════════════════════════════════════
with tab4:

    network_table = df_filtered.groupby("social_network").agg(
        Posts       = ("outbound_post",              "count"),
        Impressions = ("gdc_impressions_sum",        "sum"),
        Likes       = ("post_likes_and_reactions_sum","sum"),
        Comments    = ("post_comments_sum",           "sum"),
        Shares      = ("post_shares_sum",             "sum"),
        Clicks      = ("estimated_clicks_sum",        "sum"),
        ER          = ("ER",                          "mean"),
        AQE_post    = ("AQE",                         "mean"),
    ).round(2).reset_index()

    network_table = network_table.sort_values("Impressions", ascending=False)
    network_table["Impressions"] = network_table["Impressions"].apply(
        lambda v: f"{v:,.0f}"
    )
    network_table["ER"] = network_table["ER"].apply(lambda v: f"{v:.2f}%")

    st.dataframe(
        network_table,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.plotly_chart(chart_by_network(df_filtered), use_container_width=True, key="network_detail_by_network")
    with col_n2:
        st.plotly_chart(chart_er_by_network(df_filtered), use_container_width=True, key="network_detail_er_by_network")


# ══════════════════════════════════════════════════════════════════════════
# TAB 5 — TOP / BOTTOM POSTS
# ══════════════════════════════════════════════════════════════════════════
with tab5:

    st.markdown(
        f'<div style="color:{THEME["text_muted"]};font-size:12px;margin-bottom:16px">'
        f'Sorted by: <strong style="color:{THEME["text_primary"]}">{sort_by}</strong> · '
        f'Period: {date_start_ts.strftime("%b %d")} – {date_end_ts.strftime("%b %d, %Y")}'
        f'</div>',
        unsafe_allow_html=True,
    )
    render_top_bottom(df_filtered, sort_by)