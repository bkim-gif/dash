# 04 — App Principal: Sidebar, Header e Tabs (app.py)

> **Arquivo:** [`app.py`](../app.py)  
> É o arquivo central — orquestra tudo. Renderiza a interface, aplica filtros e chama os componentes certos em cada tab.

---

## Configuração da Página (linhas 49–54)

```python
st.set_page_config(
    page_title = f"{CLIENT['name']} · Analytics",   # Título da aba do navegador
    page_icon  = "📊",                               # Ícone da aba do navegador
    layout     = "wide",                             # Layout expandido (sem coluna central)
    initial_sidebar_state = "expanded",              # Sidebar aberta por padrão
)
```

**Para mudar o ícone:** substitua `"📊"` por qualquer emoji ou caminho para `.ico`.  
**Para layout normal (não wide):** mude `"wide"` para `"centered"`.

---

## CSS Global / Fonte (linhas 59–149)

```python
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
  # ↑ Linha 61 — Troque a fonte aqui. Ex: 'Inter', 'DM Sans', 'Roboto'

  html, body, [class*="css"] ... { font-family: 'Poppins', sans-serif !important; }

  .stApp { background-color: {THEME['bg_page']}; }
  # ↑ Linha 68 — Cor de fundo da página inteira

  .block-container { padding-top: 1.5rem !important; }
  # ↑ Linha 71 — Espaço no topo da página. Aumente para mais espaço.
""")
```

### Partes do CSS que você pode querer modificar

| Linhas | O que controla | Como modificar |
|--------|----------------|----------------|
| 61 | Fonte da página | Troque `'Poppins'` pelo nome de outra Google Font |
| 68 | Cor de fundo | Via `THEME["bg_page"]` em `config.py` |
| 71 | Padding do topo | Mude `1.5rem` para mais ou menos espaço |
| 74–77 | Cor da sidebar | Via `THEME["bg_card"]` e `THEME["border"]` |
| 80–95 | Estilo das tabs | Cor, raio, padding das abas |
| 92–95 | Tab selecionada | Cor de fundo e texto da tab ativa |
| 98 | Linha divisória (hr) | Cor e margin |
| 104–110 | Labels do sidebar | Tamanho, uppercase, letter-spacing |
| 113–120 | Cabeçalhos de seção | `.section-header` — mude `font-size`, `color` |
| 123–133 | Tags do multiselect | Cor roxa das tags dos filtros |
| 136–147 | Calendar date picker | Cores do calendário |

---

## Carregamento de Dados (linhas 155–168)

```python
df_all       = load_raw()         # Dados principais (cache 1h)
df_followers = load_followers()   # Seguidores por rede
df_comments  = load_comments()    # Comentários + sentimento

# Inicializa filtro de rede como "ALL"
if "sel_network" not in st.session_state:
    st.session_state.sel_network = "ALL"
```

---

## Sidebar — Filtros (linhas 174–231)

### Período (linhas 186–207)

```python
# Padrão: inicia no início do FY (Aug 2025) ou na data mínima dos dados
default_start = max(min_date, _fy26_start)

date_start = st.date_input("From", value=default_start, ...)
date_end   = st.date_input("To",   value=max_date, ...)

# Granularidade do gráfico de timeline
granularity = st.radio("Granularity", options=["Weekly", "Monthly"], horizontal=True)
```

**Para mudar o período padrão para "última semana":**  
Linha 194, descomente a linha comentada:
```python
# Troque por:
default_start = max_date - pd.Timedelta(days=6)
```

### Pilares (linhas 212–214)

```python
all_pillars = sorted([p for p in df_all["Pillars"].unique() if p != "Unknown"])
# "Unknown" é excluído das opções — posts sem pilar passam nos filtros mas não aparecem aqui
pillars = st.multiselect("", options=all_pillars, default=all_pillars, ...)
```

### Media Type (linhas 217–219)

```python
all_media = sorted([m for m in df_all["media_type"].unique() if pd.notna(m) and str(m).strip()])
media_types = st.multiselect("", options=all_media, default=all_media, ...)
```

### Campanha (linhas 222–224)

```python
all_campaigns = sorted(df_all["campaign_name"].unique().tolist())
campaigns = st.multiselect("", options=all_campaigns, default=all_campaigns, ...)
```

### Sort Posts By (linhas 229–230)

```python
sort_by = st.selectbox("", options=list(SORT_OPTIONS.keys()), index=0, ...)
# SORT_OPTIONS vem de config.py
```

---

## Barra de Filtro de Redes (linhas 291–381)

Esta barra mostra botões visuais com ícone circular + nome da rede no topo da área principal.

### Ícones SVG (linhas 294–301)

Cada rede tem um ícone SVG inline. Para modificar o tamanho do ícone:
```python
# Linha 295–301 — encontre a rede e mude width/height
"Instagram": '<svg ... width="26" height="26">...'
#                          ↑ tamanho em px
```

### Tamanho do círculo (linhas 319–321)

```python
.net-icon-circle {
    width: 54px;    # ← tamanho do círculo em px
    height: 54px;
    border-radius: 50%;
}
```

### Tamanho da fonte dos labels dos botões (linhas 337–341)

```python
[data-testid="stButton"] button p {
    font-size: 12px !important;   # ← fonte do nome da rede embaixo do ícone
}
```

