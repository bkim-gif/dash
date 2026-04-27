# data/loader.py — Leitura e Preparação dos Dados

## O que faz?

Lê o arquivo CSV com os dados brutos e entrega um DataFrame limpo para o app.
É o único arquivo que sabe onde o CSV está e como ele é estruturado.

---

## load_raw()

```python
@st.cache_data(ttl=3600)
def load_raw() -> pd.DataFrame:
```

Lê o CSV e normaliza os dados. O `@st.cache_data` guarda o resultado em memória por 1 hora —
ou seja, ele não relê o arquivo a cada clique. Só relê se o arquivo mudar ou após 1h.

**Para trocar o arquivo de dados:**
```python
DATA_PATH = Path(__file__).parent.parent / "SEU_ARQUIVO.csv"
```

---

## apply_filters()

Aplica os filtros escolhidos na sidebar:
- Período (data início e fim)
- Redes sociais
- Pilares
- Tipo de mídia
- Campanha

Retorna só as linhas que passam em todos os filtros.

---

## get_previous_period()

Calcula o período anterior de mesmo tamanho para mostrar os deltas (▲▼) nos KPI cards.

**Exemplo:** se você selecionou Jan 6–12 (7 dias), ele busca Dez 30–Jan 5 (7 dias anteriores).

---

## get_fy_monthly()

Agrupa todos os dados por mês para o gráfico de pacing do FY.
Posts com `Boosted = 1` são excluídos (não contam para a meta orgânica).
Retorna uma coluna `cumulative` com a soma acumulada de impressões mês a mês.

---

## _normalize()

Função interna que garante que os dados chegam padronizados:

| O que faz                  | Por quê                                         |
|----------------------------|-------------------------------------------------|
| Converte datas             | O CSV pode ter datas em formatos diferentes     |
| Preenche células vazias    | Evita erros nos gráficos                        |
| Calcula ER                 | ER = Total Engagements / Impressions × 100      |
| Calcula AQE                | AQE = Comments + Shares + Clicks                |
| Adiciona coluna `week`     | Para agrupar no gráfico semanal                 |
