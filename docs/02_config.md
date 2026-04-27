# config.py — Configurações Globais

## O que faz?

É o arquivo central de configurações. Quando você quer mudar uma cor, meta ou nome de rede,
você muda **só aqui** — o resto do dashboard pega automaticamente.

---

## CLIENT

```python
CLIENT = {
    "name": "Microsoft Learn",
}
```

Nome que aparece no topo da sidebar. Para usar em outro cliente, só muda aqui.

---

## FY_TARGET

```python
FY_TARGET = 25_000_000   # 25 milhões de impressões
FY_START  = "2025-08-01"
FY_END    = "2026-07-31"
```

Meta anual de impressões orgânicas. Usada no gauge da aba "FY Pacing".

---

## PILLAR_TARGETS

```python
PILLAR_TARGETS = {
    "Brand":          5.0,
    "Conversation":  15.0,
    "Educational":   45.0,
    "Informational": 25.0,
    "Micro-skilling":10.0,
}
```

Distribuição ideal de posts por pilar (em %). Aparece no gráfico radar como a linha de "target".

---

## NETWORK_COLORS

```python
NETWORK_COLORS = {
    "LinkedIn":  "#0179d5",
    "X":         "#47c6b2",
    "Instagram": "#ff5c38",
    "TikTok":    "#c73fcc",
    "Threads":   "#9900ff",
}
```

Cores de cada rede social. Usadas nos gráficos, badges e cards de posts.

---

## THEME

Todas as cores do tema escuro:

| Chave          | Cor       | Uso                          |
|----------------|-----------|------------------------------|
| bg_page        | #0F1923   | Fundo da página              |
| bg_card        | #1A2535   | Cards e painéis              |
| text_primary   | #FFFFFF   | Texto principal              |
| text_muted     | #4A6080   | Texto secundário / labels    |
| accent_blue    | #50E6FF   | Linha principal dos gráficos |
| accent_green   | #54D46A   | Positivo / acima da meta     |
| accent_red     | #FF4D6A   | Negativo / abaixo da meta    |
| accent_yellow  | #FFB900   | Meta / alerta                |

---

## SORT_OPTIONS e TOP_N

```python
TOP_N = 5   # quantos posts aparecem no Top/Bottom
```

Para mostrar Top 10 em vez de Top 5, só mude esse número.
