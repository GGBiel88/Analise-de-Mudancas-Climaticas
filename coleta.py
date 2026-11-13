from pathlib import Path
import re
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL_API = "https://archive-api.open-meteo.com/v1/archive"

CIDADES = {
    "São Paulo (SP)": {"latitude": -23.5505, "longitude": -46.6333},
    "Rio de Janeiro (RJ)": {"latitude": -22.9068, "longitude": -43.1729},
    "Brasília (DF)": {"latitude": -15.7801, "longitude": -47.9292},
    "Manaus (AM)": {"latitude": -3.1190, "longitude": -60.0217},
    "Porto Alegre (RS)": {"latitude": -30.0346, "longitude": -51.2177},
    "Salvador (BA)": {"latitude": -12.9714, "longitude": -38.5014},
    "Fortaleza (CE)": {"latitude": -3.7319, "longitude": -38.5267},
}

ANO_INICIO = 1980
ANO_FIM = 2025
FUSO_HORARIO = "America/Sao_Paulo"
MIN_COBERTURA_TEMPERATURA = 90.0
MIN_COBERTURA_PRECIPITACAO = 100.0


def criar_sessao() -> requests.Session:
    """Cria sessão HTTP com tentativas automáticas para erros temporários."""
    tentativas = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adaptador = HTTPAdapter(max_retries=tentativas)
    sessao = requests.Session()
    sessao.mount("https://", adaptador)
    return sessao


def carregar_dados_clima(
    sessao: requests.Session,
    cidade: str,
    latitude: float,
    longitude: float,
    data_inicio: str,
    data_fim: str,
    timezone: str,
) -> pd.DataFrame:
    parametros = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": data_inicio,
        "end_date": data_fim,
        "daily": ["temperature_2m_mean", "precipitation_sum"],
        "timezone": timezone,
    }

    resposta = sessao.get(URL_API, params=parametros, timeout=(10, 90))
    resposta.raise_for_status()
    dados = resposta.json()

    if "daily" not in dados or not dados["daily"].get("time"):
        raise ValueError(f"A API não retornou dados diários para {cidade}.")

    diario = dados["daily"]
    df = pd.DataFrame(
        {
            "cidade": cidade,
            "data": pd.to_datetime(diario["time"], errors="coerce"),
            "temperatura_media_c": diario["temperature_2m_mean"],
            "precipitacao_mm": diario["precipitation_sum"],
        }
    )

    df = df.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)
    df["ano"] = df["data"].dt.year
    df["mes"] = df["data"].dt.month

    for coluna in ["temperatura_media_c", "precipitacao_mm"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    return df


def processar_resumo_anual(df: pd.DataFrame, data_inicio: str, data_fim: str) -> pd.DataFrame:
    dias_esperados = (
        pd.date_range(data_inicio, data_fim, freq="D")
        .to_series()
        .groupby(lambda d: d.year)
        .size()
        .rename("dias_esperados")
    )

    cobertura = df.groupby(["cidade", "ano"]).agg(
        dias_retornados=("data", "nunique"),
        dias_com_temperatura=("temperatura_media_c", "count"),
        dias_com_precipitacao=("precipitacao_mm", "count"),
    )
    cobertura = cobertura.join(dias_esperados, on="ano")
    cobertura["cobertura_temperatura_pct"] = (
        100 * cobertura["dias_com_temperatura"] / cobertura["dias_esperados"]
    )
    cobertura["cobertura_precipitacao_pct"] = (
        100 * cobertura["dias_com_precipitacao"] / cobertura["dias_esperados"]
    )

    anual = df.groupby(["cidade", "ano"]).agg(
        temperatura_media_c=("temperatura_media_c", "mean"),
        precipitacao_total_bruta_mm=("precipitacao_mm", "sum"),
    ).join(cobertura)

    anual["temperatura_media_c"] = anual["temperatura_media_c"].where(
        anual["cobertura_temperatura_pct"] >= MIN_COBERTURA_TEMPERATURA
    )
    anual["precipitacao_total_mm"] = anual["precipitacao_total_bruta_mm"].where(
        anual["cobertura_precipitacao_pct"] >= MIN_COBERTURA_PRECIPITACAO
    )

    return anual.reset_index()


def executar_coleta():
    pasta_saida = Path("dados")
    pasta_saida.mkdir(parents=True, exist_ok=True)

    data_inicio = f"{ANO_INICIO}-01-01"
    data_fim = f"{ANO_FIM}-12-31"

    lista_diarios = []
    lista_anuais = []

    with criar_sessao() as sessao:
        for cidade, coords in CIDADES.items():
            print(f"Coletando dados de {cidade} ({ANO_INICIO}-{ANO_FIM})...")
            df_cidade = carregar_dados_clima(
                sessao,
                cidade,
                coords["latitude"],
                coords["longitude"],
                data_inicio,
                data_fim,
                FUSO_HORARIO,
            )
            df_anual_cidade = processar_resumo_anual(df_cidade, data_inicio, data_fim)

            lista_diarios.append(df_cidade)
            lista_anuais.append(df_anual_cidade)

    df_diario_completo = pd.concat(lista_diarios, ignore_index=True)
    df_anual_completo = pd.concat(lista_anuais, ignore_index=True)

    arq_diario = pasta_saida / f"dados_diarios_capitais_{ANO_INICIO}_{ANO_FIM}.csv"
    arq_anual = pasta_saida / f"resumo_anual_capitais_{ANO_INICIO}_{ANO_FIM}.csv"

    df_diario_completo.to_csv(arq_diario, index=False, encoding="utf-8-sig")
    df_anual_completo.to_csv(arq_anual, index=False, encoding="utf-8-sig")

    print("\nColeta e processamento concluídos com sucesso!")
    print(f"- {arq_diario} ({len(df_diario_completo):,} registros)")
    print(f"- {arq_anual} ({len(df_anual_completo):,} registros)")


if __name__ == "__main__":
    executar_coleta()
