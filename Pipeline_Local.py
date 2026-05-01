"""
pipeline.py

Script principal — rode toda semana no terminal:

    python pipeline.py

COMO USAR:
1. Edite a seção CONFIGURAÇÃO abaixo com os caminhos dos seus arquivos
2. Rode: python pipeline.py
3. O Excel aparece na mesma pasta com o nome configurado

RESULTADO:
- Aba "RAW DATA" → dados limpos e prontos para análise
- Aba "REMOVED"  → log de tudo que foi removido e por quê
"""

from __future__ import annotations

import re                                                  # expressões regulares para limpeza de texto
from datetime import datetime                              # para formatar a data no nome do arquivo
from difflib import SequenceMatcher                        # para calcular similaridade entre textos
from io import StringIO                                    # para ler CSVs com header extra da Sprinklr
from pathlib import Path                                   # para trabalhar com caminhos de arquivo

import pandas as pd                                        # biblioteca principal de tabelas


# ---------------------------------------------------------------------------
# CONFIGURAÇÃO — edite aqui toda semana
# ---------------------------------------------------------------------------

SPRINKLR_CSV = "/Users/bkim/Documents/Dash/Post Table September 1 2025-April 5 2026.xlsx - Export table.csv"  # CSV exportado da Sprinklr (Posts), com header extra
META_CSV = "/Users/bkim/Documents/Dash/Sep-01-2025_Apr-06-2026_26478322775167299.csv"                                            # CSV da Meta (Stories), ou None

# nome do arquivo de saída — formato automático: Microsoft Learn | Raw data | 2026 | Mar 15
#OUTPUT_NAME = f"Microsoft Learn | Raw data | {datetime.now().strftime('%Y | %b %d')}.xlsx"
# No pipeline.py
BASE_DIR = "/Users/bkim/Documents/Dash"
OUTPUT_NAME = f"{BASE_DIR}/data/raw/raw_data.xlsx"
# limiar de similaridade para detectar "mesmo post com texto levemente diferente"
SIMILARITY_THRESHOLD = 0.70                               # 70% de palavras em comum

# limiar para decidir se soma métricas na republicação
# se o post removido tiver >= 20% das impressões do que fica → soma
IMPRESSION_RATIO_THRESHOLD = 0.20


# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------------------

def normalize_col(original):
    """
    Transforma nome feio de coluna em nome limpo e usável.
    Ex: "GDC Impressions (SUM)" → "gdc_impressions_sum"
    """
    s = (original or "").strip().lower()                   # remove espaços e deixa minúsculo
    s = s.replace("|", " ").replace("/", " ").replace("-", " ")  # troca separadores por espaço
    s = re.sub(r"[^a-z0-9à-ú\s]", " ", s, flags=re.IGNORECASE)  # remove parênteses etc.
    s = re.sub(r"\s+", "_", s).strip("_")                 # espaços viram underscore
    return s or "coluna_sem_nome"


def dedupe_names(names):
    """
    Garante que não existam nomes de colunas duplicados.
    Ex: ["account", "account"] → ["account", "account__2"]
    """
    seen = {}; out = []
    for n in names:
        if n not in seen: seen[n] = 1; out.append(n)
        else: seen[n] += 1; out.append(f"{n}__{seen[n]}")
    return out


def read_sprinklr(path):
    """
    Lê o CSV da Sprinklr tratando as ~6 linhas de metadados do header
    e tentando diferentes encodings e separadores automaticamente.
    """
    for enc in ["utf-8", "utf-8-sig", "latin-1"]:         # testa encodings em ordem
        try:
            with open(path, "r", encoding=enc) as f: content = f.read()
        except UnicodeDecodeError: continue

        lines = content.split("\n")
        hi = 0
        for i, l in enumerate(lines):
            if l.strip().strip('"').startswith("Social Network,"):  # linha do header real
                hi = i; break
        csv = "\n".join(lines[hi:])                        # descarta metadados antes do header

        for sep in [",", ";"]:                             # testa separadores em ordem
            try:
                df = pd.read_csv(StringIO(csv), sep=sep)
                if df.shape[1] > 1:                        # mais de 1 coluna = separador correto
                    df.columns = dedupe_names([normalize_col(c) for c in df.columns])
                    print(f"   Lido: {len(df)} linhas, {df.shape[1]} colunas (enc={enc}, sep='{sep}')")
                    return df
            except: pass
    raise RuntimeError(f"Não consegui ler: {path}")


