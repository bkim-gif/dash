# 05 — Guia dos Gráficos (components/charts.py)

> **Arquivo:** [`components/charts.py`](../components/charts.py)  
> Contém todos os 9 gráficos do dashboard. Todos usam Plotly com tema escuro compartilhado.

---

## Layout Base Compartilhado — `_base_layout()` (linha 36)

Todos os gráficos usam este layout como ponto de partida:

```python
def _base_layout(**overrides) -> dict:
    base = dict(
        paper_bgcolor = "rgba(0,0,0,0)",   # Fundo transparente (aparece o card embaixo)
        plot_bgcolor  = "rgba(0,0,0,0)",   # Interior do gráfico também transparente
        font  = dict(color=THEME["text_primary"], family="Inter, sans-serif"),
        margin= dict(l=8, r=8, t=36, b=8), # Margens: left=8, right=8, top=36, bottom=8
        legend= dict(
            bgcolor     = "rgba(0,0,0,0)",
            bordercolor = THEME["border"],
            font        = dict(color=THEME["text_secondary"], size=11),
        ),
        xaxis = dict(
            gridcolor = THEME["grid_line"],
            tickfont  = dict(color=THEME["text_secondary"], size=11),
        ),
        yaxis = dict(
            gridcolor    = THEME["grid_line"],
            zerolinecolor= THEME["border"],
            tickfont     = dict(color=THEME["text_secondary"], size=11),
        ),
        hoverlabel = dict(
            bgcolor   = THEME["bg_card2"],   # Fundo do tooltip hover
            font      = dict(color=THEME["text_primary"]),
        ),
    )
```

**Para modificar um gráfico específico:** cada função chama `_base_layout()` e passa `overrides` para sobrescrever apenas o que precisa.

---

## 1. Timeline — `chart_timeline()` (linha 92)

**Onde aparece:** Tab 1 Overview (col. esquerda, linha do meio) e expandido na Tab 1.

### O que mostra:
- **Barras roxas** → Impressões por semana ou mês
- **Linha azul** → ER w/o swipes (eixo Y à direita, em %)

### Parâmetros:
```python
chart_timeline(
    df,                      # DataFrame orgânico filtrado
    granularity="Weekly",    # "Weekly" ou "Monthly" (vem da sidebar)
    date_start=None,         # Para preencher períodos sem posts
    date_end=None,
)
```

### Como modificar:

**Cor das barras de impressões (linha 142):**
```python
marker_color = THEME["accent_purple"],   # ← mude aqui
```

**Cor da linha ER (linha 154):**
```python
line = dict(color=THEME["accent_blue"], width=2.5, shape="spline", smoothing=1.3)
# shape="spline" = linha curva suave
# smoothing=1.3 = quanto mais alto, mais suave (máx ~1.3)
# width=2.5 = espessura da linha
```

**Altura (em app.py, linha 413):**
```python
fig_tl.update_layout(height=260)   # ← mude o número em px
```

**Nota de rodapé (linha 189–196):**
```python
fig.add_annotation(
    text = "ⓘ  ER excludes swipe interactions",
    # Para remover essa nota, delete essas 7 linhas
)
```

---

## 2. Impressões por Rede — `chart_by_network()` (linha 204)

**Onde aparece:** Tab 1 (col. direita, linha 3) e Tab 4 (Networks).

### O que mostra:
Barras horizontais com Impressões por rede. Cada rede tem sua cor de `NETWORK_COLORS`.

### Como modificar:

**Orientação das barras (linha 230):**
```python
orientation = "h",   # "h" = horizontal, "v" = vertical
```

**Texto dos valores fora das barras (linhas 235–238):**
```python
text         = agg["impressions"].apply(_fmt_impressions),
textposition = "outside",    # "inside" para texto dentro da barra
textfont     = dict(color=THEME["text_primary"], size=10),
```

**Margem direita (deixa espaço para os números, linha 247):**
```python
margin = dict(l=8, r=80, t=36, b=8)   # r=80 = 80px à direita para os labels
```

---

## 3. ER por Rede — `chart_er_by_network()` (linha 252)

Mesmo estilo do gráfico anterior, mas mostra ER médio por rede.  
**Atualmente não está sendo chamado no `app.py`** (disponível mas não exibido).

---

## 4. Donut de Pilares — `chart_pillar_donut()` (linha 292)

**Onde aparece:** Tab 1 (col. direita, radar) e Tab 3 (Pillars) lado a lado com radar.

### O que mostra:
Rosca com % de posts por pilar. Posts "Unknown" são excluídos da visualização.

### Como modificar:

**Tamanho do buraco central (linha 322):**
```python
hole = 0.55,   # 0 = pizza cheia, 1 = só o aro. 0.55 = buraco grande
```

**Mostrar % e label (linha 323):**
```python
textinfo = "percent",   # "percent+label" para mostrar nome do pilar também
```

**Posição da legenda (linhas 329–332):**
```python
legend = dict(orientation="v", x=1.0, y=0.5)
# orientation="h" para legenda horizontal
```

---

## 5. Radar — `chart_pillar_radar()` (linha 341)

**Onde aparece:** Tab 1 (col. direita, linha do meio) e Tab 3.

### O que mostra:
- **Linha azul** (`accent_blue`) com fill transparente → distribuição atual de posts por pilar
- **Linha amarela tracejada** (`accent_yellow`) → target do playbook (`PILLAR_TARGETS`)

### Como modificar:

