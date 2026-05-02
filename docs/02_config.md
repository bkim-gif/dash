# 02 — Guia de Configuração Completo (config.py)

> **Arquivo:** [`config.py`](../config.py)  
> **Este é o arquivo que você vai editar com mais frequência.**  
> Toda mudança de cor, meta, target ou label começa aqui — o resto do dashboard pega automaticamente.

---

## Cliente (linhas 11–14)

```python
CLIENT = {
    "name":   "Microsoft Learn",   # ← Aparece no header da sidebar
    "logo":   None,                 # ← Caminho do PNG da logo, ou None
}
```

**Onde aparece no dashboard:**
- Sidebar: título no topo (`Social Analytics Dashboard` embaixo)
- Aba do navegador: `"Microsoft Learn · Analytics"`

**Para trocar:** edite `"name"` e, se quiser logo, coloque o caminho do arquivo PNG.

---

## Metas Anuais do FY (linhas 20–23)

```python
FY_TARGET       = 25_000_000   # 25 milhões de impressões orgânicas
FY_POSTS_TARGET = 1_600        # 1.600 posts orgânicos no ano
FY_START  = "2025-08-01"       # Início do fiscal year
FY_END    = "2026-07-31"       # Fim do fiscal year
```

**Onde aparecem no dashboard:**

| Constante | Onde aparece |
|-----------|-------------|
| `FY_TARGET` | Gauge na Tab 2, números "Achieved" e "Remaining", barras de pace |
| `FY_POSTS_TARGET` | Gráfico de pacing de posts (Tab 2), título do gráfico |
| `FY_START` / `FY_END` | Período padrão da sidebar, todos os gráficos de pacing |

**Para novo FY:**
```python
FY_TARGET       = 30_000_000
FY_POSTS_TARGET = 1_800
FY_START  = "2026-08-01"
FY_END    = "2027-07-31"
```

---

## Targets do Radar por Pilar (linhas 30–36)

```python
PILLAR_TARGETS = {
    "Brand":          5.0,   # % ideal de posts do pilar Brand
    "Conversation":  15.0,   # % ideal de posts Conversation
    "Educational":   45.0,   # % ideal de posts Educational
    "Informational": 25.0,   # % ideal de posts Informational
    "Micro-skilling":10.0,   # % ideal de posts Micro-skilling
}
```

**Onde aparece:** linha amarela tracejada no Radar Chart (Tab 1 e Tab 3).  
A linha azul = distribuição atual; a amarela = target do playbook.  
**A soma deve ser 100%.**

---

## Cores das Redes Sociais (linhas 41–48) {#cores-das-redes}

```python
NETWORK_COLORS = {
    "LinkedIn":   "#0179D5",   # Azul oficial LinkedIn
    "X":          "#47C6B2",   # Teal (X/Twitter)
    "Instagram":  "#FF5C38",   # Laranja Instagram
    "IG Stories": "#FF5C38",   # Mesmo laranja do Instagram
    "TikTok":     "#C73FCC",   # Rosa/roxo TikTok
    "Threads":    "#9900FF",   # Roxo Threads
}
```

**Onde aparecem:**
- Círculos dos botões de filtro de rede no topo da página
- Barras nos gráficos "Impressions by Network"
- Badges coloridos nos cards de Top/Bottom posts
- Valor de Followers (muda de cor conforme a rede selecionada)

---

## Cores dos Pilares (linhas 54–60) {#cores-dos-pilares}

```python
PILLAR_COLORS = {
    "Brand":         "#D3A85B",   # Ouro velho
    "Conversation":  "#69A27E",   # Sálvia/Verde suave
    "Educational":   "#6B8CAE",   # Azul-aço
    "Informational": "#D17B6D",   # Coral/Terracota suave
    "Micro-skilling":"#9F86AA",   # Lilás/Púrpura suave
}
```

**Onde aparecem:**
- Donut de distribuição por pilar (Tab 1 radar e Tab 3)
- Stacked bar "Pillar Mix by Network" (Tab 3)

---

## Tema Dark Mode (linhas 65–87)

