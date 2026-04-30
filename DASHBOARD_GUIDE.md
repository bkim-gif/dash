# Dashboard Guide — Funções, Gráficos e Como Modificar

> Atualizado: 2026-04-30
> Arquivo de referência para modificações rápidas no dashboard.

---

## Estrutura de Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Layout principal, sidebar, tabs, filtros |
| `config.py` | Todas as constantes (cores, targets, labels) |
| `data/loader.py` | Leitura do CSV, normalização, cálculo de ER/AQE |
| `components/kpis.py` | Cards de KPI do topo |
| `components/charts.py` | Todos os gráficos Plotly |
| `components/posts.py` | Cards Top/Bottom posts |

---

## `config.py` — Constantes

| Constante | O que é | Como modificar |
|---|---|---|
| `CLIENT["name"]` | Nome exibido no sidebar | Troque a string |
| `FY_TARGET` | Meta de impressões do FY (25M) | Troque o número |
| `FY_START / FY_END` | Período do FY | Troque as strings `"YYYY-MM-DD"` |
| `PILLAR_TARGETS` | % alvo de cada pilar no radar | Troque os valores numéricos |
| `NETWORK_COLORS` | Cor hex de cada rede social | Troque o código hex |
| `THEME` | Todas as cores do tema escuro | Troque os valores hex |
| `AQE_COLS` | Colunas que compõem o AQE | Adicione/remova colunas |
| `SORT_OPTIONS` | Opções de ordenação dos cards Top/Bottom | Adicione um par `"Label": "coluna"` |
| `TOP_N` | Quantos posts Top e Bottom exibir | Troque o número |

---

## `data/loader.py` — Funções

### `load_raw()`
Lê o arquivo CSV/Excel e normaliza os dados. Cacheia por 1h.
- **Para trocar o arquivo de dados:** edite `DATA_PATH` no topo do arquivo.
- **Para adicionar uma nova coluna numérica:** inclua o nome em `num_cols` dentro de `_normalize()`.
- **Para adicionar uma nova coluna de texto:** inclua o nome no loop `for col in [...]` dentro de `_normalize()`.

### `apply_filters(df, date_start, date_end, networks, pillars, media_types, campaigns)`
Aplica os filtros da sidebar ao DataFrame completo.
- **Para adicionar um novo filtro:** adicione um parâmetro, uma condição `mask &= ...` e um widget correspondente na sidebar em `app.py`.

### `get_previous_period(df, date_start, date_end)`
Retorna o período anterior de mesmo tamanho (usado nos deltas dos KPIs).
- **Para desativar o delta:** comentado diretamente em `components/kpis.py` (ver item 3).

### `get_fy_monthly(df_all)`
Agrega dados por mês para o gráfico de pacing FY. Exclui posts com `Boosted=1`.
- **Para incluir posts boosted:** remova o bloco `if "Boosted" in df_all.columns`.

### `_normalize(df)` (interna)
Normaliza tipos, calcula `ER`, `ER_wo_swipes`, `AQE`, `week`, `month`.

**Cálculo do ER w/o swipes (LinkedIn Document/Pdf):**
```python
# Em _normalize(), procure _doc_types e _is_linkedin_doc
_doc_types = {"document", "pdf"}   # <- adicione tipos aqui se necessário
```
- Para incluir outro media_type no cálculo w/o swipes: adicione o nome (em minúsculas) ao set `_doc_types`.
- Para mudar a fórmula do engagement w/o swipes: edite a linha `df.loc[_is_linkedin_doc, "engagement_wo_swipes"] = ...`.

---

## `components/kpis.py` — Cards de KPI

### `render_kpis(df_current, df_previous)`
Renderiza os 4 cards: Posts | Impressions | Eng. Rate | AQE/post.

**Para adicionar um novo card:**
1. Calcule a métrica no bloco "Calcula métricas do período atual".
2. Adicione um dict em `cards = [...]` com as chaves: `label`, `value`, `raw_cur`, `raw_prev`.
3. Adicione mais uma coluna em `cols = st.columns(4)` → mude para `st.columns(5)`.

**Para reativar o delta "vs prev period":**
Localize o comentário `# Item 3` e descomente o bloco. Remova as linhas `delta_str = ""` e `delta_color = ...`.

**Card ER — formato atual:**
Exibe `X.X% / Y.Y%` (ER padrão / ER w/o swipes) com nota `*w/o swipes` abaixo.
- Para exibir só o ER padrão: volte `"value": _fmt(er_cur, is_pct=True)` e remova `"er_note"`.

---

## `components/charts.py` — Gráficos

### `_base_layout(**overrides)`
Layout base compartilhado por todos os gráficos (fundo transparente, grid, fonte).
- **Para mudar a fonte de todos os gráficos:** edite `family` dentro de `font=dict(...)`.
- **Para mudar a cor do grid:** edite `THEME["grid_line"]` em `config.py`.

---

### `chart_timeline(df, granularity)` — Performance Over Time
Barras (Impressions) + linha suave (ER w/o swipes).

