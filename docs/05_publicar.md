# Como Publicar no Streamlit Cloud

## Publicação rápida (uso do dia a dia)

Após fazer qualquer alteração no código, rode no Terminal:

```bash
/Users/bkim/Documents/Dash/publicar.sh
```

O Streamlit Cloud detecta a mudança automaticamente e atualiza o site em ~1 minuto.

---

## O que o script publicar.sh faz?

```bash
git add .           # marca todos os arquivos alterados
git commit -m "update"   # salva um ponto de histórico
git push ...        # envia para o GitHub
```

O Streamlit Cloud fica "olhando" o repositório no GitHub.
Quando detecta uma mudança, ele reinicia o app automaticamente.

---

## Estrutura necessária no GitHub

Repositório: `github.com/bkim-gif/dash`

Arquivos obrigatórios:
- `app.py` — ponto de entrada do app
- `requirements.txt` — lista de dependências Python
- `.streamlit/config.toml` — configuração do tema

---

## requirements.txt

Lista os pacotes Python que o Streamlit Cloud precisa instalar:

```
streamlit
pandas
plotly
openpyxl
```

Se você adicionar uma nova biblioteca ao código, adicione ela aqui também.

---

## Acessar o dashboard publicado

URL: `https://bkim-gif-dash-[hash].streamlit.app`

(O link exato aparece no painel do Streamlit Cloud em share.streamlit.io)

---

## Solução de problemas

| Problema                        | Solução                                      |
|---------------------------------|----------------------------------------------|
| App não atualiza após o push    | Aguarde ~2 minutos ou clique em "Reboot app" |
| Erro de dependência             | Adicione o pacote no `requirements.txt`      |
| Dados não aparecem              | Verifique se o CSV está no repositório       |
