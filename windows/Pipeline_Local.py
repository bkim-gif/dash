"""
pipeline.py

Script principal — rode toda semana no terminal:

    python Pipeline_Local.py

COMO USAR:
1. Coloque os CSVs da Sprinklr e Meta nesta mesma pasta
2. Edite a seção CONFIGURAÇÃO abaixo com os nomes dos arquivos
3. Rode: python Pipeline_Local.py
4. O Excel aparece em data/raw/ com o nome da semana

RESULTADO:
- Aba "RAW DATA" → dados limpos e prontos para análise
- Aba "REMOVED"  → log de tudo que foi removido e por quê
"""

from __future__ import annotations

import re
import sys
import math
from datetime import datetime
from difflib import SequenceMatcher
from io import StringIO
from pathlib import Path

import pandas as pd

# Permite caracteres especiais no terminal do Windows
sys.stdout.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# CONFIGURAÇÃO — edite aqui toda semana
# ---------------------------------------------------------------------------

# Pasta onde este script está (não precisa mudar)
BASE_DIR = Path(__file__).parent

# Coloque os nomes dos seus arquivos CSV aqui (devem estar na mesma pasta)
SPRINKLR_CSV = BASE_DIR / "Post Table September 1 2025-April 5 2026.xlsx - Export table.csv"
META_CSV      = BASE_DIR / "Sep-01-2025_Apr-06-2026_26478322775167299.csv"

# Saídas (não precisa mudar)
OUTPUT_NAME = BASE_DIR / "data" / "raw" / f"raw_data_{datetime.now().strftime('%Y-W%V')}.xlsx"
BASE_PATH   = BASE_DIR / "MSFT_Revised_2026 - RAW DATA (1).csv"

# Limiares de limpeza
SIMILARITY_THRESHOLD       = 0.70
IMPRESSION_RATIO_THRESHOLD = 0.20


# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------------------

def normalize_col(original):
    s = (original or "").strip().lower()
    s = s.replace("|", " ").replace("/", " ").replace("-", " ")
    s = re.sub(r"[^a-z0-9à-ú\s]", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "coluna_sem_nome"


def dedupe_names(names):
    seen = {}; out = []
    for n in names:
        if n not in seen: seen[n] = 1; out.append(n)
        else: seen[n] += 1; out.append(f"{n}__{seen[n]}")
    return out


def read_sprinklr(path):
    for enc in ["utf-8", "utf-8-sig", "latin-1"]:
        try:
            with open(path, "r", encoding=enc) as f: content = f.read()
        except UnicodeDecodeError: continue

        lines = content.split("\n")
        hi = 0
        for i, l in enumerate(lines):
            if l.strip().strip('"').startswith("Social Network,"):
                hi = i; break
        csv = "\n".join(lines[hi:])

        for sep in [",", ";"]:
            try:
                df = pd.read_csv(StringIO(csv), sep=sep)
                if df.shape[1] > 1:
                    df.columns = dedupe_names([normalize_col(c) for c in df.columns])
                    print(f"   Lido: {len(df)} linhas, {df.shape[1]} colunas (enc={enc}, sep='{sep}')")
                    return df
            except: pass
    raise RuntimeError(f"Nao consegui ler: {path}")


def to_num(df, cols):
    for c in cols:
        if c not in df.columns: df[c] = 0; continue
        if pd.api.types.is_numeric_dtype(df[c]):
            df[c] = df[c].fillna(0)
        else:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.strip()
                .str.replace(".", "", regex=False)
                .str.replace(",", "", regex=False),
                errors="coerce"
            ).fillna(0)
    return df


def similarity(a, b):
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


def idx_maior(g):
    return g.sort_values(
        ["gdc_impressions_sum", "publishedtime"],
        ascending=[False, False]
    ).index[0]