def to_num(df, cols):
    """
    Converte colunas para número de forma segura.
    Se já for numérico, só preenche NaN com 0.
    Se for texto, limpa separadores de milhar antes de converter.
    (Evita o bug de 2664.0 → str → remove ponto → 26640)
    """
    for c in cols:
        if c not in df.columns: df[c] = 0; continue
        if pd.api.types.is_numeric_dtype(df[c]):           # já é número — só trata NaN
            df[c] = df[c].fillna(0)
        else:                                              # é texto — limpa e converte
            df[c] = pd.to_numeric(
                df[c].astype(str).str.strip()
                .str.replace(".", "", regex=False)         # remove ponto como separador de milhar
                .str.replace(",", "", regex=False),        # remove vírgula como separador de milhar
                errors="coerce"
            ).fillna(0)
    return df


def similarity(a, b):
    """Calcula similaridade entre dois textos — retorna valor de 0 a 1."""
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


def idx_maior(g):
    """
    Retorna o índice do post com maior impressão no grupo.
    Em caso de empate, desempata pelo mais recente.
    """
    return g.sort_values(
        ["gdc_impressions_sum", "publishedtime"],
        ascending=[False, False]                           # maior impressão primeiro, mais recente segundo
    ).index[0]


METRIC_COLS = [                                            # colunas de métricas que somamos nas republicações
    "gdc_impressions_sum",
    "gdc_total_engagements_sum",
    "post_likes_and_reactions_sum",
    "post_comments_sum",
    "post_shares_sum",
    "estimated_clicks_sum",
]


# ---------------------------------------------------------------------------
# ETAPA 1 — MERGE COM META (antes da limpeza)
# ---------------------------------------------------------------------------

