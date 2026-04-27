# Visão Geral do Dashboard

## O que é esse projeto?

É um painel de analytics das redes sociais da Microsoft Learn.
Você abre no navegador, escolhe filtros (período, rede social, etc.) e vê os dados automaticamente.

## Como os arquivos se encaixam

```
Dash/
│
├── app.py              → o "palco" — monta tudo junto
├── config.py           → as "configurações" — cores, metas, nomes
│
├── data/
│   └── loader.py       → lê e prepara os dados do CSV
│
├── components/
│   ├── kpis.py         → os cards de números (Impressões, ER, etc.)
│   ├── charts.py       → todos os gráficos (linhas, barras, radar...)
│   └── posts.py        → os cards de Top/Bottom posts
│
├── .streamlit/
│   └── config.toml     → tema escuro para o Streamlit Cloud
│
└── publicar.sh         → script para publicar no Streamlit Cloud
```

## Fluxo de dados

```
CSV (dados brutos)
      ↓
  loader.py  (lê, limpa e calcula ER/AQE)
      ↓
   app.py    (aplica filtros da sidebar)
      ↓
  charts / kpis / posts  (exibe na tela)
```

## Como rodar localmente

```bash
streamlit run app.py
```

## Como publicar na internet

```bash
./publicar.sh
```
