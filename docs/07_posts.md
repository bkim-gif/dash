# 07 — Cards de Top/Bottom Posts (components/posts.py)

> **Arquivo:** [`components/posts.py`](../components/posts.py)  
> Renderiza a Tab 5 ("Top / Bottom Posts") com cards individuais de posts.

---

## Visão Geral

A Tab 5 exibe dois grupos de cards lado a lado:

```
▲ TOP 5 POSTS                    ▼ BOTTOM 5 POSTS
┌─────────────────────┐         ┌─────────────────────┐
│ [LinkedIn]    #1 ▲  │         │ [Instagram]  #1 ▼   │
│ Texto do post...    │         │ Texto do post...     │
│ [Impr][Eng][ER]...  │         │ [Impr][Eng][ER]...  │
│ ↗ View post         │         │ ↗ View post          │
└─────────────────────┘         └─────────────────────┘
```

---

## `render_top_bottom()` — Linha 91

```python
def render_top_bottom(df: pd.DataFrame, sort_by_label: str) -> None:
    sort_col = SORT_OPTIONS.get(sort_by_label, "gdc_total_engagements_sum")
    # sort_by_label vem da sidebar: "Total Engagement", "Impressions", "ER (%)", "AQE"
    # SORT_OPTIONS mapeia o label para o nome da coluna

    df_sorted = df.sort_values(sort_col, ascending=False)
    top    = df_sorted.head(TOP_N)         # Primeiros N = melhores
    bottom = df_sorted.tail(TOP_N)         # Últimos N = piores
    # TOP_N definido em config.py (padrão: 5)

    col1, col2 = st.columns(2)   # Duas colunas de mesma largura
```

---

## `_post_card()` — HTML de um Card (linha 17)

```python
def _post_card(row: pd.Series, rank: int, is_top: bool) -> str:
```

### Ambient Glow (linhas 19–30)

```python
if is_top:
    glow_style = (
        "border:1px solid rgba(16,185,129,0.20);"           # borda verde suave
        "border-top:1px solid rgba(16,185,129,0.30);"       # borda superior um pouco mais visível
        "box-shadow:0 -25px 50px -20px rgba(16,185,129,0.12);"  # luz difusa verde no topo
    )
else:
    glow_style = (
        "border:1px solid rgba(239,68,68,0.20);"            # borda vermelha suave
        "border-top:1px solid rgba(239,68,68,0.30);"
        "box-shadow:0 -25px 50px -20px rgba(239,68,68,0.12);"   # luz difusa vermelha
    )
```

**Para intensificar o brilho:** aumente o último valor de `rgba()` (atualmente `0.12`).  
**Para brilho na borda inferior:** mude `0 -25px` para `0 25px` e tire o `-`.

### Badge de Rede (linhas 38–40, 80–82)

```python
network   = str(row.get("social_network", ""))
net_color = NETWORK_COLORS.get(network, "#888")

# Badge:
f'<span style="
    background:{net_color}22;        /* ← cor da rede com 22/FF de alpha (13% opacidade) */
    color:{net_color};               /* ← texto na cor da rede */
    border:1px solid {net_color}55;  /* ← borda com 33% opacidade */
    border-radius:6px;
    padding:2px 8px;
    font-size:11px;
    font-weight:600;
">{network}</span>'
```

**Para badges com fundo mais visível:** mude `22` para `44` ou `66` (hexadecimal de opacidade).

### Texto do Post (linhas 33–35)

```python
text = str(row.get("outbound_post", ""))
text = (text[:140] + "…") if len(text) > 140 else text
# Trunca em 140 caracteres para caber no card
```

**Para mostrar mais texto:** aumente `140`.  
**Para mostrar o post completo:** remova a linha de truncamento.

### Rank Badge (linha 82)

```python
rank_icon = "▲" if is_top else "▼"
f'<span ...>#{rank} {rank_icon}</span>'
# Ex: "#1 ▲" para o top 1
```

### Chips de Métricas (linhas 57–74)

