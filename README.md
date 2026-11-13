# Análise Histórica de Mudanças Climáticas nas Capitais Brasileiras

Dashboard interativo desenvolvido para analisar séries históricas diárias de temperatura e precipitação de sete capitais brasileiras entre **1980 e 2025**, aplicando conceitos fundamentais de Ciência de Dados (coleta via API, armazenamento local, limpeza, validação de cobertura, análise estatística e visualização interativa).

---

## 1. Justificativa da Escolha do Tema

As mudanças climáticas e a variabilidade extrema de chuvas impactam diretamente o planejamento urbano, o abastecimento hídrico, a saúde pública e a infraestrutura das grandes cidades brasileiras. Este projeto busca tornar dados meteorológicos históricos acessíveis à população em geral e a gestores públicos, permitindo visualizar tendências de aquecimento por década e identificar anos atípicos de seca ou excesso de chuvas.

---

## 2. Fonte dos Dados (API)

Os dados são obtidos através da **Open-Meteo Historical Weather API (Archive)**, uma API pública e aberta que fornece séries históricas baseadas em modelos de reanálise meteorológica global (ERA5).

* **Endpoint utilizado:** `https://archive-api.open-meteo.com/v1/archive`
* **Cidades monitoradas:** São Paulo (SP), Rio de Janeiro (RJ), Brasília (DF), Manaus (AM), Porto Alegre (RS), Salvador (BA) e Fortaleza (CE).
* **Período coberto:** 01/01/1980 a 31/12/2025 (46 anos completos).

### Descrição das Variáveis Principais
* `cidade`: Nome e UF da capital analisada.
* `data`: Data do registro diário (`YYYY-MM-DD`).
* `temperatura_media_c`: Temperatura média diária a 2 metros do solo (°C).
* `precipitacao_mm`: Soma total de precipitação diária (mm).
* `ano` / `mes`: Colunas derivadas durante o tratamento para agregações temporais.
* `cobertura_temperatura_pct` / `cobertura_precipitacao_pct`: Percentual de dias válidos por ano (anos com menos de 100% de cobertura pluviométrica são filtrados para evitar subestimativas).

---

## 3. Perguntas-Chave Respondidas pelo Dashboard

1. **Há evidência de aumento na temperatura média anual das capitais brasileiras nas últimas quatro décadas?** (Respondida pelo gráfico de evolução térmica e pelo indicador de tendência em °C/década).
2. **Quais anos apresentaram os maiores picos de calor ou eventos extremos de seca/chuva em cada capital?** (Respondida pelos KPIs de destaque e pelo gráfico de precipitação acumulada anual).
3. **Como se comporta a sazonalidade das chuvas ao longo dos meses do ano em diferentes regiões do Brasil?** (Respondida pelo gráfico de precipitação média diária por mês, permitindo comparar, por exemplo, o verão chuvoso do Sudeste com o regime do Nordeste ou Norte).

---

## 4. Estrutura do Repositório

```text
projeto_analise_climatica/
├── coleta.py                                      # Script ETL: consulta a API, limpa os dados e salva os CSVs
├── app.py                                         # Aplicação web interativa (Dashboard em Streamlit + Plotly)
├── requirements.txt                               # Dependências do projeto
├── README.md                                      # Documentação do projeto
└── dados/
    ├── dados_diarios_capitais_1980_2025.csv       # Base diária tratada
    └── resumo_anual_capitais_1980_2025.csv        # Base agregada por ano com indicadores de cobertura
```

---

## 5. Como Executar o Projeto Localmente

### Pré-requisitos
* Python 3.10 ou superior instalado.

### Passo a passo

1. **Clone o repositório e acesse a pasta do projeto:**
   ```bash
   git clone https://github.com/GGBiel88/Analise-de-Mudancas-Climaticas
   cd projeto_analise_climatica
   ```

2. **Crie e ative um ambiente virtual (opcional, mas recomendado):**
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No Linux/macOS:
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute a coleta de dados (caso queira atualizar os arquivos locais):**
   ```bash
   python coleta.py
   ```
   *Observação: Os arquivos `.csv` já estão incluídos na pasta `dados/` para execução imediata.*

5. **Inicie o dashboard interativo:**
   ```bash
   streamlit run app.py
   ```
   O navegador abrirá automaticamente no endereço `http://localhost:8501`.

---

## 6. Capturas de Tela do Dashboard

### Visão Geral e KPIs (docs/print_kpis.png`)
![alt text](print_kpis.png)

### Análise Pluviométrica e Sazonalidade (docs/print_chuvas.png`)
![alt text](print_chuvas.png)