| O que mudar | Onde |
|---|---|
| Série da linha (ex: voltar para Engagement) | Troque `"engagement_wo_swipes"` por `"gdc_total_engagements_sum"` no `agg` e remova `er_wo_swipes` |
| Tornar linha reta | Remova `shape="spline"` do dict `line=` |
| Mover a legenda | Ajuste `x` e `y` no dict `legend=` no final da função (0=esquerda/baixo, 1=direita/topo) |
| Tamanho da fonte da legenda | `font=dict(size=13)` no dict `legend=` |
| Cor das barras | `marker_color=THEME["accent_purple"]` no `go.Bar` |
| Default de data | Veja `app.py` → `default_start` (atualmente FY26 start) |

---

### `chart_by_network(df)` — Impressions by Network
Barras horizontais de impressões por rede, coloridas por `NETWORK_COLORS`.
- **Para adicionar AQE/post como segundo eixo:** adicione um `go.Bar` com `yaxis="y2"` usando `agg["aqe_per_post"]`.
- **Para mudar a ordenação:** troque `.sort_values("impressions", ascending=True)` pela coluna desejada.

---

### `chart_er_by_network(df)` — Engagement Rate by Network *(removido da UI)*
Barras horizontais de ER médio por rede.
> **Removido do Tab 1 e Tab 4 (item 7).** A função ainda existe no código.
> Para reativar: descomente os blocos marcados com `# Item 7` em `app.py`.

---

### `chart_pillar_donut(df)` — Posts by Pillar
Donut com % de posts por pilar. Remove "Unknown" da visualização.
- **Para mudar as cores dos pilares:** edite a lista `pillar_colors` dentro da função.
- **Para mostrar o valor absoluto em vez de %:** troque `textinfo="percent"` por `textinfo="value"` ou `"label+value"`.

---

### `chart_pillar_radar(df)` — Pillar Distribution vs Target
Radar com distribuição atual vs target do playbook.
- **Para mudar os targets:** edite `PILLAR_TARGETS` em `config.py`.
- **Para mudar o range do eixo radial:** edite `range=[0, 50]` em `radialaxis`.
- **Para mudar as cores:** `THEME["accent_blue"]` = Current, `THEME["accent_yellow"]` = Target.

---

### `chart_pillar_by_network(df)` — Pillar Mix by Network
Barras horizontais empilhadas (100%) mostrando mix de pilares por rede.
- **Para mudar as cores dos pilares:** edite `pillar_colors` dentro da função.
- **Para mostrar valores absolutos em vez de %:** remova `pivot_pct = pivot.div(...) * 100` e use `pivot` diretamente.

---

### `chart_fy_pacing(monthly_df)` — FY 2026 Pacing
Barras mensais (verde=bateu o pace, vermelho=não bateu) + linha de target restante.
- **Para mudar o target:** edite `FY_TARGET` em `config.py`.
- **Para mudar o período do FY:** edite `FY_START` e `FY_END` em `config.py`.
- **Para mudar as cores das barras:** edite `THEME["accent_green"]` e `THEME["accent_red"]`.

---

## `app.py` — Layout e Filtros

### Sidebar — filtros disponíveis
| Filtro | Widget | Variável resultante |
|---|---|---|
| Período | `st.date_input` | `date_start`, `date_end` |
| Granularidade | `st.radio` | `granularity` ("Weekly"/"Monthly") |
| Pillars | `st.multiselect` | `pillars` |
| Media Type | `st.multiselect` | `media_types` |
| Campaign | `st.multiselect` | `campaigns` |
| Sort posts by | `st.selectbox` | `sort_by` |

### Network Filter Bar (botões no topo)
- **Para mudar o tamanho da fonte dos labels:** edite `font-size: 12px` no CSS com comentário `Item 1`.
- **Para adicionar uma nova rede:** adicione entrada em `_NETWORK_SVG` e `NETWORK_COLORS` em `config.py`.

### Tabs
| Tab | Conteúdo |
|---|---|
| Tab 1 — Overview | KPIs + Timeline + Impressions by Network + Radar |
| Tab 2 — FY Pacing | Gauge + gráfico mensal de pacing |
| Tab 3 — Pillars | Radar + Donut + Stacked bar + tabela |
| Tab 4 — Networks | Tabela comparativa + Impressions by Network |
| Tab 5 — Top/Bottom | Cards dos melhores e piores posts |

---

## Modificações rápidas comuns

| Quero... | Onde mexer |
|---|---|
| Mudar cor de uma rede | `NETWORK_COLORS` em `config.py` |
| Mudar meta do FY | `FY_TARGET` em `config.py` |
| Mudar fonte dos botões de rede | CSS `Item 1` em `app.py` (~linha 308) |
| Reativar delta "vs prev period" | Comentário `Item 3` em `kpis.py` |
| Voltar default de data para última semana | `default_start` em `app.py` (~linha 180) |
| Linha do timeline: ER → Engagement | `chart_timeline()` em `charts.py` |
| Reativar "ER by Network" no Tab 1 | Comentário `Item 7` em `app.py` (~linha 382) |
| Incluir novo media_type no ER w/o swipes | `_doc_types` em `loader.py` (~linha 204) |
| Aumentar N° de posts Top/Bottom | `TOP_N` em `config.py` |
