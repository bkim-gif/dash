# 01 — Estrutura e Fluxo do Projeto

## Árvore de Arquivos

```
Dash/
│
├── run.py                          ← Ponto de entrada: inicia o Streamlit
├── app.py                          ← Arquivo PRINCIPAL do dashboard
├── config.py                       ← Todas as constantes (cores, metas, labels)
│
├── data/
│   └── loader.py                   ← Lê arquivos, filtra dados, calcula métricas
│
├── components/
│   ├── kpis.py                     ← Cards de KPI (Posts, Impressões, ER, AQE, Followers)
│   ├── charts.py                   ← Todos os gráficos Plotly
│   └── posts.py                    ← Cards de Top/Bottom posts
│
├── Pipeline_Local.py               ← Script de limpeza de dados (roda manualmente)
│
├── MSFT_Revised_2026 - RAW DATA (1).csv   ← Fonte principal de dados
├── MSFT_Followers - Página1.csv           ← Dados de seguidores
└── MSFT_Comments - Total Comments.csv    ← Dados de comentários + sentimento
```

---

## Fluxo Completo de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│  1. FONTE (arquivos CSV/Excel)                                  │
│     RAW DATA + Followers + Comments                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. data/loader.py                                              │
│     load_raw() → lê + normaliza tipos + calcula ER e AQE       │
│     @st.cache_data(ttl=3600) → cache de 1 hora                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. app.py — Sidebar                                            │
│     Usuário define: período, pilares, media type, campanha      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. apply_filters()                                             │
│     Retorna df_filtered (todos os posts do período + filtros)   │
│                                                                 │
│     Derivados:                                                  │
│     df_organic      = df_filtered sem Boosted == 1              │
│     df_prev         = período anterior (mesmo tamanho)          │
│     df_prev_organic = df_prev sem Boosted == 1                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. components/ — renderização                                  │
│     kpis.py    → render_kpi_row() na Tab 1                      │
│     charts.py  → gráficos em todas as tabs                      │
│     posts.py   → Top/Bottom na Tab 5                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## O que cada arquivo faz — resumo

### `run.py`
Só serve para iniciar o app. Garante que o Streamlit rode dentro da pasta correta.  
Você **não precisa editar** este arquivo.

### `config.py`
**O arquivo mais importante para customização.**  
Contém todas as constantes: cores, metas, targets, labels.  
Para adaptar o dashboard para outro cliente, edite apenas este arquivo (e os caminhos em `loader.py`).

### `app.py`
O cérebro do dashboard. Orquestra tudo:
- Define a página (layout, CSS global)
- Carrega os dados via `loader.py`
- Renderiza a sidebar com os filtros
- Renderiza a barra de filtro de redes sociais
- Cria as 5 tabs e chama os componentes corretos em cada uma

### `data/loader.py`
Responsável por dados:
- Ler e cachear os arquivos CSV/Excel
- Normalizar tipos (datas, números, strings)
- Calcular métricas derivadas (ER, AQE, ER sem swipes)
- Aplicar filtros da sidebar
- Retornar período anterior para comparação

### `components/kpis.py`
Renderiza os 5 cards do topo de tela (Posts, Impressões, ER, AQE, Followers) e o card de Comments.

### `components/charts.py`
Contém os 8 gráficos Plotly do dashboard:
1. Timeline (linha do tempo semanal/mensal)
2. Impressões por rede (barras horizontais)
3. ER por rede
4. Donut de pilares
5. Radar Current vs Target
6. FY Pacing de impressões
7. Stacked bar pilares por rede
8. Sentimento de comentários por rede
9. FY Pacing de posts

### `components/posts.py`
Renderiza os cards de Top 5 e Bottom 5 posts com métricas e link.

### `Pipeline_Local.py`
Script **independente** do dashboard. Roda manualmente quando chega nova exportação do Sprinklr.  
Faz limpeza, deduplicação e gera o arquivo RAW DATA que o dashboard consome.

---

## Separação Orgânico vs Boosted

Este é um conceito central do dashboard:

```python
# Em app.py (linha 256–259)
_boosted_mask   = df_filtered["Boosted"].fillna(0) == 1
df_organic      = df_filtered[~_boosted_mask]   # ← posts SEM boosted
```

| Métrica | Usa df_filtered (com boosted) | Usa df_organic (sem boosted) |
|---------|-------------------------------|-------------------------------|
| Posts (contagem) | ✅ | — |
| Impressions | — | ✅ |
| ER | — | ✅ |
| AQE | — | ✅ |
| FY Pacing | — | ✅ |

---

## Período Anterior (Delta dos KPIs)

Os cards mostram seta ▲▼ comparando com o período anterior de **mesmo tamanho**.

```python
# Em data/loader.py (linha 83–103)
def get_previous_period(df, date_start, date_end):
    delta      = date_end - date_start        # duração do período atual
    prev_end   = date_start - 1 dia           # termina 1 dia antes do início atual
    prev_start = prev_end - delta             # mesma duração
```

**Exemplo:** Selecionou Jan 6–12 (7 dias) → período anterior = Dez 30–Jan 5.

---

## Session State — Filtro de Rede

O botão de rede no topo da página usa `st.session_state`:

```python
# Inicializado em app.py (linha 167–168)
if "sel_network" not in st.session_state:
    st.session_state.sel_network = "ALL"

# Modificado ao clicar no botão (linha 307–308)
def _set_network(net: str):
    st.session_state.sel_network = net
```

Isso permite que o filtro persista entre interações sem recarregar a página.
