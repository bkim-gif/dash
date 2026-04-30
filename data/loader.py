"""
data/loader.py
==============
Responsável por:
1. Ler o CSV/Excel do RAW DATA gerado pelo pipeline
2. Normalizar tipos e calcular métricas derivadas (ER, AQE)
3. Aplicar os filtros da sidebar
4. Calcular o período anterior (para deltas dos KPI cards)

COMO TROCAR A FONTE NO FUTURO:
  Só mexa nas funções _load_*  —  o resto do dashboard não muda.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
import streamlit as st
from config import AQE_COLS, FY_START, FY_END


# ---------------------------------------------------------------------------
# CONFIGURAÇÃO — edite o caminho do seu arquivo aqui
# ---------------------------------------------------------------------------
DATA_PATH = Path(__file__).parent.parent / "MSFT_Revised_2026 - RAW DATA (1).csv"

# ---------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL — chamada pelo app.py
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)   # Cache de 1h: evita reler o arquivo a cada interação
def load_raw() -> pd.DataFrame:
    """
    Lê e normaliza o RAW DATA.
    O @st.cache_data guarda o resultado em memória —
    só relê o arquivo se ele mudar ou após 1 hora.
    """
    df = _load_file(DATA_PATH)
    df = _normalize(df)
    return df


def apply_filters(
    df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
    networks: list[str],
    pillars: list[str],
    media_types: list[str],
    campaigns: list[str],
) -> pd.DataFrame:
    """
    Aplica todos os filtros da sidebar.
    Retorna o DataFrame filtrado.

    Por que separado do load?
    Porque o cache guarda os dados brutos uma vez,
    e os filtros rodam rápido em memória a cada interação.
    """
    mask = (
        (df["published_date"] >= date_start) &
        (df["published_date"] <= date_end)
    )

    if networks:
        mask &= df["social_network"].isin(networks)

    if pillars:
        mask &= df["Pillars"].isin(pillars)

    if media_types:
        mask &= df["media_format_outbound_message"].isin(media_types)

    if campaigns:
        mask &= df["campaign_name"].isin(campaigns)

    return df[mask].copy()


def get_previous_period(
    df: pd.DataFrame,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
) -> pd.DataFrame:
    """
    Retorna o DataFrame do período anterior de mesmo tamanho.
    Usado para calcular os deltas (▲▼) dos KPI cards.

    Exemplo: se o período atual é Jan 6–12 (7 dias),
    o período anterior será Dez 30–Jan 5 (7 dias).
    """
    delta = date_end - date_start
    prev_end   = date_start - pd.Timedelta(days=1)
    prev_start = prev_end - delta

    mask = (
        (df["published_date"] >= prev_start) &
        (df["published_date"] <= prev_end)
    )
    return df[mask].copy()


def get_fy_monthly(df_all: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa todos os dados por mês para o gráfico de pacing FY.
    Posts com Boosted=1 são excluídos (não contam para a meta orgânica).
    Retorna uma linha por mês com total de impressões e posts.
    """
    fy_mask = (
        (df_all["published_date"] >= pd.Timestamp(FY_START)) &
        (df_all["published_date"] <= pd.Timestamp(FY_END))
    )
    # Exclui posts boosted do pacing
    if "Boosted" in df_all.columns:
        fy_mask &= df_all["Boosted"].fillna(0) != 1
    df_fy = df_all[fy_mask].copy()
    df_fy["month"] = df_fy["published_date"].dt.to_period("M")

    monthly = df_fy.groupby("month").agg(
        impressions=("gdc_impressions_sum", "sum"),
        posts=("outbound_post", "count"),
    ).reset_index()

    monthly["month_dt"] = monthly["month"].dt.to_timestamp()
    monthly = monthly.sort_values("month_dt")
    monthly["cumulative"] = monthly["impressions"].cumsum()

    return monthly