METRIC_COLS = [
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
    if not meta_path or not Path(meta_path).exists():
        print("   Sem arquivo Meta — pulando merge.")
        return df

    df_meta = pd.read_csv(meta_path, encoding="utf-8")
    df_meta.columns = [normalize_col(c) for c in df_meta.columns]

    df_meta = df_meta.rename(columns={
        "permalink":      "permalink",
        "views":          "meta_impressoes",
        "reach":          "stories_alcance",
        "likes":          "meta_curtidas",
        "shares":         "meta_shares",
        "profile_visits": "stories_visitas_perfil",
        "replies":        "meta_respostas",
        "link_clicks":    "meta_clicks",
        "navigation":     "stories_navegacao",
        "follows":        "stories_seguimentos",
    })

    for c in ["meta_impressoes", "meta_curtidas", "meta_shares", "meta_respostas", "meta_clicks",
              "stories_alcance", "stories_visitas_perfil", "stories_navegacao", "stories_seguimentos"]:
        if c in df_meta.columns:
            df_meta[c] = pd.to_numeric(df_meta[c], errors="coerce").fillna(0)

    df["permalink"]      = df["permalink"].astype(str).str.strip()
    df_meta["permalink"] = df_meta["permalink"].astype(str).str.strip()

    join_cols = ["permalink"] + [c for c in [
        "meta_impressoes", "meta_curtidas", "meta_shares", "meta_respostas", "meta_clicks",
        "stories_alcance", "stories_visitas_perfil", "stories_navegacao", "stories_seguimentos"
    ] if c in df_meta.columns]
    df = df.merge(df_meta[join_cols], on="permalink", how="left")

    subs = {
        "gdc_impressions_sum":          "meta_impressoes",
        "post_likes_and_reactions_sum": "meta_curtidas",
        "post_shares_sum":              "meta_shares",
        "post_comments_sum":            "meta_respostas",
        "estimated_clicks_sum":         "meta_clicks",
    }
    for col_spr, col_meta in subs.items():
        if col_meta in df.columns:
            mask = df[col_meta].notna() & (df[col_meta] > 0)
            df.loc[mask, col_spr] = df.loc[mask, col_meta]
            df.drop(columns=[col_meta], inplace=True)

    mask_stories = df["stories_alcance"].notna() & (df["stories_alcance"] > 0)
    df.loc[mask_stories, "social_network"] = "IG Stories"
    print(f"   Stories identificados: {mask_stories.sum()}")

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
    df = df.copy()
    df = to_num(df, METRIC_COLS)

    antes = len(df)
    df = df[df["gdc_impressions_sum"] != 0]
    print(f"   Regra 1 (impressions=0): -{antes - len(df)} -> {len(df)}")

    antes = len(df)
    df = df[~df["campaign_name"].astype(str).str.lower().str.contains(r"social\s+reactive", na=False)]
    print(f"   Regra 2 (social reactive): -{antes - len(df)} -> {len(df)}")

    antes = len(df)
    p = df["permalink"].astype(str).str.strip()
    df = df[(p != "") & (p.str.lower() != "nan")]
    print(f"   Regra 3 (permalink vazio): -{antes - len(df)} -> {len(df)}")

    antes = len(df)
    is_auto      = df["campaign_name"].astype(str).str.strip() == "[Auto Import] (Universal)"
    starts_mention = df["outbound_post"].astype(str).str.strip().str.startswith("@")
    df = df[~(is_auto & starts_mention)]
    print(f"   Regra 4 (@mention Auto Import): -{antes - len(df)} -> {len(df)}")

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# ETAPA 3 — DEDUPLICACAO
# ---------------------------------------------------------------------------

def deduplicate(df):
    df = df.copy()
    df["publishedtime"] = pd.to_datetime(df["publishedtime"], errors="coerce")

    removidos_ids = set()
    log = []

    def log_remove(idx, motivo):
        row = df.loc[idx].to_dict()
        row["motivo_exclusao"] = motivo
        log.append(row)
        removidos_ids.add(idx)

    def soma(df, dest, origens, cols):
        for c in cols:
            if c in df.columns:
                df.loc[dest, c] += df.loc[list(origens), c].sum()
        if "boosted" in df.columns:
            if df.loc[list(origens), "boosted"].fillna(0).any():
                df.loc[dest, "boosted"] = 1
        return df

    stories_idx = set(df[df["social_network"] == "IG Stories"].index)

    for (rede, plink), g in df.groupby(["social_network", "permalink"]):
        if rede == "IG Stories": continue
        if len(g) <= 1: continue
        mn = idx_maior(g)
        for idx in g.index:
            if idx != mn:
                log_remove(idx, "Padrao 1 — Duplicata exata: mesmo permalink")

    for (rede, texto), g in df.groupby(["social_network", "outbound_post"], sort=False):
        if rede == "IG Stories": continue
        g = g[~g.index.isin(removidos_ids)]
        if len(g) <= 1: continue

        is_auto  = g["campaign_name"].astype(str).str.strip() == "[Auto Import] (Universal)"
        tem_auto = is_auto.any()
        tem_real = (~is_auto).any()

        if tem_auto and tem_real:
            mn = idx_maior(g)
            remover = [i for i in g.index if i != mn]
            df = soma(df, mn, remover, METRIC_COLS)
            camp_mn = df.loc[mn, "campaign_name"]
            for idx in remover:
                log_remove(idx, f"Padrao 2 — Somado no post de maior impressao ({camp_mn})")

        elif tem_auto and not tem_real:
            mn = idx_maior(g)
            for idx in g.index:
                if idx != mn:
                    log_remove(idx, "Padrao 4 — Todos Auto Import: mantido maior impressao")

        else:
            mn  = idx_maior(g)
            ma  = [i for i in g.index if i != mn]
            imp_mn = df.loc[mn, "gdc_impressions_sum"]
            imp_ma = df.loc[ma, "gdc_impressions_sum"].sum()

            if imp_mn > 0 and (imp_ma / imp_mn) >= IMPRESSION_RATIO_THRESHOLD:
                df = soma(df, mn, ma, METRIC_COLS)
                motivo = "Padrao 5 — Republicacao: metricas somadas no maior"
            else:
                motivo = "Padrao 6 — Republicacao: removido sem somar (impressoes insignificantes)"

            for idx in ma:
                log_remove(idx, motivo)

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
                log_remove(ma, f"Padrao 3/7 — Texto similar ({sim:.0%}): somado no maior impressao")

    todos_mantidos = set(df.index) - removidos_ids
    df_clean = df.loc[sorted(todos_mantidos)].reset_index(drop=True)
    df_log   = pd.DataFrame(log) if log else pd.DataFrame()

    print(f"   -{len(log)} removidas -> {len(df_clean)} restantes")
    print(f"   Redes: {df_clean['social_network'].value_counts().to_dict()}")

    return df_clean, df_log


# ---------------------------------------------------------------------------
# ETAPA 4 — CALCULAR ER E WEEK
# ---------------------------------------------------------------------------

def calc_er_week(df):
    df = df.copy()

    imp = df["gdc_impressions_sum"].replace(0, pd.NA)
    df["ER"] = (
        df["gdc_total_engagements_sum"].div(imp).multiply(100).fillna(0).round(2)
    )

    eng_wo = (
        df["post_likes_and_reactions_sum"]
        + df["post_comments_sum"]
        + df["post_shares_sum"]
        + df["estimated_clicks_sum"]
    )
    _doc_mask = (
        (df["social_network"].str.lower() == "linkedin") &
        (df["media_type"].str.lower().isin({"document", "pdf"}))
    )
    er_wo = df["gdc_total_engagements_sum"].div(imp).multiply(100).fillna(0)
    er_wo[_doc_mask] = eng_wo[_doc_mask].div(imp[_doc_mask]).multiply(100).fillna(0)
    df["ER w/o swipes"] = er_wo.round(2)

    dates = pd.to_datetime(df["published_date"], errors="coerce")
    week_of_month = dates.dt.day.apply(lambda d: math.ceil(d / 7) if pd.notna(d) else pd.NA)
    df["Week"] = dates.dt.strftime("%Y%m").fillna("") + "-W" + week_of_month.astype("Int64").astype(str)
    df.loc[dates.isna(), "Week"] = ""

    return df


# ---------------------------------------------------------------------------
# ETAPA 5 — ATUALIZAR BASE HISTORICA
# ---------------------------------------------------------------------------

def update_base(df_new, base_path):
    base_path = Path(base_path)

    if not base_path.exists():
        df_new.to_csv(base_path, index=False, encoding="utf-8")
        print(f"   Base criada: {len(df_new)} linhas -> {base_path.name}")
        return

    df_base  = pd.read_csv(base_path, low_memory=False)

    for col_er in ["ER", "ER w/o swipes"]:
        if col_er in df_base.columns:
            df_base[col_er] = pd.to_numeric(
                df_base[col_er].astype(str)
                    .str.replace("%", "", regex=False)
                    .str.replace(",", ".", regex=False),
                errors="coerce",
            ).fillna(0)

    df_new["permalink"]  = df_new["permalink"].astype(str).str.strip()
    df_base["permalink"] = df_base["permalink"].astype(str).str.strip()

    existing    = set(df_base["permalink"])
    mask_update = df_new["permalink"].isin(existing)
    df_upd  = df_new[mask_update].copy()
    df_novo = df_new[~mask_update].copy()

    cols_update = [c for c in METRIC_COLS + ["ER", "ER w/o swipes", "Week"] if c in df_new.columns]

    if not df_upd.empty:
        upd_map = df_upd.set_index("permalink")[cols_update].to_dict("index")
        for i, row in df_base.iterrows():
            plink = row["permalink"]
            if plink in upd_map:
                for col in cols_update:
                    df_base.at[i, col] = upd_map[plink][col]

    if not df_novo.empty:
        for col in df_base.columns:
            if col not in df_novo.columns:
                df_novo[col] = ""
        df_novo = df_novo[df_base.columns]
        df_base = pd.concat([df_base, df_novo], ignore_index=True)

    df_base.to_csv(base_path, index=False, encoding="utf-8")
    print(f"   {len(df_upd)} atualizadas | {len(df_novo)} novas | total {len(df_base)} linhas ({base_path.name})")


# ---------------------------------------------------------------------------
# ETAPA 6 — GERAR EXCEL SEMANAL
# ---------------------------------------------------------------------------

def generate_output(df_clean, df_log, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_clean.to_excel(writer, sheet_name="RAW DATA", index=False)
        if len(df_log) > 0:
            df_log.to_excel(writer, sheet_name="REMOVED", index=False)
        else:
            pd.DataFrame({"mensagem": ["Nenhuma linha foi removida."]}).to_excel(
                writer, sheet_name="REMOVED", index=False
            )

    csv_path = output_path.with_suffix(".csv")
    df_clean.to_csv(csv_path, index=False, encoding="utf-8")

    print(f"   Dashboard pronto em: {csv_path}")
    print(f"   Arquivo gerado: {output_path}")
    print(f"   Aba RAW DATA: {len(df_clean)} linhas")
    print(f"   Aba REMOVED:  {len(df_log)} linhas removidas")


# ---------------------------------------------------------------------------
# EXECUCAO PRINCIPAL
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("\n=== PIPELINE SOCIAL ANALYTICS ===\n")

    print("1) Lendo CSV Sprinklr...")
    df = read_sprinklr(SPRINKLR_CSV)

    print("\n2) Merge com Meta...")
    df = merge_meta(df, META_CSV)

    print("\n3) Limpeza...")
    df = clean_sprinklr(df)

    print("\n4) Deduplicacao...")
    df, df_log = deduplicate(df)

    print("\n5) Calculando ER e Week...")
    df = calc_er_week(df)

    print("\n6) Gerando Excel semanal...")
    generate_output(df, df_log, OUTPUT_NAME)

    print("\n7) Atualizando base historica...")
    update_base(df, BASE_PATH)

    print("\n=== CONCLUIDO ===\n")
