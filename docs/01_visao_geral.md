# 01 — Visão Geral do Dashboard

## O que é esse projeto?

É um painel de analytics das redes sociais da Microsoft Learn.  
Você abre no navegador, escolhe filtros (período, rede social, etc.) e vê os dados automaticamente.  
Construído com Python + Streamlit — sem precisar de JavaScript ou servidor web complexo.

---

## Como os arquivos se encaixam

```
Dash/
│
├── app.py              → o "palco" — monta tudo junto (635 linhas)
├── config.py           → as "configurações" — cores, metas, nomes (125 linhas)
│
├── data/
│   └── loader.py       → lê e prepara os dados do CSV (341 linhas)
│
├── components/
│   ├── kpis.py         → os cards de números no topo (530 linhas)
│   ├── charts.py       → todos os gráficos (796 linhas)
│   └── posts.py        → os cards de Top/Bottom posts (129 linhas)
│
├── Pipeline_Local.py   → script de limpeza de dados (roda manualmente)
│
├── MSFT_Revised_2026 - RAW DATA (1).csv   ← fonte principal
├── MSFT_Followers - Página1.csv           ← seguidores
└── MSFT_Comments - Total Comments.csv    ← comentários + sentimento
```

---

## Fluxo de dados

```
CSV (dados brutos)
      ↓
  loader.py  (lê, normaliza, calcula ER/AQE, cache 1h)
      ↓
   app.py    (aplica filtros da sidebar, separa orgânico/boosted)
      ↓
  charts / kpis / posts  (exibe na tela)
```

---

## As 5 Tabs

| Tab | Nome | O que mostra |
|-----|------|-------------|
| 1 | Overview | KPIs + Timeline + Radar + Sentimento |
| 2 | FY Pacing | Gauge de % do target anual + gráficos mensais |
| 3 | Pillars | Radar + Donut + Stacked bar por rede |
| 4 | Networks | Tabela comparativa + gráfico por rede |
| 5 | Top / Bottom | Cards dos 5 melhores e 5 piores posts |

---

## Como rodar localmente

```bash
# Opção 1 (recomendado)
python run.py

# Opção 2
streamlit run app.py
```

Abre em: `http://localhost:8501`

---

## Para documentação detalhada

| Documento | Conteúdo |
|-----------|---------|
| [02_config.md](02_config.md) | Cores, metas, targets — tudo em `config.py` |
| [03_loader.md](03_loader.md) | Carregamento e cálculo de dados |
| [04_components.md](04_components.md) | App principal: sidebar, tabs, layout |
| [05_graficos.md](05_graficos.md) | Cada gráfico explicado com modificações |
| [06_kpis.md](06_kpis.md) | Cards de KPI e Followers |
| [07_posts.md](07_posts.md) | Cards de Top/Bottom Posts |