# ---------------------------------------------------------------------------
# FUNÇÕES INTERNAS
# ---------------------------------------------------------------------------
def _load_file(path: Path) -> pd.DataFrame:
    """Detecta o formato e lê o arquivo."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        for enc in ["utf-8", "utf-8-sig", "latin-1"]:
            try:
                return pd.read_csv(path, encoding=enc, low_memory=False)
            except UnicodeDecodeError:
                continue
    elif suffix in [".xlsx", ".xls"]:
        return pd.read_excel(path, sheet_name="RAW DATA")
    raise ValueError(f"Formato não suportado: {suffix}")


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza tipos, calcula ER e AQE.
    Esta função é o 'contrato' entre os dados brutos e o dashboard:
    garante que as colunas esperadas existam com os tipos corretos.
    """
    df = df.copy()

    # ── Normalização de nomes de colunas gerados pelo pipeline ─────────────
    # O pipeline aplica normalize_col() que lowercaseia tudo.
    # Estas colunas precisam de capitalização específica no dashboard.
    if "pillars" in df.columns and "Pillars" not in df.columns:
        df = df.rename(columns={"pillars": "Pillars"})
    if "boosted" in df.columns and "Boosted" not in df.columns:
        df = df.rename(columns={"boosted": "Boosted"})

    # ── Datas ──────────────────────────────────────────────────────────────
    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
    df = df.dropna(subset=["published_date"])

    # ── Colunas de texto ───────────────────────────────────────────────────
    for col in ["social_network", "Pillars", "media_format_outbound_message",
                "media_type",
                "campaign_name", "outbound_post", "permalink",
                "msft_learn_primary_audience_outbound_message"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str).str.strip()

    # "Unknown" para pilares e media type vazios (facilita filtro na sidebar)
    df["Pillars"] = df["Pillars"].replace("", "Unknown")
    df["media_format_outbound_message"] = df["media_format_outbound_message"].replace("", "Unknown")

    # ── Métricas numéricas ─────────────────────────────────────────────────
    num_cols = [
        "gdc_impressions_sum",
        "gdc_total_engagements_sum",
        "post_likes_and_reactions_sum",
        "post_comments_sum",
        "post_shares_sum",
        "estimated_clicks_sum",
        "Boosted",
    ]
    for col in num_cols:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ── ER — Engagement Rate ───────────────────────────────────────────────
    # Fórmula: Total Engagements / Impressions * 100
    # Evita divisão por zero com where()
    df["ER"] = (
        df["gdc_total_engagements_sum"]
        .div(df["gdc_impressions_sum"].replace(0, pd.NA))
        .multiply(100)
        .fillna(0)
        .round(2)
    )

    # ── ER w/o swipes — LinkedIn Document/Pdf posts ────────────────────────
    # Para posts do LinkedIn com media_type = 'Document' ou 'Pdf',
    # o engajamento exclui swipes e usa: likes + comments + shares + clicks.
    # Para todos os outros posts, usa gdc_total_engagements_sum (igual ao ER padrão).
    #
    # Para ajustar quais media_types são considerados "Document":
    #   mude os valores na lista abaixo (case-insensitive).
    _doc_types = {"document", "pdf"}
    _is_linkedin_doc = (
        (df["social_network"].str.lower() == "linkedin") &
        (df["media_type"].str.lower().isin(_doc_types))
    )
    df["engagement_wo_swipes"] = df["gdc_total_engagements_sum"].copy()
    df.loc[_is_linkedin_doc, "engagement_wo_swipes"] = (
        df.loc[_is_linkedin_doc, "post_likes_and_reactions_sum"]
        + df.loc[_is_linkedin_doc, "post_comments_sum"]
        + df.loc[_is_linkedin_doc, "post_shares_sum"]
        + df.loc[_is_linkedin_doc, "estimated_clicks_sum"]
    )
    df["ER_wo_swipes"] = (
        df["engagement_wo_swipes"]
        .div(df["gdc_impressions_sum"].replace(0, pd.NA))
        .multiply(100)
        .fillna(0)
        .round(2)
    )

    # ── AQE — Average Qualified Engagement ────────────────────────────────
    # Fórmula: comments + shares + clicks (por post, calculado ao agregar)
    # Aqui criamos a coluna de soma para uso nos cards Top/Bottom
    present = [c for c in AQE_COLS if c in df.columns]
    df["AQE"] = df[present].sum(axis=1)

    # ── Semana e mês para agrupamentos ────────────────────────────────────
    df["week"]  = df["published_date"].dt.to_period("W").dt.start_time
    df["month"] = df["published_date"].dt.to_period("M").dt.to_timestamp()

    return df
