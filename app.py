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
    chart_fy_pacing, chart_fy_posts,
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
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

  html, body, [class*="css"], .stApp, .stMarkdown, p, label, div, span, button, input, textarea, select {{
      font-family: 'Poppins', sans-serif !important;
  }}

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

  /* Calendar date picker — fundo escuro, texto branco */
  [data-baseweb="calendar"],
  [data-baseweb="calendar"] * {{
      color: #FFFFFF !important;
      background-color: {THEME['bg_card']} !important;
  }}
  [data-baseweb="calendar"] [aria-selected="true"] {{
      background-color: {THEME['accent_blue']} !important;
      color: #000000 !important;
  }}
  [data-baseweb="calendar"] button:hover {{
      background-color: {THEME['bg_card2']} !important;
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

# Redes disponíveis — definido aqui para usar no filtro de topo e no sidebar
all_networks = sorted(df_all["social_network"].unique().tolist())

# Inicializa session state do filtro de rede
if "sel_network" not in st.session_state:
    st.session_state.sel_network = "ALL"


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

    # Item 5a — Padrão: início do FY26 (01-Aug-2025) ou min_date, o que for maior.
    # Para voltar ao padrão "última semana": troque a linha abaixo por:
    #   default_start = max_date - pd.Timedelta(days=6)
    from config import FY_START
    _fy26_start   = pd.Timestamp(FY_START).date()
    default_start = max(min_date, _fy26_start)

    date_start = st.date_input("From", value=default_start, min_value=min_date, max_value=max_date)
    date_end   = st.date_input("To",   value=max_date,      min_value=min_date, max_value=max_date)

    # Toggle Weekly / Monthly (para o gráfico de timeline)
    granularity = st.radio(
        "Granularity",
        options=["Weekly", "Monthly"],
        horizontal=True,
    )

    st.divider()

    # ── Pilares ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Pillars</div>', unsafe_allow_html=True)
    all_pillars = sorted([p for p in df_all["Pillars"].unique().tolist() if p != "Unknown"])
    pillars = st.multiselect("", options=all_pillars, default=all_pillars, label_visibility="collapsed", key="filter_pillars")

    # ── Tipo de mídia ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Media Type</div>', unsafe_allow_html=True)
    all_media = sorted([m for m in df_all["media_type"].unique().tolist() if pd.notna(m) and str(m).strip()])
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
# Rede(s) ativas (vem do session_state — botões no topo da página)
_sel_net = st.session_state.sel_network
networks = all_networks if (_sel_net == "ALL" or _sel_net not in all_networks) else [_sel_net]

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
# NETWORK FILTER BAR — botões com ícone + nome no topo
# ---------------------------------------------------------------------------

# SVG icons para cada rede (branco, renderizado sobre fundo colorido)
_NETWORK_SVG = {
    "Instagram": '<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="26" height="26"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5" stroke-width="3"/></svg>',
    "IG Stories": '<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="26" height="26"><rect x="2" y="2" width="20" height="20" rx="10" ry="10" stroke-dasharray="3 2"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/></svg>',
    "X":          '<svg viewBox="0 0 24 24" fill="white" width="24" height="24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.747l7.73-8.835L1.254 2.25H8.08l4.253 5.622 5.912-5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
    "LinkedIn":   '<svg viewBox="0 0 24 24" fill="white" width="24" height="24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>',
    "TikTok":     '<svg viewBox="0 0 24 24" fill="white" width="24" height="24"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.27 6.27 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.58a8.28 8.28 0 004.84 1.54V6.67a4.82 4.82 0 01-1.07.02z"/></svg>',
    "Threads":    '<svg viewBox="0 0 192 192" fill="white" width="24" height="24"><path d="M141.537 88.988a66.667 66.667 0 00-2.518-1.143c-1.482-27.307-16.403-42.94-41.457-43.1h-.34c-14.986 0-27.449 6.396-35.12 18.036l13.779 9.452c5.73-8.695 14.724-10.548 21.348-10.548h.232c8.248.053 14.474 2.452 18.502 7.13 2.932 3.405 4.893 8.111 5.864 14.05-7.314-1.243-15.224-1.626-23.68-1.14-23.82 1.371-39.134 15.264-38.105 34.568.522 9.792 5.4 18.216 13.735 23.719 7.047 4.652 16.124 6.927 25.557 6.412 12.458-.683 22.231-5.436 29.049-14.127 5.178-6.6 8.453-15.153 9.899-25.93 5.937 3.583 10.337 8.298 12.767 13.966 4.132 9.635 4.373 25.468-8.546 38.318-11.319 11.24-24.925 16.1-45.488 16.243-22.761-.163-39.976-7.466-51.154-21.71C36.037 122.848 30.6 104.704 30.4 81.893c.2-22.811 5.637-40.955 16.165-53.933C57.744 13.716 74.958 6.413 97.72 6.25c22.92.163 40.488 7.492 52.208 21.79 5.786 7.025 10.143 15.867 12.974 26.258l16.147-4.333c-3.466-12.798-9-23.744-16.52-32.652C147.042 9.645 125.327.2 97.86 0h-.38C70.132.2 48.744 9.68 34.816 28.186 22.487 44.42 16.096 67.25 15.877 95.985c.22 28.735 6.61 51.565 18.94 67.8 13.927 18.506 35.315 27.986 63.443 28.186h.38c24.678-.172 42.053-6.676 56.315-20.843 18.713-18.616 18.117-42.345 12.011-56.78-4.532-10.564-13.09-19.07-25.429-24.36z"/></svg>',
    "ALL": '<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="24" height="24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>',
}

# Cor de fundo de cada rede (fallback cinza)
_NET_BG = {**NETWORK_COLORS, "ALL": THEME["bg_card2"]}

def _set_network(net: str):
    st.session_state.sel_network = net

# CSS para a barra de filtro de redes
st.markdown(f"""
<style>
  /* Ícone circular de cada rede */
  .net-icon-wrap {{
      display: flex;
      justify-content: center;
      margin-bottom: 4px;
  }}
  .net-icon-circle {{
      width: 54px;
      height: 54px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.15s ease, box-shadow 0.15s ease;
  }}
  .net-icon-circle.active {{
      box-shadow: 0 0 0 3px {THEME['bg_page']}, 0 0 0 5px currentColor;
      transform: scale(1.08);
  }}
  .net-icon-circle.inactive {{
      opacity: 0.4;
      filter: grayscale(30%);
  }}

  /* Item 1 — Reduz fonte dos labels dos botões de rede em 2pt
     Para ajustar: mude o valor de font-size abaixo (padrão Streamlit ≈ 14px) */
  [data-testid="stButton"] button p {{
      font-size: 12px !important;
  }}
</style>
""", unsafe_allow_html=True)

# Renderiza a barra de filtros
_items = ["ALL"] + all_networks
# Limita colunas para não ficar muito espalhado em telas largas
_spacer = max(1, 8 - len(_items))
_col_widths = [1] * len(_items) + [_spacer]
_cols = st.columns(_col_widths, gap="small")

for _col, _net in zip(_cols, _items):
    with _col:
        _is_active = (st.session_state.sel_network == _net)
        _bg_color  = _NET_BG.get(_net, THEME["bg_card2"])
        _svg       = _NETWORK_SVG.get(_net, _NETWORK_SVG["ALL"])
        _label     = "All" if _net == "ALL" else _net
        _cls       = "active" if _is_active else "inactive"

        # Ícone circular (visual apenas)
        st.markdown(
            f'<div class="net-icon-wrap">'
            f'  <div class="net-icon-circle {_cls}"'
            f'       style="background:{_bg_color};color:{_bg_color}">'
            f'    {_svg}'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        # Botão com o nome da rede — active usa type="primary"
        if st.button(
            _label,
            key=f"_netbtn_{_net}",
            use_container_width=True,
            type="primary" if _is_active else "secondary",
            on_click=_set_network,
            args=(_net,),
        ):
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "FY Pacing",
    "Pillars",
    "Networks",
    "Top / Bottom",
])


# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════
with tab1:

    # KPI Cards
    render_kpis(df_filtered, df_prev)

    st.markdown("<br>", unsafe_allow_html=True)

    # Timeline (menor) + Radar ao lado
    col_tl, col_rd = st.columns([3, 2])
    with col_tl:
        fig_tl = chart_timeline(df_filtered, granularity, date_start_ts, date_end_ts)
        fig_tl.update_layout(height=320)
        st.plotly_chart(fig_tl, use_container_width=True, key="overview_timeline")
    with col_rd:
        fig_rd = chart_pillar_radar(df_filtered)
        fig_rd.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_rd, use_container_width=True, key="overview_radar")

    # Barras por rede (abaixo)
    st.plotly_chart(chart_by_network(df_filtered), use_container_width=True, key="overview_by_network")


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
        st.plotly_chart(chart_fy_posts(monthly_data), use_container_width=True, key="fy_posts")


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
    # Item 7 — "Engagement Rate by Network" removido.
    # Para reativar: col_n1, col_n2 = st.columns(2) e adicione chart_er_by_network em col_n2.
    st.plotly_chart(chart_by_network(df_filtered), use_container_width=True, key="network_detail_by_network")


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