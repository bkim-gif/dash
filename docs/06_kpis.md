# 06 — Cards de KPI (components/kpis.py)

> **Arquivo:** [`components/kpis.py`](../components/kpis.py)  
> Renderiza os 5 cards do topo (Posts, Impressions, ER, AQE, Followers) e o card de Comments.

---

## `render_kpi_row()` — Linha 224

Função principal chamada em `app.py:402`. Renderiza os **5 cards na mesma linha**.

```
┌──────────┐ ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐
│  Posts   │ │Impressions │ │ Eng.Rate │ │ AQE/post │ │ Followers │
│  1,234   │ │   15.3M    │ │   1.2%   │ │   12.5   │ │   1.2M    │
└──────────┘ └────────────┘ └──────────┘ └──────────┘ └───────────┘
```

### Lógica de cada card

| Card | Fonte dos dados | Inclui Boosted? |
|------|----------------|-----------------|
| Posts | `len(df_current)` | ✅ Sim |
| Impressions | `df_organic["gdc_impressions_sum"].sum()` | ❌ Não |
| ER | `total_engagements / impressions * 100` | ❌ Não |
| AQE/post | `(comments + shares + clicks) / n_posts` | ❌ Não |
| Followers | `get_followers_at(df_followers, date_end)` | N/A |

---

## Card de Posts (linhas 327)

```python
with c1:
    st.markdown(_card_html("Posts", _fmt(posts_cur)), unsafe_allow_html=True)
```

Conta **todos** os posts do período, incluindo boosted. Isso é intencional — reflete a atividade total de publicação.

---

## Card de Impressions (linhas 329)

```python
with c2:
    st.markdown(_card_html("Impressions", _fmt(impr_cur)), unsafe_allow_html=True)
```

Soma de `gdc_impressions_sum` dos posts **orgânicos** (sem boosted).

---

## Card de ER — Engagement Rate (linhas 258–265, 331)

```python
# LinkedIn → mostra dois valores: "1.2% / 0.8%"
if selected_network == "LinkedIn":
    er_val = f'{er_padrão} / {er_sem_swipes}'
    # Com ⓘ tooltip: "2nd value excludes swipe interactions"
else:
    er_val = f'{er_padrão}'   # Uma porcentagem só
```

**ER padrão** = `total_engagements / impressions * 100`  
**ER w/o swipes** = para posts LinkedIn Document/PDF: `(likes + comments + shares + clicks) / impressions * 100`

O tooltip aparece ao passar o mouse no ⓘ.

---

## Card de AQE (linhas 333–337)

```python
with c4:
    aqe_label_extra = '<span class="kpi-tooltip-wrap">ⓘ...'
    # Tooltip: "AQE = Comments + Shares + Clicks"
    st.markdown(_card_html("AQE / post", _fmt(aqe_cur), label_extra=aqe_label_extra), ...)
```

**Fórmula:** `(comments + shares + clicks totais) / número de posts orgânicos`

Para mudar a composição do AQE, edite `AQE_COLS` em `config.py`.

---

## Card de Followers (linhas 271–352)

```python
# Se nenhuma rede específica selecionada (ALL):
followers = snap[snap["network"].isin(["LinkedIn","X","Instagram","TikTok","Threads"])]["followers"].sum()
color     = THEME["text_primary"]   # branco

# Se uma rede específica selecionada:
followers = snap[snap["network"] == selected_network]["followers"].sum()
color     = NETWORK_COLORS[selected_network]   # cor da rede
```

A data de referência aparece em texto pequeno: `"as of Apr 30, 2026"`.  
Isso é o registro de seguidores mais recente com `date <= date_end` selecionado.

---

## `_card_html()` — HTML do Card (linhas 307–322)