```python
def chip(label: str, val: str) -> str:
    return f"""
    <div style="
        background:{THEME["bg_card2"]};   /* ← fundo do chip */
        border-radius:6px;                /* ← arredondamento */
        padding:4px 10px;                 /* ← espaçamento interno */
        text-align:center;
        min-width:56px;                   /* ← largura mínima */
    ">
        <div style="color:{THEME["text_muted"]};font-size:10px;...">{label}</div>
        <div style="color:{THEME["text_primary"]};font-size:12px;font-weight:600">{val}</div>
    </div>"""

# 7 chips por card:
chips = chip("Impr", impr) + chip("Eng", eng) + chip("ER", er) +
        chip("Likes", likes) + chip("Cmts", comments) +
        chip("Shares", shares) + chip("Clicks", clicks)
```

**Para adicionar um chip:** adicione mais uma chamada `chip("Label", valor)` na concatenação.  
**Para remover um chip:** remova a chamada correspondente.  
**Para mudar o tamanho da fonte do valor:** edite `font-size:12px` no `chip()`.

### Link "View post" (linhas 49–55)

```python
permalink = str(row.get("permalink", ""))

if permalink and permalink not in ["", "nan"]:
    link_html = f'<a href="{permalink}" target="_blank" style="
        color:{THEME["accent_blue"]};   /* ← cor do link */
        font-size:11px;
    ">↗ View post</a>'
```

**Para mudar a cor do link:** edite `THEME["accent_blue"]` em `config.py`.  
**Para mudar o texto:** troque `"↗ View post"` por outro texto.  
**Para abrir na mesma aba:** mude `target="_blank"` para `target="_self"`.

### Estrutura do Card (linhas 76–88)

```python
return f"""
<div style="
    background:{THEME["bg_card"]};    /* ← fundo */
    {glow_style}                      /* ← glow verde ou vermelho */
    border-radius:10px;               /* ← arredondamento */
    padding:16px;                     /* ← espaçamento interno */
    margin-bottom:10px;               /* ← espaço entre cards */
">
    <!-- Header: badge rede + rank -->
    <!-- Texto do post -->
    <!-- Chips de métricas -->
    <!-- Link View post -->
</div>"""
```

**Para cards mais espaçados:** aumente `padding:16px` e `margin-bottom:10px`.

---

## Títulos das Colunas (linhas 115–127)

```python
# TOP
st.markdown(
    f'<div style="color:{THEME["accent_green"]};font-weight:700;font-size:14px;...">▲ TOP {TOP_N} POSTS</div>'
)

# BOTTOM
st.markdown(
    f'<div style="color:{THEME["accent_red"]};font-weight:700;font-size:14px;...">▼ BOTTOM {TOP_N} POSTS</div>'
)
```

Para mudar o tamanho dos títulos: edite `font-size:14px`.

---

## Formatação dos Valores nos Chips

```python
def _fmt(value: float, is_pct: bool = False) -> str:   # linha 7
    if is_pct: return f"{value:.1f}%"     # 1.2%
    if value >= 1_000_000: return f"{v/1_000_000:.1f}M"  # 1.5M
    if value >= 1_000:     return f"{v/1_000:.1f}K"      # 500.0K
    return f"{int(value)}"                # 250
```

---

## Resumo das Modificações Mais Comuns

| O que modificar | Onde no arquivo | Exemplo |
|----------------|----------------|---------|
| Número de posts exibidos | `config.py:124` | `TOP_N = 10` |
| Intensidade do glow verde | `posts.py:23` | `rgba(16,185,129, 0.25)` |
| Intensidade do glow vermelho | `posts.py:28` | `rgba(239,68,68, 0.25)` |
| Tamanho máximo do texto | `posts.py:34` | `text[:200]` |
| Cor do link "View post" | `posts.py:53` | `color:{THEME["accent_blue"]}` |
| Cor de fundo dos chips | `posts.py:58` | `background:{THEME["bg_card2"]}` |
| Tamanho dos chips | `posts.py:60` | `padding:6px 14px` |
| Cor do badge da rede | Automático via `NETWORK_COLORS` em `config.py` | |
