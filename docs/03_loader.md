# 03 — Dados: Leitura, Filtros e Cálculos (data/loader.py)

> **Arquivo:** [`data/loader.py`](../data/loader.py)  
> Responsável por toda a camada de dados: ler os CSVs, normalizar tipos, calcular métricas derivadas e aplicar os filtros da sidebar.

---

## Arquivos de Dados (linhas 24–26)

```python
DATA_PATH      = Path(__file__).parent.parent / "MSFT_Revised_2026 - RAW DATA (1).csv"
FOLLOWERS_PATH = Path(__file__).parent.parent / "MSFT_Followers - Página1.csv"
COMMENTS_PATH  = Path(__file__).parent.parent / "MSFT_Comments - Total Comments.csv"
```

**Para trocar o arquivo de dados:**  
Substitua o nome do arquivo em `DATA_PATH`. O arquivo deve ficar na raiz do projeto (mesma pasta do `app.py`).

**Formatos suportados:**
- `.csv` — tenta UTF-8, depois UTF-8-sig, depois Latin-1
- `.xlsx` — lê a aba chamada `"RAW DATA"`

---

## `load_raw()` — Linha 33

```python
@st.cache_data(ttl=3600)
def load_raw() -> pd.DataFrame:
```

**O que faz:** Lê o arquivo de dados principal e normaliza tudo.

**`@st.cache_data(ttl=3600)`** = cache de 1 hora.  
O Streamlit guarda o resultado em memória — não relê o arquivo a cada clique do usuário.  
Só relê se o arquivo mudar ou após 60 minutos.

**Chamada em:** `app.py:155`  
```python
df_all = load_raw()
```

---

## `_normalize()` — Linha 244 (função interna)

Esta função é chamada automaticamente por `load_raw()`. Você não chama ela diretamente.

### O que ela faz, linha a linha:

**Renomeia colunas (linhas 255–258):**
```python
# O pipeline grava "pillars" (minúsculo), o dashboard espera "Pillars"
if "pillars" in df.columns and "Pillars" not in df.columns:
    df = df.rename(columns={"pillars": "Pillars"})
```

**Converte datas (linhas 261–262):**
```python
df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
df = df.dropna(subset=["published_date"])
# Posts sem data válida são removidos automaticamente
```

**Preenche colunas de texto vazias (linhas 265–274):**
```python
# Se uma coluna não existe no CSV, cria com "" (string vazia)
# Pilares vazios viram "Unknown" para aparecer nos filtros
df["Pillars"] = df["Pillars"].replace("", "Unknown")
```

**Converte métricas para número (linhas 278–290):**
```python
# Garante que todas as métricas sejam float, mesmo se o CSV tiver texto
# Células vazias ou inválidas viram 0
df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
```

**Calcula ER — Engagement Rate (linhas 295–301):**
```python
df["ER"] = (
    df["gdc_total_engagements_sum"]        # Total Engagements
    / df["gdc_impressions_sum"]            # ÷ Impressions
    * 100                                   # × 100
).fillna(0).round(2)
# Posts com 0 impressões ficam com ER = 0 (evita divisão por zero)
```

**Calcula ER sem swipes — LinkedIn Documents (linhas 303–328):**
```python
# Para posts LinkedIn do tipo Document/PDF, o ER usa apenas:
# Likes + Comments + Shares + Clicks (sem contar swipes)
_doc_types = {"document", "pdf"}
_is_linkedin_doc = (
    (df["social_network"].str.lower() == "linkedin") &
    (df["media_type"].str.lower().isin(_doc_types))
)
df["engagement_wo_swipes"] = df["gdc_total_engagements_sum"].copy()
df.loc[_is_linkedin_doc, "engagement_wo_swipes"] = (
    likes + comments + shares + clicks
)
```
Para adicionar outro tipo de mídia nesse cálculo, inclua no set `_doc_types`.

**Calcula AQE por post (linhas 330–334):**
```python
# AQE = soma de Comments + Shares + Clicks (por linha/post)
# O AQE/post é calculado na exibição (soma ÷ número de posts)
present = [c for c in AQE_COLS if c in df.columns]
df["AQE"] = df[present].sum(axis=1)
```

**Cria colunas de semana e mês (linhas 337–338):**
```python
df["week"]  = df["published_date"].dt.to_period("W").dt.start_time
# "week" = primeiro dia da semana que contém published_date
# Usado para agrupar no gráfico de timeline semanal

df["month"] = df["published_date"].dt.to_period("M").dt.to_timestamp()
# "month" = primeiro dia do mês
# Usado para gráficos mensais e pacing FY
```

