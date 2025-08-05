import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_echarts import st_echarts

st.set_page_config(layout="wide")

# --- BLOCO DE CONEXÃO COM O SUPABASE ---
@st.cache_resource
def init_connection():
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    return create_client(url, key)

supabase = init_connection()
# ----------------------------------------------------

st.title("📊 Análise Comparativa de Votos")
st.write(
    "Esta página compara os resultados do candidato principal com a performance dos demais candidatos em cada município."
)

# --- Carregando e Preparando os Dados da Tabela 'analise' ---
@st.cache_data(ttl=600)
def carregar_dados_eleitorais():
    # CORRIGIDO: Seleciona a coluna com seu nome correto 'total_de_votos'
    response = supabase.table('analise').select('municipio, nome_do_candidato, total_de_votos').execute()
    df = pd.DataFrame(response.data)
    
    if not df.empty:
        # CORRIGIDO: A etapa de renomeação foi removida.
        # Garante que a coluna de votos (com o nome correto) é numérica
        df['total_de_votos'] = pd.to_numeric(df['total_de_votos'], errors='coerce').fillna(0)
    
    return df

df_analise_completa = carregar_dados_eleitorais()

if df_analise_completa.empty:
    st.warning("A tabela 'analise' está vazia ou não pôde ser carregada.")
    st.stop()

st.markdown("---")

# --- Tabela Comparativa de Votos ---
st.header("Comparativo de Votos: Braselino vs. Outros Candidatos")

# 1. Separa os dados usando o nome do candidato
df_principal = df_analise_completa[df_analise_completa['nome_do_candidato'] == 'BRASELINO CARLOS DA ASSUNCAO SOUSA DA SILVA'].copy()
# CORRIGIDO: Usa 'total_de_votos' para a coluna de origem
df_principal = df_principal[['municipio', 'total_de_votos']].rename(columns={'total_de_votos': 'Votos Braselino'})

df_outros_candidatos = df_analise_completa[df_analise_completa['nome_do_candidato'] != 'BRASELINO CARLOS DA ASSUNCAO SOUSA DA SILVA'].copy()

if df_outros_candidatos.empty:
    st.warning("Não foram encontrados outros candidatos na tabela 'analise' para fazer a comparação.")
    st.write("Abaixo, a tabela de votos do candidato principal:")
    st.dataframe(df_principal, use_container_width=True, hide_index=True)
    st.stop()

# 2. Calcula as métricas do grupo de comparação
# CORRIGIDO: Usa 'total_de_votos' em todos os cálculos
idx_mais_votado = df_outros_candidatos.groupby('municipio')['total_de_votos'].idxmax()
outro_mais_votado = df_outros_candidatos.loc[idx_mais_votado][['municipio', 'nome_do_candidato', 'total_de_votos']]
outro_mais_votado.rename(columns={'total_de_votos': 'Votos Outro Candidato Top', 'nome_do_candidato': 'Nome Outro Candidato Top'}, inplace=True)

media_votos_outros = df_outros_candidatos.groupby('municipio')['total_de_votos'].mean().astype(int).reset_index()
media_votos_outros.rename(columns={'total_de_votos': 'Média Votos Outros'}, inplace=True)

# 3. Une tudo em uma tabela final de comparação
df_comparativo = pd.merge(df_principal, outro_mais_votado, on='municipio', how='left')
df_comparativo = pd.merge(df_comparativo, media_votos_outros, on='municipio', how='left')
df_comparativo['Votos Outro Candidato Top'] = df_comparativo['Votos Outro Candidato Top'].fillna(0)
df_comparativo['Média Votos Outros'] = df_comparativo['Média Votos Outros'].fillna(0)
df_comparativo.fillna('N/A', inplace=True) 

st.write("Tabela comparando a votação por município:")
st.dataframe(df_comparativo, use_container_width=True, hide_index=True)


# --- Gráfico Comparativo ---
st.markdown("---")
st.header("Visualização Comparativa")
st.subheader("Votos nos 15 Maiores Municípios (por Votação do Candidato Principal)")

df_grafico = df_comparativo.replace('N/A', 0).sort_values(by='Votos Braselino', ascending=False).head(15)

# Nenhuma alteração necessária aqui, pois já usa os nomes de coluna do df_comparativo
options_comparativo = {
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
    "legend": {"data": ["Votos Braselino", "Votos Outro Candidato Top", "Média Votos Outros"]},
    "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
    "xAxis": {"type": "value", "boundaryGap": [0, 0.01]},
    "yAxis": {"type": "category", "data": df_grafico['municipio'].tolist()[::-1]},
    "series": [
        {"name": "Votos Braselino", "type": "bar", "data": df_grafico['Votos Braselino'].tolist()[::-1]},
        {"name": "Votos Outro Candidato Top", "type": "bar", "data": df_grafico['Votos Outro Candidato Top'].tolist()[::-1]},
        {"name": "Média Votos Outros", "type": "bar", "data": df_grafico['Média Votos Outros'].tolist()[::-1]},
    ],
}
st_echarts(options=options_comparativo, height="600px")