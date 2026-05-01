"""
config.py
=========
Todas as constantes do dashboard em um único lugar.
Para adaptar a outro cliente: edite CLIENT e BRAND_COLORS.
"""

# ---------------------------------------------------------------------------
# CLIENTE
# ---------------------------------------------------------------------------
CLIENT = {
    "name":   "Microsoft Learn",
    "logo":   None,           # caminho para logo PNG, ou None
}

# ---------------------------------------------------------------------------
# FY TARGET (impressões orgânicas)
# Período: Aug 2025 → Jul 2026  |  Target: 25 milhões
# ---------------------------------------------------------------------------
FY_TARGET       = 25_000_000
FY_POSTS_TARGET = 1_600       # meta anual de posts orgânicos
FY_START  = "2025-08-01"
FY_END    = "2026-07-31"

# ---------------------------------------------------------------------------
# RADAR — targets por pilar (playbook)
# Fonte: radar_map.R  →  target = c(5, 15, 45, 25, 10)
# Valores em % de distribuição de posts
# ---------------------------------------------------------------------------
PILLAR_TARGETS = {
    "Brand":         5.0,
    "Conversation":  15.0,
    "Educational":   45.0,
    "Informational": 25.0,
    "Micro-skilling":10.0,
}

# ---------------------------------------------------------------------------
# CORES DAS REDES SOCIAIS
# ---------------------------------------------------------------------------
NETWORK_COLORS = {
    "LinkedIn":   "#0179d5",
    "X":          "#47c6b2",
    "Instagram":  "#ff5c38",
    "IG Stories": "#ff5c38",
    "TikTok":     "#c73fcc",
    "Threads":    "#9900ff",
}

# ---------------------------------------------------------------------------
# CORES DO TEMA (dark mode)
# Retiradas do relatório DOJO/MSFT
# ---------------------------------------------------------------------------
THEME = {
    # backgrounds
    "bg_page":      "#0F1923",   # fundo principal
    "bg_card":      "#1A2535",   # cards e painéis
    "bg_card2":     "#232F42",   # cards secundários / hover
    "bg_table":     "#151E2D",   # tabelas

    # texto
    "text_primary":   "#FFFFFF",
    "text_secondary": "#8BA3C0",
    "text_muted":     "#4A6080",

    # destaque (vindas do R)
    "accent_blue":    "#50E6FF",   # current / linha principal
    "accent_yellow":  "#FFB900",   # target / alerta
    "accent_green":   "#54D46A",   # positivo / acima do target
    "accent_red":     "#FF4D6A",   # negativo / abaixo do target
    "accent_purple":  "#9B72E8",   # pillar cards

    # gráficos
    "grid_line":    "#1E2F42",
    "border":       "#2A3F58",
}

# ---------------------------------------------------------------------------
# MÉTRICAS — mapeamento nome interno → label de exibição
# ---------------------------------------------------------------------------
METRIC_LABELS = {
    "gdc_impressions_sum":          "Impressions",
    "gdc_total_engagements_sum":    "Total Engagement",
    "post_likes_and_reactions_sum": "Likes",
    "post_comments_sum":            "Comments",
    "post_shares_sum":              "Shares",
    "estimated_clicks_sum":         "Clicks",
    "ER":                           "Engagement Rate (%)",
    "AQE":                          "AQE/post",
}

# Colunas que compõem o AQE (Average Qualified Engagement)
# AQE = comments + shares + clicks
AQE_COLS = [
    "post_comments_sum",
    "post_shares_sum",
    "estimated_clicks_sum",
]

# ---------------------------------------------------------------------------
# OPÇÕES DE ORDENAÇÃO para Top/Bottom posts
# ---------------------------------------------------------------------------
SORT_OPTIONS = {
    "Total Engagement": "gdc_total_engagements_sum",
    "Impressions":      "gdc_impressions_sum",
    "ER (%)":           "ER",
    "AQE":              "AQE",
}

# ---------------------------------------------------------------------------
# NÚMERO DE TOP/BOTTOM POSTS exibidos
# ---------------------------------------------------------------------------
TOP_N = 5
