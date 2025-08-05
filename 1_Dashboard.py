import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_echarts import st_echarts

# --- Configurações do Supabase ---
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- Função para Carregar Dados (com cache) ---
@st.cache_data(ttl=600)
def get_data():
    response_ajuda = supabase.from_('ajuda').select('*').execute()
    df_ajuda = pd.DataFrame(response_ajuda.data)

    response_ajuda_extra = supabase.from_('ajuda_extra').select('*').execute()
    df_ajuda_extra = pd.DataFrame(response_ajuda_extra.data)

    if not df_ajuda.empty:
        df_ajuda['data_hora'] = pd.to_datetime(df_ajuda['data_hora'])

    if not df_ajuda_extra.empty:
        df_ajuda_extra['data_hora'] = pd.to_datetime(df_ajuda_extra['data_hora'])

    return df_ajuda, df_ajuda_extra

df_ajuda, df_ajuda_extra = get_data()

# --- Pré-processamento e Mesclagem ---
if not df_ajuda.empty:
    df_ajuda_unified = df_ajuda[['id', 'municipio', 'tipo_pessoa', 'tipo_ajuda', 'descricao_outros', 'detalhes', 'quantidade', 'valor', 'data_hora']].copy()
    df_ajuda_unified['origem'] = 'Principal'
else:
    df_ajuda_unified = pd.DataFrame()

if not df_ajuda_extra.empty:
    df_ajuda_extra_unified = df_ajuda_extra[['ajuda_id', 'municipio', 'tipo_pessoa', 'tipo_ajuda', 'descricao_outros', 'detalhes', 'quantidade', 'valor', 'data_hora']].copy()
    df_ajuda_extra_unified = df_ajuda_extra_unified.rename(columns={'ajuda_id': 'id'})
    df_ajuda_extra_unified['origem'] = 'Extra'
else:
    df_ajuda_extra_unified = pd.DataFrame()

df_total_ajudas = pd.concat([df_ajuda_unified, df_ajuda_extra_unified], ignore_index=True)

# --- Título e Filtros ---
st.title('Dashboard de Solicitações de Assistência 📊')
st.sidebar.header('Filtros')

if df_ajuda.empty and df_total_ajudas.empty:
    st.warning("Não há dados para exibir.")
    st.stop()

# --- Lógica de Filtros ---
df_ajuda_filtrado = df_ajuda.copy()
df_total_ajudas_filtrado = df_total_ajudas.copy()

# Filtro por Município
municipios_disponiveis = ['Todos'] + sorted(df_ajuda_filtrado['municipio'].unique().tolist())
municipio_selecionado = st.sidebar.selectbox('Filtrar por Município', municipios_disponiveis)
if municipio_selecionado != 'Todos':
    df_ajuda_filtrado = df_ajuda_filtrado[df_ajuda_filtrado['municipio'] == municipio_selecionado]
    ids_filtrados = df_ajuda_filtrado['id'].unique()
    df_total_ajudas_filtrado = df_total_ajudas_filtrado[df_total_ajudas_filtrado['id'].isin(ids_filtrados)]

# Filtro por Tipo de Pessoa
tipos_pessoa_disponiveis = ['Todos'] + sorted(df_ajuda_filtrado['tipo_pessoa'].unique().tolist())
tipo_pessoa_selecionada = st.sidebar.selectbox('Filtrar por Tipo de Pessoa', tipos_pessoa_disponiveis)
if tipo_pessoa_selecionada != 'Todos':
    df_ajuda_filtrado = df_ajuda_filtrado[df_ajuda_filtrado['tipo_pessoa'] == tipo_pessoa_selecionada]
    ids_filtrados = df_ajuda_filtrado['id'].unique()
    df_total_ajudas_filtrado = df_total_ajudas_filtrado[df_total_ajudas_filtrado['id'].isin(ids_filtrados)]

# Filtro por Tipo de Assistência
tipos_ajuda_disponiveis = ['Todos'] + sorted(df_total_ajudas_filtrado['tipo_ajuda'].unique().tolist())
tipo_ajuda_selecionado = st.sidebar.selectbox("Filtrar por Tipo de Assistência", tipos_ajuda_disponiveis)
if tipo_ajuda_selecionado != "Todos":
    df_total_ajudas_filtrado = df_total_ajudas_filtrado[df_total_ajudas_filtrado['tipo_ajuda'] == tipo_ajuda_selecionado]
    ids_filtrados_total = df_total_ajudas_filtrado['id'].unique()
    df_ajuda_filtrado = df_ajuda_filtrado[df_ajuda_filtrado['id'].isin(ids_filtrados_total)]


# --- KPIs ---
st.markdown("---")
st.header("Métricas Principais")
col1, col2, col3 = st.columns(3)

