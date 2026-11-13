from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from coleta import executar_coleta

st.set_page_config(
    page_title="Dashboard Climático — Capitais Brasileiras",
    page_icon="🌍",
    layout="wide",
)

MESES_NOMES = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}

ARQ_DIARIO = Path("dados/dados_diarios_capitais_1980_2025.csv")
ARQ_ANUAL = Path("dados/resumo_anual_capitais_1980_2025.csv")


@st.cache_data
def carregar_bases():
    if not ARQ_DIARIO.exists() or not ARQ_ANUAL.exists():
        executar_coleta()
    df_d = pd.read_csv(ARQ_DIARIO, parse_dates=["data"])
    df_a = pd.read_csv(ARQ_ANUAL)
    return df_d, df_a


st.title("🌍 Análise Histórica de Mudanças Climáticas no Brasil")
st.markdown(
    "Exploração interativa de séries históricas diárias de **temperatura média** e **precipitação acumulada** "
    "obtidas via **Open-Meteo Archive API** (1980–2025)."
)

with st.spinner("Carregando base de dados climáticos..."):
    df_diario, df_anual = carregar_bases()

# --- BARRA LATERAL (ELEMENTOS INTERATIVOS) ---
st.sidebar.header("Filtros de Exploração")

cidades_disponiveis = sorted(df_anual["cidade"].unique())
cidade_selecionada = st.sidebar.selectbox(
    "1. Selecione a Capital:",
    options=cidades_disponiveis,
    index=cidades_disponiveis.index("São Paulo (SP)") if "São Paulo (SP)" in cidades_disponiveis else 0,
)

ano_min = int(df_anual["ano"].min())
ano_max = int(df_anual["ano"].max())
intervalo_anos = st.sidebar.slider(
    "2. Selecione o Intervalo de Anos:",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max),
    step=1,
)

meses_selecionados = st.sidebar.multiselect(
    "3. Filtrar Meses (Sazonalidade):",
    options=list(MESES_NOMES.keys()),
    default=list(MESES_NOMES.keys()),
    format_func=lambda m: MESES_NOMES[m],
)

exibir_tendencia = st.sidebar.checkbox("Exibir linha de tendência linear na temperatura", value=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    "**Nota metodológica:** Dados baseados em coordenadas centrais de cada capital (Open-Meteo Reanalysis). "
    "Totais anuais de chuva são exibidos apenas para anos com 100% de cobertura diária."
)

# --- FILTRAGEM DOS DADOS ---
if not meses_selecionados:
    st.warning("Selecione pelo menos um mês na barra lateral para visualizar os dados.")
    st.stop()

mask_diario = (
    (df_diario["cidade"] == cidade_selecionada)
    & (df_diario["ano"].between(intervalo_anos[0], intervalo_anos[1]))
    & (df_diario["mes"].isin(meses_selecionados))
)
df_d_filtrado = df_diario[mask_diario].copy()

mask_anual = (
    (df_anual["cidade"] == cidade_selecionada)
    & (df_anual["ano"].between(intervalo_anos[0], intervalo_anos[1]))
)
df_a_filtrado = df_anual[mask_anual].copy()

# Recalcula média anual caso o usuário tenha filtrado meses específicos
if len(meses_selecionados) < 12:
    df_a_exibicao = (
        df_d_filtrado.groupby("ano", as_index=False)
        .agg(
            temperatura_media_c=("temperatura_media_c", "mean"),
            precipitacao_total_mm=("precipitacao_mm", "sum"),
        )
    )
else:
    df_a_exibicao = df_a_filtrado[["ano", "temperatura_media_c", "precipitacao_total_mm"]].copy()

# --- CÁLCULO DE KPIS E TENDÊNCIA ---
temp_media_periodo = df_d_filtrado["temperatura_media_c"].mean()
precip_media_anual = df_a_exibicao["precipitacao_total_mm"].mean()

serie_temp = df_a_exibicao.dropna(subset=["temperatura_media_c"]).copy()
tendencia_decada = np.nan
r2 = np.nan
tendencia_y = None

if len(serie_temp) >= 2:
    x = serie_temp["ano"].to_numpy(dtype=float)
    y = serie_temp["temperatura_media_c"].to_numpy(dtype=float)
    inclinacao, intercepto = np.polyfit(x, y, 1)
    tendencia_y = inclinacao * x + intercepto
    tendencia_decada = inclinacao * 10
    if len(y) > 2 and not np.isclose(y.var(), 0):
        r2 = 1 - np.sum((y - tendencia_y) ** 2) / np.sum((y - y.mean()) ** 2)