### Como a seleção funciona (linhas 352–379)

```python
for _col, _net in zip(_cols, _items):
    _is_active = (st.session_state.sel_network == _net)
    # Se ativo → type="primary" (destaque), se inativo → opacity 0.4
    if st.button(_label, type="primary" if _is_active else "secondary", ...):
        st.rerun()   # Atualiza toda a página ao clicar
```

---

## Header Principal (linhas 270–286)

```python
col_title, col_period = st.columns([3, 1])
# Proporção 3:1 — título ocupa 75%, período ocupa 25%

with col_title:
    # "Social Analytics" em h1 (linha 273)
    font-size: 24px; font-weight: 700

with col_period:
    # Período selecionado + contagem de posts (linha 279–282)
    # "Jan 06 — Apr 30, 2026 \n 1234 posts"
```

Para mudar o título de "Social Analytics", edite a linha 274.

---

## Tabs (linhas 387–393)

```python
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",      # Tab 1
    "FY Pacing",     # Tab 2
    "Pillars",       # Tab 3
    "Networks",      # Tab 4
    "Top / Bottom",  # Tab 5
])
```

Para renomear uma tab, troque o texto dentro da lista.  
Para adicionar uma tab: adicione um item e crie o bloco `with tab6:` correspondente.

---

## Tab 1 — Overview (linhas 399–443)

### Linha 1: KPI Cards (linhas 402–407)
```python
render_kpi_row(
    df_filtered, df_prev, df_organic, df_prev_organic,
    selected_network = _sel_net,
    df_followers     = df_followers,
    date_end         = date_end_ts,
)
# Renderiza 5 cards: Posts | Impressions | ER | AQE | Followers
```

### Linha 2: Timeline + Radar (linhas 410–418)
```python
col_tl, col_rd = st.columns([3, 2])
# Proporção 3:2 — timeline ocupa 60%, radar ocupa 40%

fig_tl.update_layout(height=260)   # ← altura do timeline em px
fig_rd.update_layout(height=260)   # ← altura do radar em px
```

Para tornar o timeline mais alto: aumente `height=260` para `height=320`.

### Linha 3: Comments + Sentimento + Impressões por Rede (linhas 421–443)
```python
col_comm, col_sent, col_net = st.columns([1, 2, 1])
# Proporção 1:2:1 — comments ocupa 25%, sentimento 50%, redes 25%

fig_sent.update_layout(height=280)   # ← altura do gráfico de sentimento
fig_net.update_layout(height=280)    # ← altura do gráfico de redes
```

---

## Tab 2 — FY Pacing (linhas 449–522)

### Gauge (linhas 460–496)
```python
fig_gauge = go.Figure(go.Indicator(
    mode  = "gauge+number+delta",
    value = pct_fy,                          # % atingido do target
    title = dict(text="FY 2026 Target", ...),
    number= dict(suffix="%", font=dict(size=40)),   # ← tamanho do número %
    gauge = dict(
        bar = dict(color=THEME["accent_blue"]),      # ← cor da barra do gauge
        steps = [
            dict(range=[0, 50],  color=THEME["bg_card2"]),    # seção 0-50%
            dict(range=[50, 80], color="#1E3A2F"),             # seção 50-80% (verde escuro)
            dict(range=[80,100], color="#1A3A2A"),             # seção 80-100%
        ],
        threshold = dict(
            line  = dict(color=THEME["accent_yellow"], width=3),  # ← linha do target (100%)
            value = 100,
        ),
    ),
))
fig_gauge.update_layout(height=280)   # ← altura do gauge em px
```

### Números Achieved/Remaining (linhas 499–518)
```python
# Bloco HTML embaixo do gauge
# "ACHIEVED": cor accent_blue, fonte 24px
# "REMAINING": cor accent_yellow, fonte 20px
# Para mudar as cores, edite diretamente as linhas 505 e 509
```

### Gráfico de Pacing (linha 521)
```python
st.plotly_chart(chart_fy_pacing(monthly_data), ...)
st.plotly_chart(chart_fy_posts(monthly_data), ...)
```
Ver detalhes em [05_GRAFICOS.md](05_graficos.md).

---

## Tab 3 — Pillars (linhas 528–572)

```python
col_radar, col_donut = st.columns(2)
# Radar e donut lado a lado, mesma largura

st.plotly_chart(chart_pillar_by_network(df_organic), ...)
# Stacked bar em largura total abaixo

# Tabela de métricas por pilar (linhas 543–572)
# Agrupamento: média por pilar de Impressions, Likes, Comments, Shares, Clicks, ER, AQE
```

---

## Tab 4 — Networks (linhas 578–620)

```python
# Tabela comparativa por rede (linhas 581–617)
# Colunas: social_network | Posts | Impressions | Likes | Comments | Shares | Clicks | ER | AQE_post
# Posts = inclui boosted
# Demais métricas = só orgânico
# Ordenado por Impressions decrescente

# Gráfico de barras por rede (linha 620)
st.plotly_chart(chart_by_network(df_organic), ...)
```

---

## Tab 5 — Top / Bottom Posts (linhas 626–635)

```python
# Cabeçalho mostrando critério de ordenação e período
render_top_bottom(df_organic, sort_by)
# sort_by vem do selectbox da sidebar
```

Detalhes do card em [07_POSTS.md](07_posts.md).