with col1:
    # --- MÉTRICA ATUALIZADA ---
    # Calcula o número de municípios únicos no dataframe filtrado
    municipios_atendidos = df_ajuda_filtrado['municipio'].nunique()
    st.metric(label="Municípios Atendidos", value=municipios_atendidos)

with col2:
    valor_total_solicitado = df_total_ajudas_filtrado['valor'].sum() if not df_total_ajudas_filtrado.empty else 0
    st.metric(label="Valor Total de Assistência", value=f"R$ {valor_total_solicitado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

with col3:
    quantidade_total_itens = df_total_ajudas_filtrado['quantidade'].sum() if not df_total_ajudas_filtrado.empty else 0
    st.metric(label="Quantidade Total de Assistência", value=int(quantidade_total_itens))

# --- Gráficos com ECharts ---
st.markdown("---")
st.header("Análises Detalhadas")
col_grafico1, col_grafico2 = st.columns(2)

with col_grafico1:
    st.subheader("Solicitações por Município")
    if not df_ajuda_filtrado.empty:
        df_municipio = df_ajuda_filtrado['municipio'].value_counts().reset_index()
        df_municipio.columns = ['Município', 'Número de Solicitações']
        options_bar = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": [{"type": "category", "data": df_municipio['Município'].tolist(), "axisTick": {"alignWithLabel": True}, "axisLabel": {"interval": 0, "rotate": 30}}],
            "yAxis": [{"type": "value"}],
            "series": [{"name": "Solicitações", "type": "bar", "barWidth": "60%", "data": df_municipio['Número de Solicitações'].tolist()}],
        }
        st_echarts(options=options_bar, height="400px")
    else:
        st.info("Nenhum dado de município para exibir.")

with col_grafico2:
    st.subheader("Quantidade por Tipo de Serviço")
    if not df_total_ajudas_filtrado.empty:
        df_servicos = df_total_ajudas_filtrado['tipo_ajuda'].value_counts().reset_index()
        df_servicos.columns = ['Tipo de Serviço', 'Quantidade']
        data_pie = [{"value": row['Quantidade'], "name": row['Tipo de Serviço']} for index, row in df_servicos.iterrows()]
        options_pie = {
            "tooltip": {"trigger": "item"},
            "legend": {"orient": "vertical", "left": "left"},
            "series": [{"name": "Serviços Prestados", "type": "pie", "radius": "50%", "center": ['50%', '70%'], "data": data_pie, 
                        "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0, "shadowColor": "rgba(0, 0, 0, 0.5)"}}}],
        }
        st_echarts(options=options_pie, height="400px")
    else:
        st.info("Nenhum dado de tipo de ajuda para exibir.")

# --- GRÁFICO DE GASTOS GERAL ---
st.markdown("---")
st.header("Análise Financeira")

df_gastos = df_total_ajudas_filtrado[df_total_ajudas_filtrado['valor'] > 0]
if not df_gastos.empty:
    st.subheader("Valor Gasto por Tipo de Assistência")
    df_gastos_agrupado = df_gastos.groupby('tipo_ajuda')['valor'].sum().sort_values(ascending=False).reset_index()
    options_gastos_vertical = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "category", "data": df_gastos_agrupado['tipo_ajuda'].tolist(), "axisLabel": {"interval": 0, "rotate": 30}},
        "yAxis": {"type": "value", "axisLabel": {"formatter": "R$ {value}"}},
        "series": [{"name": "Valor Gasto (R$)", "type": "bar", "data": df_gastos_agrupado['valor'].tolist(),
                    "label": {"show": True, "position": "top", "formatter": ""}}],
    }
    st_echarts(options=options_gastos_vertical, height="400px")
else:
    st.info("Nenhum gasto registrado para os filtros selecionados.")

# --- GRÁFICO DE GASTOS COM CREDCIADÃO ---
st.markdown("---")
st.subheader("Gastos com CredCidadão por Município")

df_credcidadao = df_total_ajudas_filtrado[
    (df_total_ajudas_filtrado['tipo_ajuda'] == 'CredCidadão') &
    (df_total_ajudas_filtrado['valor'] > 0)
]

if not df_credcidadao.empty:
    df_gastos_credcidadao = df_credcidadao.groupby('municipio')['valor'].sum().sort_values(ascending=False).reset_index()
    options_credcidadao = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "category", "data": df_gastos_credcidadao['municipio'].tolist(), "axisLabel": {"interval": 0, "rotate": 45}},
        "yAxis": {"type": "value", "axisLabel": {"formatter": "R$ {value}"}},
        "series": [{"name": "Valor Gasto (R$)", "type": "bar", "data": df_gastos_credcidadao['valor'].tolist(),
                    "label": {"show": True, "position": "top", "formatter": ""}}],
    }
    st_echarts(options=options_credcidadao, height="500px")
else:
    st.info("Não foram encontrados gastos com CredCidadão para os filtros selecionados.")


st.markdown("---")
st.caption("Desenvolvido com Streamlit e Supabase")