def merge_meta(df, meta_path):
    """
    Incorpora dados de Stories do Instagram da planilha Meta.

    Por que antes da limpeza?
    Stories no Sprinklr vêm com impressões = 0 (a Sprinklr não mede Stories).
    Se limpássemos antes, a Regra 1 removeria todos os Stories.
    Fazendo o merge primeiro, as impressões reais da Meta chegam antes da limpeza.
    """
    if not meta_path or not Path(meta_path).exists():
        print("   Sem arquivo Meta — pulando merge.")
        return df

    df_meta = pd.read_csv(meta_path, encoding="utf-8")
    df_meta.columns = [normalize_col(c) for c in df_meta.columns]

    # renomeia colunas da Meta para o padrão do pipeline
    df_meta = df_meta.rename(columns={
        "permalink":   "permalink",
        "views":     "meta_impressoes",            # prefixo meta_ evita conflito com Sprinklr
        "reach":           "stories_alcance",
        "likes":          "meta_curtidas",
        "shares": "meta_shares",
        "profile_visits": "stories_visitas_perfil",
        "replies":         "meta_respostas",
        "link_clicks":   "meta_clicks",
        "navigation":         "stories_navegacao",
        "follows":       "stories_seguimentos",
    })

    # garante que as métricas da Meta sejam numéricas
    for c in ["meta_impressoes", "meta_curtidas", "meta_shares", "meta_respostas", "meta_clicks",
              "stories_alcance", "stories_visitas_perfil", "stories_navegacao", "stories_seguimentos"]:
        if c in df_meta.columns:
            df_meta[c] = pd.to_numeric(df_meta[c], errors="coerce").fillna(0)

    df["permalink"] = df["permalink"].astype(str).str.strip()
    df_meta["permalink"] = df_meta["permalink"].astype(str).str.strip()

    # join pelo permalink — left join para não perder nenhuma linha da Sprinklr
    join_cols = ["permalink"] + [c for c in [
        "meta_impressoes", "meta_curtidas", "meta_shares", "meta_respostas", "meta_clicks",
        "stories_alcance", "stories_visitas_perfil", "stories_navegacao", "stories_seguimentos"
    ] if c in df_meta.columns]
    df = df.merge(df_meta[join_cols], on="permalink", how="left")

    # substitui métricas da Sprinklr pelas da Meta onde a Meta tem valor
    subs = {
        "gdc_impressions_sum":            "meta_impressoes",
        "post_likes_and_reactions_sum":   "meta_curtidas",
        "post_shares_sum":                "meta_shares",
        "post_comments_sum":              "meta_respostas",
        "estimated_clicks_sum":           "meta_clicks",
    }
    for col_spr, col_meta in subs.items():
        if col_meta in df.columns:
            mask = df[col_meta].notna() & (df[col_meta] > 0)
            df.loc[mask, col_spr] = df.loc[mask, col_meta]
            df.drop(columns=[col_meta], inplace=True)

    # identifica IG Stories: qualquer linha que tem "alcance" da Meta
    mask_stories = df["stories_alcance"].notna() & (df["stories_alcance"] > 0)
    df.loc[mask_stories, "social_network"] = "IG Stories"
    print(f"   Stories identificados: {mask_stories.sum()}")

    # Recalcula gdc_total_engagements_sum para IG Stories.
    # O Sprinklr conta "navigation taps" (swipes/avanços) como engajamento total,
    # o que distorce a métrica. O correto é: likes + comments + shares + clicks.
    eng_cols = [
        "post_likes_and_reactions_sum",
        "post_comments_sum",
        "post_shares_sum",
        "estimated_clicks_sum",
    ]
    present_eng = [c for c in eng_cols if c in df.columns]
    if present_eng and mask_stories.any():
        df.loc[mask_stories, "gdc_total_engagements_sum"] = (
            df.loc[mask_stories, present_eng].sum(axis=1)
        )
        print(f"   Stories engagement recalculado (likes+comments+shares+clicks)")

    return df


# ---------------------------------------------------------------------------
# ETAPA 2 — LIMPEZA INICIAL
# ---------------------------------------------------------------------------

def clean_sprinklr(df):
    """
    Aplica as 4 regras de limpeza inicial.
    Ver CLEANING_RULES.md para detalhes completos.
    """
    df = df.copy()
    df = to_num(df, METRIC_COLS)                           # garante que métricas são numéricas

    # Regra 1: remove impressions = 0
    # (Stories já têm impressões da Meta nesse ponto, então não são removidos)
    antes = len(df)
    df = df[df["gdc_impressions_sum"] != 0]
    print(f"   Regra 1 (impressions=0): -{antes - len(df)} → {len(df)}")

    # Regra 2: remove social reactive
    antes = len(df)
    df = df[~df["campaign_name"].astype(str).str.lower().str.contains(r"social\s+reactive", na=False)]
    print(f"   Regra 2 (social reactive): -{antes - len(df)} → {len(df)}")

    # Regra 3: remove permalink vazio
    antes = len(df)
    p = df["permalink"].astype(str).str.strip()
    df = df[(p != "") & (p.str.lower() != "nan")]
    print(f"   Regra 3 (permalink vazio): -{antes - len(df)} → {len(df)}")

    # Regra 4: remove respostas a comentários
    # condição: Auto Import + texto começa com @mention
    antes = len(df)
    is_auto = df["campaign_name"].astype(str).str.strip() == "[Auto Import] (Universal)"
    starts_mention = df["outbound_post"].astype(str).str.strip().str.startswith("@")
    df = df[~(is_auto & starts_mention)]
    print(f"   Regra 4 (@mention Auto Import): -{antes - len(df)} → {len(df)}")

    return df.reset_index(drop=True)                       # renumera índices do zero


