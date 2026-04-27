# components/ — Blocos Visuais do Dashboard

Cada arquivo dentro de `components/` é responsável por um tipo de visual.
O `app.py` chama essas funções e coloca cada coisa no lugar certo na tela.

---

## kpis.py — Cards de Números

Renderiza os 5 KPI cards do topo da aba Overview:

| Card         | Métrica                          |
|--------------|----------------------------------|
| Impressions  | Soma de impressões no período    |
| Engagements  | Soma de engajamentos             |
| ER           | Média de Engagement Rate (%)     |
| Posts        | Número de posts publicados       |
| AQE/post     | Média de AQE por post            |

Cada card mostra também o **delta** (▲ ou ▼) em relação ao período anterior.
O delta fica verde se melhorou, vermelho se piorou.

---

## charts.py — Gráficos

Todos os gráficos usam a biblioteca **Plotly** (interativos — dá pra dar hover, zoom e exportar PNG).

| Função                  | Onde aparece         | O que mostra                              |
|-------------------------|----------------------|-------------------------------------------|
| `chart_timeline()`      | Overview             | Linha do tempo de impressões (sem/mensal) |
| `chart_by_network()`    | Overview / Networks  | Barras de impressões por rede             |
| `chart_er_by_network()` | Overview / Networks  | ER médio por rede                         |
| `chart_pillar_donut()`  | Pillars              | Donut de distribuição por pilar           |
| `chart_pillar_radar()`  | Pillars              | Radar atual vs target por pilar           |
| `chart_pillar_by_network()` | Pillars          | Stacked bar por rede e pilar              |
| `chart_fy_pacing()`     | FY Pacing            | Linha mensal vs meta acumulada            |

Todos os gráficos compartilham o mesmo `_base_layout()` — fundo transparente, fonte, cores da grade.

---

## posts.py — Cards Top/Bottom

Renderiza os cards da aba "Top / Bottom Posts".

Cada card mostra:
- **Badge da rede** (cor da rede)
- **Texto do post** (truncado em 140 caracteres)
- **Métricas:** Impressões, Engajamentos, ER, Likes, Comentários, Shares, Clicks
- **Link** para o post original (↗ View post)

Os posts são ordenados pela métrica escolhida na sidebar (ex: Total Engagement, Impressions...).

**Top 5** → borda verde, ícone ▲
**Bottom 5** → borda vermelha, ícone ▼

Para mostrar mais posts, mude `TOP_N` em `config.py`.
