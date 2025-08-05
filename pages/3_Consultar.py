import streamlit as st
from supabase import create_client, Client # Importação direta da biblioteca
from datetime import datetime
import pytz

# --- BLOCO DE CONEXÃO COM O SUPABASE ---
@st.cache_resource
def init_connection():
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    return create_client(url, key)

supabase = init_connection()
# ----------------------------------------

# --- FUNÇÃO PARA FORMATAR A DATA ---
def formatar_data_hora(data_str):
    """Converte a data do formato ISO do banco para o fuso de Brasília e formata para exibição."""
    if not data_str:
        return "N/A"
    try:
        # Pega a string de data antes do '+' que indica o fuso
        if '+' in data_str:
            data_str = data_str.split('+')[0]
        
        # Converte a string para um objeto datetime
        data_obj_utc = datetime.fromisoformat(data_str)
        
        # Define os fusos horários
        utc_tz = pytz.utc
        br_tz = pytz.timezone('America/Sao_Paulo')
        
        # Define que o objeto está em UTC e converte para o fuso de São Paulo
        data_obj_br = utc_tz.localize(data_obj_utc).astimezone(br_tz)
        
        # Formata para o padrão brasileiro
        return data_obj_br.strftime('%d/%m/%Y - %H:%M')
    except (ValueError, TypeError):
        # Se houver algum erro, retorna o valor original
        return data_str