# ---------------------------------------------------------------------------
# ETAPA 3 — DEDUPLICAÇÃO
# ---------------------------------------------------------------------------

def deduplicate(df):
    """
    Remove posts duplicados seguindo os padrões definidos em CLEANING_RULES.md.

    Regra principal: sempre fica o post de MAIOR IMPRESSÃO.
    Em empate de impressões: fica o mais recente.
    Métricas são somadas quando a diferença é significativa (>=20%).

    IG Stories são excluídos da deduplicação por texto
    (todos têm o texto "This message has no text." e são posts únicos).
    """
    df = df.copy()
    df["publishedtime"] = pd.to_datetime(df["publishedtime"], errors="coerce")

    removidos_ids = set()                                  # índices marcados para remoção
    log = []                                               # registro de cada remoção

    def log_remove(idx, motivo):
        """Marca um índice para remoção e registra o motivo."""
        row = df.loc[idx].to_dict()
        row["motivo_exclusao"] = motivo
        log.append(row)
        removidos_ids.add(idx)

    def soma(df, dest, origens, cols):
        """Acumula as métricas dos posts removidos no post que fica.
        Também propaga o flag 'boosted': se qualquer post removido for boosted,
        o post que fica também é marcado como boosted.
        """
        for c in cols:
            if c in df.columns:
                df.loc[dest, c] += df.loc[list(origens), c].sum()
        if "boosted" in df.columns:
            if df.loc[list(origens), "boosted"].fillna(0).any():
                df.loc[dest, "boosted"] = 1
        return df

    # IG Stories: todos ficam, sem deduplicação por texto
    stories_idx = set(df[df["social_network"] == "IG Stories"].index)

    # Padrão 1: permalink idêntico
    for (rede, plink), g in df.groupby(["social_network", "permalink"]):
        if rede == "IG Stories": continue
        if len(g) <= 1: continue
        mn = idx_maior(g)
        for idx in g.index:
            if idx != mn:
                log_remove(idx, "Padrão 1 — Duplicata exata: mesmo permalink")

    # Padrões 2-6: texto exato
    # inclui sobreviventes do Padrão 1 para não perder grupos mistos
    for (rede, texto), g in df.groupby(["social_network", "outbound_post"], sort=False):
        if rede == "IG Stories": continue
        g = g[~g.index.isin(removidos_ids)]                # exclui apenas os já removidos
        if len(g) <= 1: continue

        is_auto = g["campaign_name"].astype(str).str.strip() == "[Auto Import] (Universal)"
        tem_auto = is_auto.any()
        tem_real = (~is_auto).any()

        if tem_auto and tem_real:
            # Padrão 2: Auto Import vs post real — soma no de maior impressão
            mn = idx_maior(g)
            remover = [i for i in g.index if i != mn]
            df = soma(df, mn, remover, METRIC_COLS)
            camp_mn = df.loc[mn, "campaign_name"]
            for idx in remover:
                log_remove(idx, f"Padrão 2 — Somado no post de maior impressão ({camp_mn})")

        elif tem_auto and not tem_real:
            # Padrão 4: todos Auto Import — fica o de maior impressão
            mn = idx_maior(g)
            for idx in g.index:
                if idx != mn:
                    log_remove(idx, "Padrão 4 — Todos Auto Import: mantido maior impressão")

        else:
            # Padrão 5/6: republicação — mesma campanha, permalink diferente
            mn = idx_maior(g)
            ma = [i for i in g.index if i != mn]
            imp_mn = df.loc[mn, "gdc_impressions_sum"]
            imp_ma = df.loc[ma, "gdc_impressions_sum"].sum()

            if imp_mn > 0 and (imp_ma / imp_mn) >= IMPRESSION_RATIO_THRESHOLD:
                df = soma(df, mn, ma, METRIC_COLS)
                motivo = "Padrão 5 — Republicação: métricas somadas no maior"
            else:
                motivo = "Padrão 6 — Republicação: removido sem somar (impressões insignificantes)"

            for idx in ma:
                log_remove(idx, motivo)

    # Padrões 3/7: texto similar (>=70%)
    df_sim = df[~df.index.isin(removidos_ids | stories_idx)].copy()
    for rede, gr in df_sim.groupby("social_network"):
        if rede == "IG Stories": continue
        idxs = gr.index.tolist()
        for i in range(len(idxs)):
            ii = idxs[i]
            if ii in removidos_ids: continue
            for j in range(i + 1, len(idxs)):
                jj = idxs[j]
                if jj in removidos_ids: continue
                sim = similarity(df.loc[ii, "outbound_post"], df.loc[jj, "outbound_post"])
                if sim < SIMILARITY_THRESHOLD or sim >= 1.0: continue

                mn = ii if df.loc[ii, "gdc_impressions_sum"] >= df.loc[jj, "gdc_impressions_sum"] else jj
                ma = jj if mn == ii else ii
                df = soma(df, mn, [ma], METRIC_COLS)
                log_remove(ma, f"Padrão 3/7 — Texto similar ({sim:.0%}): somado no maior impressão")

    # monta resultado final
    todos_mantidos = set(df.index) - removidos_ids
    df_clean = df.loc[sorted(todos_mantidos)].reset_index(drop=True)
    df_log = pd.DataFrame(log) if log else pd.DataFrame()

    print(f"   -{len(log)} removidas → {len(df_clean)} restantes")
    print(f"   Redes: {df_clean['social_network'].value_counts().to_dict()}")

    return df_clean, df_log