```python
THEME = {
    # ── FUNDOS ────────────────────────────────────────────────────
    "bg_page":    "#0F0E17",   # Cor de fundo da página inteira
    "bg_card":    "#1A1826",   # Fundo dos cards (KPIs, charts)
    "bg_card2":   "#231F33",   # Cards secundários e chips dos posts
    "bg_table":   "#15121F",   # Fundo das tabelas (não usado atualmente)

    # ── TEXTO ─────────────────────────────────────────────────────
    "text_primary":   "#FFFFFE",   # Títulos e métricas (quase branco)
    "text_secondary": "#A7A9BE",   # Labels, eixos dos gráficos
    "text_muted":     "#5E5B74",   # Datas e informações secundárias

    # ── CORES DE DESTAQUE ─────────────────────────────────────────
    "accent_blue":    "#50E6FF",   # Linha ER no timeline, links, gauge
    "accent_yellow":  "#FFB900",   # Target radar, linha cumulative posts
    "accent_green":   "#10B981",   # Positivo, mês atingiu meta, delta ▲
    "accent_red":     "#EF4444",   # Negativo, mês abaixo da meta, delta ▼
    "accent_purple":  "#9B72E8",   # Barras de impressões no timeline

    # ── ESTRUTURA DOS GRÁFICOS ────────────────────────────────────
    "grid_line":  "#2D2A3D",   # Linhas de grade dos gráficos
    "border":     "#2D2A3D",   # Bordas dos cards e componentes
}
```

### Mapa visual de onde cada cor aparece

| Chave | Onde é usada no dashboard |
|-------|--------------------------|
| `bg_page` | Fundo da página (`app.py:68`) |
| `bg_card` | Cards de KPI, fundo dos gráficos (`kpis.py`, `charts.py`) |
| `bg_card2` | Chips de métricas nos posts, tooltip hover, tabs selecionadas |
| `text_primary` | Valores dos KPIs, títulos dos gráficos |
| `text_secondary` | Labels das tabs, eixos, legenda dos gráficos |
| `text_muted` | Datas no header, grid dos gráficos |
| `accent_blue` | Linha ER no timeline, barra do gauge, links "View post" |
| `accent_yellow` | Linha target no radar, linha cumulative no pacing de posts |
| `accent_green` | Delta ▲ positivo, barras de meses que bateram a meta |
| `accent_red` | Delta ▼ negativo, barras de meses abaixo da meta |
| `accent_purple` | Barras de impressões no timeline, linha "Remaining Target" |
| `border` | Borda de todos os cards e componentes |

---

## Composição do AQE (linhas 105–109)

```python
AQE_COLS = [
    "post_comments_sum",     # Comentários
    "post_shares_sum",       # Compartilhamentos
    "estimated_clicks_sum",  # Cliques
]
# AQE por post = soma desses 3 ÷ número de posts
```

Para incluir Likes no AQE, adicione `"post_likes_and_reactions_sum"`.

---

## Opções de Ordenação dos Posts (linhas 114–119)

```python
SORT_OPTIONS = {
    "Total Engagement": "gdc_total_engagements_sum",  # padrão
    "Impressions":      "gdc_impressions_sum",
    "ER (%)":           "ER",
    "AQE":              "AQE",
}
```

Aparecem no selectbox "Sort Posts By" na sidebar. Para adicionar nova opção, basta incluir uma entrada — a chave é o label e o valor é o nome da coluna.

---

## Número de Top/Bottom Posts (linha 124)

```python
TOP_N = 5   # Mostra Top 5 e Bottom 5
```

Para mostrar Top 10: `TOP_N = 10`.

---

## Checklist para novo cliente

- [ ] `CLIENT["name"]` → nome do cliente
- [ ] `FY_TARGET`, `FY_POSTS_TARGET` → metas anuais
- [ ] `FY_START`, `FY_END` → período fiscal
- [ ] `PILLAR_TARGETS` → % alvo por pilar (soma = 100)
- [ ] `NETWORK_COLORS` → cores se quiser personalizar
- [ ] `DATA_PATH` em `data/loader.py:24` → caminho do novo CSV
- [ ] `FOLLOWERS_PATH` em `data/loader.py:25` → novo arquivo de seguidores
- [ ] `COMMENTS_PATH` em `data/loader.py:26` → novo arquivo de comentários
