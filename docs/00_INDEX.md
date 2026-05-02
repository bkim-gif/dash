# Apostila do Dashboard — Microsoft Learn Social Analytics

> **Como usar esta apostila:**  
> Cada arquivo cobre uma parte do projeto. Comece pelo `01_visao_geral` para entender o fluxo, depois vá direto ao arquivo da parte que quer modificar.

---

## Índice de Documentos

| # | Arquivo | O que você encontra |
|---|---------|---------------------|
| 1 | [01_visao_geral.md](01_visao_geral.md) | Visão geral, fluxo de dados, como os arquivos se conectam |
| 2 | [02_config.md](02_config.md) | **Cores, metas, targets, labels** — tudo que muda com frequência |
| 3 | [03_loader.md](03_loader.md) | Como os dados são lidos, filtrados e calculados |
| 4 | [04_components.md](04_components.md) | App principal: sidebar, header, filtro de redes, tabs |
| 5 | [05_graficos.md](05_graficos.md) | Cada gráfico: o que faz, onde fica, como modificar |
| 6 | [06_kpis.md](06_kpis.md) | Cards de KPI (Posts, Impressões, ER, AQE, Followers) |
| 7 | [07_posts.md](07_posts.md) | Tab Top/Bottom — cards de posts individuais |

---

## Referência Rápida — "Onde mudo X?"

| Quero mudar… | Arquivo | Linha |
|---|---|---|
| Cor de uma rede social | [config.py](../config.py) | L41–48 |
| Cor de um pilar | [config.py](../config.py) | L54–60 |
| Fundo escuro da página | [config.py](../config.py) | L67 — `bg_page` |
| Meta anual de impressões (25M) | [config.py](../config.py) | L20 — `FY_TARGET` |
| Meta anual de posts (1.600) | [config.py](../config.py) | L21 — `FY_POSTS_TARGET` |
| Período do FY (Aug–Jul) | [config.py](../config.py) | L22–23 |
| Targets do radar por pilar | [config.py](../config.py) | L30–36 |
| Número de Top/Bottom posts (5) | [config.py](../config.py) | L124 — `TOP_N` |
| Arquivo de dados principal | [data/loader.py](../data/loader.py) | L24 — `DATA_PATH` |
| Arquivo de seguidores | [data/loader.py](../data/loader.py) | L25 — `FOLLOWERS_PATH` |
| Arquivo de comentários | [data/loader.py](../data/loader.py) | L26 — `COMMENTS_PATH` |
| Altura de um gráfico | [app.py](../app.py) | `fig.update_layout(height=...)` |
| Nome das tabs | [app.py](../app.py) | L387–393 |
| Fonte global da página | [app.py](../app.py) | L61 |
| Cor das barras do timeline | [components/charts.py](../components/charts.py) | L142 |
| Cor da linha ER no timeline | [components/charts.py](../components/charts.py) | L154 |
| Cor do gauge FY | [app.py](../app.py) | L476 |
| Período padrão da sidebar | [app.py](../app.py) | L194–197 |
| Tamanho dos números nos KPI cards | [components/kpis.py](../components/kpis.py) | `font-size:24px` |
| Intensidade do glow nos post cards | [components/posts.py](../components/posts.py) | L23/L28 |
| Tamanho máximo do texto do post | [components/posts.py](../components/posts.py) | L34 |

---

## Stack Tecnológica

```
Python 3.11+
├── streamlit      → interface web (sem JS necessário)
├── pandas         → manipulação de dados
├── plotly         → gráficos interativos
└── openpyxl       → leitura de arquivos .xlsx
```

**Para rodar:**
```bash
python run.py
# ou diretamente:
streamlit run app.py
```

---

## Conceitos Chave

**Orgânico vs Boosted:** Posts com `Boosted=1` são excluídos das métricas de Impressions, ER e AQE, mas contam na métrica de Posts.

**Período Anterior:** Os cards comparam com um período de mesmo tamanho imediatamente antes. Ex: semana atual vs semana passada.

**ER w/o Swipes:** Para posts LinkedIn do tipo Document/PDF, o ER exclui swipes e usa: Likes + Comments + Shares + Clicks.

**AQE (Average Qualified Engagement):** Comments + Shares + Clicks dividido pelo número de posts. Não inclui Likes (configura em `config.py → AQE_COLS`).
