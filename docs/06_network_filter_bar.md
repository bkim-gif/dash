# Network Filter Bar — Botões de Rede no Topo

## O que foi alterado

Substituição do `st.multiselect` de redes sociais no sidebar por uma barra de botões com ícone + nome no topo da área principal do dashboard.

---

## Motivação

O filtro de redes estava escondido no painel lateral junto com os outros filtros. A nova barra de botões torna a seleção de rede mais visual, imediata e acessível, exibindo os logos das plataformas em destaque no topo de cada página.

---

## Estrutura da Mudança

### 1. `app.py` — Variáveis movidas para antes do sidebar

```python
# Antes do bloco `with st.sidebar:`
all_networks = sorted(df_all["social_network"].unique().tolist())

if "sel_network" not in st.session_state:
    st.session_state.sel_network = "ALL"
```

`all_networks` era definido dentro do sidebar. Foi movido para antes dele para ser compartilhado entre o sidebar e a barra de filtro.

---

### 2. `app.py` — Remoção do Networks do sidebar

**Antes:**
```python
st.markdown('<div class="section-header">Networks</div>', unsafe_allow_html=True)
all_networks = sorted(df_all["social_network"].unique().tolist())
networks = st.multiselect("", options=all_networks, default=all_networks, ...)
```

**Depois:** seção removida. O sidebar agora contém apenas Period, Pillars, Media Type, Campaign e Sort Posts By.

---

### 3. `app.py` — Cálculo de `networks` antes de `apply_filters`

```python
_sel_net = st.session_state.sel_network
networks = all_networks if (_sel_net == "ALL" or _sel_net not in all_networks) else [_sel_net]
```

Isso garante que `networks` esteja disponível antes de `apply_filters()` ser chamado.

---

### 4. `app.py` — Barra de filtro de redes (após o header)

Adicionada entre o header principal e as tabs. Composta por:

#### Ícones SVG por rede

```python
_NETWORK_SVG = {
    "Instagram": "<svg ...>",   # câmera com círculo
    "IG Stories": "<svg ...>",  # câmera circular com borda pontilhada
    "X":          "<svg ...>",  # logo X oficial
    "LinkedIn":   "<svg ...>",  # logo LinkedIn oficial
    "TikTok":     "<svg ...>",  # logo TikTok oficial
    "Threads":    "<svg ...>",  # logo Threads oficial
    "ALL":        "<svg ...>",  # grade de 4 quadrados
}
```

#### Cores de fundo

```python
_NET_BG = {**NETWORK_COLORS, "ALL": THEME["bg_card2"]}
```

Usa as cores já definidas em `config.py → NETWORK_COLORS`.

#### Callback de seleção

```python
def _set_network(net: str):
    st.session_state.sel_network = net
```

#### Renderização das colunas

Para cada rede, a coluna exibe:
1. **`st.markdown`** — círculo colorido com ícone SVG (visual)
2. **`st.button`** — nome clicável (`type="primary"` se ativo, `type="secondary"` se inativo)

#### Estados visuais

| Estado   | Ícone                                      | Botão            |
|----------|--------------------------------------------|------------------|
| Ativo    | Ring colorida + leve aumento de escala     | `type="primary"` |
| Inativo  | Opacidade 40% + leve dessaturação          | `type="secondary"` |

---

## Fluxo de dados

```
Clique no botão
    → on_click=_set_network(net)
    → st.session_state.sel_network = net
    → Streamlit re-run
    → networks = [net]  (ou all_networks se "ALL")
    → apply_filters(..., networks=networks, ...)
    → df_filtered atualizado
    → Dashboard re-renderiza com a rede selecionada
```

---

## Comportamento

- **Default:** `"ALL"` — todas as redes exibidas
- **Clicar numa rede:** filtra o dashboard inteiro para aquela rede
- **Clicar em "All":** restaura todas as redes
- **Estado preservado:** troca de rede não reseta data, pillar, media type ou campaign
- **Redes novas nos dados:** aparecem automaticamente na barra (sem mudança de código)

---

## Arquivos modificados

| Arquivo  | Tipo de mudança                                          |
|----------|----------------------------------------------------------|
| `app.py` | Remoção do multiselect de redes do sidebar               |
| `app.py` | Adição de `all_networks` e `st.session_state.sel_network` antes do sidebar |
| `app.py` | Cálculo de `networks` via session_state antes de `apply_filters` |
| `app.py` | Nova seção "Network Filter Bar" com SVGs e botões interativos |