```python
def _card_html(label, value_html, label_extra="", color="") -> str:
    return f"""
    <div style="
        background: {THEME['bg_card']};         /* ← cor de fundo do card */
        border: 1px solid {THEME['border']};     /* ← borda */
        border-radius: 12px;                     /* ← arredondamento dos cantos */
        padding: 16px 20px;                      /* ← espaçamento interno: top/bot 16, lados 20 */
        margin-bottom: 8px;
        min-height: 100px;                       /* ← altura mínima do card */
    ">
        <div style="
            color: {THEME['text_secondary']};    /* ← cor do label (POSTS, IMPRESSIONS...) */
            font-size: 10px;                     /* ← tamanho do label */
            font-weight: 500;
            text-transform: uppercase;           /* ← label em maiúsculas */
            letter-spacing: 1.2px;
            margin-bottom: 6px;
        ">{label}</div>

        <div style="
            color: {val_color};                  /* ← cor do valor (branco ou cor da rede) */
            font-size: 24px;                     /* ← tamanho do número */
            font-weight: 700;                    /* ← negrito */
            line-height: 1;
            font-variant-numeric: tabular-nums;  /* ← números com largura fixa (não pula) */
        ">{value_html}</div>
    </div>"""
```

### Para modificar o visual dos cards:

| O que mudar | Onde |
|-------------|------|
| Cor de fundo | `background:` → via `THEME["bg_card"]` em `config.py` |
| Borda | `border:` → via `THEME["border"]` |
| Arredondamento | `border-radius: 12px` → mude o número |
| Altura mínima | `min-height: 100px` → mude o número |
| Tamanho do label | `font-size: 10px` → mude |
| Tamanho do número | `font-size: 24px` → mude |
| Espaçamento interno | `padding: 16px 20px` → mude |

---

## `render_comments_card()` — Linha 437

**Onde aparece:** Tab 1, coluna esquerda da linha 3.

### O que mostra:
```
Comments
12,345

Sentiment
● Positive   8,432   68%
● Neutral    2,109   17%
● Negative   1,804   15%
```

### Código das bolinhas de sentimento (linhas 476–491):

```python
def _dot_row(color, label, count, pct) -> str:
    return f"""
    <span style="
        width:10px; height:10px;           /* ← tamanho da bolinha */
        border-radius:50%;                 /* ← círculo */
        background:{color};                /* ← cor: green, muted, red */
    "></span>
    <span ...>{label}</span>               # Positive / Neutral / Negative
    <span ...>{count:,}</span>             # Número absoluto
    <span ...>{pct}%</span>               # Porcentagem
    """
```

**Cores:**
- Positive → `THEME["accent_green"]` (`#10B981`)
- Neutral → `THEME["text_muted"]` (`#5E5B74`)
- Negative → `THEME["accent_red"]` (`#EF4444`)

Para mudar as cores, edite em `config.py → THEME`.

---

## `_fmt()` — Formatação de Números (linha 35)

```python
def _fmt(value: float, is_pct: bool = False) -> str:
    if is_pct:
        return f"{value:.1f}%"    # 1.2%
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"   # 1.5M
    if value >= 1_000:
        return f"{value/1_000:.1f}K"       # 500.0K
    return f"{value:.0f}"                  # 250
```

Esta mesma função existe também em `posts.py` e `charts.py`. Todas funcionam da mesma forma.

Para mostrar 2 casas decimais nos milhões: mude `.1f` para `.2f`.

---

## `_safe_delta()` — Cálculo do Delta (linha 23)

```python
def _safe_delta(current, previous) -> tuple[float | None, str]:
    if previous == 0:
        return None, ""     # Não mostra delta se não há período anterior
    delta = ((current - previous) / previous) * 100
    color = THEME["accent_green"] if delta >= 0 else THEME["accent_red"]
    return delta, color
```

Delta positivo → verde (`#10B981`)  
Delta negativo → vermelho (`#EF4444`)

> **Nota:** Os deltas (▲▼) estão calculados mas o `render_kpi_row()` atual não os exibe nos cards por design — mostra apenas o valor atual. Se quiser adicionar os deltas de volta, use `_safe_delta()` e inclua o HTML no `_card_html()`.