# ---------------------------------------------------------------------------
# ETAPA 4 — GERAR EXCEL
# ---------------------------------------------------------------------------

def generate_output(df_clean, df_log, output_path):
    # 1. Gera o Excel original com as duas abas (para seu controle)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_clean.to_excel(writer, sheet_name="RAW DATA", index=False)
        if len(df_log) > 0:
            df_log.to_excel(writer, sheet_name="REMOVED", index=False)
        else:
            pd.DataFrame({"mensagem": ["Nenhuma linha foi removida."]}).to_excel(
                writer, sheet_name="REMOVED", index=False
            )

    # 2. Gera o CSV que o Dashboard espera (na mesma pasta 'raw')
    # Substitui a extensão .xlsx por .csv no caminho
    csv_path = output_path.replace(".xlsx", ".csv")
    df_clean.to_csv(csv_path, index=False, encoding="utf-8")
    
    print(f"✅ Dashboard pronto em: {csv_path}")
   



    print(f"\n   Arquivo gerado: {output_path}")
    print(f"   Aba RAW DATA: {len(df_clean)} linhas")
    print(f"   Aba REMOVED:  {len(df_log)} linhas removidas")


# ---------------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("\n=== PIPELINE SOCIAL ANALYTICS ===\n")

    # Etapa 1: leitura
    print("1) Lendo CSV Sprinklr...")
    df = read_sprinklr(SPRINKLR_CSV)

    # Etapa 2: merge com Meta (antes da limpeza!)
    print("\n2) Merge com Meta...")
    df = merge_meta(df, META_CSV)

    # Etapa 3: limpeza
    print("\n3) Limpeza...")
    df = clean_sprinklr(df)

    # Etapa 4: deduplicação
    print("\n4) Deduplicação...")
    df, df_log = deduplicate(df)

    # Etapa 5: gerar Excel
    print("\n5) Gerando Excel...")
    generate_output(df, df_log, OUTPUT_NAME)

    print("\n=== CONCLUÍDO ===\n")
