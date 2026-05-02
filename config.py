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
    "LinkedIn":   "#0179D5",
    "X":          "#47C6B2",
    "Instagram":  "#FF5C38",
    "IG Stories": "#FF5C38",
    "TikTok":     "#C73FCC",
    "Threads":    "#9900FF",
}

# ---------------------------------------------------------------------------
# CORES DOS PILARES (Muted Qualitative)
# Paleta pastel/terrosa — não "briga" com as cores das redes sociais
# ---------------------------------------------------------------------------
PILLAR_COLORS = {
    "Brand":         "#D3A85B",   # Ouro velho
    "Conversation":  "#69A27E",   # Sálvia/Verde suave
    "Educational":   "#6B8CAE",   # Azul-aço
    "Informational": "#D17B6D",   # Coral/Terracota suave
    "Micro-skilling":"#9F86AA",   # Lilás/Púrpura suave
}

# ---------------------------------------------------------------------------
# CORES DO TEMA (dark mode) — "Sophisticated Utility" / Quiet UI
# ---------------------------------------------------------------------------
THEME = {
    # backgrounds
    "bg_page":    "#0F0E17",   # App Background — roxo/cinza ultra-escuro
    "bg_card":    "#1A1826",   # Card Surface — elevação subtil
    "bg_card2":   "#231F33",   # cards secundários / hover
    "bg_table":   "#15121F",   # tabelas

    # texto
    "text_primary":   "#FFFFFE",   # Títulos e métricas — máximo contraste
    "text_secondary": "#A7A9BE",   # Labels e eixos — cinza lavanda
    "text_muted":     "#5E5B74",   # Informação muito secundária

    # destaque semântico
    "accent_blue":    "#50E6FF",   # linha de destaque principal (timeline)
    "accent_yellow":  "#FFB900",   # target / linha de referência
    "accent_green":   "#10B981",   # Success / crescimento (Emerald Green)
    "accent_red":     "#EF4444",   # Alert / queda (Red)
    "accent_purple":  "#9B72E8",   # barras de impressões

    # estrutura de gráficos
    "grid_line":  "#2D2A3D",   # Borders & Lines — linhas silenciadas
    "border":     "#2D2A3D",
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