**Escala máxima do eixo radial (linha 397):**
```python
range = [0, 50],   # ← máximo do eixo. Mude se algum pilar ultrapassar 50%
```

**Cor e estilo da linha Current (linhas 386–388):**
```python
fillcolor = "rgba(80,230,255,0.20)",   # fill azul transparente
line      = dict(color=THEME["accent_blue"], width=2),
```

**Cor e estilo da linha Target (linhas 374–376):**
```python
fillcolor = "rgba(255,185,0,0.07)",   # fill amarelo muito transparente
line      = dict(color=THEME["accent_yellow"], width=2, dash="dash"),
# dash="dash" = linha tracejada. "dot" = pontilhada, "solid" = contínua
```

**Margem/posição da legenda (linha 418):**
```python
legend = dict(orientation="h", y=-0.15)
# y=-0.15 = legenda fica 15% abaixo da área do gráfico
```

---

## 6. FY Pacing Impressões — `chart_fy_pacing()` (linha 429)

**Onde aparece:** Tab 2 (coluna direita, gráfico superior).

### O que mostra:
- **Barras coloridas** → Impressões entregues por mês:
  - Verde (`accent_green`) se o mês bateu o pace mensal necessário
  - Vermelho (`accent_red`) se ficou abaixo
- **Barras cinzas transparentes** → Pace mensal necessário (25M ÷ 12 meses)
- **Linha roxa** (eixo direito) → Target restante acumulado

### Como modificar:

**Cores das barras por condição (linhas 464–467):**
```python
bar_colors = [
    THEME["accent_green"] if imp >= monthly_pace else THEME["accent_red"]
    for imp in full["impressions"]
]
```

**Cor da linha "Remaining Target" (linha 497):**
```python
line = dict(color=THEME["accent_purple"], width=2.5),
```

**Opacidade das barras de pace (linha 487):**
```python
opacity = 0.3,   # 0 = invisível, 1 = sólido
```

---

## 7. Stacked Bar Pilares por Rede — `chart_pillar_by_network()` (linha 540)

**Onde aparece:** Tab 3 (Pillars), em largura total abaixo do radar e donut.

### O que mostra:
Barras horizontais empilhadas com % de cada pilar por rede social.

### Como modificar:

**Largura do gap entre segmentos (linha 573):**
```python
marker_line = dict(color=THEME["bg_page"], width=1.5)
# Aumentar width para gaps mais visíveis entre segmentos
```

**Mostrar % dentro da barra apenas se > 8% (linhas 575–578):**
```python
text = pivot_pct[pillar].apply(
    lambda v: f"{v:.0f}%" if v >= 8 else ""  # ← mude 8 para outro threshold
)
```

---

## 8. Sentimento por Rede — `chart_comments_by_network()` (linha 595)

**Onde aparece:** Tab 1 (coluna central, linha 3).

### O que mostra:
Barras horizontais agrupadas com % de sentimento Positivo e Negativo por rede.  
O label do eixo Y mostra: `"LinkedIn  3.5/post"` (média de comentários por post).

### Como modificar:

**Cores das barras (linhas 657–676):**
```python
# Positivo:
marker_color = THEME["accent_green"]

# Negativo:
marker_color = THEME["accent_red"]
```

**Formato do label Y com avg (linha 653):**
```python
y_tick_labels = [f"{net}  {avg:.1f}/post" for net, avg in ...]
# Para remover o "/post": f"{net}"
```

**Altura dinâmica baseada no número de redes (linha 690):**
```python
height = max(260, len(agg) * 60 + 80)
# Aumenta automaticamente se houver mais redes. Mude o multiplicador 60 se necessário.
```

---

## 9. FY Pacing Posts — `chart_fy_posts()` (linha 712)

**Onde aparece:** Tab 2 (coluna direita, gráfico inferior).

### O que mostra:
Igual ao pacing de impressões, mas para **quantidade de posts**:
- Barras verdes/vermelhas por mês
- Linha amarela (`accent_yellow`) = posts cumulativos (eixo direito)

### Como modificar:

**Meta de posts (linhas 721–722):**
```python
monthly_pace = FY_POSTS_TARGET / n_months
# FY_POSTS_TARGET vem de config.py (padrão: 1.600)
```

**Cor da linha cumulativa (linha 763):**
```python
line = dict(color=THEME["accent_yellow"], width=2.5),
```

---

## Formatação de Números nos Gráficos

```python
def _fmt_impressions(v: float) -> str:   # linha 81
    if v >= 1_000_000: return f"{v/1_000_000:.1f}M"   # 1.5M
    if v >= 1_000:     return f"{v/1_000:.1f}K"        # 500.0K
    return f"{v:.0f}"                                   # 250
```

**Para mudar para 1 casa decimal:** troque `.1f` por `.2f`.  
**Para mostrar em bilhões:** adicione uma condição antes do milhão:
```python
if v >= 1_000_000_000: return f"{v/1_000_000_000:.1f}B"
```

---

## Tooltips (hover) nos Gráficos

Todos os gráficos usam `hovertemplate`. Exemplo:

```python
hovertemplate = "<b>%{x}</b><br>Impressions: %{y:.2s}<extra></extra>"
# %{x}   = valor do eixo X
# %{y}   = valor do eixo Y
# .2s    = formatação científica (1.5M)
# :.2f   = 2 casas decimais
# <extra></extra> = remove o nome do trace do tooltip
```

Para personalizar o tooltip de um gráfico, encontre o `hovertemplate` do trace desejado.