ano_mais_quente = (
    serie_temp.loc[serie_temp["temperatura_media_c"].idxmax()]
    if not serie_temp.empty else None
)

# --- EXIBIÇÃO DOS KPIS ---
st.subheader(f"Indicadores Principais — {cidade_selecionada} ({intervalo_anos[0]}–{intervalo_anos[1]})")
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="Temperatura Média no Período",
    value=f"{temp_media_periodo:.2f} °C" if pd.notna(temp_media_periodo) else "N/D",
)

col2.metric(
    label="Tendência Térmica",
    value=f"{tendencia_decada:+.3f} °C/década" if pd.notna(tendencia_decada) else "N/D",
    delta=f"R² = {r2:.3f}" if pd.notna(r2) else None,
    delta_color="off",
)

col3.metric(
    label="Precipitação Média Anual",
    value=f"{precip_media_anual:,.1f} mm" if pd.notna(precip_media_anual) else "N/D",
)

col4.metric(
    label="Ano Mais Quente no Recorte",
    value=f"{int(ano_mais_quente['ano'])} ({ano_mais_quente['temperatura_media_c']:.2f} °C)"
    if ano_mais_quente is not None else "N/D",
)

st.markdown("---")

# --- GRÁFICO 1: TEMPERATURA MÉDIA ANUAL ---
st.subheader("1. Evolução da Temperatura Média Anual")
st.caption(
    "Acompanhamento da temperatura média anual ao longo do período selecionado, com reta de regressão linear "
    "para evidenciar a taxa de aquecimento ou resfriamento por década."
)

fig_temp = px.line(
    serie_temp,
    x="ano",
    y="temperatura_media_c",
    markers=True,
    labels={"ano": "Ano", "temperatura_media_c": "Temperatura Média (°C)"},
)
fig_temp.update_traces(name="Temperatura Média", showlegend=True, line=dict(color="#EF553B", width=2.5))

if exibir_tendencia and tendencia_y is not None:
    fig_temp.add_trace(
        go.Scatter(
            x=serie_temp["ano"],
            y=tendencia_y,
            mode="lines",
            name=f"Tendência Linear ({tendencia_decada:+.3f} °C/década)",
            line=dict(color="#1F2937", dash="dash", width=2),
        )
    )

fig_temp.update_layout(hovermode="x unified", height=420, margin=dict(t=20, b=20))
st.plotly_chart(fig_temp, use_container_width=True)

# --- GRÁFICOS 2 E 3: PRECIPITAÇÃO E SAZONALIDADE ---
col_esq, col_dir = st.columns(2)

with col_esq:
    st.subheader("2. Precipitação Acumulada Anual")
    st.caption(
        "Volume total de chuva registrado por ano (em milímetros). Permite identificar anos de seca severa "
        "(como 2014 no Sudeste) ou eventos extremos de pluviosidade."
    )
    serie_precip = df_a_exibicao.dropna(subset=["precipitacao_total_mm"]).copy()
    fig_precip = px.bar(
        serie_precip,
        x="ano",
        y="precipitacao_total_mm",
        labels={"ano": "Ano", "precipitacao_total_mm": "Precipitação Acumulada (mm)"},
        color_discrete_sequence=["#3B82F6"],
    )
    fig_precip.update_layout(hovermode="x unified", height=380, margin=dict(t=20, b=20))
    st.plotly_chart(fig_precip, use_container_width=True)

with col_dir:
    st.subheader("3. Sazonalidade Mensal da Chuva")
    st.caption(
        "Média diária de precipitação agrupada por mês no intervalo selecionado, evidenciando o regime "
        "de estiagem e o período chuvoso característico da capital."
    )
    mensal = (
        df_d_filtrado.groupby("mes", as_index=False)
        .agg(
            temperatura_media_c=("temperatura_media_c", "mean"),
            precipitacao_media_diaria_mm=("precipitacao_mm", "mean"),
        )
    )
    mensal["mes_nome"] = mensal["mes"].map(MESES_NOMES)

    fig_mensal = px.bar(
        mensal,
        x="mes_nome",
        y="precipitacao_media_diaria_mm",
        labels={"mes_nome": "Mês", "precipitacao_media_diaria_mm": "Média Diária (mm)"},
        color_discrete_sequence=["#10B981"],
    )
    fig_mensal.update_layout(height=380, margin=dict(t=20, b=20))
    st.plotly_chart(fig_mensal, use_container_width=True)

# --- TABELA DE DADOS PROCESSADOS ---
with st.expander("Visualizar tabela de dados anuais processados"):
    st.dataframe(
        df_a_filtrado.round(2),
        use_container_width=True,
        hide_index=True,
    )