def app():
    st.title("📋 Consulta de Registros")

    # Campo de busca por nome
    nome_busca = st.text_input("🔍 Buscar por nome", placeholder="Digite o nome completo ou parte dele")
    
    # Lista de municípios
    municipios_para = [
        "Abaetetuba", "Abel Figueiredo", "Acará", "Afuá", "Água Azul do Norte", "Alenquer", 
        "Almeirim", "Altamira", "Anajás", "Ananindeua", "Anapu", "Augusto Corrêa", 
        "Aurora do Pará", "Aveiro", "Bagre", "Baião", "Bannach", "Barcarena", "Belém", 
        "Belterra", "Benevides", "Bom Jesus do Tocantins", "Bonito", "Bragança", "Brasil Novo",
        "Brejo Grande do Araguaia", "Breu Branco", "Breves", "Bujaru", "Cachoeira do Arari", 
        "Cachoeira do Piriá", "Cametá", "Canaã dos Carajás", "Capanema", "Capitão Poço", 
        "Castanhal", "Chaves", "Colares", "Conceição do Araguaia", "Concórdia do Pará", 
        "Cumaru do Norte", "Curionópolis", "Curralinho", "Curuá", "Curuçá", "Dom Eliseu", 
        "Eldorado dos Carajás", "Faro", "Floresta do Araguaia", "Garrafão do Norte", 
        "Goianésia do Pará", "Gurupá", "Igarapé-Açu", "Igarapé-Miri", "Inhangapi", "Ipixuna do Pará", 
        "Irituia", "Itaituba", "Itupiranga", "Jacareacanga", "Jacundá", "Juruti", "Limoeiro do Ajuru",
        "Mãe do Rio", "Magalhães Barata", "Marabá", "Maracanã", "Marapanim", "Marituba", "Medicilândia", 
        "Melgaço", "Mocajuba", "Moju", "Monte Alegre", "Muaná", "Nova Esperança do Piriá", 
        "Nova Ipixuna", "Nova Timboteua", "Novo Progresso", "Novo Repartimento", "Óbidos", 
        "Oeiras do Pará", "Oriximiná", "Ourém", "Ourilândia do Norte", "Pacajá", "Palestina do Pará", 
        "Paragominas", "Parauapebas", "Pau D'Arco", "Peixe-Boi", "Piçarra", "Placas", 
        "Ponta de Pedras", "Portel", "Porto de Moz", "Prainha", "Primavera", "Quatipuru", 
        "Redenção", "Rio Maria", "Rondon do Pará", "Rurópolis", "Salinópolis", "Salvaterra", 
        "Santa Bárbara do Pará", "Santa Cruz do Arari", "Santa Isabel do Pará", "Santa Luzia do Pará", 
        "Santa Maria das Barreiras", "Santa Maria do Pará", "Santana do Araguaia", "Santarém", 
        "Santarém Novo", "Santo Antônio do Tauá", "São Caetano de Odivelas", "São Domingos do Araguaia",
        "São Domingos do Capim", "São Félix do Xingu", "São Francisco do Pará", "São Geraldo do Araguaia", 
        "São João da Ponta", "São João de Pirabas", "São João do Araguaia", "São Miguel do Guamá", 
        "São Sebastião da Boa Vista", "Sapucaia", "Senador José Porfírio", "Soure", "Tailândia", 
        "Terra Alta", "Terra Santa", "Tomé-Açu", "Tracuateua", "Trairão", "Tucumã", "Tucuruí", 
        "Ulianópolis", "Uruará", "Vigia", "Viseu", "Vitória do Xingu", "Xinguara"
    ]
    
    # Filtros avançados
    with st.expander("Filtros Avançados", expanded=False):
        municipio_filtro = st.selectbox("Filtrar por Município", ["Todos"] + municipios_para)
        tipo_pessoa_filtro = st.selectbox("Filtrar por Tipo de Pessoa", ["Todos", "Com vínculo", "Candidato", "Liderança"])
        tipo_ajuda_filtro = st.selectbox("Filtrar por Tipo de Ajuda (Principal)", ["Todos", "Dinheiro", "Cesta Básica", "CredCidadão", "Consulta Médica", "Consulta Odontológica", "Cirurgia Médica", 
            "CredMoradia","Exames Laboratoriais", "Emprego", "Internação Hospitalar", "Transporte/Passagem", "Outros"])

    st.markdown("---")

    # Botão para realizar a busca
    if st.button("Buscar", type="primary"):
        try:
            query = supabase.table('ajuda').select('*, ajuda_extra(*)').order('nome', desc=False)

            if nome_busca.strip():
                query = query.ilike('nome', f'%{nome_busca.strip()}%')
            
            if municipio_filtro != "Todos":
                query = query.eq('municipio', municipio_filtro)
            
            if tipo_pessoa_filtro != "Todos":
                query = query.eq('tipo_pessoa', tipo_pessoa_filtro)
            
            if tipo_ajuda_filtro != "Todos":
                query = query.eq('tipo_ajuda', tipo_ajuda_filtro)
            
            response = query.execute()
            resultados = response.data

            if not resultados:
                st.error("Nenhum registro encontrado para os critérios informados.")
            else:
                st.success(f"{len(resultados)} registro(s) encontrado(s).")
                st.markdown("---")

                for dados in resultados:
                    with st.container(border=True):
                        st.markdown(f"### {dados.get('nome', 'Nome não informado')}")
                        
                        data_formatada = formatar_data_hora(dados.get('data_hora'))
                        st.write(f"**Cadastro realizado em:** {data_formatada}")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Tipo de Pessoa:** {dados.get('tipo_pessoa', 'N/A')}")
                            if dados.get('tipo_pessoa') == "Com vínculo":
                                st.write(f"**Vínculo:** {dados.get('vinculo_descricao', 'N/A')}")
                            if dados.get('tipo_pessoa') == "Liderança":
                                st.write(f"**Candidato:** {dados.get('candidato_lideranca', 'N/A')}")
                        with col2:
                            st.write(f"**Município:** {dados.get('municipio', 'N/A')}")
                        with col3:
                            st.write(f"**Telefone:** {dados.get('telefone', 'N/A')}")
                        
                        st.markdown("---")
                        st.markdown("**Assistência Principal:**")
                        
                        valor_principal = float(dados.get('valor', 0.0))
                        valor_formatado_principal = f"R$ {valor_principal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        
                        st.write(f"- **Tipo:** {dados.get('tipo_ajuda', 'N/A')}")
                        if dados.get('descricao_outros'):
                            st.write(f"- **Descrição:** {dados.get('descricao_outros')}")
                        st.write(f"- **Quantidade:** {dados.get('quantidade', 0)}")
                        st.write(f"- **Valor:** {valor_formatado_principal}")
                        
                        if dados.get('detalhes'):
                            st.markdown("**Detalhes Adicionais:**")
                            st.info(f"{dados.get('detalhes')}")
                        
                        ajudas_extras = dados.get('ajuda_extra', [])
                        if ajudas_extras:
                            with st.expander(f"Ajudas Extras ({len(ajudas_extras)})", expanded=False):
                                for ajuda in ajudas_extras:
                                    st.markdown("---")
                                    valor_extra = float(ajuda.get('valor', 0.0))
                                    valor_formatado_extra = f"R$ {valor_extra:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                                    
                                    st.write(f"**Tipo de Ajuda:** {ajuda.get('tipo_ajuda', 'N/A')}")
                                    if ajuda.get('descricao_outros'):
                                        st.write(f"**Descrição:** {ajuda.get('descricao_outros')}")
                                    st.write(f"**Quantidade:** {ajuda.get('quantidade', 0)}")
                                    st.write(f"**Valor:** {valor_formatado_extra}")

                                    data_extra_formatada = formatar_data_hora(ajuda.get('data_hora'))
                                    st.write(f"**Adicionado em:** {data_extra_formatada}")
                        else:
                            st.info("Nenhuma ajuda extra registrada para esta pessoa.")
                    st.markdown("---")

        except Exception as e:
            st.error("Ocorreu um erro ao buscar os registros no banco de dados.")
            st.error(f"Detalhes do erro: {e}")

# Executa a função principal do app
app()