---

## `apply_filters()` — Linha 44

```python
def apply_filters(
    df,
    date_start,    # pd.Timestamp — início do período
    date_end,      # pd.Timestamp — fim do período
    networks,      # list[str] — ex: ["LinkedIn", "X"]
    pillars,       # list[str] — ex: ["Educational", "Brand"]
    media_types,   # list[str] — ex: ["Video", "Image"]
    campaigns,     # list[str] — ex: ["Campaign A"]
) -> pd.DataFrame:
```

**Como funciona:**
- Cria uma máscara booleana combinando todos os filtros com `&` (AND)
- Posts com pilar `"Unknown"` passam mesmo que "Unknown" não esteja selecionado
- Posts com `media_type` vazio passam mesmo se não estiver selecionado
- Retorna cópia do DataFrame filtrado

**Chamada em:** `app.py:243–251`

---

## `get_previous_period()` — Linha 83

```python
def get_previous_period(df, date_start, date_end) -> pd.DataFrame:
    delta      = date_end - date_start      # duração do período
    prev_end   = date_start - 1 dia         # termina antes do período atual
    prev_start = prev_end - delta           # mesma duração
```

**Propósito:** gera os dados do período anterior para calcular os deltas (▲▼) dos KPI cards.

**Exemplo:**
- Período atual: 6 Jan – 12 Jan (7 dias)
- Período anterior: 30 Dez – 5 Jan (7 dias)

**Importante:** O período anterior **não** recebe os filtros de pilar/mídia/campanha da sidebar — só o filtro de data e rede. Isso é intencional para comparar o total do período.

---

## `load_followers()` — Linha 107

Carrega o arquivo `MSFT_Followers - Página1.csv`.

**Colunas esperadas no CSV:**
- `Data` — data no formato `DD/MM/AAAA` ou `"February 22"` (assume 2026)
- `seguidores` — número de seguidores (aceita ponto como separador de milhar: `1.077.781`)
- `rede-social` — nome da rede. Mapeamento automático:

```python
_NET_MAP = {
    "IG":      "Instagram",   # Abreviação → nome completo
    "Twitter": "X",
    "X":       "X",
    "LinkedIn":"LinkedIn",
    "TikTok":  "TikTok",
    "Threads": "Threads",
}
```

---

## `get_followers_at()` — Linha 158

```python
def get_followers_at(df_followers, date_end) -> pd.DataFrame:
```

Para cada rede, retorna o registro mais recente com `date <= date_end`.  
Isso garante que o card de Followers mostre o valor correto para o período selecionado (não o dado mais recente do arquivo, que pode ser futuro).

---

## `load_comments()` — Linha 172

Carrega `MSFT_Comments - Total Comments.csv`.

**Colunas esperadas:**
- `SocialNetwork` — nome da rede (mapeado para nome padrão)
- `Sentiment` — `POSITIVE`, `NEUTRAL` ou `NEGATIVE`
- `CreatedTime` — data do comentário

**Usado em:** card de Comments (Tab 1) e gráfico de sentimento (Tab 1).

---

## `get_fy_monthly()` — Linha 199

```python
def get_fy_monthly(df_all) -> pd.DataFrame:
```

Agrupa **todos os dados** (sem filtro de sidebar) por mês dentro do período FY.  
Posts com `Boosted=1` são excluídos — apenas orgânicos contam para a meta.

**Retorna colunas:**
- `month_dt` — data do mês (primeiro dia)
- `impressions` — soma de impressões orgânicas do mês
- `posts` — contagem de posts orgânicos do mês
- `cumulative` — soma acumulada de impressões

**Chamada em:** `app.py:451` (Tab 2 — FY Pacing)

---

## Separação Orgânico vs Boosted

Esta separação acontece em `app.py` (linhas 256–259), não no loader:

```python
_boosted_mask   = df_filtered["Boosted"].fillna(0) == 1
df_organic      = df_filtered[~_boosted_mask]   # sem boosted → métricas
df_prev_organic = df_prev[~_boosted_mask_p]     # sem boosted → deltas
```

| DataFrame | Posts inclusos | Usado para |
|-----------|---------------|------------|
| `df_filtered` | Todos (incluindo boosted) | Contagem de Posts no KPI card |
| `df_organic` | Só orgânicos | Impressions, ER, AQE, todos os gráficos |
| `df_prev` | Todos | Delta do Posts card |
| `df_prev_organic` | Só orgânicos | Delta de Impressions, ER, AQE |
